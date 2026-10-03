"""
Target consistency check.

This script loads the Materials Project data and the NIST data, evaluates the
overlap between them, computes a Pearson correlation for the overlapping
entries, decides which property should be used as the primary target, and
writes two JSON artefacts:

* ``data/results/target_decision.json`` – the chosen target name and a flag
  indicating whether a fallback was required.
* ``data/results/imputation_rate_report.json`` – statistics about missing
  values, the proxy‑correlation, and the fallback flag.

The script is deliberately lightweight and uses only the public APIs that
already exist in the repository.
"""

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Tuple, Optional, Dict, List

import pandas as pd
from scipy.stats import pearsonr

# Import the logger directly to avoid the circular import problem described in
# the project’s execution failures.
from code.utils.logger import get_pipeline_logger, log_info, log_error

# -------------------------------------------------------------------------
# Helper functions
# -------------------------------------------------------------------------

def _load_json(path: Path) -> List[Dict]:
    """Load a JSON file that contains a list of dictionaries."""
    if not path.is_file():
        raise FileNotFoundError(f"Expected JSON file not found: {path}")
    with path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, list):
        raise ValueError(f"JSON content must be a list, got {type(data)}")
    return data

# -------------------------------------------------------------------------
# Core API (public as declared in the module header)
# -------------------------------------------------------------------------

def load_available_data() -> Tuple[List[Dict], List[Dict]]:
    """
    Load the raw Materials Project and NIST datasets.

    Returns
    -------
    mp_data, nist_data : tuple of list of dicts
        The raw records as they appear in the JSON files.
    """
    logger = get_pipeline_logger(__name__)
    logger.debug("Loading raw data files.")

    mp_path = Path("data/raw/materials_project_data.json")
    nist_path = Path("data/raw/nist_data.json")

    mp_data = _load_json(mp_path)
    nist_data = _load_json(nist_path)

    logger.info(
        "Loaded %d Materials Project records and %d NIST records.",
        len(mp_data),
        len(nist_data),
    )
    return mp_data, nist_data

def calculate_correlation(
    mp_data: List[Dict], nist_data: List[Dict], target_key: str = "melting_point"
) -> Tuple[Optional[float], int]:
    """
    Compute Pearson correlation for the overlapping entries.

    Parameters
    ----------
    mp_data, nist_data : list of dict
        Raw records from the two sources.
    target_key : str, optional
        The property used as the target for correlation. Defaults to
        ``melting_point`` because it is present in both sources.

    Returns
    -------
    correlation : float or None
        Pearson r value if at least two overlapping points exist, otherwise
        ``None``.
    overlap_count : int
        Number of overlapping records that have a non‑null value for the
        target key in *both* datasets.
    """
    logger = get_pipeline_logger(__name__)

    # Convert to DataFrames for easier handling
    mp_df = pd.DataFrame(mp_data)
    nist_df = pd.DataFrame(nist_data)

    # The unique identifier used to match records.  All fetch scripts store the
    # Materials Project ID under the column ``material_id``.
    id_col = "material_id"

    if id_col not in mp_df.columns or id_col not in nist_df.columns:
        raise KeyError(
            f"Both datasets must contain a '{id_col}' column for matching."
        )

    # Keep only rows where the target exists and is not NaN
    mp_target = mp_df[[id_col, target_key]].dropna()
    nist_target = nist_df[[id_col, target_key]].dropna()

    # Merge on the identifier
    merged = pd.merge(
        mp_target,
        nist_target,
        on=id_col,
        suffixes=("_mp", "_nist"),
    )

    overlap_count = len(merged)
    logger.info("Found %d overlapping records with non‑null target.", overlap_count)

    if overlap_count < 2:
        logger.warning(
            "Not enough overlapping points to compute a Pearson correlation."
        )
        return None, overlap_count

    # Compute Pearson correlation between the two sources
    r, _ = pearsonr(merged[f"{target_key}_mp"], merged[f"{target_key}_nist"])
    logger.info("Pearson correlation (r) for '%s' = %.4f", target_key, r)
    return r, overlap_count

