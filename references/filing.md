# Filing and naming standard

Use this for every multi-document project unless the user names another scheme.

## File names
`project_doc-type_vN_YYYY-MM-DD.ext`, then `_summary` before the date for the short brief.

| Part | Rule | Example |
|---|---|---|
| project | short lowercase English slug, same in every file | `feelfirst` |
| doc-type | lowercase words joined by `-`, what the document is | `business-plan`, `market-scan`, `operations-workflow`, `sales-kit` |
| vN | version of this document; a substantive rewrite bumps N, a same-day fix does not | `v2` |
| date | ISO date of the build, always last | `2026-11-28` |

Examples: `feelfirst_business-plan_v2_2026-11-28.pdf`, `feelfirst_business-plan_v2_summary_2026-11-28.pdf`.
No spaces, no Thai, no `final`/`new`/`latest` in file names. Source files keep the same base name (`.md`).

## Folders
```
<project>/docs/
  00-overview/      project summary, index
  01-strategy/      business plan, market scan, positioning
  02-research/      competitor research, notes, raw sources
  03-operations/    workflow, SOP, templates
  04-sales/         sales kit, offer sheet, lead lists
  05-finance/       models, budgets
  06-legal/         contracts, consent, compliance
  99-archive/       superseded versions (never delete them)
```
Each folder holds the PDF and its source together. The project `README.md` lists every current document with pages and a one-line purpose.

## Full and summary
Every report of 5+ pages ships as two files: the full document and a brief of at most 2 A4 pages. The brief opens with a 3-line conclusion, then key numbers (labels such as "assumption" copied from the full document), decisions for the owner, top risks, next steps and a closing line naming the full document. It adds no fact the full document lacks.
