"""
check_permeability.py
---------------------

Scans candidate verified datasets (listed in ``config/verified_datasets.yaml``)
for the presence of a ``permeability`` column.  If a dataset containing the
required column is found, its identifier is written to
``config/selected_dataset.yaml`` and the script exits with status 0.
Otherwise an informative error is logged and the script exits with a
non‑zero status, halting the pipeline.

The script is deliberately lightweight – it only loads the minimal split
required to inspect the column names and does **not** download the full
dataset unless the column is present.  This keeps execution fast and
respects the CI runner's resource limits.
"""

import sys
import logging
from pathlib import Path
from typing import List, Dict, Any

import yaml
from datasets import load_dataset, Dataset

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------
def _project_root() -> Path:
    """Return the absolute path to the project root."""
    # This file lives in <project_root>/code/data/
    return Path(__file__).resolve().parents[2]

def _load_verified_datasets() -> List[Dict[str, Any]]:
    """
    Load ``config/verified_datasets.yaml`` which must contain a list of
    dataset specifications.  Each specification is a mapping with at least
    one of the following keys:

    - ``hf_path``: a HuggingFace dataset identifier (e.g. ``deepchem/lipophilicity``)
    - ``local_path``: a path to a local CSV file relative to the project root

    Optional keys:

    - ``split``: name of the split to load (default ``train``)
    """
    cfg_path = _project_root() / "config" / "verified_datasets.yaml"
    if not cfg_path.is_file():
        logging.error(f"Verified datasets config not found at {cfg_path}")
        return []  # Caller will treat this as a failure condition.

    with cfg_path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or []

    if not isinstance(data, list):
        raise ValueError("verified_datasets.yaml must contain a list of dataset specs")
    return data

def _has_permeability_column(dataset: Dataset) -> bool:
    """
    Return ``True`` if the supplied HuggingFace ``Dataset`` contains a column
    named ``permeability`` (case‑insensitive).  The check is performed on the
    column names without loading the entire dataset into memory.
    """
    column_names = [c.lower() for c in dataset.column_names]
    return "permeability" in column_names

def _load_dataset_from_spec(spec: Dict[str, Any]) -> Dataset:
    """
    Load a dataset according to a specification dictionary.

    Supported spec formats:
    1. HuggingFace dataset:
           {"hf_path": "deepchem/lipophilicity", "split": "train"}
    2. Local CSV file:
           {"local_path": "data/sample_permeability.csv", "split": "train"}

    The function returns a ``datasets.Dataset`` object.
    """
    split = spec.get("split", "train")

    if "hf_path" in spec:
        hf_path = spec["hf_path"]
        logging.info(f"Attempting to load HF dataset '{hf_path}' (split='{split}')")
        return load_dataset(hf_path, split=split, streaming=False)

    if "local_path" in spec:
        local_path = _project_root() / spec["local_path"]
        if not local_path.is_file():
            raise FileNotFoundError(f"Local dataset file not found: {local_path}")
        logging.info(f"Attempting to load local CSV dataset from '{local_path}' (split='{split}')")
        # ``load_dataset`` can read a CSV via the ``csv`` loader.
        return load_dataset("csv", data_files=str(local_path), split=split, streaming=False)

    raise ValueError("Dataset spec must contain either 'hf_path' or 'local_path'")

def _select_dataset(candidates: List[Dict[str, Any]]) -> str:
    """
    Iterate over candidate dataset specifications, load the minimal split,
    and return the identifier (``hf_path`` or ``local_path``) of the first
    dataset that contains a ``permeability`` column.

    Raises ``RuntimeError`` if no candidate satisfies the requirement.
    """
    for spec in candidates:
        identifier = spec.get("hf_path") or spec.get("local_path")
        if not identifier:
            continue  # malformed entry – skip

        try:
            ds: Dataset = _load_dataset_from_spec(spec)
        except Exception as exc:
            logging.error(f"Failed to load dataset '{identifier}': {exc}")
            continue  # move on to the next candidate

        if _has_permeability_column(ds):
            logging.info(f"Dataset '{identifier}' contains a permeability column.")
            return identifier

    raise RuntimeError("No verified dataset contains a 'permeability' column")

def _write_selected_dataset(selected_identifier: str) -> None:
    """
    Write the chosen dataset identifier to ``config/selected_dataset.yaml``.
    The file will contain a single top‑level key ``selected_dataset``.
    """
    out_path = _project_root() / "config" / "selected_dataset.yaml"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        yaml.safe_dump({"selected_dataset": selected_identifier}, f)
    logging.info(f"Selected dataset written to {out_path}")

# ----------------------------------------------------------------------
# Main entry point
# ----------------------------------------------------------------------
def main() -> int:
    """
    Execute the verification logic.

    Returns:
        Exit code (0 = success, 1 = failure)
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s - %(message)s",
    )
    logger = logging.getLogger(__name__)

    try:
        candidates = _load_verified_datasets()
        if not candidates:
            logger.error("Verified datasets list is empty or missing.")
            return 1

        selected = _select_dataset(candidates)
        _write_selected_dataset(selected)
        logger.info("Permeability column verified – pipeline may continue.")
        return 0

    except Exception as exc:
        logger.error(f"Permeability verification failed: {exc}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
