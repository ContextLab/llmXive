"""T011: Source Verification Task.

Searches OpenNeuro, PhysioNet, and Kaggle for a single-source dataset
containing BOTH raw EEG time-series and paired tDCS motor outcome scores
for the same subjects, using the query "EEG AND tDCS AND motor".

Produces data/verified_source_manifest.json with the mandatory fields:
search_scope, query_string, status ("found"/"absent"), N_actual, and
mode_flag. If no paired dataset is found, logs "Data Insufficient:
No single-source paired dataset found" and sets mode_flag to
"Data Insufficient" so downstream tasks (T013-T050) skip execution.
"""

import json
import logging
import re
import sys
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import requests

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

QUERY_STRING = "EEG AND tDCS AND motor"
SEARCH_SCOPE = ["OpenNeuro", "PhysioNet", "Kaggle"]
MANIFEST_PATH = paths.data("verified_source_manifest.json")
REQUEST_TIMEOUT_S = 30

OPENNEURO_SEARCH_URL = "https://openneuro.org/api/search"
PHYSIONET_SEARCH_URL = "https://physionet.org/content/"
KAGGLE_SEARCH_URL = "https://www.kaggle.com/api/v1/datasets/list"

def _http_get(url: str, params: Dict[str, str]) -> requests.Response:
    """GET a URL with a timeout. Raises loudly on network failure."""
    resp = requests.get(url, params=params, timeout=REQUEST_TIMEOUT_S,
                        headers={"User-Agent": "llmXive-PROJ-164-T011/1.0"})
    resp.raise_for_status()
    return resp

def search_openneuro(query: str) -> List[Dict[str, Any]]:
    """Query the OpenNeuro public search API. Returns normalized results."""
    resp = _http_get(OPENNEURO_SEARCH_URL, {"q": query})
    payload = resp.json()
    results = payload.get("results", payload if isinstance(payload, list) else [])
    out: List[Dict[str, Any]] = []
    for r in results:
        if not isinstance(r, dict):
            continue
        out.append({
            "source": "OpenNeuro",
            "id": r.get("id") or r.get("accession"),
            "name": r.get("name") or r.get("title") or "",
            "description": (r.get("description") or "")[:500],
            "url": "https://openneuro.org/datasets/{}".format(r.get("id")) if r.get("id") else "",
            "subjects": r.get("subjects"),
        })
    return out

def search_physionet(query: str) -> List[Dict[str, Any]]:
    """Query the PhysioNet content search page and parse dataset links."""
    resp = _http_get(PHYSIONET_SEARCH_URL, {"query": query.replace(" AND ", " ")})
    hrefs = re.findall(r'href="(/content/[a-z0-9-]+/[0-9.]+/)"', resp.text)
    out: List[Dict[str, Any]] = []
    for href in dict.fromkeys(hrefs):  # dedupe, preserve order
        slug = href.strip("/").split("/")[-2]
        out.append({
            "source": "PhysioNet",
            "id": slug,
            "name": slug,
            "description": "",
            "url": "https://physionet.org{}".format(href),
            "subjects": None,
        })
    return out

def search_kaggle(query: str) -> List[Dict[str, Any]]:
    """Query the Kaggle public datasets list endpoint.

    The public list endpoint may require authentication; a 401/403 is
    recorded as a source-level search error rather than a fabricated
    result set.
    """
    resp = _http_get(KAGGLE_SEARCH_URL, {"search": query.replace(" AND ", " ")})
    payload = resp.json()
    out: List[Dict[str, Any]] = []
    for r in payload if isinstance(payload, list) else []:
        out.append({
            "source": "Kaggle",
            "id": r.get("ref") or r.get("id"),
            "name": r.get("title") or r.get("ref") or "",
            "description": (r.get("subtitle") or "")[:500],
            "url": "https://www.kaggle.com/datasets/{}".format(r.get("ref")) if r.get("ref") else "",
            "subjects": None,
        })
    return out

