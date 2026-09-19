"""
Aggregation module for generating CSV summary tables.

This module aggregates model coefficients, p-values, and imputation statistics
from various analysis outputs into consolidated CSV files:
- model_summary.csv: Primary model, binary model, and covariate-adjusted model results
- diagnostics.csv: Imputation statistics and data quality metrics

Used by User Story 3 (Reporting & Artifact Generation).
"""

import os
import pandas as pd
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List

from config_manager import get_results_path, get_config
from logging_config import get_logger

# Initialize logger
logger = get_logger(__name__)


def load_csv_safely(filepath: Path, required_columns: Optional[List[str]] = None) -> Optional[pd.DataFrame]:
    """
    Safely load a CSV file, returning None if the file doesn't exist or is empty.
    
    Args:
        filepath: Path to the CSV file
        required_columns: Optional list of columns that must exist
        
    Returns:
        DataFrame if successful, None otherwise
    """
    if not filepath.exists():
        logger.warning(f"File not found: {filepath}")
        return None
    
    try:
        df = pd.read_csv(filepath)
        if df.empty:
            logger.warning(f"File is empty: {filepath}")
            return None
        
        if required_columns:
            missing = set(required_columns) - set(df.columns)
            if missing:
                logger.warning(f"Missing required columns in {filepath}: {missing}")
                return None
        
        return df
    except Exception as e:
        logger.error(f"Error loading {filepath}: {e}")
        return None


def extract_model_summary(model_results_path: Path) -> Optional[pd.DataFrame]:
    """
    Extract model summary statistics from model result files.
    
    Aggregates results from:
    - Primary model (results/primary_model.csv)
    - Binary model (results/binary_model.csv)
    - Covariate-adjusted model (results/covariate_model.csv)
    
    Args:
        model_results_path: Path to the results directory
        
    Returns:
        DataFrame with aggregated model summaries
    """
    summary_records = []
    
    # Define model files and their types
    model_files = {
        'primary_model.csv': 'primary',
        'binary_model.csv': 'binary',
        'covariate_model.csv': 'covariate_adjusted'
    }
    
    for filename, model_type in model_files.items():
        filepath = model_results_path / filename
        df = load_csv_safely(filepath)
        
        if df is not None and not df.empty:
            # Extract key statistics for each model
            for idx, row in df.iterrows():
                record = {
                    'model_type': model_type,
                    'source_file': filename,
                    'row_index': idx
                }
                
                # Extract common statistics if they exist
                for col in ['coef', 'P>|t|', 'std err', 't', 'P>|z|']:
                    if col in df.columns:
                        record[col] = row[col]
                
                # Extract model-specific statistics
                if 'r_squared' in df.columns:
                    record['r_squared'] = row['r_squared']
                if 'adj_r_squared' in df.columns:
                    record['adj_r_squared'] = row['adj_r_squared']
                if 'aic' in df.columns:
                    record['aic'] = row['aic']
                if 'bic' in df.columns:
                    record['bic'] = row['bic']
                
                # Add interaction term specific info if available
                if 'term' in df.columns:
                    record['term'] = row['term']
                if 'variable' in df.columns:
                    record['variable'] = row['variable']
                
                summary_records.append(record)
    
    if not summary_records:
        logger.warning("No model results found to summarize")
        return None
    
    return pd.DataFrame(summary_records)


def extract_diagnostics(diagnostics_path: Path) -> Optional[pd.DataFrame]:
    """
    Extract diagnostics from imputation and data quality files.
    
    Aggregates statistics from:
    - results/diagnostics.csv (imputation diagnostics)
    - results/power_design.csv (a priori power analysis)
    - results/power_analysis.csv (retrospective power analysis)
    
    Args:
        diagnostics_path: Path to the results directory
        
    Returns:
        DataFrame with aggregated diagnostics
    """
    diag_records = []
    
    # Define diagnostic files
    diag_files = [
        'diagnostics.csv',
        'power_design.csv',
        'power_analysis.csv'
    ]
    
    for filename in diag_files:
        filepath = diagnostics_path / filename
        df = load_csv_safely(filepath)
        
        if df is not None and not df.empty:
            # Add source file info
            df = df.copy()
            df['source_file'] = filename
            diag_records.append(df)
    
    if not diag_records:
        logger.warning("No diagnostic files found")
        return None
    
    # Concatenate all diagnostic dataframes
    return pd.concat(diag_records, ignore_index=True)


def run_summary_aggregation_pipeline(results_path: Optional[Path] = None) -> Dict[str, Path]:
    """
    Run the full summary aggregation pipeline.
    
    Generates:
    - model_summary.csv: Aggregated model statistics
    - diagnostics.csv: Aggregated diagnostic statistics
    
    Args:
        results_path: Optional custom results path (uses config if not provided)
        
    Returns:
        Dictionary mapping output filenames to their paths
    """
    if results_path is None:
        results_path = get_results_path()
    
    logger.info(f"Starting summary aggregation pipeline for results at: {results_path}")
    
    # Ensure results directory exists
    os.makedirs(results_path, exist_ok=True)
    
    output_files = {}
    
    # Extract and save model summary
    model_summary_df = extract_model_summary(results_path)
    if model_summary_df is not None:
        model_summary_path = results_path / 'model_summary.csv'
        model_summary_df.to_csv(model_summary_path, index=False)
        output_files['model_summary.csv'] = model_summary_path
        logger.info(f"Saved model summary to: {model_summary_path}")
    else:
        logger.warning("Model summary could not be generated")
    
    # Extract and save diagnostics
    diagnostics_df = extract_diagnostics(results_path)
    if diagnostics_df is not None:
        diagnostics_path = results_path / 'diagnostics.csv'
        diagnostics_df.to_csv(diagnostics_path, index=False)
        output_files['diagnostics.csv'] = diagnostics_path
        logger.info(f"Saved diagnostics to: {diagnostics_path}")
    else:
        logger.warning("Diagnostics could not be generated")
    
    return output_files


def main():
    """Main entry point for summary aggregation."""
    logger.info("Running summary aggregation pipeline...")
    
    try:
        output_files = run_summary_aggregation_pipeline()
        
        if output_files:
            logger.info(f"Summary aggregation complete. Generated {len(output_files)} files:")
            for name, path in output_files.items():
                logger.info(f"  - {name}: {path}")
        else:
            logger.warning("No output files were generated")
            
    except Exception as e:
        logger.error(f"Error in summary aggregation pipeline: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
