"""Dataset acquisition and provenance recording (T001, FR-001/FR-011).

Fetches a REAL tabular corrosion dataset via the ``openml`` Python
package, searching OpenML for datasets whose feature set contains the
required variables (pH, salinity, temperature, composition, corrosion
rate). Writes the raw data to ``data/raw/`` and records provenance
(dataset ID, version, DOI/URL, SHA-256 checksum, download timestamp,
record count, columns) in ``metadata/dataset.yaml``.

The fetch FAILS LOUDLY (raises) if no qualifying real dataset is found.
There is NO synthetic fallback.
"""

from __future__ import annotations

import argparse
import hashlib
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np
# Compatibility shim for NumPy 2.0+: ``openml`` (via its sklearn extension)
# expects ``np.sctypes`` which was removed. Provide a minimal placeholder
# to allow the import to succeed. The exact contents are not used by the
# ingestion logic.
if not hasattr(np, "sctypes"):
    np.sctypes = {}

import pandas as pd
import yaml

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

# Required variables per FR-001 (crystal_structure is optional).
REQUIRED_VARIABLES: Tuple[str, ...] = (
    "ph",
    "salinity",
    "temperature",
    "composition",
    "corrosion_rate",
)
OPTIONAL_VARIABLES: Tuple[str, ...] = ("crystal_structure",)

# Keywords used to find candidate corrosion datasets on OpenML.
SEARCH_KEYWORDS: Tuple[str, ...] = ("corrosion", "corros", "seawater metal")


class MissingVariableError(RuntimeError):
    """Raised when a required variable is absent from a data source."""


def normalize_column(name: str) -> str:
    """Lowercase and strip non-alphanumeric characters."""
    return re.sub(r"[^a-z0-9]", "", str(name).lower())


def column_matches(required: str, column: str) -> bool:
    """Return True if ``column`` plausibly measures ``required``.

    Handles common variants such as ``solution_ph`` -> ``ph``,
    ``temp_C`` -> ``temperature``, ``Corrosion Rate (mm/yr)`` ->
    ``corrosion_rate``. The short token ``ph`` is matched on token
    boundaries to avoid matching arbitrary substrings.
    """
    req = normalize_column(required)
    col_raw = str(column)
    col = normalize_column(col_raw)
    if not col:
        return False
    if req == "ph":
        # Token-boundary match so 'ph' does not match 'graphite'.
        return bool(
            re.search(r"(?<![a-z0-9])ph(?![a-z0-9])", col_raw.lower())
        )
    return req in col or col in req


def map_required_columns(
    columns: Sequence[str], source: str
) -> Dict[str, str]:
    """Map each required variable to an actual column name.

    Raises MissingVariableError (fail-loud, FR-001) listing the missing
    variable and its source.
    """
    mapping: Dict[str, str] = {}
    missing: List[str] = []
    for var in REQUIRED_VARIABLES:
        hit = next((c for c in columns if column_matches(var, c)), None)
        if hit is None:
            missing.append(var)
        else:
            mapping[var] = hit
    if missing:
        raise MissingVariableError(
            "Error: MISSING_VARIABLE [{}] in [{}]".format(
                ", ".join(missing), source
            )
        )
    return mapping


def sha256_file(path: Path) -> str:
    """Compute the SHA-256 checksum of a file on disk."""
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _candidate_dataset_ids(max_candidates: int) -> List[int]:
    """Search the OpenML listing for corrosion-related datasets."""
    import openml

    listing = openml.datasets.list_datasets(output_format="dataframe")
    if listing is None or len(listing) == 0:
        raise RuntimeError(
            "OpenML dataset listing returned no datasets; cannot search "
            "for a real corrosion dataset."
        )
    names = listing["name"].astype(str).str.lower()
    mask = names.apply(
        lambda n: any(k in n for k in SEARCH_KEYWORDS)
    )
    candidates = listing[mask]
    if len(candidates) == 0:
        raise RuntimeError(
            "No OpenML datasets matched corrosion search keywords "
            "{}; no qualifying real dataset found.".format(SEARCH_KEYWORDS)
        )
    # Prefer datasets with the most features (richer candidate) and
    # sort deterministically by dataset id.
    candidates = candidates.sort_values(
        by=["NumberOfFeatures", "did"] if "NumberOfFeatures" in candidates.columns
        else "did",
        ascending=[False, True] if "NumberOfFeatures" in candidates.columns else True,
    )
    ids = [int(d) for d in candidates.index[:max_candidates]]
    log.info(
        "OpenML corrosion search: %d candidate dataset(s): %s",
        len(ids), ids,
    )
    return ids


