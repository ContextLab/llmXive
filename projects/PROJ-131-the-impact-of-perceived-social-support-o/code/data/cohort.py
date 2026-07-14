"""
data/cohort.py
--------------

This module now includes extensive logging for each stage of synthetic
cohort creation: loading pre‑processed data, propensity‑score estimation,
matching, inverse‑probability weighting, and final construction.  Fallback
logic (e.g., when the GSS dataset was skipped) is also logged.
"""

import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List

import pandas as pd
import numpy as np

from logger import get_logger
from analysis.validation import validate_synthetic_cohort

logger = get_logger(__name__)

def load_preprocessed_data() -> pd.DataFrame:
    """
    Load the pre‑processed dataset produced by ``data.preprocessing``.
    """
    path = Path("data/processed/preprocessed_data.parquet")
    logger.debug(f"Loading pre‑processed data from {path}")
    if not path.is_file():
        logger.error(f"Pre‑processed data not found at {path}")
        raise FileNotFoundError(f"Missing pre‑processed data: {path}")
    df = pd.read_parquet(path)
    logger.info(f"Pre‑processed data loaded with shape {df.shape}")
    return df

def compute_propensity_scores(df: pd.DataFrame,
                              source_indicator: str = "source",
                              covariates: List[str] = None) -> pd.DataFrame:
    """
    Compute propensity scores for the dataset source (GSS vs Cyberbullying)
    using logistic regression.
    """
    logger.info("Computing propensity scores")
    if covariates is None:
        covariates = ["age", "gender", "education", "income"]
    logger.debug(f"Covariates used: {covariates}")

    # Ensure source column exists; if not, assume all rows are from Cyberbullying
    if source_indicator not in df.columns:
        logger.warning(f"Source indicator column '{source_indicator}' missing; assuming single source.")
        df["propensity_score"] = 0.5  # placeholder neutral score
        return df

    from sklearn.linear_model import LogisticRegression

    X = pd.get_dummies(df[covariates], drop_first=True)
    y = df[source_indicator]
    model = LogisticRegression(max_iter=1000)
    model.fit(X, y)
    df["propensity_score"] = model.predict_proba(X)[:, 1]
    logger.debug("Propensity scores added to DataFrame")
    return df

def perform_matching(df: pd.DataFrame,
                     caliper: float = 0.2) -> pd.DataFrame:
    """
    Perform nearest‑neighbor matching with a caliper of ``caliper`` standard
    deviations of the logit of the propensity score.
    """
    logger.info("Performing nearest‑neighbor matching")
    if "propensity_score" not in df.columns:
        logger.error("Propensity scores missing; cannot perform matching.")
        raise ValueError("Propensity scores not computed.")

    # Compute logit
    eps = np.finfo(float).eps
    df["logit_ps"] = np.log(df["propensity_score"] + eps) - np.log(1 - df["propensity_score"] + eps)

    sd_logit = df["logit_ps"].std()
    caliper_value = caliper * sd_logit
    logger.debug(f"Caliper value (logit SD * {caliper}): {caliper_value}")

    # Simple greedy nearest‑neighbor matching
    treated = df[df["source"] == 1].copy()
    control = df[df["source"] == 0].copy()
    matches = []

    for _, t_row in treated.iterrows():
        # Compute absolute distance in logit space
        control["dist"] = np.abs(control["logit_ps"] - t_row["logit_ps"])
        eligible = control[control["dist"] <= caliper_value]
        if eligible.empty:
            logger.warning(f"No match within caliper for treated unit index {t_row.name}")
            continue
        # Choose nearest neighbor
        nearest_idx = eligible["dist"].idxmin()
        matched_control = control.loc[nearest_idx]
        matches.append((t_row.name, matched_control.name))
        # Remove matched control to avoid reuse
        control = control.drop(index=nearest_idx)

    if not matches:
        logger.error("No matches were found; matching failed.")
        raise RuntimeError("Matching yielded zero pairs.")

    # Build matched DataFrame
    matched_rows = []
    for treat_idx, ctrl_idx in matches:
        matched_rows.append(df.loc[treat_idx])
        matched_rows.append(df.loc[ctrl_idx])
    matched_df = pd.DataFrame(matched_rows).reset_index(drop=True)
    logger.info(f"Matching completed with {len(matches)} pairs ({matched_df.shape[0]} rows)")
    return matched_df

def apply_inverse_probability_weighting(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply inverse‑probability weighting to create a synthetic cohort.
    """
    logger.info("Applying inverse‑probability weighting")
    if "propensity_score" not in df.columns:
        logger.error("Propensity scores missing; cannot compute weights.")
        raise ValueError("Propensity scores not computed.")
    # Weight = 1 / P(source) for treated, 1 / (1-P(source)) for control
    df["weight"] = np.where(
        df["source"] == 1,
        1 / df["propensity_score"],
        1 / (1 - df["propensity_score"])
    )
    logger.debug("Weights column added")
    return df

def construct_synthetic_cohort() -> pd.DataFrame:
    """
    Full pipeline to construct the synthetic cohort and write it to disk.
    """
    logger.info("=== Synthetic cohort construction start ===")
    df = load_preprocessed_data()

    # Compute propensity scores (handles missing source column internally)
    df = compute_propensity_scores(df)

    # Perform matching; if matching fails due to lack of source column, fall back to weighting only
    try:
        matched_df = perform_matching(df)
    except Exception as exc:
        logger.warning(f"Matching failed ({exc}); proceeding with weighting only.")
        matched_df = df  # fallback to using the full dataset for weighting

    weighted_df = apply_inverse_probability_weighting(matched_df)

    # Validate the synthetic cohort before persisting
    try:
        validate_synthetic_cohort(weighted_df)
    except Exception as exc:
        logger.error(f"Synthetic cohort validation failed: {exc}")
        raise

    output_path = Path("data/results/synthetic_cohort.csv")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    weighted_df.to_csv(output_path, index=False)
    logger.info(f"Synthetic cohort saved to {output_path}")
    logger.info("=== Synthetic cohort construction finished ===")
    return weighted_df

def main():
    """
    Entry point for the cohort module.
    """
    logger.info("Cohort main invoked")
    return construct_synthetic_cohort()
