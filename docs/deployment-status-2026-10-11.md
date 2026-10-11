# BoxPlotR deployment status — 11 October 2026

## Status

The October BoxPlotR release is deployed and healthy on ChemGrid. Its source is
captured on the `codex/transparent-exports` branch so the production behavior,
local checkout and reviewed Git history can be reconciled before merging to
`master`.

| Surface | Status | Evidence |
| --- | --- | --- |
| Shiny website | Live | `https://boxplotr.chemgrid.org/` returns HTTP 200 and exposes the transparent-background and unfilled-shape download controls. |
| MCP guide | Live | `https://boxplotr.chemgrid.org/mcp-guide.html` returns HTTP 200 and documents the October export options. |
| Public MCP | Healthy | `https://mcp.chemgrid.org/health/boxplotr` returns `status: ok`, with anonymous quota and concurrency metadata. |
| Shared browser analytics | Matched | The public `https://chemgrid.org/chemgrid-analytics.js` and `deploy/analytics/chemgrid-analytics.js` both have SHA-256 `011acd6379facd3b40d8495088044fc9417a97cdece8aae38fb9d952ba536cd2`. |
| Local source | Release candidate | Contains the deployed transparent-export, whisker, Cairo PDF and privacy-safe analytics changes, plus their tests and deployment records. |
| GitHub | Release branch | Publish `codex/transparent-exports`; merge it to `master` only after review and CI. |

## Included changes

- Transparent backgrounds and unfilled shapes for Shiny PDF/SVG downloads.
- Matching PNG, SVG and PDF options in the local and public MCP interfaces.
- Tukey, Spear and Altman whisker selection through MCP.
- Cairo PDF output for reliable modern-engine font and vector rendering.
- Privacy-safe website and MCP analytics, including explicit ChemGrid routing
  and export-format metadata.
- Regression coverage for rendering, gateway analytics, public container
  behavior and the shared browser analytics script.

Detailed deployment and rollback information remains in
`transparent-exports-2026-10-05.md`; analytics validation and privacy notes are
in `analytics-audit-2026-10-09.md`.

## Release validation

- Both standalone R suites pass when launched from the repository root.
- The packaged MCP image passes seven unit and real-render tests.
- The HTTP contract matrix passes 12 normal CSV/TSV renders across both
  engines and all three formats, plus two transparent/unfilled SVG renders,
  schema, health and invalid-input checks.
- The shared browser analytics regression passes for BoxPlotR, GrowthCurve,
  CheckerboardR and ChemGrid search categorisation without recording private
  input values.
- R and Python syntax validation passes for the changed application, gateway,
  deployment and test files.

## Synchronization notes

The production Shiny directory is not a Git checkout. Releases are copied from
the canonical `jwildenhain/BoxPlotR.shiny` repository and production-only
runtime configuration, credentials and service state remain outside Git. The
shared production gateway also hosts ChemGrid and MolClass tools; future
BoxPlotR deployments must preserve those integrations rather than replacing
the gateway wholesale.

Direct production file checksums could not be refreshed on 11 October because
the current workstation session did not have an accepted SSH identity for the
server. Public health, feature and shared-asset checks passed, while the 5 and
9 October deployment records contain the last privileged file-level
verification.
