"""
Target Consistency Check
------------------------

This module loads the raw Materials Project data and the NIST data, merges them on a
common identifier, computes the Pearson correlation between the two target properties
(latent heat and melting point), decides which target should be used for downstream
modeling, and writes the decision to ``data/results/target_decision.json``.

The implementation follows the public API surface of the project:
  * Logging utilities are imported from ``utils.logger``.
  * Configuration (if needed) would be loaded via ``config`` but is not required for
    this script.
  * All file paths are resolved relative to the repository root using ``Path``.
"""

import json
import logging
import os
from pathlib import Path
from typing import Tuple, Optional

import pandas as pd

# Project‑wide logger utilities
from utils.logger import get_pipeline_logger, log_error, log_info

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------


def _resolve_path(relative_path: str) -> Path:
    """
    Resolve a path relative to the repository root.

    Parameters
    ----------
    relative_path: str
        Path relative to the repository root (e.g. ``data/raw/...``).

    Returns
    -------
    Path
        Absolute ``Path`` object.
    """
    repo_root = Path(__file__).resolve().parents[2]  # ``code/data`` -> repo root
    return repo_root / relative_path


def load_available_data() -> pd.DataFrame:
    """
    Load the raw Materials Project data and the NIST data, and merge them on a
    common identifier (``material_id``).

    Returns
    -------
    pd.DataFrame
        Merged DataFrame containing at least the columns
        ``material_id``, ``latent_heat`` and ``melting_point``.
    """
    logger = get_pipeline_logger()
    logger.debug("Loading raw Materials Project data.")
    mp_path = _resolve_path("data/raw/materials_project_data.json")
    nist_path = _resolve_path("data/raw/nist_data.json")

    if not mp_path.is_file():
        raise FileNotFoundError(f"Materials Project data not found at {mp_path}")
    if not nist_path.is_file():
        raise FileNotFoundError(f"NIST data not found at {nist_path}")

    # The JSON files are expected to be a list of dictionaries.
    with mp_path.open("r", encoding="utf-8") as f:
        mp_records = json.load(f)

    with nist_path.open("r", encoding="utf-8") as f:
        nist_records = json.load(f)

    mp_df = pd.DataFrame(mp_records)
    nist_df = pd.DataFrame(nist_records)

    # Ensure expected columns exist
    required_mp_cols = {"material_id", "latent_heat"}
    required_nist_cols = {"material_id", "melting_point"}

    missing_mp = required_mp_cols - set(mp_df.columns)
    missing_nist = required_nist_cols - set(nist_df.columns)

    if missing_mp:
        raise KeyError(f"Materials Project data missing columns: {missing_mp}")
    if missing_nist:
        raise KeyError(f"NIST data missing columns: {missing_nist}")

    logger.debug("Merging datasets on 'material_id'.")
    merged = pd.merge(mp_df, nist_df, on="material_id", how="inner")
    logger.info(f"Merged dataset contains {len(merged)} overlapping entries.")
    return merged


def calculate_correlation(df: pd.DataFrame) -> Optional[float]:
    """
    Calculate the Pearson correlation coefficient between ``latent_heat`` and
    ``melting_point`` in the provided DataFrame.

    Parameters
    ----------
    df: pd.DataFrame
        DataFrame containing ``latent_heat`` and ``melting_point`` columns.

    Returns
    -------
    Optional[float]
        Pearson r value, or ``None`` if the correlation cannot be computed
        (e.g., not enough data).
    """
    logger = get_pipeline_logger()
    if df.empty:
        logger.warning("Empty DataFrame supplied to calculate_correlation.")
        return None

    # Drop rows with NaN in either column
    clean_df = df.dropna(subset=["latent_heat", "melting_point"])
    if len(clean_df) < 2:
        logger.warning(
            "Insufficient non‑NaN rows (%d) for correlation calculation.",
            len(clean_df),
        )
        return None

    r = clean_df["latent_heat"].corr(clean_df["melting_point"])
    logger.info(f"Pearson correlation (latent_heat vs melting_point): {r:.4f}")
    return r


def determine_target(correlation: Optional[float]) -> str:
    """
    Decide which target property to use for downstream modeling.

    The heuristic is simple:
      * If the correlation is positive (greater than zero), we assume ``latent_heat``
        tracks ``melting_point`` sensibly and select ``latent_heat`` as the primary
        target.
      * If the correlation is zero or negative, we fall back to ``melting_point``.

    Parameters
    ----------
    correlation: Optional[float]
        Pearson r value (or ``None`` if not computable).

    Returns
    -------
    str
        Chosen target name (``latent_heat`` or ``melting_point``).
    """
    logger = get_pipeline_logger()
    if correlation is None:
        logger.warning(
            "Correlation could not be computed; defaulting to 'melting_point'."
        )
        return "melting_point"

    chosen = "latent_heat" if correlation > 0 else "melting_point"
    logger.info(f"Target decision based on correlation: {chosen}")
    return chosen


def save_decision(
    correlation: Optional[float],
    chosen_target: str,
    output_path: Optional[Path] = None,
) -> None:
    """
    Write the target decision to a JSON file.

    The JSON structure follows the contract defined in
    ``contracts/target_decision.schema.yaml`` (which expects ``correlation``,
    ``chosen_target`` and a ``timestamp``).

    Parameters
    ----------
    correlation: Optional[float]
        Pearson correlation coefficient (may be ``null`` in JSON if unavailable).
    chosen_target: str
        The target selected for downstream work.
    output_path: Optional[Path]
        Destination path; defaults to ``data/results/target_decision.json``.
    """
    logger = get_pipeline_logger()
    if output_path is None:
        output_path = _resolve_path("data/results/target_decision.json")

    decision = {
        "correlation": correlation,
        "chosen_target": chosen_target,
        "timestamp": pd.Timestamp.utcnow().isoformat() + "Z",
    }

    # Ensure the parent directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as f:
        json.dump(decision, f, indent=2)

    logger.info(f"Target decision written to {output_path}")


# ----------------------------------------------------------------------
# Main entry point
# ----------------------------------------------------------------------


def main() -> Tuple[Optional[float], str]:
    """
    Execute the full target‑consistency workflow.

    Returns
    -------
    Tuple[Optional[float], str]
        The computed Pearson correlation and the chosen target.
    """
    logger = get_pipeline_logger()
    logger.info("Starting target consistency check.")

    try:
        merged_df = load_available_data()
        correlation = calculate_correlation(merged_df)
        chosen_target = determine_target(correlation)
        save_decision(correlation, chosen_target)
        logger.info("Target consistency check completed successfully.")
        return correlation, chosen_target
    except Exception as exc:
        # Log the full traceback and re‑raise for visibility to the pipeline.
        log_error(f"Target consistency check failed: {exc}")
        raise


if __name__ == "__main__":
    # When executed as a script, run the workflow and exit with a non‑zero code
    # on failure (the exception will propagate).
    main()