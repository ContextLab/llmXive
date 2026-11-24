"""
acquire_external.py
-------------------
Script to acquire external fatigue‑related datasets from OpenML and the UCI
Machine Learning Repository (via the ``ucimlrepo`` package).  The script
implements task **T014**:

1. Search OpenML for datasets whose tag list contains any of the
   ``["fatigue", "residual stress", "steel", "aluminum"]`` strings.
2. Search the UCI repository for datasets whose description contains any
   of those keywords.
3. For each candidate, download the data, flatten any nested structures,
   add a ``source`` column identifying the origin, and validate every row
   against the JSON‑Schema defined in
   ``specs/001-predicting-the-impact-of-residual-stress/contracts/dataset_schema.yaml``.
4. Persist accepted datasets as ``data/raw/external_<safe_name>.csv``.
5. Compute a SHA‑256 checksum of the *file contents* and record it in
   ``data/raw/checksums.json``.
6. Record the full query trail (datasets inspected, those accepted, and any
   errors) in ``data/external/acquisition_log.json``.
7. The script **fails loudly** on any network or parsing error – there is
   no synthetic fallback.

The script can be invoked as a module:

    python -m src.acquire_external

and is also used by the end‑to‑end runner (``src.run_e2e``) via its
``main()`` entry point.
"""

import json
import hashlib
import logging
import re
from pathlib import Path
from typing import List, Dict, Any

import pandas as pd
import yaml
from jsonschema import Draft7Validator, ValidationError

# External libraries – declared in ``requirements.txt``.
import openml
import ucimlrepo

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Constants
# ----------------------------------------------------------------------
TAG_KEYWORDS = {"fatigue", "residual stress", "steel", "aluminum"}
CHECKSUMS_PATH = paths.raw("checksums.json")
# ``paths.raw`` points to ``data/raw``; ``../external`` steps back to ``data``
# and then into the ``external`` folder.
ACQUISITION_LOG_PATH = paths.raw("../external/acquisition_log.json")
SCHEMA_PATH = Path(
    "specs/001-predicting-the-impact-of-residual-stress/contracts/dataset_schema.yaml"
)

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------
def _load_json(path: Path) -> Dict[str, Any]:
    """Load a JSON file, returning an empty dict if the file does not exist."""
    if not path.is_file():
        return {}
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)

