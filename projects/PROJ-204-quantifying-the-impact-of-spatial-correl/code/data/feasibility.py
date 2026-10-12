"""
Data Feasibility Check Script
--------------------------------
This script probes three candidate data sources for Energy‑Dispersive X‑ray Spectroscopy (EDS)
elemental maps paired with perovskite solar‑cell performance metrics.

Sources
-------
1. NREL Perovskite Database – public API export (hypothetical endpoint).
2. Zenodo – REST API query for records containing the term ``perovskite EDS``.
3. Materials Project – metadata fallback via the ``mp_api`` package.

For each source the script records:
  * HTTP reachable flag (True/False)
  * HTTP status code (or error description)
  * Number of records returned
  * Whether at least one record links an EDS image file to performance metrics
  * Sample IDs that provide such evidence

The aggregated result is written to ``data/results/data_feasibility_report.json``.
If *no* source provides a linked EDS map the report contains ``"verdict": "halt"``
and the script exits with a non‑zero status, signalling that the downstream pipeline
must stop.

The script is invoked as a module:

    python -m code.data.feasibility

The command is documented in the project's ``quickstart.md``.
"""

import json
import sys
from pathlib import Path
from typing import Any, Dict, List

import requests
from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------
def _safe_get(url: str, params: Dict[str, Any] = None, timeout: int = 30) -> Dict[str, Any]:
    """
    Perform a GET request and return a dictionary with ``reachable``,
    ``status`` (int or str) and ``json`` (parsed body or ``None``).

    Errors are caught and transformed into a ``reachable=False`` entry;
    this behaviour satisfies the requirement to *record* failures without
    silently fabricating data.
    """
    try:
        resp = requests.get(url, params=params, timeout=timeout)
        reachable = resp.ok
        status = resp.status_code
        try:
            body = resp.json()
        except Exception:
            body = None
        return {"reachable": reachable, "status": status, "json": body}
    except requests.RequestException as exc:
        log.warning("Request to %s failed: %s", url, exc)
        return {"reachable": False, "status": str(exc), "json": None}

# ----------------------------------------------------------------------
# Source‑specific probing functions
# ----------------------------------------------------------------------
def probe_nrel() -> Dict[str, Any]:
    """
    Probe the (hypothetical) NREL Perovskite Database API export.
    The real endpoint is not publicly documented; we attempt a generic
    JSON export URL and treat any non‑200 response as unreachable.
    """
    # This URL is a best‑effort guess based on the specification.
    url = "https://perovskitedatabase.com/api/export?format=json"
    result = _safe_get(url)

    n_records = 0
    eds_linked = False
    evidence_ids: List[int] = []

    if result["reachable"] and isinstance(result["json"], list):
        n_records = len(result["json"])
        # Heuristic: a record links EDS if it contains an ``eds_images`` list
        # and a ``performance`` dict with a ``pce`` field.
        for rec in result["json"]:
            if (
                isinstance(rec, dict)
                and rec.get("eds_images")
                and isinstance(rec.get("performance"), dict)
                and rec["performance"].get("pce") is not None
            ):
                eds_linked = True
                evidence_ids.append(rec.get("id", -1))
    else:
        # If the payload is not a list, we cannot count records.
        n_records = 0

    return {
        "source": "NREL Perovskite Database",
        "url": url,
        "reachable": result["reachable"],
        "http_status": result["status"],
        "n_records": n_records,
        "eds_linked": eds_linked,
        "evidence_sample_ids": evidence_ids,
    }

