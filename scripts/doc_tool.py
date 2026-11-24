"""Comprehensive document toolkit for Thai + English document generation, layout, conversion, and QA.

Subcommands:
  md2pdf    <in.md> <out.pdf> [--title TITLE] [--css CSS] [--landscape] [--fit-one-page] [--keep-html]
  html2pdf  <in.html> <out.pdf> [--wait-ms 0]
  md2docx   <in.md> <out.docx> [--font Sarabun] [--size 14]
  json2xlsx <in.json> <out.xlsx>
  json2pptx <in.json> <out.pptx> [--font Sarabun]
  pdf-info  <in.pdf> [--md]
  pdf2img   <in.pdf> <out_dir> [--dpi 150]
  pdf-audit <in.pdf> [--expect-pages N] [--out-dir DIR]
  pdf-merge <out.pdf> <in1.pdf> <in2.pdf> ...
  pdf-split <in.pdf> <out.pdf> --pages 1-3,5
"""
import argparse
import html
import json
import os
import re
import subprocess
import sys

CHROME_PATHS = [
    "/usr/bin/google-chrome",
    "/usr/bin/google-chrome-stable",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
]

SKILL_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DEFAULT_CSS_PATH = os.path.join(SKILL_DIR, "assets", "print_a4.css")

KATEX_MERMAID_HEAD = """
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.css">
<script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.js"></script>
<script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/contrib/auto-render.min.js"
  onload="renderMathInElement(document.body, {delimiters: [{left: '$$', right: '$$', display: true}, {left: '$', right: '$', display: false}]});"></script>
<script type="module">
  import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs';
  mermaid.initialize({ startOnLoad: true, theme: 'neutral' });
</script>
"""


def find_chrome():
    for path in CHROME_PATHS:
        if os.path.isfile(path):
            return path
    raise RuntimeError("Google Chrome not found in standard paths.")


def count_pdf_pages(pdf_path):
    try:
        import pymupdf
        with pymupdf.open(pdf_path) as doc:
            return len(doc)
    except Exception:
        data = open(pdf_path, "rb").read()
        return len(re.findall(rb"/Type\s*/Page[^s]", data))


def html_to_pdf(html_path, pdf_path, wait_ms=0, quiet=False):
    chrome = find_chrome()
    abs_html = os.path.abspath(html_path).replace("\\", "/")
    abs_pdf = os.path.abspath(pdf_path)
    os.makedirs(os.path.dirname(abs_pdf) or ".", exist_ok=True)
    cmd = [
        chrome,
        "--headless",
        "--disable-gpu",
        "--no-pdf-header-footer",
    ]
    if wait_ms > 0:
        cmd.append(f"--virtual-time-budget={wait_ms}")
    cmd.extend([f"--print-to-pdf={abs_pdf}", f"file:///{abs_html}"])
    subprocess.run(cmd, check=True, capture_output=True)
    pages = count_pdf_pages(abs_pdf)
    if not quiet:
        print(f"output={abs_pdf}\npages={pages}")
    return pages


def md_to_html_str(md_text, title="", css_path=None, landscape=False, zoom=1.0):
    import markdown

    css_file = css_path or DEFAULT_CSS_PATH
    css = open(css_file, encoding="utf-8-sig").read() if os.path.isfile(css_file) else ""

    # Convert ```mermaid fenced blocks into <pre class="mermaid"> before markdown parsing
    has_mermaid = "```mermaid" in md_text
    if has_mermaid:
        md_text = re.sub(
            r"```mermaid\s*\n(.*?)```",
            lambda m: f'<pre class="mermaid">\n{html.escape(m.group(1))}</pre>',
            md_text,
            flags=re.DOTALL,
        )
    has_math = "$$" in md_text or bool(re.search(r"(?<!\$)\$[^\$\n]+\$(?!\$)", md_text))

    body = markdown.markdown(
        md_text,
        extensions=["tables", "fenced_code", "nl2br", "sane_lists", "toc"],
    )
    extra_css = ""
    if landscape:
        extra_css += "\n@page { size: A4 landscape; margin: 12mm 15mm; }\nbody { max-width: 1120px; }\n"
    if zoom != 1.0:
        margin_mm = max(int(15 * zoom), 9)
        extra_css += f"\n@page {{ margin: {margin_mm}mm; }}\nbody {{ zoom: {zoom:.3f}; }}\n"

    extra_head = KATEX_MERMAID_HEAD if (has_mermaid or has_math) else ""
    return (
        f"""<!doctype html>
<html lang="th">
<head>
<meta charset="utf-8">
<title>{html.escape(title or "Document")}</title>
<style>{css}{extra_css}</style>
{extra_head}
</head>
<body>
{body}
</body>
</html>""",
        (has_mermaid or has_math),
    )


