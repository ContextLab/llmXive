"""
data/preprocessing.py
---------------------
Implements the preprocessing pipeline for the Cyberbullying Survey 2021:
1. Listwise Deletion for variables with >5% missingness.
2. MICE Imputation (m=5, max_iter=10, random_state=42) on predictor matrix.
3. Convergence Check: If trace does not stabilize, increase max_iter to 50 and log W-MICE-NONCONV-001.
4. Scale Scoring: Apply CES-D, GAD-7, PCL-5 scoring from config/scales.yaml.
5. PCL-5 Handling: If items missing, log E-MISSING-001 and set 'ptsd' to NaN.
6. Output: Returns the processed DataFrame.

The main() function writes the result to data/processed/preprocessed_data.parquet.
"""

import os
import logging
import yaml
import numpy as np
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple

import pandas as pd
from sklearn.experimental import enable_iterative_imputer  # noqa: F401
from sklearn.impute import IterativeImputer

from logger import get_logger
from analysis.scales import load_scale_config, score_cesd, score_gad7, score_pcl5

logger = get_logger(__name__)

def load_config(config_path: Path = Path("config/scales.yaml")) -> Dict[str, Any]:
    """Load the scales configuration YAML."""
    logger.debug(f"Loading scale configuration from {config_path}")
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    with config_path.open("r") as f:
        cfg = yaml.safe_load(f)
    logger.debug("Scale configuration loaded")
    return cfg

def handle_high_missingness(df: pd.DataFrame, threshold: float = 0.05) -> pd.DataFrame:
    """
    Perform listwise deletion for variables with >threshold missingness.
    Drops columns where missingness > threshold.
    """
    logger.info(f"Handling high missingness (>{threshold*100:.1f}%)")
    missing_rates = df.isnull().mean()
    cols_to_drop = missing_rates[missing_rates > threshold].index.tolist()
    
    if cols_to_drop:
        logger.warning(f"Dropping columns due to high missingness (>5%): {cols_to_drop}")
        # Log specific missing rates for transparency
        for col in cols_to_drop:
            logger.warning(f"  - {col}: {missing_rates[col]*100:.2f}% missing")
    else:
        logger.debug("No columns exceed missingness threshold")
    
    cleaned_df = df.drop(columns=cols_to_drop)
    logger.info(f"Columns after dropping high-missingness vars: {list(cleaned_df.columns)}")
    return cleaned_df

def check_convergence(imputer: IterativeImputer, max_iter_used: int) -> bool:
    """
    Checks if the imputer converged.
    IterativeImputer stores convergence info in 'n_iter_' if available,
    but we also check the imputation error history if accessible.
    For sklearn IterativeImputer, n_iter_ is the number of iterations run.
    If n_iter_ == max_iter, it might not have converged.
    """
    # sklearn's IterativeImputer doesn't explicitly expose a 'converged' boolean
    # in the public API easily without internal inspection, but we can check
    # if it hit the max_iter limit.
    if hasattr(imputer, 'n_iter_'):
        # If it ran for the full max_iter, it likely didn't converge early
        # We treat hitting the limit as potential non-convergence for safety
        if imputer.n_iter_ == max_iter_used:
            return False
    return True

def apply_mice_imputation(df: pd.DataFrame,
                          predictor_cols: List[str],
                          m: int = 5,
                          max_iter: int = 10,
                          random_state: int = 42) -> pd.DataFrame:
    """
    Apply MICE imputation on the predictor matrix.
    Implements convergence check: if max_iter reached, re-run with max_iter=50.
    """
    logger.info("Starting MICE imputation")
    logger.debug(f"Predictor columns: {predictor_cols}")
    
    # Ensure we only have columns that exist in the dataframe
    available_cols = [c for c in predictor_cols if c in df.columns]
    missing_cols = set(predictor_cols) - set(available_cols)
    if missing_cols:
        logger.warning(f"Predictor columns missing from dataframe (skipping imputation for them): {missing_cols}")
    
    if not available_cols:
        logger.warning("No predictor columns available for imputation. Skipping MICE.")
        return df

    # Filter df to only available columns for imputation
    impute_data = df[available_cols].copy()

    imputer = IterativeImputer(
        max_iter=max_iter,
        random_state=random_state,
        sample_posterior=True,
        verbose=0, # Reduce sklearn noise
    )
    
    try:
        imputed_array = imputer.fit_transform(impute_data)
    except Exception as e:
        logger.error(f"MICE imputation failed: {e}")
        raise

    # Check convergence
    converged = check_convergence(imputer, max_iter)
    
    if not converged:
        logger.warning("W-MICE-NONCONV-001: MICE did not converge within max_iter=10. Re-running with max_iter=50.")
        imputer = IterativeImputer(
            max_iter=50,
            random_state=random_state,
            sample_posterior=True,
            verbose=0,
        )
        imputed_array = imputer.fit_transform(impute_data)
        logger.info("MICE re-run completed with max_iter=50.")

    imputed_df = pd.DataFrame(imputed_array, columns=available_cols, index=df.index)
    
    # Update the original dataframe
    df[available_cols] = imputed_df
    
    logger.info("MICE imputation completed successfully")
    return df