def probe_zenodo() -> Dict[str, Any]:
    """
    Probe Zenodo for records matching ``perovskite EDS``.
    The Zenodo REST API returns a JSON object with a ``hits`` field.
    """
    base_url = "https://zenodo.org/api/records/"
    params = {"q": "perovskite EDS", "size": 1000}  # request up to 1000 hits
    result = _safe_get(base_url, params=params)

    n_records = 0
    eds_linked = False
    evidence_ids: List[int] = []

    if result["reachable"] and isinstance(result["json"], dict):
        hits = result["json"].get("hits", {})
        n_records = hits.get("total", 0)
        records = hits.get("hits", [])
        for rec in records:
            # Zenodo record IDs are integers under the ``id`` key.
            rec_id = rec.get("id")
            files = rec.get("files", [])
            has_image = any(
                f.get("key", "").lower().endswith((".tif", ".tiff", ".png", ".jpg", ".jpeg"))
                for f in files
            )
            # Performance metrics may be stored in the record metadata;
            # we look for a ``metadata`` dict containing a ``pce`` field.
            metadata = rec.get("metadata", {})
            has_perf = "pce" in metadata or "PCE" in metadata
            if has_image and has_perf:
                eds_linked = True
                evidence_ids.append(rec_id)
    else:
        n_records = 0

    return {
        "source": "Zenodo",
        "url": f"{base_url}?q=perovskite+EDS",
        "reachable": result["reachable"],
        "http_status": result["status"],
        "n_records": n_records,
        "eds_linked": eds_linked,
        "evidence_sample_ids": evidence_ids,
    }

def probe_materials_project() -> Dict[str, Any]:
    """
    Probe the Materials Project API via the ``mp_api`` package.
    The API requires an API key; if the key is missing or the request
    fails we record ``reachable=False``.
    """
    try:
        from mp_api.client import MPRester
    except Exception as exc:
        log.warning("mp_api not available: %s", exc)
        return {
            "source": "Materials Project",
            "url": "https://materialsproject.org/api",
            "reachable": False,
            "http_status": str(exc),
            "n_records": 0,
            "eds_linked": False,
            "evidence_sample_ids": [],
        }

    # The Materials Project does not host EDS maps directly; we use the
    # ``get_data`` endpoint for perovskite compositions as a fallback.
    try:
        with MPRester() as mpr:
            # Query for perovskite structures (formula contains "Pb").
            # This is a lightweight query returning only ids.
            entries = mpr.summary.search_criteria(
                {"elements": ["Pb", "I", "C", "N", "H"]}, fields=["material_id"]
            )
            n_records = len(entries)
            # No EDS images are provided, so ``eds_linked`` stays False.
            return {
                "source": "Materials Project",
                "url": "https://materialsproject.org/api",
                "reachable": True,
                "http_status": 200,
                "n_records": n_records,
                "eds_linked": False,
                "evidence_sample_ids": [],
            }
    except Exception as exc:
        log.error("Materials Project query failed: %s", exc)
        return {
            "source": "Materials Project",
            "url": "https://materialsproject.org/api",
            "reachable": False,
            "http_status": str(exc),
            "n_records": 0,
            "eds_linked": False,
            "evidence_sample_ids": [],
        }

# ----------------------------------------------------------------------
# Main orchestration
# ----------------------------------------------------------------------
def main() -> None:
    """
    Execute the feasibility check for all three sources and write the
    consolidated JSON report.
    """
    log.info("Starting data feasibility check...")

    reports = []
    for probe in (probe_nrel, probe_zenodo, probe_materials_project):
        try:
            rpt = probe()
            reports.append(rpt)
            log.info(
                "Source %s reachable=%s status=%s records=%s eds_linked=%s",
                rpt["source"],
                rpt["reachable"],
                rpt["http_status"],
                rpt["n_records"],
                rpt["eds_linked"],
            )
        except Exception as exc:
            # Defensive – any unexpected error should be captured in the report.
            log.exception("Unexpected error probing source: %s", exc)
            reports.append(
                {
                    "source": probe.__name__,
                    "url": "unknown",
                    "reachable": False,
                    "http_status": str(exc),
                    "n_records": 0,
                    "eds_linked": False,
                    "evidence_sample_ids": [],
                }
            )

    # Determine overall verdict
    any_linked = any(r.get("eds_linked") for r in reports)
    overall = {"sources": reports, "verdict": "continue" if any_linked else "halt"}

    # Write JSON report
    out_path: Path = paths.results("data_feasibility_report.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as fp:
        json.dump(overall, fp, indent=2)
    log.info("Feasibility report written to %s", out_path)

    if not any_linked:
        log.error("No source provided linked EDS maps – halting pipeline.")
        sys.exit(1)

if __name__ == "__main__":
    main()