def cmd_md2pdf(args):
    md_text = open(args.input, encoding="utf-8-sig").read()
    html_path = os.path.splitext(args.output)[0] + ".html"
    os.makedirs(os.path.dirname(os.path.abspath(args.output)) or ".", exist_ok=True)

    zooms = [1.0, 0.93, 0.86, 0.80, 0.74] if args.fit_one_page else [1.0]
    used_zoom = 1.0
    pages = 0
    try:
        for z in zooms:
            used_zoom = z
            html_str, needs_wait = md_to_html_str(
                md_text,
                title=args.title,
                css_path=args.css,
                landscape=args.landscape,
                zoom=z,
            )
            open(html_path, "w", encoding="utf-8").write(html_str)
            pages = html_to_pdf(html_path, args.output, wait_ms=2500 if needs_wait else 0, quiet=True)
            if pages <= 1:
                break
        print(f"output={os.path.abspath(args.output)}\npages={pages}" + (f"\nzoom={used_zoom}" if used_zoom != 1.0 else ""))
    finally:
        if not args.keep_html and os.path.isfile(html_path):
            os.remove(html_path)


def cmd_html2pdf(args):
    html_to_pdf(args.input, args.output, wait_ms=args.wait_ms)


def set_docx_run_font(run, font_name, size_pt=None, bold=None, color_rgb=None):
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    from docx.shared import Pt, RGBColor

    run.font.name = font_name
    if size_pt is not None:
        run.font.size = Pt(size_pt)
    if bold is not None:
        run.font.bold = bold
    if color_rgb is not None:
        run.font.color.rgb = RGBColor(*color_rgb)

    rPr = run._element.get_or_add_rPr()
    rFonts = rPr.find(qn("w:rFonts"))
    if rFonts is None:
        rFonts = OxmlElement("w:rFonts")
        rPr.insert(0, rFonts)
    for attr in ("w:ascii", "w:hAnsi", "w:eastAsia", "w:cs"):
        rFonts.set(qn(attr), font_name)


def set_docx_table_layout_props(table):
    """Set repeating header row (tblHeader), row keep-together (cantSplit), and header shading."""
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn

    for r_idx, row in enumerate(table.rows):
        trPr = row._tr.get_or_add_trPr()
        cantSplit = OxmlElement("w:cantSplit")
        trPr.append(cantSplit)
        if r_idx == 0:
            tblHeader = OxmlElement("w:tblHeader")
            trPr.append(tblHeader)
            for cell in row.cells:
                tcPr = cell._tc.get_or_add_tcPr()
                shd = OxmlElement("w:shd")
                shd.set(qn("w:val"), "clear")
                shd.set(qn("w:color"), "auto")
                shd.set(qn("w:fill"), "F1F5F9")
                tcPr.append(shd)


def add_inline_runs(paragraph, text, font_name, size_pt=14):
    tokens = re.split(r"(\*\*.*?\*\*|`.*?`)", text)
    for tok in tokens:
        if not tok:
            continue
        if tok.startswith("**") and tok.endswith("**") and len(tok) > 4:
            r = paragraph.add_run(tok[2:-2])
            set_docx_run_font(r, font_name, size_pt=size_pt, bold=True)
        elif tok.startswith("`") and tok.endswith("`") and len(tok) > 2:
            r = paragraph.add_run(tok[1:-1])
            set_docx_run_font(r, "Consolas", size_pt=max(size_pt - 2, 10))
        else:
            r = paragraph.add_run(tok)
            set_docx_run_font(r, font_name, size_pt=size_pt)


