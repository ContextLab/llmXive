"""
Fetch Materials Project data with a robust fallback to a verified matbench dataset.

This script attempts to retrieve a curated set of materials data from the
Materials Project API using the provided API key (configured in `config.yaml`).
If the API request fails (e.g., due to network issues, authentication problems,
or rate‑limiting), the script logs the failure and falls back to loading a
publicly available matbench dataset. The resulting list of material records is
written to `data/raw/materials_project_data.json` together with a SHA‑256
checksum file `data/raw/materials_project_data.sha256`.

The script validates that at least 5 000 material records are present; if the
count is lower, it raises a `RuntimeError` so the pipeline can abort early.
"""

import json
from pathlib import Path
from typing import Any, Dict, List

# Import logger functions directly from the concrete module to avoid triggering
# utils/__init__ (which can cause circular import issues).
from code.utils.logger import (
    get_pipeline_logger,
    log_error,
    log_info,
    log_warning,
)
from config import get_api_key
from utils.checksum import compute_sha256

MIN_ROWS = 5_000  # Minimum number of material entries required


def fetch_materials_project_data() -> List[Dict[str, Any]]:
    """
    Retrieve materials data from the Materials Project API.

    Returns
    -------
    List[Dict[str, Any]]
        A list of dictionaries, each representing a material with selected
        properties.
    """
    api_key = get_api_key()
    try:
        # Import inside the function to avoid import‑time failures if the
        # dependency is missing; the exception will be caught by the caller.
        from mp_api.client import MPRester
    except Exception as exc:
        log_error(f"mp-api package not available: {exc}")
        raise

    try:
        with MPRester(api_key) as mpr:
            # Retrieve a concise set of properties useful for downstream
            # descriptor computation and modeling.
            docs = mpr.materials.summary.search(
                criteria={},
                properties=[
                    "material_id",
                    "pretty_formula",
                    "formation_energy_per_atom",
                    "band_gap",
                    "e_above_hull",
                ],
            )
            # `docs` is an iterable of dict‑like objects.
            data = [dict(doc) for doc in docs]
            log_info(f"Fetched {len(data)} records from Materials Project.")
            return data
    except Exception as exc:
        log_error(f"Error while querying Materials Project: {exc}")
        raise


def fetch_matbench_fallback() -> List[Dict[str, Any]]:
    """
    Load a verified matbench dataset as a fallback source.

    Returns
    -------
    List[Dict[str, Any]]
        A list of dictionaries containing material records from the matbench
        dataset.
    """
    try:
        from datasets import load_dataset
    except Exception as exc:
        log_error(f"`datasets` package not available: {exc}")
        raise

    try:
        # The "matbench_expt_gap" subset is a well‑curated benchmark that
        # includes Materials Project IDs and several physical properties.
        ds = load_dataset("matbench", "matbench_expt_gap", split="train")
        data = [dict(row) for row in ds]
        log_info(f"Loaded {len(data)} records from matbench fallback.")
        return data
    except Exception as exc:
        log_error(f"Failed to load matbench fallback dataset: {exc}")
        raise


def _validate_row_count(data: List[Dict[str, Any]]) -> None:
    """
    Ensure that the fetched data meets the minimum row‑count requirement.

    Parameters
    ----------
    data : List[Dict[str, Any]]
        The material records to validate.

    Raises
    ------
    RuntimeError
        If the number of records is below `MIN_ROWS`.
    """
    row_count = len(data)
    if row_count < MIN_ROWS:
        raise RuntimeError(
            f"Insufficient material records: {row_count} < required {MIN_ROWS}"
        )
    log_info(f"Validated row count: {row_count} records (≥ {MIN_ROWS}).")


def main() -> None:
    """
    Entry point for the script.

    Attempts to fetch data from the Materials Project API; on any exception,
    falls back to the matbench dataset. The final data is written to
    `data/raw/materials_project_data.json` together with a SHA‑256 checksum.
    """
    logger = get_pipeline_logger(__name__)

    output_path = Path("data/raw/materials_project_data.json")
    checksum_path = output_path.with_suffix(".sha256")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        materials_data = fetch_materials_project_data()
        log_info("Successfully retrieved Materials Project data.")
    except Exception:
        log_warning(
            "Materials Project fetch failed – falling back to matbench dataset."
        )
        try:
            materials_data = fetch_matbench_fallback()
        except Exception as fallback_exc:
            log_error(
                f"Both primary and fallback data sources failed: {fallback_exc}"
            )
            raise

    # Validate that we have enough rows before persisting.
    _validate_row_count(materials_data)

    # Write the data atomically to avoid partial writes on interruption.
    temp_path = output_path.with_suffix(".tmp")
    with open(temp_path, "w", encoding="utf-8") as f:
        json.dump(materials_data, f, indent=2, ensure_ascii=False)
    temp_path.replace(output_path)

    # Compute and store a SHA‑256 checksum for downstream integrity checks.
    checksum = compute_sha256(output_path)
    checksum_path.write_text(checksum, encoding="utf-8")

    log_info(f"Materials data written to {output_path}")
    log_info(f"Checksum written to {checksum_path}")


if __name__ == "__main__":
    main()
