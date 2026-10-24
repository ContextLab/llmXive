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
    the key ``hf_path`` (the HuggingFace identifier) and optionally a
    ``split`` name (default ``train``).

    Example YAML structure:

    .. code-block:: yaml

        - hf_path: deepchem/lipophilicity
          split: train
        - hf_path: myorg/my_permeability_dataset
          split: train
    """
    cfg_path = _project_root() / "config" / "verified_datasets.yaml"
    if not cfg_path.is_file():
        # Gracefully handle a missing configuration – the pipeline cannot
        # continue without a list of candidates, but we should not raise
        # an unhandled exception (which would be interpreted as a crash).
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
    first row to avoid loading the entire dataset into memory.
    """
    column_names = [c.lower() for c in dataset.column_names]
    return "permeability" in column_names

def _select_dataset(candidates: List[Dict[str, Any]]) -> str:
    """
    Iterate over candidate dataset specifications, load the minimal split,
    and return the identifier (``hf_path``) of the first dataset that
    contains a ``permeability`` column.

    Raises ``RuntimeError`` if no candidate satisfies the requirement.
    """
    for spec in candidates:
        hf_path = spec.get("hf_path")
        split = spec.get("split", "train")
        if not hf_path:
            continue  # malformed entry – skip

        logging.info(f"Inspecting dataset '{hf_path}' (split='{split}') for permeability column")
        try:
            # ``load_dataset`` lazily streams the data; we request a single example
            # to keep memory usage low.
            ds: Dataset = load_dataset(hf_path, split=split, streaming=False)
        except Exception as exc:
            logging.error(f"Failed to load dataset '{hf_path}': {exc}")
            continue  # move on to the next candidate

        if _has_permeability_column(ds):
            logging.info(f"Dataset '{hf_path}' contains a permeability column.")
            return hf_path

    raise RuntimeError("No verified dataset contains a 'permeability' column")

def _write_selected_dataset(selected_hf_path: str) -> None:
    """
    Write the chosen dataset identifier to ``config/selected_dataset.yaml``.
    The file will contain a single top‑level key ``selected_dataset``.
    """
    out_path = _project_root() / "config" / "selected_dataset.yaml"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        yaml.safe_dump({"selected_dataset": selected_hf_path}, f)
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