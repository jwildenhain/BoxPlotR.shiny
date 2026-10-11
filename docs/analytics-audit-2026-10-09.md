# ChemGrid analytics audit — 9 October 2026

## Published dashboard

**ChemGrid tools — Website and MCP usage** is published in account `62191002`, central ChemGrid property `383641389`, under **Reports → Custom dashboards**. Dashboard/report ID: `16094479806`; collection ID: `16094476771`.

Dashboard URL: https://analytics.google.com/analytics/web/#/a62191002p383641389/reports/builder/16094479806

Saved tables:
- Active users and event count by **Application Name** (`app_name`).
- Active users and event count by **Interface** (`interface`) and **Application Name**.

The new event-scoped Interface custom dimension was registered on 9 October. Newly labelled `web` and `mcp` data may take 24–48 hours to populate normal reports. Historical events remain `(not set)` for this new dimension. Event names can distinguish MCP events immediately in Realtime.

## Tool properties and collection

All five properties exist in the account and are starred for access from the property picker's Favorites tab.

| Tool | Property ID | Measurement ID | Bootstrap tag |
| --- | --- | --- | --- |
| ChemGrid | 383641389 | G-LMCPLNFJPV | G-LMCPLNFJPV |
| MolClass | 552950102 | G-0S0YE5CENT | G-0S0YE5CENT |
| BoxPlotR | 552903567 | G-J42YT6MQP8 | GT-W6J48KPS |
| CheckerboardR | 552923653 | G-KFX6ZPPV76 | G-KFX6ZPPV76 |
| GrowthCurve | 552944438 | G-2WLRQJV9NP | G-2WLRQJV9NP |

Each website configures its individual tag and the central ChemGrid destination, once per destination. Browser events carry `app_name` and `interface=web`. Shared MCP events already use `app_name` and `interface=mcp` in the central property. The shared website script is served from `/var/www/html/chemgrid-analytics.js`, including MolClass's alias. Tested local source: `deploy/analytics/chemgrid-analytics.js`.

## Fixes deployed

1. CheckerboardR was missing the shared analytics script. Added one script tag to live `/srv/shiny-server/checkerboardr/ui.R` and local `/home/jw/Source/CheckerBoardR.shiny/ui.R`. R syntax validation passed. Backup: `/var/backups/checkerboardr-analytics-20261009-045048/ui.R`.
2. BoxPlotR's measurement-ID bootstrap URL returned HTTP 404. The signed-in Analytics installation panel supplied working Google tag `GT-W6J48KPS`. Updated the shared script to load/configure that tag, ran Google's installation test successfully, and confirmed manual setup. BoxPlotR events subsequently appeared in its own property and the central property.
3. Added website collection into the central property for all tools, preserving individual website destinations. Added explicit `interface=web` labels and registered Interface in the central Analytics property.

Shared-script rollback backup: `/var/backups/chemgrid-analytics-20261009-053309/chemgrid-analytics.js`. Intermediate backup before BoxPlotR bootstrap correction: `chemgrid-analytics.before-boxplotr-tag.js` in the same directory. Final deployed SHA-256: `1799b74802b37565da4de08cbba664c7b63422b391b6cb46dd4e13fe65438b0b`.

## Verified evidence

- Every final Google tag bootstrap endpoint returned HTTP 200 with JavaScript.
- All five live websites loaded their expected tag. The deployed shared script matches the tested local source; cache headers enforce revalidation.
- Routing checks covered both destinations, one configuration per destination, website/app labels, query-string privacy and duplicate prevention on all five hosts. Known-bot exclusion also passed.
- Google installation test for BoxPlotR: `Your Google tag was correctly detected on your website.` Confirmed setup.
- Google installation panel for CheckerboardR: `Congratulations! Google tag is already installed`.
- BoxPlotR Realtime in its own property showed one website user and `app_view`, `page_view`, `first_visit`, `session_start` after repair.
- CheckerboardR Realtime showed one website user and `app_view`, `page_view`, `first_visit`, `session_start` after restoring its script.
- Central Realtime showed BoxPlotR browser views alongside `mcp_plot_generated` and `boxplotr_mcp_user_activity` from a fresh public MCP plot request. Inspected the collected `page_view` parameter value `interface=web` directly in Realtime.
- Central dashboard historical table showed 54 BoxPlotR events and 2 MolClass events for Sep 11–Oct 8; these are observed counts for that range, not general usage estimates.
- MolClass's property had 5 active users and GrowthCurve's had 1 active user in the last seven days. ChemGrid's property had existing recorded traffic.

