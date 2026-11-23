"""
Download logic for Materials Project and NIST data sources.

This module provides functions to fetch raw alloy data from the Materials
Project (using the `matminer` wrapper around the Materials Project REST API)
and from the verified NIST Materials Data Repository (via the HuggingFace
`datasets` library). The fetched data are saved as JSON files under the
project's ``data/raw`` directory.

The implementation follows the contract described in the task
specification (T009a) and raises clear exceptions if required
environment variables are missing or if the remote source cannot be
accessed.
"""

import os
import json
from pathlib import Path
from typing import List, Dict, Any, Optional

from logging_config import get_logger

# The logger is deliberately tolerant; it will write JSON‑structured logs
# to ``data/logs/app.log`` as configured by ``logging_config.setup_logging``.
logger = get_logger("download_logic")

def _ensure_output_dir(output_dir: Optional[Path]) -> Path:
    """
    Resolve the output directory, creating it if necessary.

    Parameters
    ----------
    output_dir: Optional[Path]
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

def fetch_materials_project_data(output_dir: Optional[Path] = None) -> List[Dict[str, Any]]:
    """
    Fetch alloy data for aluminum‑based compounds from the Materials Project.

    The function requires a valid Materials Project API key set in the
    ``MP_API_KEY`` environment variable. It queries for entries that contain
    aluminum and for which the elastic properties (Poisson's ratio and
    Young's modulus) are available. The raw records are written to
    ``data/raw/mp_raw.json`` and also returned as a list of dictionaries.

    Parameters
    ----------
    output_dir: Optional[Path]
        Directory where ``mp_raw.json`` will be saved. If omitted the
        default ``data/raw`` directory is used.

    Returns
    -------
    List[Dict[str, Any]]
        A list of raw alloy records.

    Raises
    ------
    ValueError
        If the ``MP_API_KEY`` environment variable is not set.
    RuntimeError
        If the query returns zero records or the remote service cannot be
        reached.
    """
    api_key = os.getenv("MP_API_KEY")
    if not api_key:
        raise ValueError("Environment variable MP_API_KEY must be set to access the Materials Project API.")

    # Lazy import to keep the module importable even when matminer is not
    # installed (e.g., during documentation builds). The import error is
    # turned into a RuntimeError with a clear message.
    try:
        from pymatgen.ext.matproj import MPRester
    except Exception as exc:
        raise RuntimeError("Failed to import MPRester – ensure that 'matminer' and its dependencies are installed.") from exc

    logger.info("Starting Materials Project extraction.", extra={"source": "Materials Project", "stage": "fetch"})

    # Query for entries that contain Al and have elastic properties.
    # The `$all` operator ensures Al is present in the element list.
    criteria = {"elements": {"$all": ["Al"]}}
    properties = [
        "material_id",
        "pretty_formula",
        "elasticity",          # contains Poisson's ratio, Young's modulus, etc.
        "elastic_tensor",      # optional, kept for completeness
    ]

    try:
        with MPRester(api_key) as mpr:
            records = mpr.query(criteria=criteria, properties=properties)
    except Exception as exc:
        raise RuntimeError(f"Materials Project query failed: {exc}") from exc

    if not records:
        raise RuntimeError("Materials Project query returned zero records.")

    # Transform the raw records into a flat structure suitable for downstream
    # processing.  Only the fields required by later pipeline steps are kept.
    processed: List[Dict[str, Any]] = []
    for rec in records:
        elasticity = rec.get("elasticity", {})
        # Some entries may miss individual fields; we keep them as ``None`` –
        # later cleaning steps will filter them out.
        entry = {
            "material_id": rec.get("material_id"),
            "formula": rec.get("pretty_formula"),
            "poisson_ratio": elasticity.get("poisson_ratio"),
            "youngs_modulus": elasticity.get("youngs_modulus"),
            "elastic_tensor": rec.get("elastic_tensor"),
        }
        processed.append(entry)

    out_dir = _ensure_output_dir(output_dir)
    out_path = out_dir / "mp_raw.json"
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(processed, f, indent=2)

    logger.info(
        "Materials Project extraction completed.",
        extra={"source": "Materials Project", "stage": "fetch", "records": len(processed), "output_path": str(out_path)},
    )
    return processed

def fetch_nist_data(output_dir: Optional[Path] = None) -> List[Dict[str, Any]]:
    """
    Fetch alloy data from the verified NIST Materials Data Repository.

    The dataset is accessed via the HuggingFace ``datasets`` library using
    the identifier ``materials/alloy-elastic``.  The function verifies that
    the loaded dataset matches the expected configuration name and then
    writes the raw records to ``data/raw/nist_alloys.json``.

    Parameters
    ----------
    output_dir: Optional[Path]
        Directory where ``nist_alloys.json`` will be saved.  If omitted the
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
    logger.info("Starting NIST MDR extraction.", extra={"source": "NIST", "stage": "fetch"})

    try:
        from datasets import load_dataset
    except Exception as exc:
        raise ImportError("The 'datasets' package is required to fetch NIST data.") from exc

    try:
        ds = load_dataset("materials/alloy-elastic", split="train")
    except Exception as exc:
        raise RuntimeError(f"Failed to load NIST dataset via HuggingFace: {exc}") from exc

    # Verify that the dataset configuration matches expectations.
    if getattr(ds.info, "config_name", None) != "materials/alloy-elastic":
        raise RuntimeError(
            f"NIST dataset config mismatch: expected 'materials/alloy-elastic', got '{getattr(ds.info, 'config_name', None)}'"
        )

    records = [r for r in ds]  # materialise the dataset into a list of dicts
    if not records:
        raise RuntimeError("NIST MDR dataset is empty after loading.")

    out_dir = _ensure_output_dir(output_dir)
    out_path = out_dir / "nist_alloys.json"
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(records, f, indent=2)

    logger.info(
        "NIST MDR extraction completed.",
        extra={"source": "NIST", "stage": "fetch", "records": len(records), "output_path": str(out_path)},
    )
    return records

def run_extraction(mp_output_dir: Optional[Path] = None, nist_output_dir: Optional[Path] = None) -> Dict[str, List[Dict[str, Any]]]:
    """
    Orchestrate the extraction of both Materials Project and NIST data.

    The function returns a dictionary with two keys, ``materials_project`` and
    ``nist``, each mapping to the list of raw records obtained from the
    respective source.

    Parameters
    ----------
    mp_output_dir, nist_output_dir
        Optional directories for the two output files.  If omitted the
        default ``data/raw`` directory is used for both.

    Returns
    -------
    Dict[str, List[Dict[str, Any]]]
        ``{'materials_project': [...], 'nist': [...]}``
    """
    mp_data = fetch_materials_project_data(mp_output_dir)
    nist_data = fetch_nist_data(nist_output_dir)
    return {"materials_project": mp_data, "nist": nist_data}

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
        raise
