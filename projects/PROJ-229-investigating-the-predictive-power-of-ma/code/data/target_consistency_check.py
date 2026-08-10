"""
Target Consistency Check Script (T005a).

Loads a sample of Materials Project data, calculates the Pearson correlation
between 'melting_point' and 'latent_heat', and writes the decision
(which target to use) and coefficient to 'data/results/target_decision.json'.

Must run before T006a.
"""

import os
import json
import logging
from pathlib import Path
from typing import Tuple, Optional

import pandas as pd
import numpy as np

from config import get_config
from utils.logger import get_pipeline_logger

# Configure logger
logger = get_pipeline_logger()

def load_available_data() -> Optional[pd.DataFrame]:
    """
    Attempts to load a sample of Materials Project data.
    Prefers the raw JSON from data/raw if available, otherwise attempts
    to fetch a small sample via the API (if configured) or falls back
    to a specific known file if the project has pre-downloaded data.

    For this task, we assume the existence of a raw data file or
    attempt to fetch a minimal sample if the API key is present.
    """
    config = get_config()
    data_dir = Path(config.get("data_dirs", {}).get("raw", "data/raw"))
    raw_file = data_dir / "materials_project_raw.json"

    # Strategy 1: Load from existing raw JSON if present
    if raw_file.exists():
        logger.info(f"Loading raw data from {raw_file}")
        try:
            df = pd.read_json(raw_file)
            # Ensure we have the required columns
            if "melting_point" in df.columns and "latent_heat" in df.columns:
                return df
            else:
                logger.warning(f"Raw file {raw_file} exists but lacks required columns.")
        except Exception as e:
            logger.warning(f"Failed to parse {raw_file}: {e}")

    # Strategy 2: If no raw file, try to fetch a small sample from MP API
    # This requires the MP API key to be set in config.yaml
    api_key = config.get("api_keys", {}).get("materials_project")
    if api_key:
        logger.info("No raw data found. Attempting to fetch a small sample from Materials Project API.")
        try:
            from pymatgen.ext.matproj import MPRester
            with MPRester(api_key) as mpr:
                # Fetch a small sample (e.g., first 500 entries) to save time
                # We request specific fields to keep it light
                docs = mpr.query(
                    criteria={"nelements": {"$gt": 1}}, # Just oxides/compounds
                    properties=["formula", "melting_point", "latent_heat"],
                    limit=500
                )
                if not docs:
                    logger.warning("MP API returned no documents.")
                    return None
                df = pd.DataFrame(docs)
                # Flatten if necessary (some APIs return nested dicts)
                if "melting_point" in df.columns and "latent_heat" in df.columns:
                    return df
                else:
                    logger.warning("MP API response lacks required columns.")
                    return None
        except Exception as e:
            logger.error(f"Failed to fetch from MP API: {e}")
            raise RuntimeError("Cannot load data from file or API. Please ensure data/raw/materials_project_raw.json exists or a valid MP API key is configured.")
    else:
        raise RuntimeError(
            "No raw data file found and no Materials Project API key configured. "
            "Please run T011a to fetch data first, or provide an API key in config.yaml."
        )

def calculate_correlation(df: pd.DataFrame) -> Tuple[float, int]:
    """
    Calculates the Pearson correlation coefficient between melting_point and latent_heat.
    Returns (coefficient, sample_size).
    """
    # Drop rows where either value is null
    clean_df = df.dropna(subset=["melting_point", "latent_heat"])
    sample_size = len(clean_df)

    if sample_size < 2:
        raise ValueError("Insufficient data points to calculate correlation.")

    corr_matrix = clean_df[["melting_point", "latent_heat"]].corr()
    coeff = corr_matrix.loc["melting_point", "latent_heat"]
    return float(coeff), sample_size

def determine_target(coeff: float) -> str:
    """
    Determines the target variable based on the correlation coefficient.
    Logic:
    - If correlation is high (e.g., > 0.7), either could work, but we prefer 'latent_heat'
      if it is scientifically more stable for phase change prediction, or 'melting_point'
      if it is more commonly available.
    - For this specific task (T005a), the decision rule is:
      If |coeff| > 0.6, choose 'latent_heat' as the primary target (assuming strong coupling).
      Otherwise, choose 'melting_point' as the fallback (more robust data availability).
    """
    if abs(coeff) > 0.6:
        return "latent_heat"
    else:
        return "melting_point"

def save_decision(target: str, coeff: float, rationale: str, output_path: Path):
    """
    Saves the decision and coefficient to a JSON file.
    """
    decision = {
        "target": target,
        "coefficient": coeff,
        "decision_rationale": rationale,
        "target_override": False
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(decision, f, indent=2)
    logger.info(f"Decision saved to {output_path}")

def main():
    """
    Main entry point for the target consistency check.
    """
    logger.info("Starting Target Consistency Check (T005a)...")
    config = get_config()
    results_dir = Path(config.get("data_dirs", {}).get("results", "data/results"))
    output_path = results_dir / "target_decision.json"

    try:
        # 1. Load Data
        df = load_available_data()
        if df is None or df.empty:
            raise ValueError("No data loaded for analysis.")

        # 2. Calculate Correlation
        coeff, sample_size = calculate_correlation(df)
        logger.info(f"Calculated Pearson correlation: {coeff:.4f} (n={sample_size})")

        # 3. Determine Target
        target = determine_target(coeff)
        rationale = (
            f"Correlation between melting_point and latent_heat is {coeff:.4f}. "
            f"Based on the threshold (|r| > 0.6), the target is set to '{target}'."
        )
        logger.info(f"Target decision: {target}")

        # 4. Save Decision
        save_decision(target, coeff, rationale, output_path)

        logger.info("Target Consistency Check completed successfully.")

    except Exception as e:
        logger.error(f"Target Consistency Check failed: {e}")
        raise

if __name__ == "__main__":
    main()