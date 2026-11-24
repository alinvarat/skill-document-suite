---
name: document-suite
description: Create, convert or audit local Thai/English documents and PDFs. Use Sarabun for Thai text.
---

# Local documents

1. Select the route. Native Word/Sheets/Slides/Google Docs use an available format-specific skill and connector; this suite handles local conversion and Thai layout. Do not invent a `gdocs` skill.
2. Preserve sources. Back up before an authorized in-place edit. Use requested names/destinations; otherwise save under `~/Project/` (e.g. `~/Project/Reports/`, `~/Project/Quotes/`, `~/Project/Slides/`) with sortable English filenames. Never write deliverables to `~/Documents/` or its localized equivalent unless the user names that folder. Before `mkdir`, run `ls ~/Project` and reuse the closest existing folder. Never invent prices, dates, parts, names or legal terms; leave missing fields blank and report them.
3. Use Sarabun unless the user requests another font. Read only the requested-format section in [local workflows](references/local-workflows.md), then run the full command shown there. Templates are optional layouts, not required sections.
3a. Illustrated step-by-step plans (itineraries, guides):
   - Source images from a free library (e.g. Wikimedia Commons) or user-supplied files; download, then inspect the file name and content before placing it. Reject pictures of the wrong building, terminal, or line.
   - Caption every generic photo as a general illustration of the place, not the user's exact gate/platform/counter, unless verified. Unverifiable items get an explicit "(verify)" tag, not a guessed description.
   - Tell the user which items still have no photo and where they can be found; do not claim coverage that the file list does not show.
   - For Sarabun, use `[  ]` for checkboxes; the `☐` glyph risks tofu.
3b. Large multi-part reports (60+ pages, several charts, data from many sources): build in stages, never one giant script. Each stage writes a file (data JSON, SVG module, HTML part, build script) and is checked before the next. Follow section H in [local workflows](references/local-workflows.md). Why: one oversized turn hits the model output-length limit, and the runtime then drops the whole action unexecuted.
4. Verify the actual output:
   - Every page, not just page 1: render with `pdftoppm -r 50 -png` and view each PNG; `pdftotext` alone does not prove glyphs render.
   - PDF: run `python3 "~/.claude/skills/document-suite/scripts/doc_tool.py" pdf-audit OUTPUT.pdf --out-dir QA_DIR > QA_DIR/audit.log 2>&1`, then read the log file; stdout from long runs gets truncated, so a file is the only reliable record. Add `--expect-pages N` only when known. Open rendered pages; check Thai marks, clipping, tables, breaks and signatures. Check font embedding with `pdffonts`.
   - Ink ratio is a spillover heuristic, not a quality grade: low ink (under about 2%) on a page of URL lists, reference tails or a short section break is expected. Read that page's text with `pdftotext -f N -l N` before calling it a defect; flag it as a defect only when the text or layout is actually wrong.
   - Text-level gate for reports: `pdftotext` the whole file and check for raw markdown `**`, raw HTML tags, replacement characters (U+FFFD) and `☐`, and check every required heading or model number appears. Report the counts.
   - Vision checks: pass the exact existing absolute path to the PNG (confirm with `ls` first; `media file not found` means the path is wrong, not the model). Use underscore names the audit created (`page_NN.png`). If a call fails with "no result event", retry once; if it still fails, use the text gate instead of guessing what the page shows. Build a contact sheet (16 pages per image) to scan the whole book in one call.
   - Before reporting counts (pages, images), run `pdfinfo` and `pdfimages -list` and quote the numbers; do not carry counts from an earlier build. Confirm the copy in the destination folder is the same build.
   - Office: reopen with a suitable library; compare text, tables, sheets/slides and formulas with the input. Preview when layout matters. Size/counts alone are insufficient.
   - Extract/merge/split: reopen; compare requested content, page count/order and ranges with sources.
   - Delivered copies: after copying into the destination folder, compare `sha256sum` of source and copy and quote both results. Count-based checks are not proof that the copy is the same build.
5. Return verified paths and any unchecked appearance/content. A file exit code is not visual proof. Save task memory only when the `memory` skill's explicit trigger applies.
