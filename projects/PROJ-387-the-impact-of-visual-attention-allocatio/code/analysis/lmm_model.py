import os
import sys
import argparse
import json
from pathlib import Path
from typing import List, Dict, Any, Optional

import pandas as pd
import numpy as np
from statsmodels.regression.mixed_linear_model import MixedLM

# Import project utilities matching the API surface
from utils.config import get_project_root, load_config, get_data_path
from utils.logger import get_logger

logger = get_logger(__name__)


def load_processed_data(data_path: Optional[Path] = None) -> pd.DataFrame:
    """
    Load the processed data for LMM analysis.
    Handles missing recall scores by logging a warning and skipping those rows.
    
    Args:
        data_path: Optional path to the processed data file. Defaults to config.
        
    Returns:
        pd.DataFrame: Cleaned dataframe with missing recall scores removed.
    """
    if data_path is None:
        root = get_project_root()
        data_path = root / "data" / "processed" / "combined_analysis_data.csv"
    
    if not data_path.exists():
        logger.error(f"Processed data file not found: {data_path}")
        raise FileNotFoundError(f"Processed data file not found: {data_path}")
    
    logger.info(f"Loading processed data from {data_path}")
    df = pd.read_csv(data_path)
    
    # T025 Implementation: Error handling for missing recall scores
    # Check for missing values in the 'recall_accuracy' column
    missing_mask = df['recall_accuracy'].isna()
    
    if missing_mask.any():
        count_missing = missing_mask.sum()
        total_count = len(df)
        percentage = (count_missing / total_count) * 100
        
        # Log warning as per task requirement
        logger.warning(
            f"Found {count_missing} rows ({percentage:.2f}%) with missing recall scores. "
            "Skipping these rows to continue processing."
        )
        
        # Drop rows with missing recall scores
        df_cleaned = df.dropna(subset=['recall_accuracy'])
        
        # Log the result of the cleaning
        logger.info(
            f"Data cleaned: {len(df_cleaned)} rows remaining for analysis "
            f"(removed {count_missing} rows)."
        )
        return df_cleaned
    else:
        logger.info("No missing recall scores found. Proceeding with full dataset.")
        return df


def fit_lmm_for_combination(
    df: pd.DataFrame,
    metric: str,
    valence: str
) -> Optional[Dict[str, Any]]:
    """
    Fit a Linear Mixed-Effects Model for a specific metric and valence combination.
    
    Args:
        df: Cleaned dataframe
        metric: The attention metric column name
        valence: The valence category filter
        
    Returns:
        Dictionary with model results or None if fit fails.
    """
    # Filter by valence
    subset = df[df['valence'] == valence]
    
    if len(subset) < 10:
        logger.warning(f"Not enough data points for valence={valence}, metric={metric}. Skipping.")
        return None
    
    # Define fixed and random effects
    # Assuming 'participant_id' is the random effect grouping variable
    # Formula: recall_accuracy ~ attention_metric + (1|participant_id)
    try:
        # Ensure required columns exist
        if metric not in subset.columns:
            logger.warning(f"Metric column '{metric}' not found in data. Skipping.")
            return None
        
        # Fit model
        # Using statsmodels MixedLM
        # Random intercepts for participant_id
        model = MixedLM(
            endog=subset['recall_accuracy'],
            exog=subset[[metric]],
            groups=subset['participant_id']
        )
        
        result = model.fit()
        
        # Extract coefficients and p-values
        # Fixed effects: intercept + metric coefficient
        fixed_params = result.fe_params
        fixed_pvalues = result.pvalues
        
        return {
            "metric": metric,
            "valence": valence,
            "n_obs": len(subset),
            "n_groups": subset['participant_id'].nunique(),
            "coef": float(fixed_params[metric]),
            "p_raw": float(fixed_pvalues[metric]),
            "intercept": float(fixed_params['Intercept']),
            "log_likelihood": float(result.llf)
        }
    except Exception as e:
        logger.warning(f"Failed to fit LMM for metric={metric}, valence={valence}: {str(e)}")
        return None


def run_lmm_analysis(
    df: pd.DataFrame,
    metrics: List[str],
    valences: List[str]
) -> List[Dict[str, Any]]:
    """
    Run LMM analysis for all combinations of metrics and valences.
    
    Args:
        df: Cleaned dataframe
        metrics: List of attention metric column names
        valences: List of valence categories
        
    Returns:
        List of result dictionaries.
    """
    results = []
    
    logger.info(f"Starting LMM analysis for {len(metrics)} metrics x {len(valences)} valences.")
    
    for metric in metrics:
        for valence in valences:
            logger.debug(f"Fitting model for {metric} x {valence}")
            result = fit_lmm_for_combination(df, metric, valence)
            if result:
                results.append(result)
    
    logger.info(f"LMM analysis complete. Generated {len(results)} results.")
    return results


def save_results(results: List[Dict[str, Any]], output_path: Optional[Path] = None) -> None:
    """
    Save LMM results to CSV and JSON.
    
    Args:
        results: List of result dictionaries
        output_path: Optional path to save results. Defaults to config.
    """
    if output_path is None:
        root = get_project_root()
        output_path = root / "output" / "results" / "lmm_summary.csv"
    
    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Convert to DataFrame and save CSV
    if results:
        df_results = pd.DataFrame(results)
        df_results.to_csv(output_path, index=False)
        logger.info(f"Saved LMM results to {output_path}")
        
        # Also save JSON for compatibility with other modules
        json_path = output_path.with_suffix('.json')
        with open(json_path, 'w') as f:
            json.dump(results, f, indent=2)
        logger.info(f"Saved LMM results JSON to {json_path}")
    else:
        logger.warning("No results to save.")
        # Create empty file to indicate completion
        output_path.touch()


def main():
    """Main entry point for LMM analysis."""
    parser = argparse.ArgumentParser(description="Run LMM analysis on eye-tracking and recall data.")
    parser.add_argument("--data", type=str, help="Path to processed data CSV")
    parser.add_argument("--output", type=str, help="Path to output results CSV")
    parser.add_argument("--metrics", type=str, nargs="+", 
                        default=["fixation_duration", "saccade_amplitude", "gaze_distribution"],
                        help="List of attention metrics to analyze")
    parser.add_argument("--valences", type=str, nargs="+", 
                        default=["positive", "negative", "neutral"],
                        help="List of valence categories to analyze")
    
    args = parser.parse_args()
    
    try:
        # Load data (T025: handles missing recall scores)
        data_path = Path(args.data) if args.data else None
        df = load_processed_data(data_path)
        
        # Run analysis
        results = run_lmm_analysis(
            df,
            metrics=args.metrics,
            valences=args.valences
        )
        
        # Save results
        output_path = Path(args.output) if args.output else None
        save_results(results, output_path)
        
        logger.info("LMM analysis completed successfully.")
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"Data file not found: {e}")
        return 1
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())