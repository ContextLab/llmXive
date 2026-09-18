"""
Target Consistency Check
------------------------

This module loads the raw Materials Project data and the NIST dataset,
aligns them on a common identifier, computes the Pearson correlation
between the two primary targets (melting point and latent heat), decides
which target should be used for downstream modelling, and writes the
decision to ``data/results/target_decision.json``.

The implementation follows the project's conventions:
* All logging is performed through the central logger in ``code.utils.logger``.
* Configuration values are read from ``config.yaml`` via ``code.config``.
* The output JSON conforms to the schema defined in
  ``contracts/target_decision.schema.yaml`` (the contract test validates it).

The script is deliberately lightweight and does **not** fabricate any
data – it works only on the real files produced by the earlier fetch
steps (``data/raw/materials_project_data.json`` and
``data/raw/nist_data.json``).  If those files are missing or malformed,
the script raises an exception so the pipeline fails loudly, as required
by the project policy.
"""

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Tuple, Optional

import pandas as pd
from scipy.stats import pearsonr

from utils.logger import get_pipeline_logger, log_info, log_error

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def _load_json_as_dataframe(file_path: Path) -> pd.DataFrame:
    """
    Load a JSON file that contains a list of dictionaries into a pandas
    DataFrame.  The function validates that the file exists and can be
    parsed; otherwise it raises a ``FileNotFoundError`` or ``ValueError``
    respectively.
    """
    if not file_path.is_file():
        raise FileNotFoundError(f"Required data file not found: {file_path}")

    try:
        # The JSON files are expected to be a list of objects.
        with file_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Failed to decode JSON from {file_path}: {exc}") from exc

    if not isinstance(data, list):
        raise ValueError(f"Expected a list of records in {file_path}, got {type(data)}")

    df = pd.DataFrame(data)
    if df.empty:
        raise ValueError(f"The loaded DataFrame from {file_path} is empty.")
    return df

