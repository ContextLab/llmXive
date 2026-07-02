import os
import sys
import argparse
import json
from pathlib import Path
from typing import List, Dict, Any, Optional

import pandas as pd
import numpy as np
from statsmodels.regression.mixed_linear_model import MixedLM

# Import project utilities
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.config import get_project_root, get_data_path, get_output_path
from utils.logger import get_logger
from analysis.memory_loader import load_data_chunked

# Explicit associational label constant for FR-005 compliance
ASSOCIATION_LABEL = "associational"

logger = get_logger(__name__)

def load_processed_data() -> pd.DataFrame:
    """
    Load the processed eye-tracking and recall data.
    In a real pipeline, this would read from data/processed/merged.csv
    For this implementation, we assume the file exists as per T012/T013.
    """
    root = get_project_root()
    # Construct expected path based on project structure
    data_path = root / "data" / "processed" / "merged_data.csv"
    
    if not data_path.exists():
        # Fallback for testing if T012 hasn't generated it yet, 
        # but in real execution, this should be a real file.
        # We attempt to load from a generic 'data.csv' in data/raw if processed is missing
        # to prevent immediate crash during unit testing of T033, 
        # but log a warning that real data is expected.
        alt_path = root / "data" / "raw" / "eye_tracking.csv"
        if alt_path.exists():
            logger.warning(f"Processed data not found at {data_path}, loading raw {alt_path}")
            df = pd.read_csv(alt_path)
        else:
            raise FileNotFoundError(f"Could not find processed data at {data_path} or raw fallback.")
    else:
        df = pd.read_csv(data_path)
    
    # Memory efficient handling as per T026
    if df.memory_usage(deep=True).sum() > 7 * 1024**3:
        logger.warning("Data exceeds memory threshold, using sampling.")
        df = df.sample(n=min(len(df), 10000), random_state=42)
        
    return df

def fit_lmm_for_combination(df: pd.DataFrame, metric: str, valence: str) -> Optional[Dict[str, Any]]:
    """
    Fit a Linear Mixed-Effects Model for a specific metric and valence category.
    Formula: recall_accuracy ~ metric + (1|participant_id)
    """
    try:
        # Filter for specific valence
        subset = df[df['valence_category'] == valence].copy()
        
        if subset.empty:
            logger.debug(f"No data for valence={valence}")
            return None

        # Ensure numeric types
        subset = subset.dropna(subset=[metric, 'recall_accuracy', 'participant_id'])
        
        if len(subset) < 10:
            logger.debug(f"Insufficient data points for valence={valence}, metric={metric}")
            return None

        # Define formula
        # Using 'participant_id' as random effect grouping variable
        # Note: statsmodels mixedlm expects group and exog/dependent
        group = subset['participant_id']
        endog = subset['recall_accuracy']
        exog = subset[[metric]]
        
        # Fit model
        # Use sparse solver for efficiency if data is large
        model = MixedLM(endog, exog, groups=group)
        result = model.fit()
        
        # Extract coefficients
        # Fixed effects: intercept + metric coefficient
        # We are interested in the metric's effect
        coef = result.params.iloc[1] if len(result.params) > 1 else 0.0
        p_value = result.pvalues.iloc[1] if len(result.pvalues) > 1 else 1.0
        
        return {
            "metric": metric,
            "valence": valence,
            "coef": float(coef),
            "p_raw": float(p_value),
            "n_obs": len(subset),
            "converged": result.converged,
            "association_label": ASSOCIATION_LABEL  # FR-005 Compliance
        }
    except Exception as e:
        logger.error(f"Failed to fit LMM for {metric}/{valence}: {e}")
        return None

def run_lmm_analysis(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Run LMM analysis for all combinations of metrics and valence categories.
    Metrics: fixation_duration, saccade_amplitude, gaze_distribution
    Valence: positive, negative, neutral
    """
    metrics = ['fixation_duration', 'saccade_amplitude', 'gaze_distribution']
    valences = ['positive', 'negative', 'neutral']
    
    results = []
    for metric in metrics:
        for valence in valences:
            res = fit_lmm_for_combination(df, metric, valence)
            if res:
                results.append(res)
                
    logger.info(f"Completed LMM analysis for {len(results)} combinations.")
    return results

def save_results(results: List[Dict[str, Any]], output_path: Optional[str] = None) -> str:
    """
    Save LMM results to a CSV file.
    """
    root = get_project_root()
    if output_path is None:
        output_path = str(root / "output" / "results" / "lmm_summary.csv")
    
    # Ensure directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    df_results = pd.DataFrame(results)
    df_results.to_csv(output_path, index=False)
    logger.info(f"Saved LMM results to {output_path}")
    return output_path

def main():
    """
    Main entry point for LMM analysis script.
    """
    parser = argparse.ArgumentParser(description="Run LMM Analysis on Eye-Tracking Data")
    parser.add_argument("--input", type=str, help="Path to input data CSV", default=None)
    parser.add_argument("--output", type=str, help="Path to output CSV", default=None)
    args = parser.parse_args()

    logger.info("Starting LMM Analysis...")
    
    try:
        # Load data
        # If input arg provided, use it; otherwise load processed data
        if args.input:
            df = pd.read_csv(args.input)
        else:
            df = load_processed_data()
        
        # Run analysis
        results = run_lmm_analysis(df)
        
        # Save results
        out_path = save_results(results, args.output)
        
        logger.info(f"Analysis complete. Results saved to {out_path}")
        return 0
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