def cmd_md2docx(args):
    from docx import Document
    from docx.shared import Mm, Pt

    font_name = args.font
    body_pt = args.size
    lines = open(args.input, encoding="utf-8-sig").read().splitlines()

    doc = Document()
    for sec in doc.sections:
        sec.page_width = Mm(210)
        sec.page_height = Mm(297)
        sec.top_margin = Mm(20)
        sec.bottom_margin = Mm(20)
        sec.left_margin = Mm(22)
        sec.right_margin = Mm(20)

    i = 0
    while i < len(lines):
        line = lines[i].rstrip()
        if not line.strip():
            i += 1
            continue

        # Markdown table block
        if "|" in line and i + 1 < len(lines) and re.match(r"^\s*\|?[\s:\-\|]+\|?\s*$", lines[i + 1]):
            table_lines = [line]
            i += 2
            while i < len(lines) and "|" in lines[i] and lines[i].strip():
                table_lines.append(lines[i].rstrip())
                i += 1
            rows = [
                [c.strip() for c in r.strip().strip("|").split("|")]
                for r in table_lines
            ]
            cols = max(len(r) for r in rows)
            tbl = doc.add_table(rows=len(rows), cols=cols)
            tbl.style = "Table Grid"
            for r_idx, r_vals in enumerate(rows):
                for c_idx in range(cols):
                    val = r_vals[c_idx] if c_idx < len(r_vals) else ""
                    cell = tbl.cell(r_idx, c_idx)
                    p = cell.paragraphs[0]
                    p.paragraph_format.space_before = Pt(3)
                    p.paragraph_format.space_after = Pt(3)
                    run = p.add_run(val)
                    set_docx_run_font(
                        run,
                        font_name,
                        size_pt=body_pt,
                        bold=(r_idx == 0),
                    )
            set_docx_table_layout_props(tbl)
            continue

        # Headings (keep_with_next prevents orphan headings at bottom of page)
        m_head = re.match(r"^(#{1,4})\s+(.*)$", line)
        if m_head:
            level = len(m_head.group(1))
            sizes = {1: body_pt + 6, 2: body_pt + 3, 3: body_pt + 1, 4: body_pt}
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(10 if level <= 2 else 6)
            p.paragraph_format.space_after = Pt(4)
            p.paragraph_format.keep_with_next = True
            p.paragraph_format.keep_together = True
            run = p.add_run(m_head.group(2).strip())
            set_docx_run_font(run, font_name, size_pt=sizes[level], bold=True, color_rgb=(15, 23, 42))
            i += 1
            continue

        # Bullet / numbered list
        m_ul = re.match(r"^\s*[-*+]\s+(.*)$", line)
        m_ol = re.match(r"^\s*\d+\.\s+(.*)$", line)
        if m_ul or m_ol:
            p = doc.add_paragraph(style="List Bullet" if m_ul else "List Number")
            p.paragraph_format.space_before = Pt(1)
            p.paragraph_format.space_after = Pt(2)
            add_inline_runs(p, (m_ul or m_ol).group(1), font_name, size_pt=body_pt)
            i += 1
            continue

        # Normal paragraph
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(2)
        p.paragraph_format.space_after = Pt(4)
        add_inline_runs(p, line, font_name, size_pt=body_pt)
        i += 1

    os.makedirs(os.path.dirname(os.path.abspath(args.output)) or ".", exist_ok=True)
    doc.save(args.output)
    print(f"output={os.path.abspath(args.output)}\nparagraphs={len(doc.paragraphs)}\ntables={len(doc.tables)}")