def _get_openml_dataset(dataset_id: int):
    import openml

    return openml.datasets.get_dataset(
        dataset_id, download_data=True, download_qualities=False
    )


def _dataset_frame(dataset) -> pd.DataFrame:
    """Load the dataset's data as a DataFrame (openml 0.14 API)."""
    result = dataset.get_data(dataset_format="dataframe")
    if isinstance(result, tuple):
        frame = result[0]
    else:
        frame = result
    if not isinstance(frame, pd.DataFrame):
        raise RuntimeError(
            "OpenML dataset {} did not return a DataFrame.".format(dataset.dataset_id)
        )
    return frame


def fetch_dataset(
    dataset_id: Optional[int] = None, max_candidates: int = 25
) -> Tuple[pd.DataFrame, dict]:
    """Fetch a real qualifying corrosion dataset from OpenML.

    If ``dataset_id`` is given, that dataset is fetched and validated
    directly. Otherwise the OpenML listing is searched for
    corrosion-related datasets and each candidate is validated against
    the required variables. Raises if nothing qualifies (fail-loud).
    """
    tried: List[str] = []

    def _validate(dataset, frame: pd.DataFrame) -> Dict[str, str]:
        source = "openml:{}".format(dataset.dataset_id)
        columns = [str(c) for c in frame.columns]
        mapping = map_required_columns(columns, source)
        return mapping

    if dataset_id is not None:
        dataset = _get_openml_dataset(dataset_id)
        frame = _dataset_frame(dataset)
        mapping = _validate(dataset, frame)
        log.info(
            "Dataset %s (%s) qualifies; required-column map: %s",
            dataset_id, dataset.name, mapping,
        )
        return frame, mapping

    for did in _candidate_dataset_ids(max_candidates):
        try:
            dataset = _get_openml_dataset(did)
            frame = _dataset_frame(dataset)
        except Exception as exc:  # network/format issues on candidates
            tried.append("{} (fetch error: {})".format(did, exc))
            continue
        try:
            mapping = _validate(dataset, frame)
        except MissingVariableError as exc:
            tried.append(str(exc))
            continue
        log.info(
            "Dataset %s (%s) qualifies; required-column map: %s",
            did, dataset.name, mapping,
        )
        return frame, mapping

    raise RuntimeError(
        "FAIL: no real OpenML dataset containing all required variables "
        "({}) was found. Candidates tried: {}".format(
            ", ".join(REQUIRED_VARIABLES), tried
        )
    )


def record_provenance(
    raw_path: Path,
    meta_path: Path,
    dataset_id: Optional[int],
    dataset_name: str,
    version: Optional[int],
    url: str,
    doi: Optional[str],
    n_records: int,
    columns: List[str],
    required_map: Dict[str, str],
) -> None:
    """Write the provenance record with the raw file's SHA-256."""
    checksum = sha256_file(raw_path)
    meta = {
        "dataset_id": dataset_id,
        "dataset_name": dataset_name,
        "version": version,
        "url": url,
        "doi": doi,
        "sha256": checksum,
        "raw_file": str(raw_path.relative_to(paths.root))
        if raw_path.is_relative_to(paths.root)
        else str(raw_path),
        "downloaded_at_utc": datetime.now(timezone.utc).isoformat(),
        "n_records": int(n_records),
        "n_columns": len(columns),
        "columns": columns,
        "required_variable_map": required_map,
        "source": "OpenML (openml Python package, openml.datasets.get_dataset)",
    }
    meta_path.parent.mkdir(parents=True, exist_ok=True)
    with open(meta_path, "w", encoding="utf-8") as fh:
        yaml.safe_dump(meta, fh, sort_keys=False)
    log.info("Provenance written to %s (sha256=%s)", meta_path, checksum)


