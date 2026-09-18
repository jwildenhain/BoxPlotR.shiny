# BoxPlotR consolidation — 18 September 2026

## Sources compared

| Source | Revision / location | Result |
| --- | --- | --- |
| Local checkout at the start | `9d35b96450ef498f997bbbcebb41bb327bbc5270` | Two commits behind the maintained default branch; local UI edits and untracked `test-data/` existed. |
| Maintained GitHub repository | `jwildenhain/BoxPlotR.shiny`, `master` at `bce2e5d` | Canonical base, including MCP hardening, gateway, container, CI, and deployment configuration. |
| Older GitHub repository | `jwildenhain/shiny-boxplot`, `master` at `830dfbc` | Its only commit absent from the maintained history is a README redirect to the maintained repository. No unique application implementation needs importing. |
| Deployed Shiny application | `tyerschem2:/srv/shiny-server/boxplotr` | No `.git` directory. Imported the UI, sanitized-error setting, public MCP documentation, guide, and static examples. |
| Deployed HTTP gateway | `tyerschem2:/opt/boxplotr-mcp/app.py` | Byte-identical to the maintained repository's gateway. |
| Deployed worker | `tyerschem2:/srv/shiny-server/boxplotr/boxplotr_mcp_server.py` | Matches maintained source apart from whitespace, before the whisker correction below. |
| Deployed systemd service | `/etc/systemd/system/boxplotr-mcp.service` | Byte-identical to the maintained service template. |

The initial local-only assessment understated what was already committed to
GitHub: MCP escaping, timeouts, telemetry, and the tool-discovery fix were
already in the maintained repository.

## Reconciliation decisions

- Keep `BoxPlotR.shiny` as the single maintained repository. The older
  `shiny-boxplot` README already redirects there; no remote deletion or archive
  is needed.
- Preserve the locally edited UI's output-delivery notes and format examples.
  Retain its stdio explanation as a separate FAQ alongside the deployed HTTP
  connection instructions.
- Preserve both the deployed user documentation and repository container
  instructions, with deployment details under `deploy/boxplotr_mcp/README.md`.
- Import `www/` assets and the deployed `assets/mcp_test_plot.png` example.
  Exclude server backup copies, bytecode, state, issued keys, and secrets.
- Preserve the deployed key-management and former email-access source in
  `deploy/boxplotr_mcp/legacy/`. These handlers are not mounted by the current
  gateway and remain inactive.
- Preserve the user's pre-existing `test-data/` directory without changing or
  adding its contents to version control.
- Fix both worker boxplot paths to pass `range = -1.5`, which selects Tukey
  whiskers in the custom statistics helper. Positive `1.5` selected Altman
  percentiles. The Shiny UI already passed the correct negative coefficient.
- Stop excluding `www/`, PNGs, and XLSX files from the shared Docker context;
  the Shiny image requires them. Keep the MCP image's explicit source copies.
- Keep the additional `origin/codex/fix-review-findings` branch (`8f84a42`)
  separate. It is not deployed and contains behavioral changes to log notches,
  validation, and downloads. Its PNG-only restriction conflicts with the
  released SVG/PDF support. Consolidation does not silently promote those
  unmerged changes; the branch remains available for a separate review.

## Validation

- Compared both GitHub default-branch histories and all source file trees.
- Python source parses; all six top-level R files parse.
- MCP tool discovery and Tukey statistics regression tests pass locally.
- All three regression tests pass against the merged source in a disposable
  directory on tyerschem2, including six real renders (classic and ggplot2,
  each with PNG, PDF, and SVG) and a quoted title.
- Every relative image/download link in the imported HTML guide resolves.
- Existing `testthat` tests could not run on the server because `testthat` is
  not installed. Locally, their plotting dependencies are missing.
- The local Docker daemon is unavailable. The MCP CI workflow now runs the
  new regressions in addition to its HTTP integration checks.

No live source, service configuration, credentials, or runtime database was
changed. Temporary validation files were removed after execution.