def cmd_json2xlsx(args):
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
    from openpyxl.utils import get_column_letter

    spec = json.load(open(args.input, encoding="utf-8-sig"))
    sheets = spec.get("sheets") or [spec]
    font_name = spec.get("font", "Sarabun")

    wb = Workbook()
    wb.remove(wb.active)

    thin = Side(border_style="thin", color="94A3B8")
    border = Border(left=thin, right=thin, top=thin, bottom=thin)
    header_fill = PatternFill("solid", fgColor="1E293B")
    header_font = Font(name=font_name, size=11, bold=True, color="FFFFFF")
    body_font = Font(name=font_name, size=11, color="0F172A")
    bold_font = Font(name=font_name, size=11, bold=True, color="0F172A")
    zebra_fill = PatternFill("solid", fgColor="F8FAFC")
    total_fill = PatternFill("solid", fgColor="E2E8F0")

    for sh in sheets:
        title = sh.get("name", "Sheet1")[:31]
        ws = wb.create_sheet(title=title)
        # Fit all columns onto 1 page wide when printed
        ws.sheet_properties.pageSetUpPr.fitToPage = True
        ws.page_setup.fitToWidth = 1
        ws.page_setup.fitToHeight = 0

        headers = sh.get("headers", [])
        rows = sh.get("rows", [])
        formats = sh.get("column_formats", {})

        if headers:
            ws.append(headers)
            ws.freeze_panes = "A2"
            ws.print_title_rows = "1:1"
            ws.row_dimensions[1].height = 24
            for col_idx in range(1, len(headers) + 1):
                c = ws.cell(row=1, column=col_idx)
                c.fill = header_fill
                c.font = header_font
                c.border = border
                c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

        for r_idx, row_vals in enumerate(rows, start=2 if headers else 1):
            ws.append(row_vals)
            ws.row_dimensions[r_idx].height = 20
            is_total = any(isinstance(v, str) and ("รวม" in v or "Total" in v or v.startswith("=SUM")) for v in row_vals)
            for col_idx in range(1, len(row_vals) + 1):
                c = ws.cell(row=r_idx, column=col_idx)
                c.font = bold_font if is_total else body_font
                if is_total:
                    c.fill = total_fill
                elif r_idx % 2 == 1:
                    c.fill = zebra_fill
                c.border = border
                col_letter = get_column_letter(col_idx)
                fmt = formats.get(str(col_idx)) or formats.get(col_letter)
                if fmt:
                    c.number_format = fmt
                elif isinstance(c.value, float):
                    c.number_format = "#,##0.00"
                elif isinstance(c.value, int) and not isinstance(c.value, bool):
                    c.number_format = "#,##0"

        for col in ws.columns:
            col_letter = get_column_letter(col[0].column)
            max_len = 0
            for cell in col:
                val_str = str(cell.value or "")
                if val_str.startswith("="):
                    max_len = max(max_len, 14)
                else:
                    max_len = max(max_len, len(val_str))
            ws.column_dimensions[col_letter].width = max(min(max_len + 5, 55), 10)

    os.makedirs(os.path.dirname(os.path.abspath(args.output)) or ".", exist_ok=True)
    wb.save(args.output)
    print(f"output={os.path.abspath(args.output)}\nsheets={len(wb.sheetnames)}")


