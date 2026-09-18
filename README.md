# BoxPlotR

The canonical repository is [jwildenhain/BoxPlotR.shiny](https://github.com/jwildenhain/BoxPlotR.shiny). The older [shiny-boxplot](https://github.com/jwildenhain/shiny-boxplot) repository is retained for historical reference. This repository contains the Shiny application, stdio plotting engine, public MCP gateway, deployment configuration, and illustrated guide.

See [deployment instructions](deploy/boxplotr_mcp/README.md) and the [consolidation record](docs/consolidation-2026-09-18.md).

[![R Version](https://img.shields.io/badge/R-v4.6.0-blue.svg)](https://www.r-project.org/)
[![Shiny Version](https://img.shields.io/badge/Shiny-v1.13.0-blue.svg)](https://shiny.posit.co/)
[![Docker Environment](https://img.shields.io/badge/Docker-rocker/shiny:latest-blue.svg)](https://hub.docker.com/r/rocker/shiny)
[![Model Context Protocol](https://img.shields.io/badge/MCP-Compliant-success.svg)](https://modelcontextprotocol.io)
[![Whiskers](https://img.shields.io/badge/Whiskers-Tukey%20%7C%20Spear%20%7C%20Altman-green.svg)](#advanced-statistical-capabilities)
[![Confidence Intervals](https://img.shields.io/badge/CI-Median%20Notches%20%7C%20Mean%20CI-blue.svg)](#advanced-statistical-capabilities)

This is the repository for the Shiny application presented in **"BoxPlotR: a web tool for generation of box plots"** (Spitzer et al. 2014).

![BoxPlotR Modernized Preview](assets/boxplotr_preview.png)

Advanced Statistical Capabilities
---------------------------------

BoxPlotR v2.0.0 is engineered for biostatistics and rigorous exploratory data analysis, automating standard publication-quality data summaries:

### 1. Robust Whisker Calculations
* **Tukey Whiskers (`range = -1.5` in the custom BoxPlotR helper):** Whiskers extend to the most extreme data point within $1.5 \times \text{IQR}$ (Interquartile Range) from the box hinges. Outliers are plotted individually.
* **Spear Whiskers (`range = 0`):** Whiskers span the absolute minimum and maximum data values, treating no data points as outliers.
* **Altman Percentiles (`range > 0`):** Whiskers represent symmetric percentiles (e.g. 5th and 95th, or 2.5th and 97.5th percentiles) directly from the sample distribution—ideal for larger clinical datasets.

### 2. Precise Median Notches (Confidence Intervals)
Notches represent the $95\%$ confidence interval around the median, calculated using:
$$\text{Median} \pm 1.58 \times \frac{\text{IQR}}{\sqrt{n}}$$
If the notches of two box plots do not overlap, their medians differ with strong statistical evidence (approx. $95\%$ confidence level).

### 3. Sample-Size Weighted Box Widths (`varwidth`)
Align box widths proportionally to the square root of the number of observations ($\sqrt{n}$) to immediately alert reviewers to sample size variations across groups.

### 4. Mean & Confidence Interval Overlays
Superimpose sample means as high-contrast red diamonds, with customizable error bars showing $83\%$, $90\%$, or $95\%$ confidence intervals of the mean.

### 5. Multi-Modal Density Estimation
Toggle from standard summaries to **Violin Plots** or **Beanplots** to inspect kernel density bandwidths, skewness, and multimodal distributions.

---

Installation and Run Options
----------------------------

### 1) Run Natively via Docker (Recommended Isolated Deployment)

Deploy the fully-configured modern version natively without installing R dependencies directly onto your host system:

```bash
# Build the Docker image
docker build -t boxplotr:latest .

# Run the container (maps the container server to port 3838)
docker run -d -p 3838:3838 boxplotr:latest
```
Access the application in your web browser at: `http://localhost:3838`

### 2) Running the Isolated Test Suite
The container comes equipped with `testthat` to run the project's automated test suite inside the same isolated sandbox:

```bash
docker run --rm boxplotr:latest Rscript -e "library(testthat); test_dir('/srv/shiny-server/tests')"
```

---

### 3) Launch Natively from R and GitHub

Before running natively, ensure you have the latest versions of R and RStudio installed:

1. Launch R / RStudio Console.
2. Install the necessary packages:
   ```R
   install.packages(c("shiny", "beeswarm", "vioplot", "beanplot", "RColorBrewer", "readxl", "sm", "testthat", "ggplot2"))
   ```
3. Start the application directly:
   ```R
   shiny::runGitHub("BoxPlotR.shiny", "jwildenhain")
   ```

---

### 4) Install Natively on Shiny Server

To run BoxPlotR as a service on a dedicated Linux host (e.g. Ubuntu):

1. Install Shiny Server system dependencies:
   ```bash
   sudo apt-get update
   sudo apt-get install gdebi-core R-base
   ```
2. Download and install POSIT's Shiny Server from [posit.co/download/shiny-server/](https://posit.co/download/shiny-server/).
3. Pull the BoxPlotR repository into your Shiny server apps directory (e.g., `/srv/shiny-server/` or your custom `SHINY_APP_HOME`).
4. Install all required R packages system-wide:
   ```bash
   sudo R -e 'install.packages(c("shiny", "beeswarm", "vioplot", "beanplot", "RColorBrewer", "readxl", "sm", "ggplot2"), repos="https://cloud.r-project.org/")'
   ```
5. Restart the server service:
   ```bash
   sudo systemctl restart shiny-server
   ```

---

### 5) Public Model Context Protocol (MCP) service

BoxPlotR is available to MCP-compatible AI assistants over public Streamable HTTP:

- Endpoint: `https://mcp.chemgrid.org/boxplotr/`
- Tool: `generate_boxplot`
- Authentication: none required
- Dataset limit: 5 MiB per request
- Usage limit: 20 plot generations per client IP per UTC day
- Capacity: 10 plot jobs can run concurrently
- Execution timeout: 120 seconds
- Output formats: PNG, SVG and PDF

#### Codex

Register the public remote server directly:

```bash
codex mcp add boxplotr --url https://mcp.chemgrid.org/boxplotr/
```

Other clients, including Claude Desktop and Antigravity, can connect when they support remote Streamable HTTP MCP servers. No API key or custom authorization header is required.

#### Tool input

`generate_boxplot` accepts CSV or tab-separated data in `values`, with column headers and at least one data row. Its principal options are:

| Parameter | Values / purpose |
| --- | --- |
| `values` | CSV or TSV dataset; columns represent groups |
| `plot_type` | `boxplot`, `violin` or `beanplot` |
| `plot_engine` | `ggplot2` or the supported classic engine |
| `style_guide` | Rendering style, or `none` |
| `orientation` | `vertical` or `horizontal` |
| `log_scale` | Enable logarithmic scaling |
| `title`, `x_label`, `y_label` | Figure labels |
| `colors` | List of plot colours |
| `show_points`, `add_means` | Optional plot overlays |
| `output_format` | `png`, `svg` or `pdf` |

Example tool arguments:

```json
{
  "values": "Control,Treatment\n1.2,2.4\n1.5,2.9\n1.8,3.1",
  "plot_type": "boxplot",
  "plot_engine": "ggplot2",
  "title": "Treatment response",
  "show_points": true,
  "add_means": true,
  "output_format": "png"
}
```

The generated file is returned directly in the MCP response. Server-created temporary outputs are removed after their retention period; clients should save any plot they need to keep.

#### Illustrated guide and tested scenarios

The shareable guide at `https://boxplotr.chemgrid.org/mcp-guide.html` documents four plots generated through the live public endpoint:

- the bundled five-sample CSV with custom colours, jittered observations and mean markers;
- the bundled text scenario as a Nature-style violin plot;
- the bundled Excel scenario, checked and converted to CSV, on a logarithmic axis with Science styling;
- an original Economist Impact-inspired editorial plot using illustrative reconstructed values, with attribution to Figure 11a of the public LAC Infrascope 2021/22 report.

The editorial example demonstrates a visual treatment only. It does not reproduce or claim to contain the report's underlying data.

#### Privacy and analytics

Datasets and raw client addresses are not sent to Google Analytics. The service records operational usage in its private database and sends privacy-safe GA4 events for successful and failed plot requests. Analytics parameters include the application/interface, plot type, rendering engine, output format, processing duration, dataset dimensions and error category. Client addresses are immediately converted to one-way pseudonymous identifiers for quota enforcement and analytics.

### 6) Local stdio development server

The repository also includes `boxplotr_mcp_server.py` for local development over standard input/output. This local mode is separate from the hosted service and does not provide hosted authentication or quotas.

```bash
./boxplotr_mcp_server.py
```
