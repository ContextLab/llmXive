"""
Discovery script for GEO/ENCODE datasets (T009/T010/T011/T012).

Loads raw discovery results (``output/discovery_results.json``). If that
file does not exist yet, the raw results are fetched from the REAL NCBI
GEO API (E-utilities esearch/esummary on the ``gds`` database) using a
hardcoded list of search queries, and cached to disk. No synthetic data
is ever generated — a failed network fetch raises.

The datasets are then filtered by organism (mouse, C. elegans,
Drosophila) and by metadata completeness (fluctuation timescale and
amplitude). Fully matched datasets are written to
``output/filtered_datasets.json``; datasets that pass the organism
filter but lack complete fluctuation metadata are flagged as
"Partial Match" and retained in the candidate list for manual review
(US0 acceptance scenario 3). A status file
``output/discovery_status.json`` records a ``halt_signal`` if fewer
than three fully matched datasets are found (T012) — the downstream
orchestrator (``code/main.py``) reads this file and halts the pipeline
when ``halt_signal`` is true.
"""

import argparse
import json
import logging
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Real GEO data acquisition (E-utilities)
# ----------------------------------------------------------------------
EUTILS_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
GDS_DB = "gds"

SEARCH_QUERIES = [
    "multigenerational methylation RNA-seq mouse",
    "transgenerational DNA methylation gene expression mouse",
    "multi-generational methylation RNA-seq Caenorhabditis elegans",
    "transgenerational epigenetic inheritance C. elegans expression",
    "multigenerational methylation Drosophila expression",
    "transgenerational gene expression Drosophila stress",
    "fluctuating temperature multigenerational methylation expression",
]

ORGANISM_FIELD_KEYS = ["organism", "taxon", "Organism"]

# Minimum number of fully matched datasets required to proceed (FR-000)
MIN_VALID_DATASETS = 3