def cmd_json2pptx(args):
    from pptx import Presentation
    from pptx.dml.color import RGBColor
    from pptx.util import Inches, Pt

    spec = json.load(open(args.input, encoding="utf-8-sig"))
    font_name = spec.get("font", args.font)
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6]

    for s in spec.get("slides", []):
        slide = prs.slides.add_slide(blank_layout)
        stype = s.get("type", "bullets")

        if stype == "title":
            tb = slide.shapes.add_textbox(Inches(1.0), Inches(2.2), Inches(11.3), Inches(2.2))
            tf = tb.text_frame
            tf.word_wrap = True
            p = tf.paragraphs[0]
            p.text = s.get("title", "")
            p.font.name = font_name
            p.font.size = Pt(44)
            p.font.bold = True
            p.font.color.rgb = RGBColor(15, 23, 42)
            if s.get("subtitle"):
                p2 = tf.add_paragraph()
                p2.text = s["subtitle"]
                p2.font.name = font_name
                p2.font.size = Pt(22)
                p2.font.color.rgb = RGBColor(71, 85, 105)
            continue

        # Header bar for content slides
        tb_head = slide.shapes.add_textbox(Inches(0.8), Inches(0.5), Inches(11.7), Inches(0.9))
        tf_h = tb_head.text_frame
        tf_h.word_wrap = True
        ph = tf_h.paragraphs[0]
        ph.text = s.get("title", "")
        ph.font.name = font_name
        ph.font.size = Pt(30)
        ph.font.bold = True
        ph.font.color.rgb = RGBColor(15, 23, 42)

        if stype == "table" and s.get("rows"):
            headers = s.get("headers", [])
            rows = s["rows"]
            all_rows = ([headers] if headers else []) + rows
            r_cnt = len(all_rows)
            c_cnt = max(len(r) for r in all_rows)
            tbl_shape = slide.shapes.add_table(r_cnt, c_cnt, Inches(0.8), Inches(1.6), Inches(11.7), Inches(0.55 * r_cnt))
            tbl = tbl_shape.table
            for r_i, r_vals in enumerate(all_rows):
                for c_i in range(c_cnt):
                    cell = tbl.cell(r_i, c_i)
                    cell.text = str(r_vals[c_i]) if c_i < len(r_vals) else ""
                    for p in cell.text_frame.paragraphs:
                        p.font.name = font_name
                        p.font.size = Pt(16)
                        p.font.bold = (r_i == 0 and bool(headers))
        else:
            tb_body = slide.shapes.add_textbox(Inches(0.9), Inches(1.6), Inches(11.5), Inches(5.2))
            tf_b = tb_body.text_frame
            tf_b.word_wrap = True
            for idx, item in enumerate(s.get("bullets", [])):
                p = tf_b.paragraphs[0] if idx == 0 else tf_b.add_paragraph()
                p.text = f"•  {item}"
                p.font.name = font_name
                p.font.size = Pt(20)
                p.font.color.rgb = RGBColor(30, 41, 59)
                p.space_after = Pt(12)

    os.makedirs(os.path.dirname(os.path.abspath(args.output)) or ".", exist_ok=True)
    prs.save(args.output)
    print(f"output={os.path.abspath(args.output)}\nslides={len(prs.slides)}")


def cmd_pdf_info(args):
    import pymupdf

    with pymupdf.open(args.input) as doc:
        print(f"file={os.path.abspath(args.input)}")
        print(f"pages={len(doc)}")
        for i, page in enumerate(doc, 1):
            r = page.rect
            print(f"page_{i}={r.width:.1f}x{r.height:.1f}pt")
    if args.md:
        import pymupdf4llm
        print("--- MARKDOWN ---")
        print(pymupdf4llm.to_markdown(args.input))


def cmd_pdf2img(args):
    import pymupdf

    os.makedirs(args.out_dir, exist_ok=True)
    with pymupdf.open(args.input) as doc:
        for i, page in enumerate(doc, 1):
            pix = page.get_pixmap(dpi=args.dpi)
            out_path = os.path.join(args.out_dir, f"page_{i:02d}.png")
            pix.save(out_path)
            print(out_path)


def cmd_pdf_audit(args):
    import pymupdf

    out_dir = args.out_dir
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    issues = []
    with pymupdf.open(args.input) as doc:
        n_pages = len(doc)
        print(f"file={os.path.abspath(args.input)}")
        print(f"pages={n_pages}")
        if args.expect_pages and n_pages != args.expect_pages:
            issues.append(f"PAGE_COUNT_MISMATCH: expected {args.expect_pages}, got {n_pages}")

        for i, page in enumerate(doc, 1):
            pix = page.get_pixmap(dpi=120, colorspace=pymupdf.csGRAY)
            samples = pix.samples
            non_white = sum(1 for b in samples if b < 245)
            ink_pct = (non_white / len(samples)) * 100.0 if samples else 0.0
            print(f"page_{i}_ink={ink_pct:.2f}%")
            if i == n_pages and n_pages > 1 and ink_pct < 1.2:
                issues.append(f"SPARSE_TRAILING_PAGE: page {i} has only {ink_pct:.2f}% ink (likely accidental overflow)")
            if out_dir:
                color_pix = page.get_pixmap(dpi=150)
                img_path = os.path.join(out_dir, f"page_{i:02d}.png")
                color_pix.save(img_path)
                print(f"page_{i}_png={img_path}")

    if issues:
        for iss in issues:
            print(f"AUDIT_WARN={iss}")
    else:
        print("AUDIT_STATUS=OK")


