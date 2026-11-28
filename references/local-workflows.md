# Local layout and conversion workflows

Read only the sections for the requested output format. These are adaptable templates; retain user-requested content and layout.

## 1. Document Structure & Organization Templates
Organize every document into a predictable visual hierarchy before generating:
- **Technical Specification / Engineering Report**:
  1. Header block (`.doc-header`) + Metadata box (`.doc-meta`: Document ID, Revision, Date, Project/Target).
  2. Overview & Scope (1 short paragraph or `.grid-2` summary cards).
  3. Architecture / Block Diagram (`mermaid` flowchart or `figure`) & Key Parameters (`table.kv` or bordered table).
  4. Detailed Pinout / BOM / Test Results (table with right-aligned numbers `.r` and status pills `.badge.ok`/`.warn`/`.danger`).
  5. Notes / Constraints (`.callout`) & Sign-off (`.sign-row` if formal approval is needed).
- **Formal Thai Document / Contract / Memo / Receipt**:
  1. Header + Date in Buddhist Era ((Buddhist Era = CE + 543)).
  2. Parties / Reference block (`.doc-meta`).
  3. Numbered clauses or line-item table with `Grand total` summary row.
  4. Terms & Conditions + Paired signature blocks (`.sign-row` > `.sign-box`, kept together on the same page).
- **Step-by-step travel / checklist plan (Thai)**: one checkbox per action, grouped by date and place, with the time, location, document needed and fallback for each step. Mark every unconfirmed detail with a visible tag such as `(verify)` instead of stating it as fact.

## 2. Page Layout, Pagination & Thai Typography Rules
- **Fonts**: Default to **Sarabun for every document**. Use another font only if the user asks; check with `pdffonts` that the PDF actually embeds Sarabun, not a fallback.
- **Glyph safety**: Sarabun may lack symbol glyphs such as `☐` (U+2610) and emoji; they render as blank or tofu. Use ASCII markers like `[  ]` for checkboxes and plain text for symbols.
- **Pagination & Anti-Overflow**:
  - **One-page fit (`--fit-one-page`)**: Pass `--fit-one-page` to `md2pdf` for single-page forms/summaries; it automatically steps down zoom (`1.0` -> `0.93` -> `0.86` -> `0.80`) if content spills onto page 2.
  - **Landscape (`--landscape`)**: Use `--landscape` for wide multi-column tables or schedules.
  - **Keep-together protection**: Wrap any card, callout, diagram, or signature block that must never split across a page boundary in `.keep-together`, `.section-card`, `.callout`, `figure`, or `.sign-row` (`break-inside: avoid`).
  - **Multi-page tables**: Always use `<thead>` and `<tbody>` so column headers repeat automatically at the top of every new page (`thead { display: table-header-group; }`).
  - **Word (`.docx`) layout**: `doc_tool.py md2docx` automatically sets complex-script fonts (`w:ascii`, `w:hAnsi`, `w:eastAsia`, `w:cs`), `keep_with_next` on all headings (no orphan headings at page bottom), `w:tblHeader` (repeating table headers), and `w:cantSplit` on table rows.
  - **Excel (`.xlsx`) layout**: `doc_tool.py json2xlsx` automatically locks the header row (`freeze_panes = "A2"`), repeats row 1 on print (`print_title_rows = "1:1"`), applies zebra striping, and sets `fitToWidth = 1` / `fitToHeight = 0` so wide tables never split columns across printed pages.

## 3. Format Workflows (`scripts/doc_tool.py`)

Run commands with `python3 "~/.claude/skills/document-suite/scripts/doc_tool.py" <subcommand> ...`:

