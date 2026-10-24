"""
Data Feasibility Check Script
------------------------------
Probes three candidate data sources for EDS elemental maps paired with
perovskite solar‑cell performance metrics:

1. NREL Perovskite Database – public API export endpoint.
2. Zenodo – REST API query for records matching ``perovskite EDS``.
3. Materials Project – metadata fallback via the ``mp_api`` package.

For each source the script records:
  * HTTP reachable flag (True/False)
  * HTTP status code (or error description)
  * Number of records returned
  * Count of samples that provide both an EDS image and performance metrics
  * Boolean ``has_linked_eds`` indicating whether any such linked sample exists

The aggregated result is written to
``data/results/feasibility_report.json``.  The JSON always contains a
top‑level ``verdict`` field:

* ``"continue"`` – at least one source provides linked EDS maps.
* ``"halt"``     – no source provides linked EDS maps.

The script exits with status code 1 if the verdict is ``halt``, and 0
otherwise.

Invoked as a module:

    python -m code.data.feasibility

"""

import json
import sys
from pathlib import Path
from typing import Any, Dict, List

import requests
from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

IMAGE_EXTENSIONS = (".tif", ".tiff", ".png", ".jpg", ".jpeg", ".bmp")


def _safe_get(url: str, params: Dict[str, Any] = None, timeout: int = 30) -> Dict[str, Any]:
    """
    Perform a GET request and return a dictionary with ``reachable``,
    ``status`` (int or str) and ``json`` (parsed body or ``None``).

    Connection errors are caught and transformed into a ``reachable=False``
    entry; this records the failure honestly without fabricating data.
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


def _process_hits(records: List[Dict[str, Any]]) -> List[int]:
    """
    Helper to extract record IDs that contain both an image file and a
    performance hint (e.g. the word ``pce`` in the description or title).
    """
    evidence_ids: List[int] = []
    for rec in records:
        rec_id = rec.get("id")
        files = rec.get("files", []) or []
        has_image = any(
            str(f.get("key", "")).lower().endswith(IMAGE_EXTENSIONS) for f in files
        )
        metadata = rec.get("metadata", {}) or {}
        desc = str(metadata.get("description", "")) + str(metadata.get("title", ""))
        has_perf = "pce" in desc.lower() or "efficiency" in desc.lower()
        if has_image and has_perf:
            evidence_ids.append(rec_id)
    return evidence_ids


def probe_nrel() -> Dict[str, Any]:
    """Probe the NREL Perovskite Database API export endpoint."""
    url = "https://perovskitedatabase.com/api/export?format=json"
    result = _safe_get(url)

    n_records = 0
    linked_ids: List[int] = []

    if result["reachable"] and isinstance(result["json"], list):
        n_records = len(result["json"])
        for rec in result["json"]:
            if (
                isinstance(rec, dict)
                and rec.get("eds_images")
                and isinstance(rec.get("performance"), dict)
                and rec["performance"].get("pce") is not None
            ):
                linked_ids.append(rec.get("id", -1))

    return {
        "source": "NREL Perovskite Database",
        "url": url,
        "reachable": result["reachable"],
        "http_status": result["status"],
        "n_records": n_records,
        "linked_sample_count": len(linked_ids),
        "has_linked_eds": bool(linked_ids),
    }


def probe_zenodo() -> Dict[str, Any]:
    """
    Probe Zenodo for records matching ``perovskite EDS``.

    The Zenodo REST API returns a JSON object with a ``hits`` field.
    The page size is capped at 100 (the API rejects larger values).
    """
    base_url = "https://zenodo.org/api/records/"
    params = {"q": "perovskite EDS", "size": 100}
    result = _safe_get(base_url, params=params)

    n_records = 0
    linked_ids: List[int] = []

    if result["reachable"] and isinstance(result["json"], dict):
        hits = result["json"].get("hits", {})
        n_records = hits.get("total", 0)
        records = hits.get("hits", [])
        linked_ids = _process_hits(records)

    return {
        "source": "Zenodo",
        "url": "https://zenodo.org/api/records/?q=perovskite+EDS",
        "reachable": result["reachable"],
        "http_status": result["status"],
        "n_records": n_records,
        "linked_sample_count": len(linked_ids),
        "has_linked_eds": bool(linked_ids),
    }


def probe_materials_project() -> Dict[str, Any]:
    """
    Probe the Materials Project API via the ``mp_api`` package.

    The API requires an API key; if the package is unavailable or the
    request fails we record ``reachable=False`` with the error message.
    Materials Project provides composition metadata only (no EDS maps),
    so ``has_linked_eds`` is always False for this fallback source.
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
            "linked_sample_count": 0,
            "has_linked_eds": False,
        }

    try:
        with MPRester() as mpr:
            docs = mpr.materials.summary.search(
                elements=["Pb", "I"], fields=["material_id"]
            )
            n_records = len(docs)
            return {
                "source": "Materials Project",
                "url": "https://materialsproject.org/api",
                "reachable": True,
                "http_status": 200,
                "n_records": n_records,
                "linked_sample_count": 0,
                "has_linked_eds": False,
            }
    except Exception as exc:
        log.error("Materials Project query failed: %s", exc)
        return {
            "source": "Materials Project",
            "url": "https://materialsproject.org/api",
            "reachable": False,
            "http_status": str(exc),
            "n_records": 0,
            "linked_sample_count": 0,
            "has_linked_eds": False,
        }


def main() -> int:
    """
    Execute the feasibility check for all three sources and write the
    consolidated JSON report to ``data/results/feasibility_report.json``.

    Returns:
        0 – the check completed and at least one source provided linked EDS maps.
        1 – the check completed but no source provided linked EDS maps (verdict: halt).
    """
    log.info("Starting data feasibility check...")

    reports = []
    for probe in (probe_nrel, probe_zenodo, probe_materials_project):
        try:
            rpt = probe()
            reports.append(rpt)
            log.info(
                "Source %s reachable=%s status=%s records=%s linked=%s",
                rpt["source"],
                rpt["reachable"],
                rpt["http_status"],
                rpt["n_records"],
                rpt["has_linked_eds"],
            )
        except Exception as exc:  # defensive: record the failure honestly
            log.exception("Unexpected error probing source: %s", exc)
            reports.append(
                {
                    "source": probe.__name__,
                    "url": "unknown",
                    "reachable": False,
                    "http_status": str(exc),
                    "n_records": 0,
                    "linked_sample_count": 0,
                    "has_linked_eds": False,
                }
            )

    any_linked = any(r.get("has_linked_eds") for r in reports)
    overall = {
        "sources": reports,
        "verdict": "continue" if any_linked else "halt",
    }

    out_path: Path = paths.results("feasibility_report.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as fp:
        json.dump(overall, fp, indent=2)

    log.info("Feasibility report written to %s", out_path)

    if not any_linked:
        log.error(
            "No source provided linked EDS maps – verdict is 'halt'. "
            "Downstream steps should respect this."
        )
        return 1
    else:
        log.info("At least one source provides linked EDS maps – verdict 'continue'.")
        return 0


if __name__ == "__main__" or __name__ == "code.data.feasibility":
    sys.exit(main())