def parse_page_spec(spec_str, max_pages):
    pages = []
    for part in spec_str.split(","):
        part = part.strip()
        if "-" in part:
            a, b = part.split("-", 1)
            pages.extend(range(int(a), int(b) + 1))
        else:
            pages.append(int(part))
    return [p - 1 for p in pages if 1 <= p <= max_pages]


def cmd_pdf_merge(args):
    from pypdf import PdfWriter

    writer = PdfWriter()
    for path in args.inputs:
        writer.append(path)
    os.makedirs(os.path.dirname(os.path.abspath(args.output)) or ".", exist_ok=True)
    with open(args.output, "wb") as f:
        writer.write(f)
    print(f"output={os.path.abspath(args.output)}\npages={len(writer.pages)}")


def cmd_pdf_split(args):
    from pypdf import PdfReader, PdfWriter

    reader = PdfReader(args.input)
    idxs = parse_page_spec(args.pages, len(reader.pages))
    writer = PdfWriter()
    for idx in idxs:
        writer.add_page(reader.pages[idx])
    os.makedirs(os.path.dirname(os.path.abspath(args.output)) or ".", exist_ok=True)
    with open(args.output, "wb") as f:
        writer.write(f)
    print(f"output={os.path.abspath(args.output)}\npages={len(writer.pages)}")


def main():
    parser = argparse.ArgumentParser(description="Document Suite CLI")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_md2pdf = sub.add_parser("md2pdf")
    p_md2pdf.add_argument("input")
    p_md2pdf.add_argument("output")
    p_md2pdf.add_argument("--title", default="")
    p_md2pdf.add_argument("--css", default=None)
    p_md2pdf.add_argument("--landscape", action="store_true")
    p_md2pdf.add_argument("--fit-one-page", action="store_true")
    p_md2pdf.add_argument("--keep-html", action="store_true")
    p_md2pdf.set_defaults(func=cmd_md2pdf)

    p_html2pdf = sub.add_parser("html2pdf")
    p_html2pdf.add_argument("input")
    p_html2pdf.add_argument("output")
    p_html2pdf.add_argument("--wait-ms", type=int, default=0)
    p_html2pdf.set_defaults(func=cmd_html2pdf)

    p_md2docx = sub.add_parser("md2docx")
    p_md2docx.add_argument("input")
    p_md2docx.add_argument("output")
    p_md2docx.add_argument("--font", default="Sarabun")
    p_md2docx.add_argument("--size", type=int, default=14)
    p_md2docx.set_defaults(func=cmd_md2docx)

    p_xlsx = sub.add_parser("json2xlsx")
    p_xlsx.add_argument("input")
    p_xlsx.add_argument("output")
    p_xlsx.set_defaults(func=cmd_json2xlsx)

    p_pptx = sub.add_parser("json2pptx")
    p_pptx.add_argument("input")
    p_pptx.add_argument("output")
    p_pptx.add_argument("--font", default="Sarabun")
    p_pptx.set_defaults(func=cmd_json2pptx)

    p_info = sub.add_parser("pdf-info")
    p_info.add_argument("input")
    p_info.add_argument("--md", action="store_true")
    p_info.set_defaults(func=cmd_pdf_info)

    p_img = sub.add_parser("pdf2img")
    p_img.add_argument("input")
    p_img.add_argument("out_dir")
    p_img.add_argument("--dpi", type=int, default=150)
    p_img.set_defaults(func=cmd_pdf2img)

    p_audit = sub.add_parser("pdf-audit")
    p_audit.add_argument("input")
    p_audit.add_argument("--expect-pages", type=int, default=None)
    p_audit.add_argument("--out-dir", default=None)
    p_audit.set_defaults(func=cmd_pdf_audit)

    p_merge = sub.add_parser("pdf-merge")
    p_merge.add_argument("output")
    p_merge.add_argument("inputs", nargs="+")
    p_merge.set_defaults(func=cmd_pdf_merge)

    p_split = sub.add_parser("pdf-split")
    p_split.add_argument("input")
    p_split.add_argument("output")
    p_split.add_argument("--pages", required=True)
    p_split.set_defaults(func=cmd_pdf_split)

    args = parser.add_args() if hasattr(parser, "read_args") else parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
