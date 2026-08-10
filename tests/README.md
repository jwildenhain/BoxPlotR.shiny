# Test suite

Run the R and MCP regression tests from the repository root:

```sh
Rscript tests/test_ggplot_boxplot.R
Rscript tests/test_vioplot_edge_cases.R
python3 -m unittest tests/test_mcp_server.py
```

The browser suite expects an installed Playwright package and a running Shiny Server instance serving this application. Set the application URL if it is not the default:

```sh
BOXPLOTR_URL=http://127.0.0.1:3838 node tests/playwright_boxplotr.mjs
```

It verifies initial rendering, both plotting engines, logarithmic notches, PDF download, and invalid-data feedback.