### A. Print-Ready A4 PDF (Markdown or HTML -> Headless Chrome)
Supports Markdown tables, HTML layout classes (`print_a4.css`), **Mermaid diagrams** (```` ```mermaid ````), and **KaTeX math** (`$...$`, `$$...$$`):
```bash
python3 "~/.claude/skills/document-suite/scripts/doc_tool.py" md2pdf input.md output.pdf --title "Document Title" [--cover "kicker|subtitle|meta"] [--toc] [--footer "text" | --footer ""] [--fit-one-page] [--landscape] [--keep-html]
python3 "~/.claude/skills/document-suite/scripts/doc_tool.py" html2pdf input.html output.pdf [--wait-ms 2500]
```
- **Built-in layout classes (`assets/print_a4.css`)**:
  - `.doc-header`, `.doc-meta`: Document header & shaded metadata box.
  - `.grid-2`, `.grid-3`, `.section-card`: 2-column / 3-column grid and bordered card (`break-inside: avoid`).
  - `table.kv`, `table.plain`: Borderless key-value table and minimal table.
  - `td.num` / `.r`, `td.center` / `.c`: Right-aligned tabular numbers and centered cells.
  - `.callout` (`.ok`, `.warn`, `.danger`) & `.badge` (`.ok`, `.warn`, `.danger`): Highlight boxes and status pills.
  - `p.indent`, `p.justify`: Thai paragraph first-line indent (`2.5em`) and inter-cluster justification.
  - `.sign-row` > `.sign-box`, `.fill`: Paired dashed signature blocks and dashed fill-in lines.
  - `.page-break`, `.keep-together`: Explicit page break and page-split prevention.

### B. Editable Word Document (`.docx`)
```bash
python3 "~/.claude/skills/document-suite/scripts/doc_tool.py" md2docx input.md output.docx --font Sarabun --size 14
```

### C. Excel Spreadsheet (`.xlsx`)
```bash
python3 "~/.claude/skills/document-suite/scripts/doc_tool.py" json2xlsx spec.json output.xlsx
```
- **JSON schema**: `{"font": "Sarabun", "sheets": [{"name": "Summary", "headers": ["Item", "Quantity", "Unit price", "Total"], "rows": [["ESP32-S3", 2, 180.0, "=B2*C2"], ["Grand total", "", "", "=SUM(D2:D2)"]], "column_formats": {"C": "#,##0.00", "D": "#,##0.00"}}]}`
- Always use live Excel formulas (`=SUM(...)`, `=B2*C2`) rather than hardcoded calculated sums.

### D. PowerPoint Presentation (`.pptx`)
```bash
python3 "~/.claude/skills/document-suite/scripts/doc_tool.py" json2pptx slides.json output.pptx --font Sarabun
```
- **JSON schema**: `{"font": "Sarabun", "slides": [{"type": "title", "title": "...", "subtitle": "..."}, {"type": "bullets", "title": "...", "bullets": ["...", "..."]}, {"type": "table", "title": "...", "headers": ["..."], "rows": [["..."]]}]}`

### E. PDF Audit, Inspection, Merge & Split
- **Automated Layout Audit & PNG Export** (checks page count, detects accidental trailing spillover pages with `< 1.2%` ink coverage, and exports PNGs):
  ```bash
  python3 "~/.claude/skills/document-suite/scripts/doc_tool.py" pdf-audit output.pdf --expect-pages 1 --out-dir pages_qa/ [--contact-sheet] [--font "Sarabun"]
  ```
- **Info & Markdown extraction**: `pdf-info input.pdf --md`
- **Merge / Split PDFs**: `pdf-merge merged.pdf part1.pdf part2.pdf` and `pdf-split input.pdf extracted.pdf --pages 1-2,4`

### F. HTML/SVG Visual Guide or Diagram to PNG
For Thai visual guides, step-by-step diagrams, or infographics, build a fixed-size HTML + inline SVG page using `Sarabun` and render with Headless Chrome (avoids Thai vowel/tone-mark clipping common in Pillow/Matplotlib):
```bash
google-chrome --headless --disable-gpu --screenshot=output.png --window-size=1200,820 file:///ABS_PATH/input.html
```

### G. Reportlab fallback for multi-page Thai PDF (no HTML layout needed)
Use when a plain structured PDF (checklist, schedule) is enough and HTML layout is overkill.
- Register Sarabun with `pdfmetrics.registerFont(TTFont('S', '<Sarabun-Regular.ttf>'))` and a separate bold face; set `fontName` on every `ParagraphStyle`. Without it, Thai renders as boxes.
- Build with `SimpleDocTemplate` + `Paragraph` flowables; use `pdftoppm -r 50 -png` for previews and check every page.
- Find the Sarabun font file under `~/.local/share/fonts/Sarabun/` first (`fc-list` may not list it).

## H. Staged build for large multi-part PDF reports
Use for reports of 60+ pages with charts, data tables and a citation ledger. Each step is a separate short tool call that writes to disk:
1. **Extract data first**: one script reads the source markdown/JSON and writes `data/*.json` (sections split by heading, URLs deduplicated). Print only counts, never the content.
2. **Register sources**: if a citation ledger is required, build it from the extracted URL list and read back the count.
3. **Compute numbers**: run calculators per case and write results to one JSON file. Check the keys with a small `python3 -c` that prints only the top-level structure before you reference any key in a later script. Flat keys are easier to reference than nested ones.
4. **Charts as SVG modules**: one module with one function per chart, returning an SVG string; constants come from the data JSON. Split long diagrams into lines before escaping; keep label text short for Thai.
5. **HTML in parts**: front matter, body chapters and appendices in separate modules, plus a build script that joins them and inlines one stylesheet (`@page` A4 margins, first-page override, running header/footer).
6. **Render and audit**: `html2pdf` the built HTML, then `pdf-audit` into `QA_DIR` with output redirected to a log file, then the text gate and page checks in SKILL.md step 4.
7. **Deliver**: copy to the destination and compare `sha256sum`.

Pitfalls:
- Keep each script or file edit under roughly 150 lines per turn; a larger write gets cut off and nothing runs.
- Run `--help` for each subcommand as a separate command; chaining with `&&` hides the first failure's exit code and error text.
- Check that a file exists before reading it; a missing data file produces an exit 1 that looks like a code bug.
- After any patch, re-read the function you changed; do not assume the file matches your last write.