def _dump_json(data: Dict[str, Any], path: Path) -> None:
    """Write *data* as pretty‑printed JSON to *path*."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, sort_keys=True)

def _file_checksum(path: Path) -> str:
    """Return the SHA‑256 checksum of the file *path*."""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def _safe_name(name: str) -> str:
    """Return a filesystem‑safe version of *name* (alphanumerics + underscore)."""
    return re.sub(r"[^a-zA-Z0-9_]+", "_", name).strip("_")

def _load_schema() -> Dict[str, Any]:
    """Load the dataset JSON‑Schema used throughout the project."""
    with SCHEMA_PATH.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def _validate_dataframe(df: pd.DataFrame) -> None:
    """
    Validate *df* against the project schema.  Raises ``ValueError`` if any
    row fails validation.
    """
    schema = _load_schema()
    validator = Draft7Validator(schema)

    for idx, row in df.iterrows():
        row_dict = row.to_dict()
        # Ensure ``other_process_params`` is a JSON‑encoded string.
        if isinstance(row_dict.get("other_process_params"), (dict, list)):
            row_dict["other_process_params"] = json.dumps(
                row_dict["other_process_params"]
            )
        try:
            validator.validate(row_dict)
        except ValidationError as exc:
            raise ValueError(
                f"Schema validation failed for row {idx} of dataset "
                f"{row_dict.get('source', '<unknown>')}: {exc.message}"
            ) from exc

def _flatten_nested(df: pd.DataFrame) -> pd.DataFrame:
    """
    Flatten columns that contain ``dict`` or ``list`` objects by JSON‑encoding
    them.  The function returns a *new* DataFrame.
    """
    df = df.copy()
    for col in df.columns:
        if df[col].apply(lambda x: isinstance(x, (dict, list))).any():
            df[col] = df[col].apply(
                lambda x: json.dumps(x) if isinstance(x, (dict, list)) else x
            )
    return df

# ----------------------------------------------------------------------
# OpenML acquisition
# ----------------------------------------------------------------------
def _search_openml() -> List[openml.datasets.OpenMLDataset]:
    """
    Return a list of OpenMLDataset objects whose tags intersect ``TAG_KEYWORDS``.
    The function raises any network‑related exception immediately.
    """
    log.info("Searching OpenML for datasets with tags %s", TAG_KEYWORDS)
    # ``list_datasets`` returns a DataFrame keyed by dataset ID.
    all_datasets = openml.datasets.list_datasets(output_format="dataframe")
    matches = []
    for _, row in all_datasets.iterrows():
        tags_raw = row.get("tag", "")
        if pd.isna(tags_raw):
            continue
        tags = {t.strip().lower() for t in tags_raw.split(",")}
        if tags & TAG_KEYWORDS:
            try:
                dataset = openml.datasets.get_dataset(row["did"])
                matches.append(dataset)
            except Exception as exc:
                log.error(
                    "Failed to retrieve OpenML dataset ID %s: %s", row["did"], exc
                )
                raise
    log.info("OpenML search yielded %d candidate datasets", len(matches))
    return matches

def _process_openml_dataset(dataset: openml.datasets.OpenMLDataset) -> Dict[str, Any]:
    """
    Download *dataset*, validate, and write it to ``data/raw``.
    Returns a dict describing the outcome for logging.
    """
    name = dataset.name
    safe = _safe_name(name)
    log.info("Downloading OpenML dataset %s (id=%s)", name, dataset.dataset_id)

    # ``get_data`` returns (X, y, categorical_indicator, attribute_names)
    X, y, _, attribute_names = dataset.get_data(dataset_format="dataframe")
    df = X.copy()
    if y is not None:
        df[dataset.default_target_attribute] = y

    df = _flatten_nested(df)

    # Add source column
    df["source"] = f"openml:{safe}"

    # Validate against schema
    _validate_dataframe(df)

    # Persist
    out_path = paths.raw(f"external_{safe}.csv")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False)

    # Compute checksum of the whole file
    checksum = _file_checksum(out_path)

    return {
        "origin": "openml",
        "name": name,
        "dataset_id": dataset.dataset_id,
        "file": str(out_path),
        "checksum": checksum,
        "status": "success",
    }

# ----------------------------------------------------------------------
# UCI acquisition
# ----------------------------------------------------------------------
def _search_uciml() -> List[Dict[str, Any]]:
    """
    Return a list of UCI dataset metadata dictionaries whose description
    contains any of the ``TAG_KEYWORDS``.  ``ucimlrepo`` raises its own
    network exceptions which we let propagate.
    """
    log.info("Searching UCI repository for datasets with keywords %s", TAG_KEYWORDS)
    all_meta = ucimlrepo.list_datasets()
    matches = []
    for meta in all_meta:
        description = meta.get("description", "").lower()
        if any(keyword in description for keyword in TAG_KEYWORDS):
            matches.append(meta)
    log.info("UCI search yielded %d candidate datasets", len(matches))
    return matches

def _process_uciml_dataset(meta: Dict[str, Any]) -> Dict[str, Any]:
    """
    Download a UCI dataset given its metadata, validate, write CSV and
    return a logging dict.
    """
    name = meta.get("name", "unknown")
    safe = _safe_name(name)
    log.info("Downloading UCI dataset %s", name)

    # ``get_dataset`` returns a pandas DataFrame.
    df = ucimlrepo.get_dataset(name)

    df = _flatten_nested(df)

    # Add source column
    df["source"] = f"uci:{safe}"

    # Validate against schema
    _validate_dataframe(df)

    # Persist
    out_path = paths.raw(f"external_{safe}.csv")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False)

    # Compute checksum
    checksum = _file_checksum(out_path)

    return {
        "origin": "uci",
        "name": name,
        "file": str(out_path),
        "checksum": checksum,
        "status": "success",
    }

# ----------------------------------------------------------------------
# Main orchestration
# ----------------------------------------------------------------------
def main() -> None:
    """
    Execute the full acquisition pipeline:

    * Search OpenML and UCI for candidate datasets.
    * Attempt to download, flatten, validate and persist each candidate.
    * Record per‑file SHA‑256 checksums in ``data/raw/checksums.json``.
    * Write a detailed log of the acquisition process to
      ``data/external/acquisition_log.json``.
    """
    # Load existing checksum mapping (may be empty)
    checksums = _load_json(CHECKSUMS_PATH)

    # Prepare log structure
    log_record: Dict[str, Any] = {
        "openml": {"candidates": [], "acquired": []},
        "uci": {"candidates": [], "acquired": []},
    }

    # ---------------------------- OpenML ----------------------------
    openml_candidates = _search_openml()
    for ds in openml_candidates:
        cand_entry = {
            "origin": "openml",
            "name": ds.name,
            "dataset_id": ds.dataset_id,
        }
        log_record["openml"]["candidates"].append(cand_entry)

    for ds in openml_candidates:
        try:
            result = _process_openml_dataset(ds)
            log_record["openml"]["acquired"].append(result)
            # Update checksums.json
            checksums[result["file"]] = result["checksum"]
        except Exception as exc:
            err_entry = {
                "origin": "openml",
                "name": ds.name,
                "dataset_id": ds.dataset_id,
                "status": "failed",
                "error": str(exc),
            }
            log_record["openml"]["acquired"].append(err_entry)
            # Propagate the exception – the task must fail loudly.
            raise

    # ---------------------------- UCI ----------------------------
    uci_candidates = _search_uciml()
    for meta in uci_candidates:
        cand_entry = {
            "origin": "uci",
            "name": meta.get("name", "unknown"),
            "url": meta.get("url", ""),
        }
        log_record["uci"]["candidates"].append(cand_entry)

    for meta in uci_candidates:
        try:
            result = _process_uciml_dataset(meta)
            log_record["uci"]["acquired"].append(result)
            checksums[result["file"]] = result["checksum"]
        except Exception as exc:
            err_entry = {
                "origin": "uci",
                "name": meta.get("name", "unknown"),
                "status": "failed",
                "error": str(exc),
            }
            log_record["uci"]["acquired"].append(err_entry)
            raise

    # Write updated checksums
    _dump_json(checksums, CHECKSUMS_PATH)

    # Write acquisition log
    _dump_json(log_record, ACQUISITION_LOG_PATH)

    log.info("Acquisition completed. %d files written.", len(checksums))

if __name__ == "__main__":
    main()
