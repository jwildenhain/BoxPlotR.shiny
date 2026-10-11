# Transparent figure exports — 5 October 2026

The web app now has **Transparent background** and **Unfilled shapes** options
above the PDF/SVG download buttons. They apply to downloads; the preview keeps
its colours. Background transparency overrides both white and journal-style
backgrounds. Unfilled distribution shapes retain their outlines, whiskers,
medians and other statistical marks, including outlier dots.

The public MCP exposes `transparent_background` and `unfilled_shapes`, both
booleans defaulting to `false`. Local stdio accepts the same fields under
`styling`. Both engines support these options in PNG, SVG and PDF. PDF output
uses Cairo to support the modern engine's fonts while retaining vector shapes.

## Existing production behavior preserved

The deployed worker already included whisker controls and the modern Cairo PDF
fix from `origin/codex/cairo-pdf-matrix`; these were retained locally. The live
HTTP gateway also registers ChemGrid and MolClass tools, which are managed
outside this repository. Deployment patched that gateway in place rather than
replacing it with this repository's standalone BoxPlotR gateway. Future updates
to the shared production gateway must preserve those integrations.

## Analytics correction

Google's strict Measurement Protocol validator rejected the existing
`mcp.<hash>` client IDs. Both plot events and service user-activity events now
use a numeric, pseudonymous `number.number` ID derived from the existing
service-specific hash, and a session identifier for a 30-minute time bucket.
Plot events include the two export-option flags. Dataset content, plot titles,
raw client addresses and API keys are excluded from these payloads.

## Validation

- Existing R suite: 6 assertions passed, no failures or warnings.
- Worker regression suite: 5 tests passed, including actual SVG output for
  box, violin and bean plots in both engines and strict boolean validation.
- HTTP integration suite: 12 normal renders spanning both engines, CSV/TSV,
  and PNG/SVG/PDF; 2 transparent/unfilled SVG renders; schema, health and
  invalid-input checks all passed.
- Gateway analytics suite: 2 tests passed, checking privacy-safe parameters,
  numeric client IDs and resilience to analytics transport failures.
- Browser UX: controls toggled correctly; the preview kept its colours;
  normal downloads remained opaque; Classic and modern PDF/SVG downloads
  worked. Horizontal notched modern PDF output also worked locally.
- Live public MCP: 6 transparent/unfilled renders passed (both engines and
  all three formats). PNG/PDF background alpha was verified; PDFs contained
  no embedded raster images. ChemGrid and MolClass tools remained available.
- Live website: Classic PDF and modern PDF/SVG downloads passed transparency
  and vector checks. No browser errors were reported during those downloads.
- Analytics: the browser loaded the BoxPlotR Google tag. Both corrected MCP
  event payloads passed Google's strict validator with zero messages, and
  real collection requests returned HTTP 204. The six public test renders
  were recorded as successful in the gateway database. Report visibility
  could not be verified because the Analytics connector lacks credentials.
- Deployed Shiny source, worker, guide and patched gateway checksums matched
  the verified files. Both services remained active with no recent error
  entries in the MCP service journal.

## Deployment and rollback

Five live files were backed up before deployment under
`/var/backups/boxplotr-transparent-20261005-bYe4QJ` on Chemgrid:
`server.R`, `ui.R`, `boxplotr_mcp_server.py`, `mcp-guide.html`, and `app.py`.
The Shiny app was refreshed using `restart.txt`; the MCP service was restarted.
Runtime secrets and usage state were retained.

To roll back, restore these files to their original application/gateway paths,
update the app's `restart.txt`, and restart `boxplotr-mcp`. The gateway backup
includes all existing ChemGrid/MolClass integrations.
