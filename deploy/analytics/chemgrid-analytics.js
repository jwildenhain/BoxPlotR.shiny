(function () {
  "use strict";
  var measurementIds = {
    "chemgrid.org": "G-LMCPLNFJPV",
    "www.chemgrid.org": "G-LMCPLNFJPV",
    "molclass.chemgrid.org": "G-0S0YE5CENT",
    "boxplotr.chemgrid.org": "G-J42YT6MQP8",
    "checkerboardr.chemgrid.org": "G-KFX6ZPPV76",
    "growthcurve.chemgrid.org": "G-2WLRQJV9NP"
  };
  var measurementId = measurementIds[window.location.hostname];
  var trackedHosts = new Set(["chemgrid.org","www.chemgrid.org","molclass.chemgrid.org","boxplotr.chemgrid.org","checkerboardr.chemgrid.org","growthcurve.chemgrid.org"]);
  var knownBot = /(?:SleepBot|meta-webindexer|Baiduspider|bingbot|PetalBot|Applebot|UptimeRobot|Sogou web spider|GoogleOther|Googlebot|crawler|spider|bot\b)/i.test(navigator.userAgent || "");
  if (knownBot) return;
  var legacyPath = /^\/cgm(?:\/|$)/.test(window.location.pathname);
  if (legacyPath || !trackedHosts.has(window.location.hostname) || !measurementId || window.__chemgridAnalyticsLoaded) return;
  window.__chemgridAnalyticsLoaded = true;
  window.dataLayer = window.dataLayer || [];
  window.gtag = window.gtag || function () { window.dataLayer.push(arguments); };
  // BoxPlotR's Analytics setup supplies this Google tag ID for loading gtag.js.
  var googleTagId = window.location.hostname === "boxplotr.chemgrid.org" ? "GT-W6J48KPS" : measurementId;
  var googleTag = document.createElement("script");
  googleTag.async = true;
  googleTag.src = "https://www.googletagmanager.com/gtag/js?id=" + encodeURIComponent(googleTagId);
  document.head.appendChild(googleTag);
  window.gtag("js", new Date());
  var centralMeasurementId = measurementIds["chemgrid.org"];
  var eventDestinations = measurementId === centralMeasurementId ? [measurementId] : [measurementId, centralMeasurementId];
  var tagOptions = {send_page_view:false,cookie_domain:"chemgrid.org",allow_google_signals:false,allow_ad_personalization_signals:false,interface:"web"};
  window.gtag("config", googleTagId, tagOptions);
  if (measurementId !== centralMeasurementId) {
    window.gtag("config", centralMeasurementId, tagOptions);
  }

  var appNames = {
    "boxplotr.chemgrid.org": "boxplotr",
    "checkerboardr.chemgrid.org": "checkerboardr",
    "growthcurve.chemgrid.org": "growthcurve",
    "molclass.chemgrid.org": "molclass",
    "chemgrid.org": "chemgrid",
    "www.chemgrid.org": "chemgrid"
  };
  var appName = appNames[window.location.hostname] || "unknown";
  window.gtag("set", {app_name:appName,interface:"web"});
  var appTitles = {
    chemgrid: "ChemGrid CGM",
    molclass: "MolClass V2",
    boxplotr: "BoxPlotR",
    checkerboardr: "CheckerboardR",
    growthcurve: "GrowthCurve 2.0"
  };
  var appTitle = appTitles[appName] || document.title || "ChemGrid application";
  if (!document.title) document.title = appTitle;

  function safeName(value) {
    return String(value || "unknown").toLowerCase()
      .replace(/[^a-z0-9_-]+/g, "_").replace(/^_+|_+$/g, "").slice(0, 80) || "unknown";
  }

  function sendAppEvent(eventName, details) {
    var parameters = { app_name: appName, interface: "web", send_to:eventDestinations };
    Object.keys(details || {}).forEach(function (key) { parameters[key] = details[key]; });
    window.gtag("event", eventName, parameters);
  }

  function analyticsPath() {
    var path = window.location.pathname;
    if (window.location.hostname !== "chemgrid.org" && window.location.hostname !== "www.chemgrid.org") return path;
    var params = new URLSearchParams(window.location.search);
    if (params.has("compound")) return "/compounds/detail";
    if (params.has("gene")) return "/genes/detail";
    if (params.get("view") === "screen") return "/screens/workspace";
    if (params.has("screen") && params.has("plot")) return "/screens/plot";
    if (params.has("screen")) return "/screens/results";
    var stateView = window.history.state && window.history.state.view;
    var allowedViews = ["home","compounds","screens","compare","structure","highlights","genes"];
    return allowedViews.indexOf(stateView) >= 0 ? "/" + stateView : "/";
  }

  var lastPath = "";
  function sendPageView() {
    var path = analyticsPath();
    if (path === lastPath) return;
    lastPath = path;
    var reportPath = appName === "chemgrid" ? path : "/apps/" + appName + path;
    window.gtag("event", "page_view", {app_name:appName,interface:"web",send_to:eventDestinations,page_title:appTitle,page_location:window.location.origin+path,page_path:reportPath});
    sendAppEvent("app_view", {view_name:safeName(path)});
  }
  sendPageView();
  // Count completed searches by category, never by the submitted query or SMILES.
  if (appName === "chemgrid" && window.fetch) {
    var originalFetch = window.fetch;
    window.fetch = function (resource, options) {
      var requestResult = originalFetch.apply(this, arguments);
      try {
        var requestUrl = new URL(typeof resource === "string" || resource instanceof URL ? resource : resource.url, window.location.href);
        var searchTypes = {"/api/v1/compounds/search":"compound","/api/v1/structures/search":"structure","/api/v1/genes/search":"gene"};
        var searchType = requestUrl.origin === window.location.origin && searchTypes[requestUrl.pathname];
        if (searchType) {
          var method = searchType === "compound" ? requestUrl.searchParams.get("field") : "unknown";
          if (searchType === "structure" && options && typeof options.body === "string") {
            try { method = JSON.parse(options.body).mode; } catch (ignore) {}
          }
          var allowedMethods = ["name","chemgridId","formula","smiles","cas","inchikey","id","substructure","exact","similarity"];
          var searchMethod = allowedMethods.indexOf(method) >= 0 ? safeName(method) : "other";
          requestResult.then(function (response) {
            if (response.ok) sendAppEvent("search", {search_type:searchType,search_method:searchMethod});
          }).catch(function () {});
        }
      } catch (ignore) {}
      return requestResult;
    };
  }
  ["pushState","replaceState"].forEach(function (method) {
    var original = window.history[method];
    window.history[method] = function () { var result=original.apply(this,arguments); window.setTimeout(sendPageView,0); return result; };
  });
  window.addEventListener("popstate", function () { window.setTimeout(sendPageView,0); });

  if (appName === "molclass") {
    document.addEventListener("click", function (event) {
      var control = event.target.closest && event.target.closest("button, [role=button]");
      if (control) {
        sendAppEvent("app_action", {control_name:safeName(control.id || control.name || control.getAttribute("aria-label")),control_type:"button"});
        return;
      }
      var link = event.target.closest && event.target.closest("a[href]");
      if (link) {
        try {
          var destination = new URL(link.href, window.location.href);
          if (destination.origin === window.location.origin) sendAppEvent("navigation", {view_name:safeName(destination.pathname)});
        } catch (ignore) {}
      }
    }, true);
    document.addEventListener("change", function (event) {
      var target = event.target;
      if (target && target.matches && target.matches("input, select, textarea")) {
        sendAppEvent("input_change", {control_name:safeName(target.id || target.name || target.getAttribute("aria-label")),control_type:safeName(target.type || target.tagName)});
      }
    }, true);
    document.addEventListener("submit", function (event) {
      var form = event.target;
      sendAppEvent("form_submit", {control_name:safeName(form.id || form.name)});
    }, true);
  }

  if (/^(boxplotr|checkerboardr|growthcurve)$/.test(appName)) {
    var shinySessionSent = false;
    var sendSessionStart = function () {
      if (shinySessionSent) return;
      shinySessionSent = true;
      sendAppEvent("app_session_start", {});
      var activeTab = document.querySelector(".nav-tabs li.active a, .tabbable .nav li.active a");
      if (activeTab) {
        var initialTab = activeTab.getAttribute("data-value") || activeTab.getAttribute("href") || activeTab.textContent;
        sendAppEvent("tab_view", {tab_name:safeName(initialTab)});
      }
    };
    if (window.jQuery) window.jQuery(document).one("shiny:connected", sendSessionStart);
    else document.addEventListener("shiny:connected", sendSessionStart);
    document.addEventListener("click", function (event) {
      var download = event.target.closest && event.target.closest("a.shiny-download-link");
      if (download) {
        if (download.classList.contains("disabled") || download.getAttribute("aria-disabled") === "true" || !download.getAttribute("href")) return;
        var downloadFormats = {
          downloadPlotPDF:"pdf",downloadPlotSVG:"svg",downloadPlotEPS:"eps",downloadBoxplotData:"csv",downloadMatrixCSV:"csv",
          wellPlotDownload:"pdf",platePlotDownload:"pdf",paramPlatePlotDownload:"pdf",paramPlateDiffPlotDownload:"pdf",
          downloadWellPlotData:"csv",downloadWellPlotErrorData:"csv",plateDataDownload:"csv",
          PlateParameterTableDownload:"csv",ScreenParameterTableDownload:"csv"
        };
        var format = downloadFormats[download.id] || "other";
        sendAppEvent("file_download", {control_name:safeName(download.id),file_extension:format,output_format:format});
        return;
      }
      var action = event.target.closest && event.target.closest(".action-button");
      if (action) sendAppEvent("app_action", {control_name:safeName(action.id)});
    }, true);
    document.addEventListener("change", function (event) {
      var target = event.target;
      if (target && target.matches && target.matches('input[type="file"]')) {
        if (!target.files || !target.files.length) return;
        sendAppEvent("file_upload", {control_name:safeName(target.id),control_type:"file",file_count:target.files ? target.files.length : 0});
        return;
      }
      if (target && target.matches && target.matches("input, select, textarea")) {
        sendAppEvent("input_change", {control_name:safeName(target.id || target.name),control_type:safeName(target.type || target.tagName)});
      }
    }, true);
    if (window.jQuery) {
      window.jQuery(document).on("shown.bs.tab", 'a[data-toggle="tab"]', function (event) {
        var tab = event.target.getAttribute("data-value") || event.target.getAttribute("href") || event.target.textContent;
        sendAppEvent("tab_view", {tab_name:safeName(tab)});
      });
      var seenOutputs = new Set();
      window.jQuery(document).on("shiny:value", function (event) {
        var outputName = safeName(event.name);
        if (outputName === "unknown" || seenOutputs.has(outputName)) return;
        seenOutputs.add(outputName);
        sendAppEvent("output_rendered", {output_name:outputName});
      });
    }
  }
})();