## Limits

Custom-dimension processing is asynchronous. New routing applies going forward and does not backfill past website traffic into the central property. Pseudonymous MCP clients are not necessarily individual people. Public shared MCP collection was established for ChemGrid, MolClass and BoxPlotR; no public CheckerboardR or GrowthCurve MCP collection was established by this audit. No account access permissions, API secrets or MCP runtime configuration were changed. The source changes are recorded on the `codex/transparent-exports` release branch together with the related BoxPlotR export work.

## Follow-up: visitors and detailed activity

The central dashboard now also contains active-user line charts grouped by Application Name, with Day and Week granularity respectively. Weekly values count users within the week, rather than summing daily users.

Shared website telemetry now adds `file_extension` and `output_format` to export requests for BoxPlotR, CheckerboardR and GrowthCurve. PDF/SVG/EPS and CSV controls are mapped explicitly from the live applications. Disabled exports and cancelled file selections do not emit action events. Upload events record only file count, never filenames or contents. Website events explicitly route to both the app's measurement ID and the central destination.

ChemGrid website search events count successful compound, structure and gene search responses. They contain `search_type` and a predefined `search_method`; query text and SMILES are excluded. Repeated search requests, including pagination, count as operations. Cached results do not issue a new request.

ChemGrid's shared MCP callback now categorizes completed API operations (search, compound detail, analogues, scaffold family, screen list/results, gene network, measurements, screening summary, SONAR and structural prediction). Existing `chemgrid_mcp_user_activity` events carry `activity_type` and search-category parameters where applicable. One MCP tool can perform multiple API operations. BoxPlotR MCP plot events also carry `file_extension` for a shared export-format breakdown. MCP user identity remains pseudonymous.

Registered event-scoped dimensions: Search Type (`search_type`), Search Method (`search_method`), Activity Type (`activity_type`), Export Format (`output_format`). The built-in File extension parameter is also sent, but the dashboard uses Export Format for compatibility with the new dashboard editor.

Live gateway changes were applied incrementally, preserving all 19 public MCP tools and MolClass integration. Live health returned `ok`, and a fresh public ChemGrid search returned `isError=False`. Category tests verified omission of query text, SMILES and compound identifiers. Website tests verified all three apps' upload/export events, explicit central routing, response preservation and exclusion of failed/external searches. Test: `node tests/test_chemgrid_analytics.cjs`.

Backup before this follow-up: `/var/backups/chemgrid-actions-20261009/` contains the previous shared script, gateway `app.py`, and `chemgrid_tools.py`. The second script backup `chemgrid-analytics.before-explicit-routing.js` precedes explicit routing. Final shared-script SHA-256: `011acd6379facd3b40d8495088044fc9417a97cdece8aae38fb9d952ba536cd2`. Gateway patch is recorded in `deploy/analytics/gateway/app-analytics.patch`; the deployed category module is recorded beside it.

CheckerboardR currently exposes a local stdio MCP script. GrowthCurve has no deployed MCP service. This follow-up instruments their websites; it does not create new public MCP services or collect telemetry from users' local scripts.

The separate jw-netsolutions account form is prepared. Google requires an account-creation agreement and legal country selection; the user has been asked to complete that step. The existing property has not yet been moved.

Final dashboard structure (10 cards): application totals; website/MCP split; daily website visitors; weekly website visitors; upload users/count by application; export users/count by application, event name and format; search users/count by type, method and interface; ChemGrid website views; ChemGrid MCP operation categories; website users by country and application. Visitor/country cards filter `page_view`, upload card filters `file_upload`, exports select `file_download` or `mcp_plot_generated`. Weekly active users are deduplicated within each week. Country is a browser aggregate, not individual user identification.

Browser upload automation could not open Shiny's file chooser in the in-app browser. Upload handling was verified through the event tests, including file-count-only telemetry and cancelled selections; a complete live file-upload flow was not verified during this follow-up. Google dashboard custom card titles did not persist through Save, including native typing; saved charts use automatic titles. The daily chart has Day granularity and the following chart has Week granularity.

A fresh public MCP compound search and a transparent/unfilled BoxPlotR PDF generation both returned `isError=False` after the gateway update. Central Analytics Realtime subsequently exposed the new `activity_type`, `search_method` and `interface` keys on `chemgrid_mcp_user_activity`. New website export-format and search-category values have not yet been independently confirmed in Realtime; live pages load both destinations and event regression tests pass. Historical website collection was verified earlier in this audit.
