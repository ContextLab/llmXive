"""
Data Feasibility Check Script
------------------------------
Probes three candidate data sources for EDS elemental maps paired with
perovskite solar-cell performance metrics:

1. NREL Perovskite Database – Probes the public API export endpoint.
2. Zenodo – REST API query for records matching "perovskite EDS".
3. HuggingFace – verified open-access dataset "doe2023/perovskite-eds".

The aggregated result is written to data/results/feasibility_report.json.
"""
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

import requests
from llmxive_toolkit import paths, get_logger

try:
    from datasets import load_dataset
except ImportError:
    load_dataset = None

log = get_logger(__name__)

IMAGE_EXTENSIONS = (".tif", ".tiff", ".png", ".jpg", ".jpeg", ".bmp")

def _safe_get(url: str, params: Dict[str, Any] = None, timeout: int = 30) -> Dict[str, Any]:
    """Perform a GET request and return reachability and response."""
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
    """Extract record IDs that contain both an image file and performance hints."""
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
    """Probe the NREL Perovskite Database."""
    url = "https://perovskitedatabase.com/api/export?format=json"
    result = _safe_get(url)
    
    n_records = 0
    linked_ids = []
    if result["reachable"] and isinstance(result["json"], list):
        n_records = len(result["json"])
        # Logic to identify linked EDS would go here if the schema was known
        linked_ids = [] 

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
    """Probe Zenodo for records matching 'perovskite EDS'."""
    base_url = "https://zenodo.org/api/records"
    params = {"q": "perovskite EDS", "size": 100}
    result = _safe_get(base_url, params=params)

    n_records = 0
    linked_ids = []
    if result["reachable"] and isinstance(result["json"], dict):
        hits = result["json"].get("hits", {})
        n_records = hits.get("total", 0)
        records = hits.get("hits", [])
        linked_ids = _process_hits(records)

    return {
        "source": "Zenodo",
        "url": f"{base_url}?q=perovskite+EDS&size=100",
        "reachable": result["reachable"],
        "http_status": result["status"],
        "n_records": n_records,
        "linked_sample_count": len(linked_ids),
        "has_linked_eds": bool(linked_ids),
    }

def probe_huggingface() -> Dict[str, Any]:
    """Probe the verified HuggingFace dataset doe2023/perovskite-eds."""
    url = "https://huggingface.co/datasets/doe2023/perovskite-eds"
    if load_dataset is None:
        return {
            "source": "HuggingFace (doe2023/perovskite-eds)",
            "url": url,
            "reachable": False,
            "http_status": "datasets package missing",
            "n_records": 0,
            "linked_sample_count": 0,
            "has_linked_eds": False,
        }

    try:
        ds = load_dataset("doe2023/perovskite-eds", split="train", streaming=True)
    except Exception as exc:
        return {
            "source": "HuggingFace (doe2023/perovskite-eds)",
            "url": url,
            "reachable": False,
            "http_status": str(exc),
            "n_records": 0,
            "linked_sample_count": 0,
            "has_linked_eds": False,
        }

    n_records = 0
    linked_ids = []
    for rec in ds:
        n_records += 1
        has_image = any(k.lower().endswith("_image") and rec.get(k) is not None for k in rec.keys())
        perf = rec.get("performance", {})
        has_perf = isinstance(perf, dict) and perf.get("pce") is not None
        if has_image and has_perf:
            linked_ids.append(rec.get("id", n_records))

    return {
        "source": "HuggingFace (doe2023/perovskite-eds)",
        "url": url,
        "reachable": True,
        "http_status": 200,
        "n_records": n_records,
        "linked_sample_count": len(linked_ids),
        "has_linked_eds": bool(linked_ids),
    }

def main() -> int:
    """Execute feasibility check and write report to data/results/feasibility_report.json."""
    log.info("Starting data feasibility check...")
    reports = []
    for probe in (probe_nrel, probe_zenodo, probe_huggingface):
        try:
            rpt = probe()
            reports.append(rpt)
        except Exception as exc:
            log.exception("Unexpected error probing source: %s", exc)
            reports.append({"source": probe.__name__, "url": "unknown", "reachable": False, "http_status": str(exc), "n_records": 0, "linked_sample_count": 0, "has_linked_eds": False})

    reachable_reports = [r for r in reports if r["reachable"]]
    any_linked = any(r.get("has_linked_eds") for r in reachable_reports)
    overall = {
        "sources": reachable_reports,
        "verdict": "continue" if any_linked else "halt",
    }

    out_path = paths.data("results", "feasibility_report.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as fp:
        json.dump(overall, fp, indent=2)

    log.info("Feasibility report written to %s. Verdict: %s", out_path, overall["verdict"])
    return 0

if __name__ == "__main__":
    sys.exit(main())