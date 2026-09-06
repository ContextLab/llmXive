"""
Aggregate Summary Generation (T029)

Generates CSV summary tables aggregating coefficients, p-values, and imputation stats.
Outputs:
  - results/model_summary.csv
  - results/diagnostics.csv
"""
import os
import pandas as pd
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List

from config_manager import get_results_path, get_config
from logging_config import get_logger
from models import save_model_results
from preprocessing import run_preprocessing_pipeline
from robustness import run_all_robustness_checks, save_robustness_results
from binary_model import save_binary_model_results
from aggregate_robustness import run_aggregation_pipeline
from power import run_retrospective_power_analysis

logger = get_logger(__name__)

def load_csv_safely(file_path: Path) -> Optional[pd.DataFrame]:
    """Safely load a CSV file, returning None if it doesn't exist."""
    if not file_path.exists():
        logger.warning(f"File not found: {file_path}")
        return None
    try:
        return pd.read_csv(file_path)
    except Exception as e:
        logger.error(f"Error loading {file_path}: {e}")
        return None

def extract_model_summary(primary_results_path: Path, binary_results_path: Path) -> pd.DataFrame:
    """
    Aggregate model results from primary and binary models into a summary table.
    Expected input files:
      - results/primary_model_results.csv
      - results/binary_model_results.csv
    """
    rows = []
    
    # Load Primary Model
    df_primary = load_csv_safely(primary_results_path)
    if df_primary is not None and not df_primary.empty:
        # Assuming standard statsmodels output columns or custom save format
        # We normalize to a standard schema for the summary
        for idx, row in df_primary.iterrows():
            rows.append({
                "model_type": "primary",
                "term": row.get('term', row.get('variable', 'intercept')),
                "coefficient": row.get('coef', row.get('coefficient', 0.0)),
                "std_error": row.get('std_err', row.get('std_error', 0.0)),
                "p_value": row.get('p-value', row.get('p_value', 1.0)),
                "conf_int_low": row.get('conf_int_low', row.get('lower', 0.0)),
                "conf_int_high": row.get('conf_int_high', row.get('upper', 0.0)),
                "significant": row.get('significant', row.get('sig', False))
            })

    # Load Binary Model
    df_binary = load_csv_safely(binary_results_path)
    if df_binary is not None and not df_binary.empty:
        for idx, row in df_binary.iterrows():
            rows.append({
                "model_type": "binary",
                "term": row.get('term', row.get('variable', 'intercept')),
                "coefficient": row.get('coef', row.get('coefficient', 0.0)),
                "std_error": row.get('std_err', row.get('std_error', 0.0)),
                "p_value": row.get('p-value', row.get('p_value', 1.0)),
                "conf_int_low": row.get('conf_int_low', row.get('lower', 0.0)),
                "conf_int_high": row.get('conf_int_high', row.get('upper', 0.0)),
                "significant": row.get('significant', row.get('sig', False))
            })

    if not rows:
        logger.warning("No model results found to aggregate.")
        return pd.DataFrame()

    return pd.DataFrame(rows)

def extract_diagnostics(imputed_data_path: Path, missingness_log_path: Optional[Path] = None) -> pd.DataFrame:
    """
    Aggregate diagnostics from preprocessing (imputation stats).
    """
    stats = []
    
    # Load Imputed Data to calculate basic stats if available
    df_imp = load_csv_safely(imputed_data_path)
    if df_imp is not None:
        # Calculate missingness per column from original (if we had it) or just report shape
        # Since we only have imputed data here, we report the shape and basic stats
        stats.append({
            "metric": "total_rows",
            "value": len(df_imp),
            "details": "Total observations after imputation"
        })
        stats.append({
            "metric": "total_columns",
            "value": len(df_imp.columns),
            "details": "Total variables"
        })
        
        # Check for any remaining NaNs (should be 0 if MICE worked correctly)
        na_counts = df_imp.isna().sum()
        if na_counts.sum() > 0:
            for col, count in na_counts[na_counts > 0].items():
                stats.append({
                    "metric": "remaining_na",
                    "value": count,
                    "details": f"Missing values in {col}"
                })
        else:
            stats.append({
                "metric": "remaining_na",
                "value": 0,
                "details": "No missing values remaining"
            })

    # Try to load a specific diagnostics file if it exists (e.g., from T014)
    # If T014 produced 'diagnostics.csv' directly, we might just return that.
    # But here we are aggregating into a summary.
    # Let's assume we generate a summary row based on the imputation process.
    
    return pd.DataFrame(stats)

def run_summary_aggregation_pipeline() -> None:
    """
    Main pipeline to generate model_summary.csv and diagnostics.csv.
    """
    results_path = get_results_path()
    ensure_dirs(results_path)
    
    logger.info("Starting summary aggregation pipeline...")
    
    # Define paths
    primary_results_path = results_path / "primary_model_results.csv"
    binary_results_path = results_path / "binary_model_results.csv"
    imputed_data_path = get_results_path().parent / "processed" / "imputed_data.csv" # Adjust path based on T014 output
    
    # 1. Generate Model Summary
    logger.info("Aggregating model results...")
    model_summary_df = extract_model_summary(primary_results_path, binary_results_path)
    
    if not model_summary_df.empty:
        output_summary_path = results_path / "model_summary.csv"
        model_summary_df.to_csv(output_summary_path, index=False)
        logger.info(f"Saved model summary to {output_summary_path}")
    else:
        logger.warning("Model summary is empty. Check if primary/binary model results exist.")
    
    # 2. Generate Diagnostics
    logger.info("Aggregating diagnostics...")
    # Note: If T014 produced a specific diagnostics file, we should load that.
    # Assuming T014 output is in data/processed/imputed_data.csv or similar.
    # We try to find the imputed data.
    processed_path = get_results_path().parent / "processed"
    imputed_file = processed_path / "imputed_data.csv"
    
    if not imputed_file.exists():
        # Fallback if path is different
        imputed_file = get_results_path().parent / "imputed_data.csv"
        
    diagnostics_df = extract_diagnostics(imputed_file)
    
    if not diagnostics_df.empty:
        output_diag_path = results_path / "diagnostics.csv"
        diagnostics_df.to_csv(output_diag_path, index=False)
        logger.info(f"Saved diagnostics to {output_diag_path}")
    else:
        logger.warning("Diagnostics summary is empty.")

def main():
    """Entry point for the summary aggregation task."""
    setup_logging()
    run_summary_aggregation_pipeline()

if __name__ == "__main__":
    main()
