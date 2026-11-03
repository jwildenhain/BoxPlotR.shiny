# BoxPlotR search visibility release — 2 November 2026

## Changes

- Replaced the generic homepage title with a descriptive search title and
  added a concise meta description, canonical URL, robots directive, Open
  Graph metadata and Twitter card metadata.
- Added `SoftwareApplication` JSON-LD linking BoxPlotR to its canonical GitHub
  repository and Nature Methods publication.
- Added visible introductory copy and crawlable links near the top of the
  Shiny page.
- Added `robots.txt` and an XML sitemap.
- Added four focused, internally linked static guides for box plots, violin
  plots, vector publication exports and whisker definitions.
- Reused existing example figures so the new pages include descriptive image
  alternative text without adding duplicate binary assets.
- Added the verified TogoTV BoxPlotR walkthrough to the box-plot guide with a
  privacy-enhanced lazy YouTube embed and `VideoObject` structured data, plus
  links to four additional BoxPlotR-specific YouTube tutorials.
- Added responsive layout rules for the header, guide navigation, Shiny tabs,
  generated plot and statistics table, and added accessible labels to the
  X- and Y-axis range fields.

## Validation

- Exercised the sample-data workflow at 1440×1000, 1024×768 and 390×844 in a
  real browser. All three sizes render without page-level horizontal overflow.
- Verified classic and ggplot2 rendering, raw-point plot regeneration, the
  statistics table, and PDF and SVG downloads.
- Verified the responsive video guide and found no application console errors.
- Passed the SEO regression suite, R syntax validation, ggplot regression test
  and violin edge-case tests.

## Deployment follow-up

After deploying `ui.R` and `www/`, verify the homepage and every sitemap URL,
then submit `https://boxplotr.chemgrid.org/sitemap.xml` in Google Search
Console and Bing Webmaster Tools. Request recrawling of the homepage and the
four new guide URLs.

The historical HTTP URL already redirects to the canonical site. The
historical HTTPS hostname `shiny.chemgrid.org` currently presents a certificate
that does not cover that hostname. Add the hostname to a valid certificate
before relying on its HTTPS redirect; redirects cannot repair a TLS name error
that occurs before the HTTP request reaches Apache.

Search rankings are not guaranteed. The static guides provide useful,
query-specific content; future work should earn relevant links from laboratory,
university, publication and scientific-software resource pages rather than
creating repetitive keyword pages.
