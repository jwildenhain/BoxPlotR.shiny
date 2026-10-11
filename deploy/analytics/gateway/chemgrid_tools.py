"""Read-only ChemGrid CGM tools for the public ChemGrid FastMCP gateway."""

from __future__ import annotations

import asyncio
import hashlib
import hmac
import ipaddress
import time
from contextvars import ContextVar
from pathlib import Path

import json
import re
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Literal
from measured_tools import register_measured_tools

API_BASE = "http://127.0.0.1/api/v1"
MAX_RESPONSE_BYTES = 5 * 1024 * 1024
REQUEST_TIMEOUT_SECONDS = 25
IDENTIFIER_PATTERN = re.compile(r"^[A-Za-z0-9 _.-]{1,80}$")
USAGE_CALLBACK = None
PREDICTION_CLIENT_IP: ContextVar[str | None] = ContextVar("prediction_client_ip", default=None)
PREDICTION_FORWARD_KEY = Path("/etc/boxplotr-mcp/prediction-forward.key")


def _identifier(value: str, field: str) -> str:
    normalized = value.strip()
    if not IDENTIFIER_PATTERN.fullmatch(normalized):
        raise ValueError(f"{field} contains unsupported characters or is too long")
    return normalized


def _page(value: int, maximum: int = 1000) -> int:
    if value < 1 or value > maximum:
        raise ValueError(f"page must be between 1 and {maximum}")
    return value


def _per_page(value: int, maximum: int = 100) -> int:
    if value < 1 or value > maximum:
        raise ValueError(f"per_page must be between 1 and {maximum}")
    return value


def _request(path: str, query: dict[str, Any] | None = None, body: dict[str, Any] | None = None, *, prediction_ip: str | None = None) -> dict[str, Any]:
    url = f"{API_BASE}{path}"
    if query:
        encoded = urllib.parse.urlencode({key: value for key, value in query.items() if value not in (None, "")})
        if encoded:
            url = f"{url}?{encoded}"
    data = None
    headers = {"Accept": "application/json", "User-Agent": "ChemGrid-MCP/1.0"}
    if body is not None:
        data = json.dumps(body, separators=(",", ":")).encode("utf-8")
        headers["Content-Type"] = "application/json"
    if prediction_ip is not None:
        if path != "/structures/predict" or data is None:
            raise ValueError("Signed IP forwarding is restricted to prediction requests")
        address = ipaddress.ip_address(prediction_ip).compressed
        timestamp = str(int(time.time()))
        key = PREDICTION_FORWARD_KEY.read_bytes().strip()
        if len(key) < 32:
            raise RuntimeError("Prediction forwarding is not configured")
        message = f"{timestamp}\n{address}\n{hashlib.sha256(data).hexdigest()}"
        headers.update({"X-Chemgrid-Mcp-IP": address, "X-Chemgrid-Mcp-Time": timestamp,
                        "X-Chemgrid-Mcp-Signature": hmac.new(key, message.encode(), hashlib.sha256).hexdigest()})
    request = urllib.request.Request(url, data=data, headers=headers, method="POST" if body is not None else "GET")
    try:
        with urllib.request.urlopen(request, timeout=120 if prediction_ip is not None else REQUEST_TIMEOUT_SECONDS) as response:
            payload = response.read(MAX_RESPONSE_BYTES + 1)
    except urllib.error.HTTPError as error:
        detail = error.read(8192).decode("utf-8", errors="replace")
        try:
            message = json.loads(detail).get("error", {}).get("message", detail)
        except json.JSONDecodeError:
            message = detail
        raise RuntimeError(f"ChemGrid API returned HTTP {error.code}: {message}") from error
    except urllib.error.URLError as error:
        raise RuntimeError("ChemGrid API is unavailable") from error
    if len(payload) > MAX_RESPONSE_BYTES:
        raise RuntimeError("ChemGrid API response exceeded the 5 MB MCP limit")
    try:
        result = json.loads(payload)
    except json.JSONDecodeError as error:
        raise RuntimeError("ChemGrid API returned an invalid JSON response") from error
    if USAGE_CALLBACK is not None:
        try:
            # Report the operation category, never query text, structures or IDs.
            activity = {"activity_type": "other"}
            if path in {"/compounds/search", "/structures/search", "/genes/search"}:
                search_type = {"/compounds/search": "compound", "/structures/search": "structure", "/genes/search": "gene"}[path]
                method = (query or {}).get("field") if search_type == "compound" else (body or {}).get("mode")
                allowed = {"name", "chemgridId", "formula", "smiles", "cas", "inchikey", "id", "substructure", "exact", "similarity"}
                activity.update(activity_type="search", search_type=search_type,
                                search_method=str(method).lower() if method in allowed else "other")
            elif path == "/structures/predict":
                activity["activity_type"] = "structural_prediction"
            elif path == "/screens":
                activity["activity_type"] = "screen_list"
            elif path.startswith("/screens/"):
                activity["activity_type"] = "screen_results"
            elif path == "/genes/screen-network":
                activity["activity_type"] = "gene_network"
            elif path.startswith("/compounds/"):
                suffix = path.rsplit("/", 1)[-1]
                activity["activity_type"] = {"analogs":"analogues", "scaffold-family":"scaffold_family",
                    "targets":"sonar_bioactivity", "structural-targets":"sonar_structure",
                    "measurements":"measurements", "screening-summary":"screening_summary"}.get(suffix, "compound_detail")
            USAGE_CALLBACK(activity)
        except Exception:
            pass
    return result