def is_paired_eeg_tdcs(entry: Dict[str, Any]) -> bool:
    """Heuristic check: does the entry mention BOTH EEG and tDCS?

    A single-source paired dataset must contain raw EEG time-series and
    tDCS motor outcome scores for the same subjects.
    """
    text = " ".join([
        str(entry.get("name") or ""),
        str(entry.get("description") or ""),
    ]).lower()
    has_eeg = "eeg" in text or "electroencephal" in text
    has_tdcs = "tdcs" in text or "transcranial direct current" in text
    return has_eeg and has_tdcs

def _search_all_sources(query: str) -> Dict[str, Any]:
    """Run all three source searches, recording per-source outcomes."""
    searchers = {
        "OpenNeuro": search_openneuro,
        "PhysioNet": search_physionet,
        "Kaggle": search_kaggle,
    }
    per_source: Dict[str, Any] = {}
    for source, fn in searchers.items():
        try:
            per_source[source] = {
                "status": "searched",
                "n_results": None,
                "results": fn(query),
            }
            per_source[source]["n_results"] = len(per_source[source]["results"])
            log.info("Searched %s for '%s': %d results",
                     source, query, per_source[source]["n_results"])
        except Exception as exc:  # record the failure honestly
            per_source[source] = {"status": "search_error", "error": str(exc)}
            log.warning("Search of %s failed: %s", source, exc)
    return per_source

def verify_source() -> Dict[str, Any]:
    """Search OpenNeuro, PhysioNet, and Kaggle for a paired EEG + tDCS dataset.

    Returns the manifest dict with search_scope, query_string, status
    ("found"/"absent"), dataset details, N_actual, and mode_flag.
    """
    per_source = _search_all_sources(QUERY_STRING)

    searched_ok = [s for s, r in per_source.items() if r.get("status") == "searched"]
    if not searched_ok:
        raise RuntimeError(
            "Source verification could not reach ANY of the search APIs "
            "({}); refusing to declare a dataset absent without a real "
            "search.".format(SEARCH_SCOPE)
        )

    candidates: List[Dict[str, Any]] = []
    for source, record in per_source.items():
        if record.get("status") != "searched":
            continue
        for entry in record["results"]:
            if is_paired_eeg_tdcs(entry):
                candidates.append(entry)

    if candidates:
        best = candidates[0]
        n_actual = best.get("subjects")
        n_actual = int(n_actual) if isinstance(n_actual, (int, float)) else 0
        manifest = {
            "search_scope": SEARCH_SCOPE,
            "query_string": QUERY_STRING,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "per_source": {
                s: {"status": r.get("status"), "n_results": r.get("n_results")}
                for s, r in per_source.items()
            },
            "status": "found",
            "dataset": best,
            "N_actual": n_actual,
            "mode_flag": "Primary",
        }
        log.info("Primary Mode: single-source paired dataset found: %s", best.get("url"))
    else:
        manifest = {
            "search_scope": SEARCH_SCOPE,
            "query_string": QUERY_STRING,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "per_source": {
                s: {"status": r.get("status"), "n_results": r.get("n_results")}
                for s, r in per_source.items()
            },
            "status": "absent",
            "dataset": None,
            "N_actual": 0,
            "mode_flag": "Data Insufficient",
            "reason": ("No single-source dataset containing both raw EEG and "
                       "paired tDCS motor outcome scores was found in "
                       "OpenNeuro, PhysioNet, or Kaggle. Cross-repository "
                       "pairing is prohibited (FR-015), so the pipeline "
                       "terminates downstream statistical tasks."),
        }
        log.warning("Data Insufficient: No single-source paired dataset found")

    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2) + "\n")
    log.info("Manifest written to %s (status=%s)", MANIFEST_PATH, manifest["status"])
    return manifest

def main() -> int:
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(name)s %(message)s")
    manifest = verify_source()
    if manifest["status"] == "absent":
        log.warning("Downstream tasks T013-T050 will be skipped "
                    "(mode_flag=%s).", manifest["mode_flag"])
    return 0

if __name__ == "__main__":
    sys.exit(main())