def determine_target(
    correlation: Optional[float],
    overlap_count: int,
    fallback_threshold: int = 500,
    correlation_threshold: float = 0.0,
) -> Tuple[str, bool]:
    """
    Decide which property should be used as the primary target.

    The rule set follows the original specification:

    * If the overlap between the two sources is **≥ fallback_threshold**
      *and* the correlation is greater than ``correlation_threshold``,
      the primary target is the property itself (e.g. ``melting_point``).
    * Otherwise we fall back to a proxy target (here we use ``melting_point`` as
      a generic proxy) and set ``fallback_flag`` to ``True``.

    Returns
    -------
    target_name : str
        The chosen target column name.
    fallback_flag : bool
        ``True`` if a fallback was required, ``False`` otherwise.
    """
    logger = get_pipeline_logger(__name__)

    if overlap_count >= fallback_threshold and correlation is not None and correlation > correlation_threshold:
        logger.info(
            "Sufficient overlap (%d) and correlation (%.4f) – using primary target.",
            overlap_count,
            correlation,
        )
        return "melting_point", False
    else:
        logger.warning(
            "Insufficient overlap (%d) or low correlation – falling back to proxy target.",
            overlap_count,
        )
        return "melting_point", True

def save_decision(
    target_name: str,
    fallback_flag: bool,
    imputation_rate: float,
    proxy_correlation: Optional[float],
) -> None:
    """
    Write the decision artefacts to ``data/results``.

    Parameters
    ----------
    target_name : str
        The chosen target column.
    fallback_flag : bool
        Whether a fallback was triggered.
    imputation_rate : float
        Fraction of missing target values in the NIST dataset (0‑1).
    proxy_correlation : float or None
        Correlation used for the proxy decision.
    """
    logger = get_pipeline_logger(__name__)

    results_dir = Path("data/results")
    results_dir.mkdir(parents=True, exist_ok=True)

    # target_decision.json
    target_decision_path = results_dir / "target_decision.json"
    target_content = {
        "target_name": target_name,
        "fallback_flag": fallback_flag,
        "generated_at": datetime.utcnow().isoformat() + "Z",
    }
    with target_decision_path.open("w", encoding="utf-8") as fh:
        json.dump(target_content, fh, indent=2)
    logger.info("Wrote target decision to %s", target_decision_path)

    # imputation_rate_report.json
    imputation_report_path = results_dir / "imputation_rate_report.json"
    imputation_content = {
        "imputation_rate": imputation_rate,
        "proxy_correlation": proxy_correlation,
        "fallback_flag": fallback_flag,
        "generated_at": datetime.utcnow().isoformat() + "Z",
    }
    with imputation_report_path.open("w", encoding="utf-8") as fh:
        json.dump(imputation_content, fh, indent=2)
    logger.info("Wrote imputation report to %s", imputation_report_path)

# -------------------------------------------------------------------------
# Main entry point
# -------------------------------------------------------------------------

def main() -> None:
    """
    Execute the full target‑consistency workflow.

    The steps are:

    1. Load the raw datasets.
    2. Compute the overlap‑based Pearson correlation.
    3. Determine whether a fallback is required.
    4. Compute the imputation rate for the NIST dataset.
    5. Persist the decision and the imputation report.
    """
    logger = get_pipeline_logger(__name__)
    try:
        mp_data, nist_data = load_available_data()
        correlation, overlap = calculate_correlation(mp_data, nist_data)

        target_name, fallback_flag = determine_target(correlation, overlap)

        # Compute imputation rate: proportion of NIST records missing the target.
        nist_df = pd.DataFrame(nist_data)
        target_key = "melting_point"
        missing = nist_df[target_key].isna().sum()
        imputation_rate = missing / len(nist_df) if len(nist_df) > 0 else 0.0
        logger.info(
            "Imputation rate for target '%s' in NIST data: %.2%f",
            target_key,
            imputation_rate,
        )

        save_decision(
            target_name=target_name,
            fallback_flag=fallback_flag,
            imputation_rate=imputation_rate,
            proxy_correlation=correlation,
        )
        logger.info("Target consistency check completed successfully.")
    except Exception as exc:  # pragma: no cover – logger will capture details
        log_error(f"Target consistency check failed: {exc}")
        raise

if __name__ == "__main__":
    main()
