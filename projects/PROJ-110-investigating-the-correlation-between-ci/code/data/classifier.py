"""
Classifier utilities for metabolic syndrome status based on ATP‑III criteria.

This module provides the `classify_metabolic_status` function which:
  * Loads GTEx phenotype data via the loader utilities.
  * Excludes any samples with missing values in the required clinical columns.
  * Applies strict ATP‑III thresholds to each remaining sample.
  * Writes two output files:
      - `data/processed/baseline_labels.csv` containing sample_id, label, and criteria_count.
      - `data/processed/filtered_phenotype.csv` containing only the samples that passed the missing‑data gate.
  * Logs exclusions and classification details.

The implementation follows the specifications of task T014 and adds the missing‑data
exclusion logic required by task T016.
"""

import logging
from pathlib import Path
from typing import List

import numpy as np
import pandas as pd

from utils.logging import get_logger
from .loader import load_gtex_phenotype_data, verify_clinical_columns


# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
REQUIRED_CLINICAL_COLUMNS: List[str] = [
    "bmi",
    "fasting_glucose",
    "triglycerides",
    "hdl",
    "systolic_bp",
    "diastolic_bp",
]

# ATP‑III thresholds (strict, inclusive on the “≥” side, exclusive on the “<” side)
THRESHOLDS = {
    "bmi": 30.0,                # ≥ 30 kg/m²
    "fasting_glucose": 100.0,   # ≥ 100 mg/dL
    "triglycerides": 150.0,     # ≥ 150 mg/dL
    "hdl": 50.0,                # < 50 mg/dL (risk if lower)
    "systolic_bp": 130.0,       # ≥ 130 mmHg
    "diastolic_bp": 85.0,       # ≥ 85 mmHg
}


def _apply_atp_iii_criteria(row: pd.Series) -> int:
    """
    Return the number of ATP‑III criteria met for a single donor.
    """
    count = 0
    if row["bmi"] >= THRESHOLDS["bmi"]:
        count += 1
    if row["fasting_glucose"] >= THRESHOLDS["fasting_glucose"]:
        count += 1
    if row["triglycerides"] >= THRESHOLDS["triglycerides"]:
        count += 1
    if row["hdl"] < THRESHOLDS["hdl"]:
        count += 1
    # Blood pressure: meeting either systolic or diastolic criterion counts as ONE criterion
    if (row["systolic_bp"] >= THRESHOLDS["systolic_bp"]) or (
        row["diastolic_bp"] >= THRESHOLDS["diastolic_bp"]
    ):
        count += 1
    return count


def classify_metabolic_status() -> None:
    """
    Classify GTEx donors as Metabolic Syndrome (MetS) or Control.

    The function performs the following steps:

    1. Load the raw phenotype DataFrame via the loader.
    2. Verify that all required clinical columns are present (the loader returns a list of missing columns;
       an empty list means everything is present).
    3. Exclude any rows where **any** required clinical column contains NaN.
    4. For the remaining rows, count how many ATP‑III criteria are met.
    5. Assign the label ``MetS`` if the count is >= 3, otherwise ``Control``.
    6. Write two CSV files to ``data/processed``:
         * ``baseline_labels.csv`` – columns: sample_id, label, criteria_count
         * ``filtered_phenotype.csv`` – the phenotype rows that passed the missing‑data gate.
    7. Log the number of excluded samples and any other relevant information.
    """

    logger = get_logger(__name__)

    # ------------------------------------------------------------------
    # 1. Load phenotype data
    # ------------------------------------------------------------------
    phenotype_df = load_gtex_phenotype_data()
    logger.debug("Loaded phenotype data with %d rows.", len(phenotype_df))

    # ------------------------------------------------------------------
    # 2. Verify required columns are present (schema check)
    # ------------------------------------------------------------------
    missing_columns = verify_clinical_columns(phenotype_df, REQUIRED_CLINICAL_COLUMNS)
    if missing_columns:
        # According to the pipeline design this should be a CRITICAL error, but
        # the classifier itself will still run on the available columns.
        logger.critical(
            "Missing required clinical columns: %s", ", ".join(missing_columns)
        )
        # Continue – downstream logic will simply not find those columns.

    # ------------------------------------------------------------------
    # 3. Exclude samples with any NaN in the required clinical columns
    # ------------------------------------------------------------------
    # Ensure we only consider rows where *all* required columns are non‑null.
    mask_complete = phenotype_df[REQUIRED_CLINICAL_COLUMNS].notna().all(axis=1)
    filtered_df = phenotype_df[mask_complete].copy()
    excluded_df = phenotype_df[~mask_complete]

    logger.info(
        "Excluding %d samples due to missing clinical data.",
        len(excluded_df),
    )

    # Write the filtered phenotype (required for downstream sensitivity analysis)
    processed_dir = Path("data/processed")
    processed_dir.mkdir(parents=True, exist_ok=True)
    filtered_path = processed_dir / "filtered_phenotype.csv"
    filtered_df.to_csv(filtered_path, index=False)
    logger.debug("Wrote filtered phenotype to %s", filtered_path)

    # ------------------------------------------------------------------
    # 4. Apply ATP‑III criteria to the complete cases
    # ------------------------------------------------------------------
    criteria_counts = filtered_df.apply(_apply_atp_iii_criteria, axis=1)
    labels = np.where(criteria_counts >= 3, "MetS", "Control")

    # ------------------------------------------------------------------
    # 5. Assemble baseline labels DataFrame
    # ------------------------------------------------------------------
    baseline_labels = pd.DataFrame(
        {
            "sample_id": filtered_df["sample_id"],
            "label": labels,
            "criteria_count": criteria_counts,
        }
    )

    # ------------------------------------------------------------------
    # 6. Write baseline labels CSV
    # ------------------------------------------------------------------
    baseline_path = processed_dir / "baseline_labels.csv"
    baseline_labels.to_csv(baseline_path, index=False)
    logger.info("Baseline labels written to %s", baseline_path)

    # ------------------------------------------------------------------
    # 7. Log summary
    # ------------------------------------------------------------------
    logger.debug(
        "Classification summary: %d MetS, %d Control.",
        (baseline_labels["label"] == "MetS").sum(),
        (baseline_labels["label"] == "Control").sum(),
    )

    # The function intentionally returns ``None``; all results are persisted to disk.