def register_chemgrid_tools(mcp, usage_callback=None) -> None:
    global USAGE_CALLBACK
    USAGE_CALLBACK = usage_callback
    register_measured_tools(mcp, _request, _identifier)

    @mcp.tool(description="Search ChemGrid compounds by identifier, name, formula, structure field, or another API-supported field.")
    async def chemgrid_search_compounds(
        query: str,
        field: str = "name",
        library: str = "all",
        page: int = 1,
        per_page: int = 20,
    ) -> dict[str, Any]:
        if not query.strip() or len(query) > 500:
            raise ValueError("query must contain 1 to 500 characters")
        return _request("/compounds/search", {
            "q": query.strip(),
            "field": _identifier(field, "field"),
            "library": _identifier(library, "library"),
            "page": _page(page),
            "perPage": _per_page(per_page),
        })

    @mcp.tool(description="Get ChemGrid compound identity, structures, library records, external identifiers, and descriptors.")
    async def chemgrid_get_compound(compound_id: str, library: str = "") -> dict[str, Any]:
        cid = _identifier(compound_id, "compound_id")
        return _request(f"/compounds/{urllib.parse.quote(cid, safe='')}", {"library": library.strip()})

    @mcp.tool(description="Get strict ChemGrid structural analogues with ECFP4 Tanimoto similarity at or above 0.85.")
    async def chemgrid_get_analogues(compound_id: str, library: str = "") -> dict[str, Any]:
        cid = _identifier(compound_id, "compound_id")
        return _request(f"/compounds/{urllib.parse.quote(cid, safe='')}/analogs", {"library": library.strip()})

    @mcp.tool(description="Get related compounds by generic Murcko scaffold topology, including molecule and scaffold similarity scores.")
    async def chemgrid_get_scaffold_family(compound_id: str, library: str = "") -> dict[str, Any]:
        cid = _identifier(compound_id, "compound_id")
        return _request(f"/compounds/{urllib.parse.quote(cid, safe='')}/scaffold-family", {"library": library.strip()})

    @mcp.tool(description="List ChemGrid screening experiments for a library, including strains, species, plates, replicates, and hit counts.")
    async def chemgrid_list_screens(library: str, page: int = 1, per_page: int = 50) -> dict[str, Any]:
        return _request("/screens", {
            "library": _identifier(library, "library"),
            "page": _page(page),
            "perPage": _per_page(per_page, 200),
        })

    @mcp.tool(description="Get ranked compounds from a ChemGrid screen for the bioactive, toxic, or outlier result class.")
    async def chemgrid_get_screen_compounds(
        library: str,
        species: str,
        strain: str,
        result_class: str = "bioactive",
        page: int = 1,
        per_page: int = 25,
    ) -> dict[str, Any]:
        if result_class not in {"bioactive", "toxic", "outlier"}:
            raise ValueError("result_class must be bioactive, toxic, or outlier")
        segments = [_identifier(value, name) for value, name in ((library, "library"), (species, "species"), (strain, "strain"))]
        path = "/screens/" + "/".join(urllib.parse.quote(value, safe="") for value in segments) + "/compounds"
        return _request(path, {"class": result_class, "page": _page(page), "perPage": _per_page(per_page)})

    @mcp.tool(description="Get the screened yeast gene interaction network and screening activity around a gene ORF or symbol.")
    async def chemgrid_get_gene_network(
        focus: str,
        library: str = "",
        species: str = "",
        strain: str = "",
    ) -> dict[str, Any]:
        query: dict[str, Any] = {"focus": _identifier(focus, "focus")}
        if library or species or strain:
            if not all((library, species, strain)):
                raise ValueError("library, species, and strain must be supplied together")
            query.update({
                "library": _identifier(library, "library"),
                "species": _identifier(species, "species"),
                "strain": _identifier(strain, "strain"),
                "origin": "screen",
            })
        return _request("/genes/screen-network", query)

    @mcp.tool(description="Search ChemGrid structures by SMILES using substructure, exact, or similarity matching.")
    async def chemgrid_search_structures(
        smiles: str,
        mode: str = "similarity",
        library: str = "all",
        threshold: float = 0.7,
        limit: int = 25,
        stereo: bool = False,
        strict: bool = False,
    ) -> dict[str, Any]:
        if mode not in {"substructure", "exact", "similarity"}:
            raise ValueError("mode must be substructure, exact, or similarity")
        if not 0.0 <= threshold <= 1.0:
            raise ValueError("threshold must be between 0 and 1")
        if not smiles.strip() or len(smiles) > 10000:
            raise ValueError("smiles must contain 1 to 10000 characters")
        return _request("/structures/search", body={
            "query": smiles.strip(),
            "queryFormat": "smiles",
            "mode": mode,
            "library": _identifier(library, "library"),
            "threshold": threshold,
            "stereo": stereo,
            "strict": strict,
            "limit": _per_page(limit, 75),
        })

    @mcp.tool(description="Get SONAR target rankings from a ChemGrid compound's measured bioactivity profile. Returns the existing bioactivity SONAR result with its calculation availability, profile provenance, target ORFs, gene descriptions, scores, enrichment statistics and pagination. These are inferred targets, not confirmed binding targets. Use chemgrid_get_structural_sonar for stored structure-predicted profiles. Network all combines genetic and physical interactions.")
    async def chemgrid_get_bioactivity_sonar(
        compound_id: str,
        network: Literal["genetic", "physical", "all"] = "genetic",
        page: int = 1,
        per_page: int = 5,
    ) -> dict[str, Any]:
        cid = _identifier(compound_id, "compound_id")
        if network not in {"genetic", "physical", "all"}:
            raise ValueError("network must be genetic, physical, or all")
        return _request(f"/compounds/{urllib.parse.quote(cid, safe='')}/targets", {
            "network": network, "page": _page(page), "perPage": _per_page(per_page),
        })

    @mcp.tool(description="Get SONAR target rankings from a ChemGrid compound's stored structure-predicted activity profile. Returns structural prediction provenance, availability, active/universe ORF counts, inferred targets, scores, enrichment statistics and pagination as supplied by ChemGrid. These are model-derived hypotheses, not measured activity or confirmed binding targets. Requires an existing ChemGrid compound ID; does not predict a new SMILES. Network all combines genetic and physical interactions.")
    async def chemgrid_get_structural_sonar(
        compound_id: str,
        network: Literal["genetic", "physical", "all"] = "genetic",
        page: int = 1,
        per_page: int = 5,
    ) -> dict[str, Any]:
        cid = _identifier(compound_id, "compound_id")
        if network not in {"genetic", "physical", "all"}:
            raise ValueError("network must be genetic, physical, or all")
        return _request(f"/compounds/{urllib.parse.quote(cid, safe='')}/structural-targets", {
            "network": network, "page": _page(page), "perPage": _per_page(per_page),
        })

    @mcp.tool(description="Predict a new molecule's structural bioactivity profile and SONAR target rankings from one SMILES string. Returns the strain/ORF activity probabilities, active/inactive/unknown calls, applicability information, scaffold distance, model provenance, and genetic/physical/combined SONAR results. No MolClass integration. These are model predictions, not measured activity or confirmed targets. Each submission consumes one of 100 molecules per requester IP per UTC day, shared with the ChemGrid website; remaining quota and reset time are returned. Repeated submissions count again; reuse returned networks instead of resubmitting. Invalid SMILES are not charged. Do not automatically retry a timeout because the submission may already have been charged.")
    async def chemgrid_predict_smiles(smiles: str) -> dict[str, Any]:
        if not smiles.strip() or len(smiles.encode("utf-8")) > 10000:
            raise ValueError("smiles must contain 1 to 10000 UTF-8 bytes")
        address = PREDICTION_CLIENT_IP.get()
        if address is None:
            raise RuntimeError("Prediction requires a verified requester IP")
        result = await asyncio.to_thread(_request, "/structures/predict",
            body={"molecules": [smiles.strip()], "includeGo": False}, prediction_ip=address)
        # Keep this tool focused on the activity profile and SONAR, without GO or MolClass.
        for profile in result.get("data", result).get("predictions", []):
            profile.pop("goEnrichment", None)
        return result
