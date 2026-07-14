"""
data/preprocessing.py
---------------------

Adds detailed logging around each preprocessing step:
- handling of high‑missingness variables,
- MICE imputation,
- scale scoring.

The functional logic remains identical to the original implementation; only
logging statements have been inserted.
"""

import os
import logging
import yaml
from pathlib import Path
from typing import List, Optional, Dict, Any

import pandas as pd

from logger import get_logger
from analysis.scales import load_scale_config, score_cesd, score_gad7, score_pcl5

logger = get_logger(__name__)

def load_config(config_path: Path = Path("config/scales.yaml")) -> Dict[str, Any]:
    """Load the scales configuration YAML."""
    logger.debug(f"Loading scale configuration from {config_path}")
    with config_path.open("r") as f:
        cfg = yaml.safe_load(f)
    logger.debug("Scale configuration loaded")
    return cfg

def handle_high_missingness(df: pd.DataFrame, threshold: float = 0.05) -> pd.DataFrame:
    """
    Perform listwise deletion for variables with >threshold missingness.
    """
    logger.info(f"Handling high missingness (>{threshold*100:.1f}%)")
    missing_rates = df.isnull().mean()
    cols_to_drop = missing_rates[missing_rates > threshold].index.tolist()
    if cols_to_drop:
        logger.warning(f"Dropping columns due to high missingness: {cols_to_drop}")
    else:
        logger.debug("No columns exceed missingness threshold")
    cleaned_df = df.drop(columns=cols_to_drop)
    logger.info(f"Columns after dropping: {list(cleaned_df.columns)}")
    return cleaned_df

def apply_mice_imputation(df: pd.DataFrame,
                          predictor_cols: List[str],
                          m: int = 5,
                          max_iter: int = 10,
                          random_state: int = 42) -> pd.DataFrame:
    """
    Apply MICE imputation on the predictor matrix.
    """
    logger.info("Starting MICE imputation")
    logger.debug(f"Predictor columns: {predictor_cols}")
    from sklearn.experimental import enable_iterative_imputer  # noqa
    from sklearn.impute import IterativeImputer

    imputer = IterativeImputer(
        max_iter=max_iter,
        random_state=random_state,
        sample_posterior=True,
    )
    # Fit only on the predictor columns
    impute_data = df[predictor_cols]
    imputed_array = imputer.fit_transform(impute_data)
    imputed_df = pd.DataFrame(imputed_array, columns=predictor_cols, index=df.index)
    df[predictor_cols] = imputed_df
    logger.info("MICE imputation completed")
    return df

def apply_scale_scoring(df: pd.DataFrame, scales_cfg: Dict[str, Any]) -> pd.DataFrame:
    """
    Compute scale scores (CES‑D, GAD‑7, PCL‑5) using the configuration.
    """
    logger.info("Applying scale scoring")
    # CES‑D
    if "CES-D" in scales_cfg:
        logger.debug("Scoring CES‑D")
        df["cesd_score"] = score_cesd(df, scales_cfg["CES-D"])
    # GAD‑7
    if "GAD-7" in scales_cfg:
        logger.debug("Scoring GAD‑7")
        df["gad7_score"] = score_gad7(df, scales_cfg["GAD-7"])
    # PCL‑5 (optional)
    if "PCL-5" in scales_cfg:
        logger.debug("Scoring PCL‑5")
        df["pcl5_score"] = score_pcl5(df, scales_cfg["PCL-5"])
    logger.info("Scale scoring completed")
    return df

def run_preprocessing() -> pd.DataFrame:
    """
    Orchestrates the full preprocessing pipeline.
    """
    logger.info("=== Preprocessing pipeline start ===")
    # Load the combined raw data (the original implementation expects a function)
    from data.cohort import load_preprocessed_data  # reuse existing loader

    df = load_preprocessed_data()
    logger.debug(f"Loaded data shape: {df.shape}")

    # 1️⃣ High missingness handling
    df = handle_high_missingness(df)

    # 2️⃣ MICE imputation on selected predictors
    predictor_cols = [
        "age", "gender", "education", "income", "social_support",
        "harassment_severity", "depression", "anxiety", "ptsd"
    ]
    df = apply_mice_imputation(df, predictor_cols)

    # 3️⃣ Scale scoring
    scales_cfg = load_config()
    df = apply_scale_scoring(df, scales_cfg)

    logger.info("=== Preprocessing pipeline finished ===")
    return df

def main():
    """
    Entry point for the preprocessing module.
    """
    logger.info("Preprocessing main invoked")
    processed_df = run_preprocessing()
    # Persist the processed data for downstream steps
    output_path = Path("data/processed/preprocessed_data.parquet")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    processed_df.to_parquet(output_path)
    logger.info(f"Preprocessed data saved to {output_path}")
    return processed_df