def _esearch(query: str, retmax: int = 20) -> List[str]:
    """Run a real NCBI esearch query on the gds database; return UIDs."""
    params = {
        "db": GDS_DB,
        "term": query,
        "retmax": retmax,
        "retmode": "json",
        "usehistory": "n",
    }
    resp = requests.get(f"{EUTILS_BASE}/esearch.fcgi", params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    return data.get("esearchresult", {}).get("idlist", [])


def _esummary(uids: List[str]) -> Dict[str, Dict[str, Any]]:
    """Fetch real esummary records for GEO DataSets UIDs."""
    if not uids:
        return {}
    params = {"db": GDS_DB, "id": ",".join(uids), "retmode": "json"}
    resp = requests.get(f"{EUTILS_BASE}/esummary.fcgi", params=params, timeout=60)
    resp.raise_for_status()
    return resp.json().get("result", {})


def fetch_geo_results(queries: Optional[List[str]] = None) -> List[Dict]:
    """
    Query the real GEO API for candidate multi-generational datasets.

    Returns a list of dataset dictionaries with accession, title,
    summary, organism and any extractable metadata. Raises on network
    or API failure — never falls back to synthetic data.
    """
    queries = queries or SEARCH_QUERIES
    datasets: List[Dict] = []
    seen: set = set()

    for query in queries:
        try:
            uids = _esearch(query)
        except Exception as exc:
            raise RuntimeError(
                f"Real GEO esearch query failed for '{query}': {exc}"
            ) from exc
        log.info(f"GEO query '{query}' returned {len(uids)} UIDs")

        summaries = {}
        if uids:
            try:
                summaries = _esummary(uids)
            except Exception as exc:
                raise RuntimeError(
                    f"Real GEO esummary fetch failed for query '{query}': {exc}"
                ) from exc

        for uid in uids:
            rec = summaries.get(uid)
            if not rec or not isinstance(rec, dict):
                continue
            accession = rec.get("accession", "")
            if not accession or accession in seen:
                continue
            seen.add(accession)
            datasets.append(
                {
                    "accession": accession,
                    "title": rec.get("title", ""),
                    "summary": rec.get("summary", ""),
                    "organism": rec.get("taxon", ""),
                    "gds_type": rec.get("gdstype", ""),
                    "n_samples": rec.get("n_samples", 0),
                    "source": "GEO",
                    "query": query,
                }
            )
        time.sleep(0.4)  # respect NCBI rate limit (<=3 req/s)

    log.info(f"Fetched {len(datasets)} unique real GEO datasets")
    return datasets


# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def _load_raw_results() -> List[Dict]:
    """
    Load the raw discovery results produced by the GEO/ENCODE query step.
    If the file does not exist, fetch real results from the GEO API and
    cache them to ``output/discovery_results.json``.

    Returns:
        A list of dataset dictionaries.
    """
    raw_path = paths.path("output", "discovery_results.json")
    if not raw_path.is_file():
        log.info("Raw discovery results not found; querying real GEO API")
        datasets = fetch_geo_results()
        raw_path.parent.mkdir(parents=True, exist_ok=True)
        with raw_path.open("w", encoding="utf-8") as f:
            json.dump(datasets, f, indent=2, sort_keys=True)
        log.info(f"Cached {len(datasets)} real GEO results to {raw_path}")
        return datasets

    with raw_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError("Discovery results must be a list of dataset objects")
    log.info(f"Loaded {len(data)} raw discovery entries")
    return data


def filter_by_organism(
    datasets: List[Dict],
    allowed_organisms: Optional[List[str]] = None,
) -> List[Dict]:
    """
    Keep only datasets whose ``organism`` field matches one of the allowed
    model organisms (case-insensitive substring match).

    Args:
        datasets: List of dataset dictionaries.
        allowed_organisms: List of organism identifiers. If ``None`` the
          default list (mouse, C. elegans, Drosophila) is used.

    Returns:
        Sub-set of ``datasets`` that belong to a supported model organism.
    """
    default_orgs = ["mouse", "mus musculus", "c. elegans", "caenorhabditis elegans", "drosophila"]
    organisms = [o.lower() for o in (allowed_organisms or default_orgs)]

    filtered = []
    for ds in datasets:
        org_field = str(ds.get("organism", "")).lower()
        if any(org in org_field for org in organisms):
            filtered.append(ds)

    log.info(f"Filtered by organism: {len(filtered)} of {len(datasets)} remain")
    return filtered


def check_metadata_completeness(dataset: Dict) -> bool:
    """
    Determine whether a dataset contains the required metadata fields:
    a fluctuation timescale (or equivalent) and a fluctuation amplitude
    (or equivalent). Presence of *any* of the recognised keys for each
    category is considered sufficient. Additionally, the free-text
    title/summary is scanned for recognised mentions.

    Recognised keys:
      Timescale – ``fluctuation_timescale``, ``fluctuation_period``,
      ``env_period``.
      Amplitude – ``fluctuation_amplitude``, ``amplitude``.

    Returns:
        True if **both** a timescale and an amplitude entry exist and are
        non-empty; False otherwise.
    """
    timescale_keys = [
        "fluctuation_timescale",
        "fluctuation_period",
        "env_period",
    ]
    amplitude_keys = ["fluctuation_amplitude", "amplitude"]

    has_timescale = any(dataset.get(k) for k in timescale_keys)
    has_amplitude = any(dataset.get(k) for k in amplitude_keys)

    # Fall back to scanning title/summary text for explicit metadata
    # mentions (GEO summaries rarely carry structured keys).
    text = " ".join(
        str(dataset.get(k, "")) for k in ("title", "summary")
    ).lower()
    if not has_timescale and any(
        kw in text
        for kw in ("fluctuation timescale", "fluctuation period", "env period")
    ):
        has_timescale = True
    if not has_amplitude and "fluctuation amplitude" in text:
        has_amplitude = True

    complete = bool(has_timescale and has_amplitude)
    if not complete:
        log.debug(
            f"Dataset {dataset.get('accession', '<unknown>')} missing required metadata"
        )
    return complete


def _write_json(data, out_path: Path) -> None:
    """Utility to write JSON (list or dict) as pretty-printed output."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, sort_keys=True)
    log.info(f"Wrote JSON to {out_path}")


def _write_status(
    valid_count: int,
    total_count: int,
    partial_matches: List[Dict],
    out_path: Path,
) -> Dict:
    """
    Write the discovery status file (T012). If fewer than three *valid*
    datasets are present, ``halt_signal`` is set to ``true`` and a short
    reason is provided. Datasets that passed the organism filter but
    lack complete fluctuation metadata are flagged as "Partial Match"
    and listed for manual review.

    The file format matches what ``code/main.py`` expects:
    {
        "halt_signal": bool,
        "status": "Data Available" | "Data Unavailable",
        "reason": str,
        "valid_datasets": int,
        "total_datasets": int,
        "partial_matches": [accession, ...]
    }

    Returns:
        The status dictionary that was written.
    """
    status = {
        "valid_datasets": valid_count,
        "total_datasets": total_count,
        "partial_matches": [
            ds.get("accession", "<unknown>") for ds in partial_matches
        ],
    }

    if valid_count < MIN_VALID_DATASETS:
        status["halt_signal"] = True
        status["status"] = "Data Unavailable"
        status["reason"] = (
            f"Insufficient fully-matched datasets: {valid_count} found; "
            f"minimum required is {MIN_VALID_DATASETS}."
        )
        log.warning("HALT SIGNAL: " + status["reason"])
    else:
        status["halt_signal"] = False
        status["status"] = "Data Available"
        status["reason"] = "Sufficient datasets found."

    _write_json(status, out_path)
    return status


# ----------------------------------------------------------------------
# Core discovery routine
# ----------------------------------------------------------------------
def run_discovery(
    allowed_organisms: Optional[List[str]] = None,
    output_dir: Optional[Path] = None,
) -> List[Dict]:
    """
    Execute the discovery workflow:

    1. Load raw results (fetching real GEO data if not cached).
    2. Filter by organism.
    3. Separate fully-matched (metadata-complete) from partial matches
       (flagged "Partial Match", retained for manual review).
    4. Write the filtered list (only fully-matched) to
       ``output/filtered_datasets.json``.
    5. Write ``output/discovery_status.json`` containing a halt flag if
       fewer than three fully-matched datasets exist.

    Returns:
        List of fully-matched dataset dictionaries.
    """
    raw = _load_raw_results()
    organisms_filtered = filter_by_organism(raw, allowed_organisms)

    full_matches = []
    partial_matches = []

    for ds in organisms_filtered:
        if check_metadata_completeness(ds):
            full_matches.append(ds)
        else:
            # Flag as Partial Match but retain for manual review (US0
            # acceptance scenario 3).
            ds = dict(ds)
            ds["match_status"] = "Partial Match"
            partial_matches.append(ds)

    # Determine output locations
    out_dir = output_dir or paths.path("output")
    filtered_path = out_dir / "filtered_datasets.json"
    partial_path = out_dir / "partial_match_datasets.json"
    status_path = out_dir / "discovery_status.json"

    # Write filtered (full) list
    _write_json(full_matches, filtered_path)

    # Write partial-match candidate list for manual review
    _write_json(partial_matches, partial_path)

    # Write status (including partial matches)
    _write_status(
        valid_count=len(full_matches),
        total_count=len(organisms_filtered),
        partial_matches=partial_matches,
        out_path=status_path,
    )

    return full_matches


# ----------------------------------------------------------------------
# CLI entry point
# ----------------------------------------------------------------------
def main() -> int:
    """
    Command-line interface.

    Optional arguments:
      --organisms  Comma-separated list of organism identifiers to keep.
      --refresh    Re-query the real GEO API even if cached results exist.

    Returns:
        Process exit code (0 on success — including the expected
        "Data Unavailable" halt outcome, which is a valid discovery
        result, not an error).
    """
    parser = argparse.ArgumentParser(
        description="Discover and validate GEO/ENCODE multi-generational datasets."
    )
    parser.add_argument(
        "--organisms",
        type=str,
        default=None,
        help="Comma-separated list of organism identifiers to retain (e.g., mouse,c. elegans)",
    )
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="Re-query the real GEO API, ignoring cached results.",
    )
    args = parser.parse_args()

    orgs = (
        [org.strip() for org in args.organisms.split(",")]
        if args.organisms
        else None
    )

    if args.refresh:
        cache = paths.path("output", "discovery_results.json")
        if cache.is_file():
            cache.unlink()
            log.info("Removed cached discovery results; will re-query GEO")

    try:
        run_discovery(allowed_organisms=orgs)
        log.info("Discovery completed successfully.")
        return 0
    except Exception as exc:
        log.error(f"Discovery failed: {exc}", exc_info=True)
        raise


if __name__ == "__main__":
    raise SystemExit(main())