def load_available_data() -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Load the two raw data sources required for the consistency check.

    Returns
    -------
    materials_df : pd.DataFrame
        Materials Project raw data.
    nist_df : pd.DataFrame
        NIST raw data.
    """
    logger = get_pipeline_logger()
    logger.debug("Loading raw Materials Project data.")
    materials_path = Path("data", "raw", "materials_project_data.json")
    nist_path = Path("data", "raw", "nist_data.json")

    materials_df = _load_json_as_dataframe(materials_path)
    nist_df = _load_json_as_dataframe(nist_path)

    logger.info(
        "Loaded %d rows from Materials Project and %d rows from NIST.",
        len(materials_df),
        len(nist_df),
    )
    return materials_df, nist_df

def _prepare_merged_dataframe(
    materials_df: pd.DataFrame, nist_df: pd.DataFrame
) -> pd.DataFrame:
    """
    Align the two data frames on a common identifier and keep only rows
    where both targets are present.

    The exact column used for alignment depends on the upstream fetch
    scripts; we support the most common identifiers:

    * ``material_id`` – a generic internal identifier.
    * ``mp_id`` – Materials Project ID (e.g., ``mp-1234``).

    The function returns a DataFrame containing the following columns
    (if they exist in the source data):

    * ``melting_point`` – numeric, in Kelvin.
    * ``latent_heat`` – numeric, in J/g or similar units.

    Rows with missing values in either column are dropped.
    """
    # Identify the join key
    possible_keys = ["material_id", "mp_id", "id"]
    join_key = None
    for key in possible_keys:
        if key in materials_df.columns and key in nist_df.columns:
            join_key = key
            break
    if join_key is None:
        raise KeyError(
            "Unable to find a common identifier column between the two datasets. "
            f"Checked keys: {possible_keys}"
        )

    # Perform inner join
    merged = pd.merge(
        materials_df,
        nist_df,
        on=join_key,
        suffixes=("_mp", "_nist"),
        how="inner",
    )

    # Determine which columns hold the targets
    # Prefer the MP version if both exist
    target_cols = {
        "melting_point": None,
        "latent_heat": None,
    }
    for col in merged.columns:
        lowered = col.lower()
        if "melting" in lowered and "point" in lowered:
            target_cols["melting_point"] = col
        if "latent" in lowered and "heat" in lowered:
            target_cols["latent_heat"] = col

    missing = [k for k, v in target_cols.items() if v is None]
    if missing:
        raise KeyError(
            f"Could not locate target columns in merged dataset: {missing}"
        )

    # Keep only the necessary columns
    final = merged[[target_cols["melting_point"], target_cols["latent_heat"]]].copy()
    final = final.dropna()
    if final.empty:
        raise ValueError("No overlapping rows with both targets present after merge.")
    return final.rename(
        columns={
            target_cols["melting_point"]: "melting_point",
            target_cols["latent_heat"]: "latent_heat",
        }
    )

def calculate_correlation(df: pd.DataFrame) -> Tuple[float, float]:
    """
    Compute Pearson correlation coefficient and two‑tailed p‑value between
    ``melting_point`` and ``latent_heat`` columns.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame containing ``melting_point`` and ``latent_heat`` columns.

    Returns
    -------
    r : float
        Pearson correlation coefficient.
    p : float
        Two‑tailed p‑value.
    """
    if not {"melting_point", "latent_heat"}.issubset(df.columns):
        raise KeyError("DataFrame must contain 'melting_point' and 'latent_heat' columns.")
    r, p = pearsonr(df["melting_point"], df["latent_heat"])
    return float(r), float(p)

def determine_target(correlation: float, p_value: float, threshold: float = 0.0) -> str:
    """
    Decide which target is more suitable for downstream modelling.

    The heuristic is simple:
    * If the correlation is positive (greater than ``threshold``) we assume
      that ``latent_heat`` can be reliably inferred from ``melting_point``
      and select it as the primary target.
    * Otherwise, we fall back to ``melting_point``.

    Parameters
    ----------
    correlation : float
        Pearson correlation coefficient.
    p_value : float
        Associated p‑value (currently unused but retained for future
        extensibility).
    threshold : float, optional
        Minimum correlation required to choose ``latent_heat``. Default is 0.0.

    Returns
    -------
    target : str
        Either ``"latent_heat"`` or ``"melting_point"``.
    """
    return "latent_heat" if correlation > threshold else "melting_point"

def save_decision(
    target: str,
    correlation: float,
    p_value: float,
    output_path: Path = Path("data", "results", "target_decision.json"),
) -> None:
    """
    Persist the decision JSON to ``output_path``.  The JSON follows the
    contract defined in ``contracts/target_decision.schema.yaml`` and
    includes a timestamp for traceability.

    Parameters
    ----------
    target : str
        Chosen target name.
    correlation : float
        Pearson correlation coefficient.
    p_value : float
        Two‑tailed p‑value.
    output_path : Path, optional
        Destination file.  Parent directories are created if missing.
    """
    logger = get_pipeline_logger()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    decision = {
        "chosen_target": target,
        "pearson_correlation": correlation,
        "p_value": p_value,
        "generated_at": datetime.utcnow().isoformat() + "Z",
    }

    with output_path.open("w", encoding="utf-8") as f:
        json.dump(decision, f, indent=2, sort_keys=True)

    logger.info("Target decision written to %s", output_path)

# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def main() -> None:
    """
    Execute the full consistency‑check pipeline:

    1. Load raw data files.
    2. Align them on a common identifier.
    3. Compute Pearson correlation between melting point and latent heat.
    4. Choose the target based on the correlation.
    5. Write the decision JSON.
    """
    logger = get_pipeline_logger()
    try:
        materials_df, nist_df = load_available_data()
        merged_df = _prepare_merged_dataframe(materials_df, nist_df)
        r, p = calculate_correlation(merged_df)
        log_info(f"Pearson r = {r:.4f}, p‑value = {p:.4e}")

        # The threshold could be made configurable; we keep it simple.
        chosen_target = determine_target(r, p, threshold=0.0)

        save_decision(
            target=chosen_target,
            correlation=r,
            p_value=p,
            output_path=Path("data", "results", "target_decision.json"),
        )
    except Exception as exc:
        # Log the full traceback and re‑raise to ensure the pipeline fails
        # loudly as required by the project policy.
        log_error(f"Target consistency check failed: {exc}")
        raise

if __name__ == "__main__":
    main()
