"""
Data download logic for Materials Project and NIST Materials Data Repository.
Implements fetching of raw alloy data and writes JSON files to the project's
data/raw directory. The functions raise clear exceptions on failure to
satisfy FR‑001 which requires both sources.
"""
import json
import os
from pathlib import Path
from typing import List, Dict, Any, Optional

from logging_config import get_logger

logger = get_logger(__name__)

# ----------------------------------------------------------------------
# Helper
# ----------------------------------------------------------------------
def _ensure_output_dir(output_dir: Optional[Path] = None) -> Path:
    """
    Resolve the output directory, creating it if necessary.

    Parameters
    ----------
    output_dir : Optional[Path]
        Desired output directory. If ``None`` the function uses the
        project's ``data/raw`` folder.

    Returns
    -------
    Path
        The directory that will receive the JSON file.
    """
    if output_dir is None:
        output_dir = Path("data") / "raw"
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir

# ----------------------------------------------------------------------
# Materials Project download (already implemented elsewhere)
# ----------------------------------------------------------------------
# The function ``fetch_materials_project_data`` is provided by the existing
# module ``_download_logic`` in the repository.  We simply import it here
# to keep a single public API surface.
from _download_logic import fetch_materials_project_data  # type: ignore

# ----------------------------------------------------------------------
# NIST Materials Data Repository download
# ----------------------------------------------------------------------
def fetch_nist_data(output_dir: Optional[Path] = None) -> List[Dict[str, Any]]:
    """
    Fetch alloy data from the verified NIST Materials Data Repository.

    The dataset is accessed via the HuggingFace ``datasets`` library using
    the identifier ``materials/alloy-elastic``. The function verifies that
    the loaded dataset matches the expected configuration name and then
    writes the raw records to ``data/raw/nist_alloys.json``.

    Parameters
    ----------
    output_dir : Optional[Path]
        Directory where ``nist_alloys.json`` will be saved. If omitted the
        default ``data/raw`` directory is used.

    Returns
    -------
    List[Dict[str, Any]]
        The list of raw alloy records.

    Raises
    ------
    ImportError
        If the ``datasets`` package is not installed.
    RuntimeError
        If the dataset cannot be loaded, does not contain any records, or
        fails the configuration‑name check.
    """
    try:
        from datasets import load_dataset
    except ImportError as exc:
        logger.error("The 'datasets' package is required for NIST data download.")
        raise ImportError(
            "Please install the 'datasets' package (e.g., pip install datasets)."
        ) from exc

    logger.info("Starting download of NIST Materials Data Repository alloy dataset.")

    # Load the dataset; we use the default configuration which is expected
    # to contain the required fields (composition, Poisson's ratio, etc.).
    try:
        ds = load_dataset("materials/alloy-elastic", split="train")
    except Exception as exc:
        logger.error(f"Failed to load NIST dataset via HuggingFace: {exc}")
        raise RuntimeError("Unable to load NIST alloy dataset.") from exc

    # Basic sanity check – ensure we have records
    if len(ds) == 0:
        logger.error("NIST dataset loaded but contains zero records.")
        raise RuntimeError("NIST dataset is empty after loading.")

    # Convert to a list of Python dicts
    records: List[Dict[str, Any]] = [dict(item) for item in ds]

    # Verify that the expected configuration name is present.
    # The dataset should contain a field named 'configuration' with value
    # 'alloy-elastic' (or similar). This check guards against accidental
    # loading of a wrong split.
    config_name = ds.info.builder_name if hasattr(ds, "info") else None
    if config_name and "alloy-elastic" not in config_name:
        logger.error(
            f"Unexpected NIST dataset configuration: {config_name!r}. "
            "Expected a configuration containing 'alloy-elastic'."
        )
        raise RuntimeError(
            f"NIST dataset configuration mismatch: {config_name!r}"
        )

    # Write JSON output
    out_dir = _ensure_output_dir(output_dir)
    out_path = out_dir / "nist_alloys.json"
    try:
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(records, f, ensure_ascii=False, indent=2)
    except Exception as exc:
        logger.error(f"Failed to write NIST data to {out_path}: {exc}")
        raise RuntimeError(f"Could not write NIST data to {out_path}") from exc

    logger.info(f"NIST alloy data successfully written to {out_path}")
    return records

# ----------------------------------------------------------------------
# Orchestrator
# ----------------------------------------------------------------------
def run_extraction(
    mp_output_dir: Optional[Path] = None,
    nist_output_dir: Optional[Path] = None,
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Orchestrate the extraction of both Materials Project and NIST data.

    Returns
    -------
    Dict[str, List[Dict[str, Any]]]
        ``{'materials_project': [...], 'nist': [...]}``
    """
    logger.info("Running combined data extraction workflow.")
    mp_records = fetch_materials_project_data(mp_output_dir)
    nist_records = fetch_nist_data(nist_output_dir)

    if not mp_records:
        logger.error("Materials Project extraction returned zero records.")
        raise RuntimeError("Materials Project dataset is empty.")
    if not nist_records:
        logger.error("NIST extraction returned zero records.")
        raise RuntimeError("NIST dataset is empty.")

    logger.info(
        f"Extraction complete: {len(mp_records)} MP records, {len(nist_records)} NIST records."
    )
    return {"materials_project": mp_records, "nist": nist_records}

def main() -> None:
    """
    Command‑line entry point.  When the module is executed as a script it
    performs the full extraction workflow and exits with a non‑zero status
    if any step fails.
    """
    try:
        run_extraction()
    except Exception as exc:
        logger.error(f"Data extraction failed: {exc}")
        raise SystemExit(1) from exc
