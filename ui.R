shinyUI(fluidPage(
  style = "padding: 30px; max-width: 1400px; margin: 0 auto;",
  div(
    class = "header-bar",
    h1("BoxPlotR", span("a web-tool for generation of box plots", class = "subtitle")),
    span("v2.1 Modernized", class = "version-badge")
  ),
  tags$head(
    tags$script(src = "https://chemgrid.org/chemgrid-analytics.js?v=20260905-2"),
    tags$title("BoxPlotR"),
    tags$style(HTML(
      "
      @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
      
      body, h1, h2, h3, h4, h5, h6, .shiny-text-output, label {
        font-family: 'Inter', sans-serif !important;
      }
      
      body {
        background: linear-gradient(135deg, #f0f7ff 0%, #f8fafc 100%);
        background-attachment: fixed;
        min-height: 100vh;
      }
      
      .header-bar {
        display: flex;
        align-items: center;
        justify-content: space-between;
        background: rgba(255, 255, 255, 0.7);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.4);
        padding: 18px 28px;
        border-radius: 20px;
        margin-top: 10px;
        margin-bottom: 28px;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.04);
      }
      
      .header-bar h1 {
        font-size: 26px;
        font-weight: 700;
        margin: 0;
        background: linear-gradient(135deg, #0f172a 0%, #0369a1 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        display: flex;
        align-items: baseline;
        gap: 12px;
      }
      
      .header-bar .subtitle {
        font-size: 15px;
        font-weight: 400;
        color: #64748b;
        -webkit-text-fill-color: #64748b;
      }
      
      .version-badge {
        background: linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%);
        color: white;
        font-size: 12px;
        font-weight: 600;
        padding: 4px 12px;
        border-radius: 99px;
        box-shadow: 0 4px 10px rgba(14, 165, 233, 0.2);
      }
      
      label.radio { display: inline-block; }
      .radio input[type=\"radio\"] { float: none; }
      
      /* Glassmorphism Sidebar */
      .well {
        max-width: 330px;
        background: rgba(255, 255, 255, 0.7) !important;
        backdrop-filter: blur(16px) !important;
        -webkit-backdrop-filter: blur(16px) !important;
        border: 1px solid rgba(255, 255, 255, 0.5) !important;
        border-radius: 20px !important;
        box-shadow: 0 15px 35px rgba(15, 23, 42, 0.04) !important;
        padding: 24px !important;
      }
      .span4 { max-width: 330px; }
      
      /* Inputs and Form Controls */
      input[type=\"text\"], input[type=\"number\"], select, textarea {
        background: rgba(255, 255, 255, 0.9) !important;
        border: 1px solid #cbd5e1 !important;
        border-radius: 10px !important;
        padding: 8px 12px !important;
        font-size: 14px !important;
        transition: all 0.2s ease-in-out !important;
        box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.02) !important;
        color: #1e293b !important;
      }
      input[type=\"text\"]:focus, input[type=\"number\"]:focus, select:focus, textarea:focus {
        border-color: #0ea5e9 !important;
        box-shadow: 0 0 0 4px rgba(14, 165, 233, 0.15), inset 0 2px 4px rgba(0, 0, 0, 0.02) !important;
        outline: none !important;
      }
      
      /* Premium Selectize styling to remove default blue focus bubble and match 34px height */
      .selectize-control .selectize-input {
        background: rgba(255, 255, 255, 0.9) !important;
        border: 1px solid #cbd5e1 !important;
        border-radius: 10px !important;
        padding: 6px 12px !important;
        font-size: 14px !important;
        transition: all 0.2s ease-in-out !important;
        box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.02) !important;
        color: #1e293b !important;
        height: 34px !important;
        min-height: 34px !important;
        line-height: 20px !important;
        box-sizing: border-box !important;
      }
      /* Prevent custom input[type='text'] styles from bloating the selectize inline search box */
      .selectize-control .selectize-input > input[type='text'] {
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
        padding: 0 !important;
        margin: 0 !important;
        height: auto !important;
        min-height: 0 !important;
        line-height: inherit !important;
        box-sizing: border-box !important;
      }
      .selectize-control .selectize-input.focus {
        border-color: #0ea5e9 !important;
        box-shadow: 0 0 0 4px rgba(14, 165, 233, 0.15), inset 0 2px 4px rgba(0, 0, 0, 0.02) !important;
        outline: none !important;
        border-radius: 10px !important;
      }
      .selectize-dropdown {
        border-radius: 12px !important;
        border: 1px solid rgba(0, 0, 0, 0.05) !important;
        box-shadow: 0 10px 25px rgba(15, 23, 42, 0.08) !important;
        overflow: hidden !important;
        background: #ffffff !important;
        padding: 6px 0 !important;
      }
      .selectize-dropdown .selected {
        background: linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%) !important;
        color: white !important;
        font-weight: 600 !important;
      }
      .selectize-dropdown .active {
        background: rgba(14, 165, 233, 0.08) !important;
        color: #0284c7 !important;
        font-weight: 500 !important;
      }
      
      label {
        font-weight: 600 !important;
        color: #334155 !important;
        font-size: 13.5px !important;
        margin-bottom: 6px !important;
      }
      
      /* Tabs Container */
      .nav-tabs {
        border-bottom: 2px solid #e2e8f0 !important;
        margin-bottom: 24px !important;
        display: flex;
        gap: 6px;
      }
      .nav-tabs > li {
        margin-bottom: -2px !important;
      }
      .nav-tabs > li > a {
        border: none !important;
        border-radius: 12px 12px 0 0 !important;
        padding: 10px 18px !important;
        color: #64748b !important;
        font-weight: 600 !important;
        background: transparent !important;
        transition: all 0.25s ease !important;
        font-size: 14.5px !important;
      }
      .nav-tabs > li > a:hover {
        color: #0f172a !important;
        background: rgba(14, 165, 233, 0.05) !important;
      }
      .nav-tabs > li.active > a, 
      .nav-tabs > li.active > a:focus, 
      .nav-tabs > li.active > a:hover {
        color: #ffffff !important;
        background: linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%) !important;
        box-shadow: 0 8px 20px rgba(14, 165, 233, 0.2) !important;
      }
      
      /* Buttons */
      .btn-default {
        background: linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%) !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 10px 18px !important;
        font-weight: 600 !important;
        font-size: 13.5px !important;
        box-shadow: 0 4px 14px rgba(14, 165, 233, 0.3) !important;
        transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1) !important;
        margin-bottom: 5px;
      }
      .btn-default:hover {
        background: linear-gradient(135deg, #0284c7 0%, #0369a1 100%) !important;
        color: #ffffff !important;
        transform: translateY(-1.5px) !important;
        box-shadow: 0 6px 20px rgba(14, 165, 233, 0.4) !important;
      }
      .btn-default:active {
        transform: translateY(0.5px) !important;
      }
      
      /* Card Layout for Plots */
      .plot-card {
        background: #ffffff !important;
        border-radius: 24px !important;
        padding: 28px !important;
        box-shadow: 0 20px 40px rgba(15, 23, 42, 0.05) !important;
        margin-top: 15px;
        margin-bottom: 28px;
        border: 1px solid rgba(226, 232, 240, 0.8) !important;
        transition: transform 0.3s ease;
      }
      .plot-card:hover {
        transform: translateY(-2px);
      }
      
      .table-card {
        background: #ffffff !important;
        border-radius: 20px !important;
        padding: 24px !important;
        box-shadow: 0 10px 30px rgba(15, 23, 42, 0.03) !important;
        border: 1px solid rgba(226, 232, 240, 0.8) !important;
      }
      
      .table-card table {
        width: 100%;
        border-collapse: separate;
        border-spacing: 0;
        margin-top: 12px;
      }
      .table-card th {
        background: #f8fafc;
        color: #475569;
        font-weight: 700;
        text-transform: uppercase;
        font-size: 11px;
        letter-spacing: 0.05em;
        padding: 12px 16px;
        border-bottom: 2px solid #e2e8f0;
      }
      .table-card td {
        padding: 12px 16px;
        border-bottom: 1px solid #f1f5f9;
        color: #334155;
        font-size: 13.5px;
      }
      .table-card tr:last-child td {
        border-bottom: none;
      }
      
      .controls-row {
        display: flex; gap: 10px; margin-top: 15px; flex-wrap: wrap;
      }
      
      h4 {
        font-size: 18px !important;
        font-weight: 700 !important;
        color: #0f172a !important;
        margin-top: 0 !important;
        margin-bottom: 16px !important;
      }
      h5 {
        font-size: 15px !important;
        font-weight: 600 !important;
        color: #1e293b !important;
        margin-top: 18px !important;
        margin-bottom: 10px !important;
      }
      p {
        color: #475569 !important;
        line-height: 1.6 !important;
        font-size: 14px !important;
      }
      
      /* Beautiful custom sliders */
      .irs-bar {
        background: linear-gradient(90deg, #0ea5e9 0%, #0284c7 100%) !important;
        border-top: 1px solid #0284c7 !important;
        border-bottom: 1px solid #0284c7 !important;
        height: 8px !important;
      }
      .irs-single {
        background: #0284c7 !important;
        font-weight: 600 !important;
        border-radius: 6px !important;
      }
      .irs-slider {
        background: #f8fafc !important;
        border: 2px solid #0284c7 !important;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1) !important;
        width: 18px !important;
        height: 18px !important;
        border-radius: 99px !important;
      }
      .irs-line {
        height: 8px !important;
        border-radius: 4px !important;
      }
    "
    ))
  ),
  sidebarLayout(
    sidebarPanel(
      conditionalPanel(
        condition = "input.tabs1=='About'",
        h4("Introduction")
      ),
      conditionalPanel(
        condition = "input.tabs1=='Data upload'",
        h4("Enter data"),
        radioButtons(
          "dataInput", "",
          list("Load sample data" = 1, "Upload file" = 2, "Paste data" = 3)
        ),
        conditionalPanel(
          condition = "input.dataInput=='1'",
          h5("Load sample data:"),
          radioButtons(
            "sampleData", "Load sample data",
            list(
              "Example 1 (100,76,16,76,41 data points)" = 1,
              "Example 2 (3 columns with 100 data points)" = 2,
              "Example 3 (Log scale, Excel format)" = 3
            )
          )
        ),
        conditionalPanel(
          condition = "input.dataInput=='2'",
          h5("Upload data file: "),
          fileInput(
            "upload", "", multiple = FALSE,
            accept = c(
              "text/csv", "text/comma-separated-values",
              "text/tab-separated-values", "text/plain",
              ".csv", ".tsv", ".xls", ".xlsx"
            )
          ),
          radioButtons(
            "fileSepDF", "Delimiter (ignored for Excel files):",
            list("Comma" = 1, "Tab" = 2, "Semicolon" = 3)
          ),
          HTML(paste(
            "<p>Supports .csv, .tab, .txt, .xls, and .xlsx. ",
            "Data in <a href=\"http://en.wikipedia.org/wiki/",
            "Delimiter-separated_values\">delimited text files </a> can be ",
            "separated by comma, tab or semicolon. Excel files will be read ",
            "automatically from the first sheet. </p>",
            sep = ""
          ))
        ),
        conditionalPanel(
          condition = "input.dataInput=='3'",
          h5("Paste data below:"),
          tags$textarea(id = "myData", rows = 10, cols = 5, ""),
          actionButton("clearText_button", "Clear data"),
          radioButtons(
            "fileSepP", "Separator:",
            list("Comma" = 1, "Tab" = 2, "Semicolon" = 3)
          )
        )
      ),
      conditionalPanel(
        condition = "input.tabs1=='Data visualization'",
        radioButtons("plotType", "", list("Boxplot" = 0, "Other" = 1)),
        conditionalPanel(
          condition = "input.plotType=='1'",
          radioButtons(
            "otherPlotType", "",
            list("Violin plot" = 0, "Bean plot" = 1)
          ),
          HTML(paste(
            "<p style=\"color:#808080\">Violin plots are generated with the ",
            "<a href=\"https://cran.r-project.org/web/packages/vioplot/",
            "index.html\">vioplot package</a>. Bean plots are generated ",
            "with the <a href=\"https://cran.r-project.org/web/packages/",
            "beanplot/index.html\">beanplot package</a>.</p>",
            sep = ""
          )),
          textInput(
            "myOtherPlotColours", "Colour(s):",
            value = c("light grey, white")
          ),
          conditionalPanel(
            condition = "input.otherPlotType=='0'",
            helpText("Colour of the 'violin area'"),
            textInput("violinBorder", "Border colour:", value = c("grey"))
          ),
          conditionalPanel(
            condition = "input.otherPlotType=='1'",
            helpText(paste(
              "up to 4 colours can be specified: area of the beans, lines ",
              "inside the bean, lines outside the bean, and average line ",
              "per bean",
              sep = ""
            )),
            textInput("beanBorder", "Border colour:", value = c("grey")),
            radioButtons(
              "beanPlotMedianMean", "Display: ",
              list("Median" = 0, "Mean" = 1)
            )
          )
        ),
        selectInput(
          "styleGuide", "Preset Style Guide:",
          list(
            "Custom / None" = "none",
            "Nature Journal" = "nature",
            "Science Journal" = "science",
            "The Economist" = "economist",
            "Financial Times" = "ft"
          ),
          selected = "none"
        ),
        radioButtons(
          "plotEngine", "Plot rendering engine:",
          list("Classic (Base R)" = "classic", "Modern (ggplot2)" = "ggplot")
        ),
        h4("Plot options"),
        checkboxInput("plotDataPoints", "Minimum number of data points", FALSE),
        conditionalPanel(
          condition = "input.plotDataPoints",
          numericInput(
            "nrOfDataPoints", "Data point limit: ",
            value = 5, min = 5
          )
        ),
        checkboxInput("showDataPoints", "Add data points", FALSE),
        conditionalPanel(
          condition = "input.showDataPoints",
          radioButtons(
            "datapointType", "",
            list("Default" = 0, "Bee swarm" = 1, "Jittered" = 2)
          ),
          sliderInput(
            "pointTransparency", "Transparency of data points",
            min = 0, max = 99, value = 50
          ),
          sliderInput(
            "pointSize", "Size of data points",
            min = 1, max = 20, value = 10
          ),
          HTML(paste(
            "<p style=\"color:#808080\">Using the <a href=\"http://www.",
            "cbs.dtu.dk/~eklund/beeswarm/\">beeswarm package</a>.</p>",
            sep = ""
          )),
          textInput("pointColors", "Colour(s):", value = c("black"))
        ),
        checkboxInput("showNrOfPoints", "Display number of data points", FALSE),
        conditionalPanel(
          condition = "input.plotType=='0'",
          checkboxInput(
            "whiskerDefinition", "Definition of whisker extent", FALSE
          ),
          conditionalPanel(
            condition = "input.whiskerDefinition",
            radioButtons(
              "whiskerType", "",
              list("Tukey" = 0, "Spear" = 1, "Altman" = 2)
            ),
            HTML(paste(
              "<p style=\"color:#808080\">Tukey - whiskers extend to data ",
              "points that are less than 1.5 x <a href=\"http://en.wikipedia.",
              "org/wiki/Interquartile_range\">IQR</a> away from 1st/3rd ",
              "<a href=:\"http://en.wikipedia.org/wiki/Quartile\">quartile",
              "</a>; Spear - whiskers extend to minimum and maximum values; ",
              "Altman - whiskers extend to 5th and 95th percentile ",
              "(use only if n>40)</p>",
              sep = ""
            ))
          ),
          checkboxInput("addMeans", "Add sample means", FALSE),
          conditionalPanel(
            condition = "input.addMeans",
            checkboxInput(
              "addMeanCI", "Add confidence intervals of means", FALSE
            ),
            conditionalPanel(
              condition = "input.addMeanCI",
              radioButtons(
                "meanCI", "Define confidence interval of means:",
                list("83%" = 83, "90%" = 90, "95%" = 95)
              )
            )
          ),
          checkboxInput("myVarwidth", "Variable width boxes", FALSE),
          helpText(paste(
            "Widths of boxes are proportional to square-roots of the ",
            "number of observations.",
            sep = ""
          )),
          checkboxInput("myNotch", "Add notches", FALSE),
          HTML(paste(
            "<p style=\"color:#808080\">+/-1.58*<a href=\"http://en.wikipedia.",
            "org/wiki/Interquartile_range\">IQR</a>/sqrt(n) - gives roughly ",
            "95% confidence that two medians differ (Chambers et al., 1983)",
            "</p>",
            sep = ""
          )),
          conditionalPanel(
            condition = "input.myNotch",
            HTML(paste(
              "<p>The notches are defined as +/-1.58*<a href=\"http://en.",
              "wikipedia.org/wiki/Interquartile_range\">IQR</a>/sqrt(n) and ",
              "represent the 95% <a href=\"http://en.wikipedia.org/wiki/",
              "Confidence_interval\">confidence interval</a> for each median. ",
              "Non-overlapping notches give roughly 95% confidence that two ",
              "medians differ, ie, in 19 out of 20 cases the population ",
              "medians (estimated based on the samples) are in fact ",
              "different (Chambers et al., 1983).</p>",
              sep = ""
            ))
          ),
          textInput("myColours", "Colour(s):", value = c("light grey, white")),
          helpText(paste(
            "Colours in HEX format can be chosen on ",
            "http://colorbrewer2.org/",
            sep = ""
          ))
        ),
        checkboxInput("labelsTitle", "Modify labels and title", FALSE),
        conditionalPanel(
          condition = "input.labelsTitle",
          checkboxInput("xaxisLabelAngle", "Rotate sample names", FALSE),
          textInput("myXlab", "X-axis label:", value = c("")),
          textInput("myYlab", "Y-axis label:", value = c("")),
          textInput("myTitle", "Boxplot title:", value = c("")),
          textInput("mySubtitle", "Boxplot subtitle:", value = c(""))
        ),
        checkboxInput("plotSize", "Adjust plot size", FALSE),
        conditionalPanel(
          condition = "input.plotSize",
          numericInput("myHeight", "Plot height:", value = 550),
          numericInput("myWidth", "Plot width:", value = 750)
        ),
        checkboxInput("fontSizes", "Change font sizes", FALSE),
        conditionalPanel(
          condition = "input.fontSizes",
          numericInput("cexTitle", "Title font size:", value = 14),
          numericInput("cexAxislabel", "Axis label size:", value = 14),
          numericInput("cexAxis", "Axis font size:", value = 12)
        ),
        h5("Orientation of box plots:"),
        radioButtons(
          "myOrientation", "",
          list("Vertical" = 0, "Horizontal" = 1)
        ),
        conditionalPanel(
          condition = "input.myOrientation=='0'",
          h5("Y-axis range (eg., '0,10'):"),
          textInput("ylimit", "", value = "")
        ),
        conditionalPanel(
          condition = "input.myOrientation=='1'",
          h5("X-axis range (eg., '0,10'):"),
          textInput("xlimit", "", value = "")
        ),
        checkboxInput(
          "logScale", "Change to log scale (only for data >0)", FALSE
        ),
        h5("Add grid: "),
        radioButtons(
          "addGrid", "",
          list("None" = 0, "X & Y" = 1, "X only" = 2, "Y only" = 3)
        )
      )
    ),
    mainPanel(
      tabsetPanel(
        tabPanel(
          "About",
          HTML(paste(
            "<br><p>This application was developed with Nature Methods and ",
            "you can find the publication <a href=\"http://www.nature.com/",
            "nmeth/journal/v11/n2/full/nmeth.2811.html\">here</a>. ",
            "The BoxPlotR has also been mentioned in this <a href=\"http://",
            "www.nature.com/nmeth/journal/v11/n2/full/nmeth.2837.html\">",
            "editorial</a> and this <a href=\"http://blogs.nature.com/",
            "methagora/2014/01/bring-on-the-box-plots-boxplotr.html\">",
            "blog entry</a>. Nature methods also dedicated a <a href=\"",
            "http://www.nature.com/nmeth/journal/v11/n2/full/nmeth.2807.html\"",
            ">Points of View</a> and a <a href=\"http://www.nature.com/nmeth/",
            "journal/v11/n2/full/nmeth.2813.html\">Points of Significance",
            "</a> column to box plots. We hope that you find the <a href= ",
            "\"http://www.nature.com/nmeth/journal/v11/n2/full/nmeth.2811.html",
            "\">BoxPlotR</a> useful and we welcome suggestions for ",
            "additional features by our users. </p>",
            sep = ""
          )),
          h5("Support BoxPlotR"),
          HTML(paste(
            "<p>Please consider supporting the development and maintenance ",
            "of BoxPlotR with a <a href=\"https://www.paypal.com/pools/c/",
            "9oezkBOeV3\" target=\"_blank\">donation</a>.</p>",
            sep = ""
          )),
          h5("Software references"),
          HTML(paste(
            "<p>R Development Core Team. <i><a href=\"http://www.r-project.",
            "org/\">R</a>: A Language and Environment for Statistical ",
            "Computing.</i> R Foundation for Statistical Computing, Vienna ",
            "(2013) <br> RStudio and Inc. <i><a href=\"http://www.rstudio.com/",
            "shiny/\">shiny</a>: Web Application Framework for R.</i> R ",
            "package version 0.5.0 (2013) <br> Adler, D. <i><a href=\"http://",
            "cran.r-project.org/web/packages/vioplot/index.html\">vioplot",
            "</a>: Violin plot.</i> R package version 0.2 (2005)<br> Eklund, ",
            "A. <i><a href=\"http://cran.r-project.org/web/packages/beeswarm/",
            "index.html\"> beeswarm</a>: The bee swarm plot, an alternative ",
            "to stripchart.</i> R package version 0.1.5 (2012)<br> Kampstra, ",
            "P. <i><a href=\"http://cran.r-project.org/web/packages/beanplot/",
            "index.html\">Beanplot</a>: A Boxplot Alternative for Visual ",
            "Comparison of Distributions.</i> Journal of Statistical ",
            "Software, Code Snippets 28(1). 1-9 (2008) <br> Neuwirth, E. ",
            "<i><a href=\"http://cran.r-project.org/web/packages/RColorBrewer/",
            "index.html\">RColorBrewer</a>: ColorBrewer palettes.</i> R ",
            "package version 1.0-5. (2011)</p>",
            sep = ""
          )),
          h6(paste(
            "This application was created by the Tyers and Rappsilber labs. ",
            "Please send bugs and feature requests to Michaela Spitzer ",
            "(michaela.spitzer(at)gmail.com) and Jan Wildenhain ",
            "(jan.wildenhain(at)gmail.com). This application uses the shiny ",
            "package from RStudio.",
            sep = ""
          ))
        ),
        tabPanel(
          "Data upload",
          tableOutput("filetable"),
          h6("This application was created by the Tyers and Rappsilber labs.")
        ),
        tabPanel(
          "Data visualization",
          div(
            class = "controls-row",
            downloadButton("downloadPlotEPS", "Download eps-file"),
            downloadButton("downloadPlotPDF", "Download pdf-file"),
            downloadButton("downloadPlotSVG", "Download svg-file")
          ),
          div(
            class = "plot-card",
            plotOutput("boxPlot", height = "100%", width = "100%")
          ),
          div(
            class = "table-card",
            h4("Box plot statistics"),
            tableOutput("boxplotStatsTable")
          ),
          br(),
          h6("This application was created by the Tyers and Rappsilber labs.")
        ),
        tabPanel(
          "Figure legend template",
          h5("Box plot description for figure legend:"),
          textOutput("FigureLegend"),
          h5("Further information to be added to the figure legend:"),
          p("What do the box plots show, explain colours if used."),
          downloadButton(
            "downloadBoxplotData", "Download box plot data as .CSV file"
          ),
          h6("This application was created by the Tyers and Rappsilber labs.")
        ),
        tabPanel(
          "News",
          h5("September 13, 2026"),
          HTML(paste(
            "<p><b>Public BoxPlotR MCP launch:</b> AI assistants can now connect directly to <code>https://mcp.chemgrid.org/boxplotr/</code> without an account or API key. ",
            "The live service was verified through a registered Codex client using the bundled scenarios. A new <a href=\"mcp-guide.html\" target=\"_blank\">illustrated MCP guide</a> shows custom colours, ",
            "raw-point and mean overlays, violin geometry, logarithmic axes, journal styles and an original Economist Impact-inspired editorial example.</p>",
            sep = ""
          )),
          h5("August 11, 2026"),
          HTML(paste(
            "<p><b>MCP output delivery update:</b> The BoxPlotR MCP server now returns generated plot files directly in the JSON-RPC tool response, ",
            "while still saving the file to <code>output_path</code>. PNG and SVG outputs are returned as MCP <code>image</code> content, ",
            "and PDF outputs are returned as MCP <code>resource</code> content with a base64 payload. This makes BoxPlotR easier to use from AI assistants ",
            "because the generated figure can be displayed inline without separately retrieving the saved file.</p>",
            sep = ""
          )),
          h5("May 30, 2026"),
          HTML(paste(
            "<p>Introduced support for the <b>Modern (ggplot2)</b> rendering engine! ",
            "Users can now seamlessly toggle between Classic (Base R) and Modern (ggplot2) plot rendering. ",
            "Implemented stunning ggplot2 box plots, violin plots, and bean plots with real-time customized fill colors, ",
            "alpha levels, jittered raw data point overlays, red sample means, and error bars showing confidence intervals.</p>",
            sep = ""
          )),
          h5("May 29, 2026"),
          HTML(paste(
            "<p>Upgraded the application environment and Docker container configurations to fully support ",
            "the latest R version 4.6.0 and Shiny version 1.13.0, ensuring long-term compatibility, stability, ",
            "and security. In addition, the application's user interface has been fully modernized with a premium ",
            "glassmorphic theme, responsive page layouts, customized form controls, and improved plot statistics tables.</p>",
            sep = ""
          )),
          h5("April 16, 2026"),
          HTML("<p>Number of sessions increased to 50.</p>"),
          h5("April 8, 2026"),
          HTML(paste(
            "<p>The shiny server backend has been updated. The number of ",
            "concurrent sessions has been limited to 15 and the session ",
            "idle timeout set to 10 minutes. We are currently reworking ",
            "the code to support the latest R and shiny versions.</p>",
            sep = ""
          )),
          h5("January 17, 2021"),
          HTML(paste(
            "<p>There are several recent updates. The jitter of points is ",
            "now consistent for all samples. When data points are added to ",
            "the plot, the size can now be modified with sliders.</p>",
            sep = ""
          ))
        ),
        tabPanel(
          "MCP API",
          h4("Use BoxPlotR directly from an AI assistant"),
          HTML(paste(
            "<p>BoxPlotR provides a public Model Context Protocol service using Streamable HTTP. No account or API key is required.</p>",
            "<ul>",
            "<li><b>Endpoint:</b> <code>https://mcp.chemgrid.org/boxplotr/</code></li>",
            "<li><b>Tool:</b> <code>generate_boxplot</code></li>",
            "<li><b>Authentication:</b> None required.</li>",
            "<li><b>Limits:</b> 5 MiB per dataset, 20 plot generations per client IP per UTC day, and 10 simultaneous plot jobs.</li>",
            "<li><b>Input:</b> CSV or TSV text in <code>values</code>, with one numeric group per column.</li>",
            "<li><b>Formats:</b> Set <code>output_format</code> to <code>png</code>, <code>svg</code> or <code>pdf</code>. PNG is returned as an MCP image; SVG and PDF as embedded file resources.</li>",
            "</ul>",
            "<h4>Codex setup</h4>",
            "<pre><code>codex mcp add boxplotr --url https://mcp.chemgrid.org/boxplotr/</code></pre>",
            "<p>Claude Desktop, Antigravity and other clients can use the same endpoint when configured for remote Streamable HTTP MCP. No authorization header is required.</p>",
            "<p><a class=\"btn btn-primary\" href=\"mcp-guide.html\" target=\"_blank\">Open the illustrated MCP guide</a></p>",
            "<h4>Example tool arguments</h4>",
            "<pre><code>{\n  \"values\": \"Control,Treatment\\n1.2,2.4\\n1.5,2.9\\n1.8,3.1\",\n  \"plot_type\": \"boxplot\",\n  \"plot_engine\": \"ggplot2\",\n  \"title\": \"Treatment response\",\n  \"show_points\": true,\n  \"add_means\": true,\n  \"output_format\": \"png\"\n}</code></pre>",
            "<h4>Privacy and analytics</h4>",
            "<p>The service records privacy-safe usage events. Datasets and raw client addresses are never sent to Google Analytics. Client addresses are immediately converted to one-way pseudonymous identifiers for quota enforcement and analytics. Analytics records the interface, plot options, processing time, dataset dimensions and success/failure.</p>",
            sep = ""
          ))
        ),
        tabPanel(
          "FAQ",
          h5("Q: I have trouble editing the graphic files."),
          p(paste(
            "A: For EPS files make sure to 'ungroup' all objects so they ",
            "can be edited independently. In Adobe Illustrator you will ",
            "also need to use the 'release compound path' command.",
            sep = ""
          )),
          h5("Q: How do I install Docker, clone BoxPlotR from GitHub, and run it in a container?"),
          HTML(paste(
            "<p>A: Here is the step-by-step guide to installing Docker, pulling the repository from GitHub, and running BoxPlotR inside a container:</p>",
            "<ol>",
            "<li><b>Install Docker</b>:",
            "<ul>",
            "<li><b>Windows / macOS</b>: Download and install <a href=\"https://www.docker.com/products/docker-desktop/\" target=\"_blank\">Docker Desktop</a>.</li>",
            "<li><b>Linux (Ubuntu/Debian)</b>: Run these terminal commands to install and start Docker:<br>",
            "<pre><code>sudo apt-get update\nsudo apt-get install -y docker.io\nsudo systemctl start docker\nsudo systemctl enable docker</code></pre></li>",
            "</ul></li>",
            "<li><b>Clone the Repository from GitHub</b>:<br>",
            "<pre><code>git clone https://github.com/jwildenhain/BoxPlotR.shiny.git\ncd BoxPlotR.shiny</code></pre></li>",
            "<li><b>Build the pre-configured Docker image</b>:<br>",
            "<pre><code>docker build -t boxplotr .</code></pre></li>",
            "<li><b>Run the container</b>:<br>",
            "<pre><code>docker run -d -p 3838:3838 --name boxplotr-app boxplotr</code></pre>",
            "<p>Now you can open <code>http://localhost:3838</code> in your browser to run the full glassmorphic web app!</p></li>",
            "</ol>",
            sep = ""
          )),
          h5("Q: Does BoxPlotR support integration with AI coding assistants (e.g. Claude Desktop, Cursor, Antigravity)?"),
          HTML(paste(
            "<p>A: Yes. Register the public Streamable HTTP endpoint with <code>codex mcp add boxplotr --url https://mcp.chemgrid.org/boxplotr/</code>, ",
            "or enter the same URL in another remote-MCP client. No account, API key or SSH access is required. The <code>generate_boxplot</code> tool returns the generated figure directly in the MCP response. ",
            "See the <a href=\"mcp-guide.html\" target=\"_blank\">illustrated MCP guide</a> for tested examples.</p>",
            sep = ""
          )),
          h5("Q: Can I run the MCP server locally?"),
          HTML("<p>A: Run <code>boxplotr_mcp_server.py</code> over standard I/O (<code>stdio</code>). The local tool supports both rendering engines and returns the generated figure in its MCP response while saving it to <code>output_path</code>.</p>"),
          h5("Q: Which plot modifications can an AI assistant request?"),
          HTML(paste(
            "<p>A: The public tool supports box, violin and bean plots; ggplot2 and supported classic rendering; Nature, Science, Economist and Financial Times styles; ",
            "vertical or horizontal orientation; linear or logarithmic axes; custom titles, axis labels and colours; raw-point overlays; mean markers for box plots; and PNG, SVG or PDF output. ",
            "Requests are limited to 5 MiB and 20 plot generations per client IP per UTC day.</p>",
            sep = ""
          )),
          h5("Q: Which options are available through the public MCP endpoint?"),
          HTML("<p>A: The public tool accepts <code>values</code>, <code>plot_type</code>, <code>plot_engine</code>, <code>style_guide</code>, <code>orientation</code>, <code>log_scale</code>, <code>title</code>, <code>x_label</code>, <code>y_label</code>, <code>colors</code>, <code>show_points</code>, <code>add_means</code> and <code>output_format</code>. Use six-digit hexadecimal colours such as <code>#2563eb</code>. Notches, variable box widths, mean confidence intervals, subtitles, grid selection and point-style controls are local stdio options, not public tool parameters.</p>"),
          h5("Q: What does the public MCP endpoint return?"),
          HTML("<p>A: Set <code>output_format</code> to <code>png</code>, <code>svg</code> or <code>pdf</code>. The response contains a text summary plus a PNG image or an embedded SVG/PDF resource with a MIME type and base64 <code>blob</code>. Save the returned attachment in your client. The public tool chooses a temporary server path; it does not accept <code>output_path</code>.</p>"),
          h5("Q: How do output formats work with the local stdio server?"),
          HTML(paste(
            "<p>A: Set the requested format by changing the file extension in <code>output_path</code>. Use <code>.png</code> for a raster image, ",
            "<code>.svg</code> for an editable vector image, or <code>.pdf</code> for a publication-ready document. The MCP response includes a text summary plus the file payload: ",
            "PNG and SVG are returned as MCP <code>image</code> content, while PDF is returned as MCP <code>resource</code> content with MIME type and base64 blob. ",
            "The same file is also saved on disk at <code>output_path</code> for reproducibility.</p>",
            sep = ""
          )),
          h5("Q: How can I run the local stdio MCP server inside a Shiny Docker container?"),
          HTML(paste(
            "<p>A: You can easily route MCP commands to run inside the active BoxPlotR Docker container. ",
            "First, make sure the Dockerfile installs Python 3 (e.g., <code>RUN apt-get update && apt-get install -y python3</code>). ",
            "Then, add the following configuration to your AI assistant's configuration file (e.g., <code>claude_desktop_config.json</code>) ",
            "to execute the server via standard input/output redirection:</p>",
            "<pre><code>{\n  \"mcpServers\": {\n    \"boxplotr-docker\": {\n      \"command\": \"docker\",\n      \"args\": [\n        \"exec\",\n        \"-i\",\n        \"boxplotr-container-name\",\n        \"python3\",\n        \"/srv/shiny-server/boxplotr_mcp_server.py\"\n      ]\n    }\n  }\n}</code></pre>",
            "<p>This maps standard stdio streams directly into the running R environment in the container without exposing ports!</p>",
            sep = ""
          )),
          h5("Q: How can I test the MCP server locally with a JSON-RPC request?"),
          HTML(paste(
            "<p>A: You can test the stdio MCP server from your command line by piping a standard JSON-RPC 2.0 <code>tools/call</code> request directly into the Python script. Since the server operates over line-by-line stdio (<code>readline()</code>), the JSON-RPC request payload must be sent as a single line (no newlines within the JSON string itself). Here is a concrete JSON example using a wide-format dataset (where columns represent samples) to generate a ggplot2 box plot with the Economist style preset:</p>",
            "<pre><code>{\n  \"jsonrpc\": \"2.0\",\n  \"id\": 1,\n  \"method\": \"tools/call\",\n  \"params\": {\n    \"name\": \"generate_boxplot\",\n    \"arguments\": {\n      \"data_config\": {\n        \"values\": \"SampleA,SampleB\\n12.5,8.9\\n14.2,10.1\\n15.8,11.5\\n13.1,9.4\"\n      },\n      \"visualization\": {\n        \"plot_type\": \"boxplot\",\n        \"plot_engine\": \"ggplot2\",\n        \"style_guide\": \"economist\",\n        \"orientation\": \"vertical\",\n        \"log_scale\": false\n      },\n      \"styling\": {\n        \"title\": \"Comparison of Sample A and Sample B\",\n        \"xlab\": \"Group\",\n        \"ylab\": \"Value\",\n        \"colors\": [\"#0ea5e9\", \"#ef4444\"],\n        \"add_grid\": \"y\"\n      },\n      \"overlays\": {\n        \"show_points\": true,\n        \"point_type\": \"jittered\",\n        \"point_size\": 1.2,\n        \"point_transparency\": 30,\n        \"add_means\": true,\n        \"notch\": true\n      },\n      \"output_path\": \"/absolute/path/to/output_plot.png\"\n    }\n  }\n}</code></pre>",
            "<p>Run the following command in your terminal (with the JSON payload minified onto a single line) to test execution:</p>",
            "<pre><code>echo '{\"jsonrpc\": \"2.0\", \"id\": 1, \"method\": \"tools/call\", \"params\": {\"name\": \"generate_boxplot\", \"arguments\": {\"data_config\": {\"values\": \"SampleA,SampleB\\n12.5,8.9\\n14.2,10.1\\n15.8,11.5\\n13.1,9.4\"}, \"visualization\": {\"plot_type\": \"boxplot\", \"plot_engine\": \"ggplot2\", \"style_guide\": \"economist\", \"orientation\": \"vertical\", \"log_scale\": false}, \"styling\": {\"title\": \"Comparison of Sample A and Sample B\", \"xlab\": \"Group\", \"ylab\": \"Value\", \"colors\": [\"#0ea5e9\", \"#ef4444\"], \"add_grid\": \"y\"}, \"overlays\": {\"show_points\": true, \"point_type\": \"jittered\", \"point_size\": 1.2, \"point_transparency\": 30, \"add_means\": true, \"notch\": true}, \"output_path\": \"assets/mcp_test_plot.png\"}}}' | python3 boxplotr_mcp_server.py</code></pre>",
            "<p>This command runs the Python server, triggers the R script dynamically, and outputs a JSON-RPC response with two content items: ",
            "a text summary and the generated plot image payload. For PNG output, the second content item has <code>type: image</code> and <code>mimeType: image/png</code>. ",
            "You can change <code>assets/mcp_test_plot.png</code> to <code>assets/mcp_test_plot.svg</code> or <code>assets/mcp_test_plot.pdf</code> to test vector outputs.</p>",
            sep = ""
          ))
        ),
        id = "tabs1"
      )
    )
  )
))