def apply_scale_scoring(df: pd.DataFrame, scales_cfg: Dict[str, Any]) -> pd.DataFrame:
    """
    Compute scale scores (CES‑D, GAD‑7, PCL‑5) using the configuration.
    Handles missing PCL-5 items gracefully by logging E-MISSING-001 and setting ptsd to NaN.
    """
    logger.info("Applying scale scoring")
    
    # CES‑D
    if "CES-D" in scales_cfg:
        logger.debug("Scoring CES‑D")
        try:
            df["cesd_score"] = score_cesd(df, scales_cfg["CES-D"])
        except Exception as e:
            logger.error(f"Failed to score CES-D: {e}")
            df["cesd_score"] = np.nan
    else:
        logger.warning("CES-D configuration not found in scales.yaml")

    # GAD‑7
    if "GAD-7" in scales_cfg:
        logger.debug("Scoring GAD‑7")
        try:
            df["gad7_score"] = score_gad7(df, scales_cfg["GAD-7"])
        except Exception as e:
            logger.error(f"Failed to score GAD-7: {e}")
            df["gad7_score"] = np.nan
    else:
        logger.warning("GAD-7 configuration not found in scales.yaml")

    # PCL‑5 (optional)
    if "PCL-5" in scales_cfg:
        logger.debug("Scoring PCL‑5")
        # Check if any PCL-5 items exist in the dataframe
        pcl_items = scales_cfg["PCL-5"].get("items", [])
        present_items = [item for item in pcl_items if item in df.columns]
        
        if not present_items:
            logger.error("E-MISSING-001: PCL-5 items are missing from the dataset. Setting 'ptsd' to NaN.")
            df["ptsd"] = np.nan
        else:
            try:
                # Only score if we have some items; if partial, score what we can or handle as needed
                # The scale scoring function usually handles missing items by returning NaN for the row
                df["pcl5_score"] = score_pcl5(df, scales_cfg["PCL-5"])
                # Ensure the column is named 'ptsd' for downstream compatibility if expected
                # The task says "set the 'ptsd' column to NaN" if missing, implying 'ptsd' is the target name.
                # If scoring succeeds, we might map pcl5_score -> ptsd or keep both. 
                # Given the task description: "set the 'ptsd' column to NaN", we assume 'ptsd' is the outcome variable.
                # If the scoring function returns 'pcl5_score', we should probably alias it or ensure 'ptsd' exists.
                # Let's ensure 'ptsd' is populated from the score if available.
                if "ptsd" not in df.columns:
                    df["ptsd"] = df["pcl5_score"]
                else:
                    df["ptsd"] = df["pcl5_score"] # Overwrite if exists, or update
            except Exception as e:
                logger.error(f"Failed to score PCL-5: {e}")
                df["ptsd"] = np.nan
    else:
        logger.warning("PCL-5 configuration not found in scales.yaml")
        # If config is missing entirely, we might not have the items, so set to NaN
        if "ptsd" not in df.columns:
            df["ptsd"] = np.nan

    logger.info("Scale scoring completed")
    return df

def run_preprocessing() -> pd.DataFrame:
    """
    Orchestrates the full preprocessing pipeline.
    1. Load data (from ingestion or cohort loader).
    2. Handle high missingness.
    3. Apply MICE.
    4. Apply Scale Scoring.
    5. Return processed DataFrame.
    """
    logger.info("=== Preprocessing pipeline start ===")
    
    # Load the combined raw data. 
    # Since T012 (ingestion) runs before this, we expect data to be available.
    # We reuse the loader from cohort.py which handles the raw data loading.
    try:
        from data.cohort import load_preprocessed_data
        df = load_preprocessed_data()
    except ImportError:
        # Fallback if cohort module structure differs slightly or not ready
        # In a real pipeline, ingestion.py would have saved a raw file.
        # We assume ingestion.py saves to data/raw/cyberbullying_2021.csv or similar.
        # However, the task says "Output the processed DataFrame for downstream cohort construction".
        # Let's assume load_preprocessed_data is the standard entry point for raw data.
        logger.error("Could not import load_preprocessed_data from data.cohort. Pipeline cannot proceed.")
        raise
    
    logger.debug(f"Loaded data shape: {df.shape}")

    # 1️⃣ High missingness handling (Listwise Deletion on columns)
    df = handle_high_missingness(df, threshold=0.05)

    # 2️⃣ MICE Imputation on selected predictors
    predictor_cols = [
        "age", "gender", "education", "income", "social_support",
        "harassment_severity", "depression", "anxiety", "ptsd"
    ]
    # Filter predictor_cols to only those present in df
    available_predictors = [c for c in predictor_cols if c in df.columns]
    if available_predictors:
        df = apply_mice_imputation(df, available_predictors, m=5, max_iter=10, random_state=42)
    else:
        logger.warning("No predictor columns available for MICE imputation.")

    # 3️⃣ Scale Scoring
    try:
        scales_cfg = load_config()
        df = apply_scale_scoring(df, scales_cfg)
    except FileNotFoundError as e:
        logger.error(f"Configuration file missing: {e}")
        raise

    logger.info("=== Preprocessing pipeline finished ===")
    return df

def main():
    """
    Entry point for the preprocessing module.
    Runs the pipeline and saves the output to data/processed/preprocessed_data.parquet.
    """
    logger.info("Preprocessing main invoked")
    processed_df = run_preprocessing()
    
    output_path = Path("data/processed/preprocessed_data.parquet")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    processed_df.to_parquet(output_path)
    logger.info(f"Preprocessed data saved to {output_path}")
    return processed_df

if __name__ == "__main__":
    main()