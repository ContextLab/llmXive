import os
import sys
import logging
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
import numpy as np

# Import from sibling modules as per API surface
from analysis.statistical_test import run_full_analysis
from utils.config import get_config

logger = logging.getLogger(__name__)

def load_analysis_data() -> pd.DataFrame:
    """
    Load the matched analysis dataset containing review durations and classifications.
    Expects data/processed/matched_cohort.parquet (output of T022).
    """
    config = get_config()
    input_path = config["paths"]["data_processed"] / "matched_cohort.parquet"
    
    if not input_path.exists():
        # Fallback for testing if matching hasn't run yet, but strictly speaking
        # this task depends on T022 output.
        logger.warning(f"Input file {input_path} not found. Attempting to load raw classified data if available.")
        raw_path = config["paths"]["data_processed"] / "classified_snippets.parquet"
        if raw_path.exists():
            df = pd.read_parquet(raw_path)
            # Simulate missing review_duration if not present, but this is a failure state
            if "review_duration" not in df.columns:
                raise FileNotFoundError("Required 'review_duration' column missing from input data.")
            return df
        else:
            raise FileNotFoundError(
                f"Analysis data file not found at {input_path}. "
                "Ensure T022 (matching) has completed successfully."
            )
    
    return pd.read_parquet(input_path)

def stratify_by_stars(df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
    """
    Stratify the dataset by repository star-count quartiles.
    Returns a dictionary mapping quartile label to subset DataFrame.
    """
    if "star_count" not in df.columns:
        raise ValueError("Column 'star_count' not found in dataset. Cannot stratify.")
    
    # Handle potential NaNs in star_count
    df_clean = df.dropna(subset=["star_count"])
    
    if df_clean.empty:
        logger.warning("No valid star_count data available for stratification.")
        return {}

    # Calculate quartiles
    quartiles = df_clean["star_count"].quantile([0.25, 0.50, 0.75]).values
    q1, q2, q3 = quartiles

    def assign_quartile(stars):
        if stars <= q1:
            return "Q1_Low"
        elif stars <= q2:
            return "Q2_MedLow"
        elif stars <= q3:
            return "Q3_MedHigh"
        else:
            return "Q4_High"

    df_clean = df_clean.copy()
    df_clean["star_quartile"] = df_clean["star_count"].apply(assign_quartile)
    
    subsets = {}
    for label, group in df_clean.groupby("star_quartile"):
        subsets[label] = group.copy()
        
    logger.info(f"Stratified into {len(subsets)} subsets: {list(subsets.keys())}")
    return subsets

def run_sensitivity_analysis(subsets: Dict[str, pd.DataFrame]) -> Tuple[Dict[str, Dict], bool]:
    """
    Run statistical tests on each subset and check for consistency.
    
    Returns:
        Tuple of (results_dict, is_consistent)
        results_dict: {quartile_label: {"p_value": float, "effect_size": float, ...}}
        is_consistent: True if p < 0.05 in >= 80% of subsets.
    """
    if not subsets:
        logger.error("No subsets provided for sensitivity analysis.")
        return {}, False

    results = {}
    significant_count = 0
    total_count = len(subsets)

    for label, subset_df in subsets.items():
        logger.info(f"Running sensitivity analysis on subset: {label} (n={len(subset_df)})")
        
        # Ensure we have the necessary columns
        required_cols = ["review_duration", "generation_source"]
        missing_cols = [c for c in required_cols if c not in subset_df.columns]
        if missing_cols:
            logger.warning(f"Subset {label} missing columns {missing_cols}. Skipping.")
            results[label] = {"error": f"Missing columns: {missing_cols}", "p_value": None}
            continue

        # Filter for valid review durations (must be > 0)
        valid_df = subset_df[subset_df["review_duration"] > 0]
        if len(valid_df) < 2:
            logger.warning(f"Subset {label} has insufficient data points after filtering. Skipping.")
            results[label] = {"error": "Insufficient data", "p_value": None}
            continue

        try:
            # Run the full statistical analysis (Shapiro, Test Selection, T-test/MW)
            # This function is expected to return a dict with 'p_value' and 'effect_size'
            # based on the API surface of analysis.statistical_test
            analysis_result = run_full_analysis(
                data=valid_df,
                target_col="review_duration",
                group_col="generation_source",
                treatment_group="LLM-like",
                control_group="Human"
            )
            
            p_val = analysis_result.get("p_value")
            effect = analysis_result.get("effect_size", 0.0)
            
            results[label] = {
                "p_value": p_val,
                "effect_size": effect,
                "n_samples": len(valid_df),
                "test_type": analysis_result.get("test_type", "unknown")
            }
            
            if p_val is not None and p_val < 0.05:
                significant_count += 1
                logger.info(f"Subset {label}: p={p_val:.4f} (Significant)")
            else:
                logger.info(f"Subset {label}: p={p_val:.4f} (Not Significant)")
                
        except Exception as e:
            logger.error(f"Error running analysis on subset {label}: {e}")
            results[label] = {"error": str(e), "p_value": None}

    if total_count == 0:
        return results, False

    consistency_ratio = significant_count / total_count
    is_consistent = consistency_ratio >= 0.80
    
    logger.info(f"Sensitivity Consistency Check: {significant_count}/{total_count} subsets significant. "
                f"Ratio: {consistency_ratio:.2f}. Consistent: {is_consistent}")
                
    return results, is_consistent

def main():
    """
    Main entry point for T030: Sensitivity Consistency Check.
    1. Load matched data.
    2. Stratify by star count quartiles.
    3. Run statistical tests on each subset.
    4. Check if p < 0.05 in >= 80% of subsets.
    5. Write data/processed/sensitivity_summary.json.
    """
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    config = get_config()
    output_path = config["paths"]["data_processed"] / "sensitivity_summary.json"
    
    try:
        # 1. Load Data
        logger.info("Loading analysis data...")
        df = load_analysis_data()
        
        # 2. Stratify
        logger.info("Stratifying by star count...")
        subsets = stratify_by_stars(df)
        
        if not subsets:
            raise RuntimeError("Stratification resulted in empty subsets. Cannot proceed.")
        
        # 3. Run Analysis
        logger.info("Running sensitivity analysis across subsets...")
        results, is_consistent = run_sensitivity_analysis(subsets)
        
        # 4. Prepare Output
        summary = {
            "total_subsets": len(subsets),
            "consistent": is_consistent,
            "consistency_threshold": 0.80,
            "results_by_quartile": results,
            "timestamp": str(pd.Timestamp.now())
        }
        
        # 5. Write Output
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(summary, f, indent=2, default=str)
            
        logger.info(f"Sensitivity summary written to {output_path}")
        logger.info(f"Consistency Check Result: {'PASSED' if is_consistent else 'FAILED'}")
        
        return 0 if is_consistent else 1 # Return non-zero if consistency check fails (for gate)
        
    except Exception as e:
        logger.critical(f"Pipeline failed during sensitivity analysis: {e}")
        # Write a failure report if possible
        error_summary = {
            "error": str(e),
            "consistent": False,
            "timestamp": str(pd.Timestamp.now())
        }
        try:
            with open(output_path, "w") as f:
                json.dump(error_summary, f, indent=2)
        except:
            pass
        return 1

if __name__ == "__main__":
    sys.exit(main())