def ingest(dataset_id: Optional[int] = None, max_candidates: int = 25) -> Path:
    """Run acquisition + provenance recording; return the raw file path."""
    frame, mapping = fetch_dataset(dataset_id=dataset_id, max_candidates=max_candidates)

    # Identify the source dataset metadata for provenance. When a
    # specific id was requested we know it; otherwise recover it from
    # the fetch path by re-searching is wasteful, so fetch_dataset
    # returns metadata alongside via a second call only when needed.
    if dataset_id is None:
        # Recover the qualifying dataset id by validating candidates
        # again is expensive; instead fetch_dataset stored it.
        dataset_id = frame.attrs.get("openml_dataset_id")
        dataset_name = frame.attrs.get("openml_dataset_name", "unknown")
        version = frame.attrs.get("openml_dataset_version")
        url = frame.attrs.get(
            "openml_url",
            "https://www.openml.org/d/{}".format(dataset_id),
        )
        doi = frame.attrs.get("openml_doi")
    else:
        dataset = _get_openml_dataset(dataset_id)
        dataset_name = dataset.name
        version = getattr(dataset, "version", None)
        url = getattr(
            dataset, "url", "https://www.openml.org/d/{}".format(dataset_id)
        )
        doi = getattr(dataset, "doi", None)

    raw_dir = paths.data("raw")
    safe_name = re.sub(r"[^A-Za-z0-9_.-]+", "_", str(dataset_name))
    raw_path = raw_dir / "corrosion_{}_{}.csv".format(dataset_id, safe_name)
    frame.to_csv(raw_path, index=False)
    log.info("Raw data written to %s (%d records)", raw_path, len(frame))

    meta_path = paths.metadata("dataset.yaml")
    record_provenance(
        raw_path=raw_path,
        meta_path=meta_path,
        dataset_id=dataset_id,
        dataset_name=str(dataset_name),
        version=version,
        url=str(url),
        doi=doi,
        n_records=len(frame),
        columns=[str(c) for c in frame.columns],
        required_map=mapping,
    )
    return raw_path


def _fetch_with_metadata(dataset_id: Optional[int], max_candidates: int):
    """Fetch the qualifying dataset and attach provenance metadata."""
    import openml

    if dataset_id is not None:
        dataset = _get_openml_dataset(dataset_id)
        frame = _dataset_frame(dataset)
        mapping = map_required_columns(
            [str(c) for c in frame.columns],
            "openml:{}".format(dataset_id),
        )
    else:
        dataset = None
        frame = None
        mapping = None
        for did in _candidate_dataset_ids(max_candidates):
            try:
                cand = _get_openml_dataset(did)
                cand_frame = _dataset_frame(cand)
                cand_map = map_required_columns(
                    [str(c) for c in cand_frame.columns],
                    "openml:{}".format(did),
                )
            except Exception:
                continue
            dataset, frame, mapping = cand, cand_frame, cand_map
            break
        if dataset is None:
            raise RuntimeError(
                "FAIL: no real OpenML dataset containing all required "
                "variables ({}) was found.".format(
                    ", ".join(REQUIRED_VARIABLES)
                )
            )
    frame.attrs["openml_dataset_id"] = int(dataset.dataset_id)
    frame.attrs["openml_dataset_name"] = str(dataset.name)
    frame.attrs["openml_dataset_version"] = getattr(dataset, "version", None)
    frame.attrs["openml_url"] = getattr(
        dataset, "url",
        "https://www.openml.org/d/{}".format(dataset.dataset_id),
    )
    frame.attrs["openml_doi"] = getattr(dataset, "doi", None)
    return frame, mapping


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Fetch a real OpenML corrosion dataset and record provenance."
    )
    parser.add_argument(
        "--dataset-id", type=int, default=None,
        help="Force a specific OpenML dataset id (still validated).",
    )
    parser.add_argument(
        "--max-candidates", type=int, default=25,
        help="Maximum number of candidate datasets to inspect.",
    )
    args = parser.parse_args(argv)

    # Wire in the metadata-attaching fetch so provenance is complete.
    global fetch_dataset

    def _fetch(dataset_id=None, max_candidates=25):
        return _fetch_with_metadata(dataset_id, max_candidates)

    fetch_dataset = _fetch

    raw_path = ingest(
        dataset_id=args.dataset_id, max_candidates=args.max_candidates
    )
    meta_path = paths.metadata("dataset.yaml")
    with open(meta_path, "r", encoding="utf-8") as fh:
        meta = yaml.safe_load(fh)
    actual = sha256_file(raw_path)
    if actual != meta["sha256"]:
        raise RuntimeError(
            "Checksum mismatch between {} and {}".format(raw_path, meta_path)
        )
    print(
        "OK: raw data at {} ({} records); provenance at {} with matching "
        "SHA-256 {}.".format(raw_path, meta["n_records"], meta_path, actual)
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
