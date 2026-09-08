"""
T035: Generate final report summary table with cluster coordinates and behavioral correlations.

This script generates `docs/report_summary.csv` by joining cluster data from T025
and correlation data from T033.

Schema:
cluster_id, x, y, z, t, p_val_fdr, r_corr, p_val_beh, description

Logic:
- Load cluster metadata from `data/processed/fdr_clusters.csv` (T025).
- Load correlation results from `data/processed/correlation_results.json` (T033).
- Join on subject_id where applicable, or aggregate global stats.
- Handle missing p_val_fdr as NaN.
"""
import os
import sys
import json
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add project root to path for imports if running as script
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from stats_config import load_config

def setup_logging() -> logging.Logger:
    """Setup logging for the report generation script."""
    logger = logging.getLogger("report_summary")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger

def load_cluster_data(logger: logging.Logger) -> pd.DataFrame:
    """
    Load cluster metadata from T025 output.
    Expected file: data/processed/fdr_clusters.csv
    Expected columns: cluster_id, x, y, z, t, p_val_fdr, description (or similar)
    """
    cluster_path = PROJECT_ROOT / "data" / "processed" / "fdr_clusters.csv"
    
    if not cluster_path.exists():
        logger.error(f"Cluster data file not found: {cluster_path}")
        raise FileNotFoundError(f"Cluster data file not found: {cluster_path}")
    
    try:
        df = pd.read_csv(cluster_path)
        logger.info(f"Loaded cluster data: {len(df)} clusters from {cluster_path}")
        
        # Ensure required columns exist, fill missing with NaN
        required_cols = ['cluster_id', 'x', 'y', 'z', 't', 'p_val_fdr', 'description']
        for col in required_cols:
            if col not in df.columns:
                df[col] = np.nan
                logger.warning(f"Column '{col}' missing in cluster data, filled with NaN.")
        
        return df
    except Exception as e:
        logger.error(f"Error loading cluster data: {e}")
        raise

def load_correlation_data(logger: logging.Logger) -> pd.DataFrame:
    """
    Load correlation results from T033 output.
    Expected file: data/processed/correlation_results.json
    Expected structure: { "pearson_r": float, "p_value": float, "n": int, "description": str }
    """
    corr_path = PROJECT_ROOT / "data" / "processed" / "correlation_results.json"
    
    if not corr_path.exists():
        logger.error(f"Correlation results file not found: {corr_path}")
        raise FileNotFoundError(f"Correlation results file not found: {corr_path}")
    
    try:
        with open(corr_path, 'r') as f:
            data = json.load(f)
        
        # Flatten into a single-row DataFrame for joining/merging logic
        # We will broadcast this to all clusters or keep as global summary
        row = {
            'r_corr': data.get('pearson_r', np.nan),
            'p_val_beh': data.get('p_value', np.nan),
            'description': data.get('description', 'Global Correlation')
        }
        
        df = pd.DataFrame([row])
        logger.info(f"Loaded correlation data: r={row['r_corr']}, p={row['p_val_beh']}")
        return df
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding correlation JSON: {e}")
        raise
    except Exception as e:
        logger.error(f"Error loading correlation data: {e}")
        raise

def generate_report_summary(cluster_df: pd.DataFrame, corr_df: pd.DataFrame, logger: logging.Logger) -> pd.DataFrame:
    """
    Join cluster data and correlation data to create the final summary table.
    
    Logic:
    - If cluster_df has multiple rows, we duplicate the correlation data for each cluster
      to show the global behavioral correlation alongside each cluster's stats.
    - Columns: cluster_id, x, y, z, t, p_val_fdr, r_corr, p_val_beh, description
    - Handle missing p_val_fdr as NaN (already done in load_cluster_data).
    """
    # Prepare columns for the final output
    final_cols = ['cluster_id', 'x', 'y', 'z', 't', 'p_val_fdr', 'r_corr', 'p_val_beh', 'description']
    
    # If we have clusters, broadcast correlation data
    if not cluster_df.empty:
        # Merge correlation data (which has 1 row) with cluster data
        # We use a cross join logic by adding a dummy key or simply repeating the correlation row
        # Since corr_df has 1 row, we can just assign its values to the cluster_df
        # But to be safe with pandas merge, we'll do a cross join via a dummy key if needed.
        # Simpler approach: assign the values directly if we know corr_df has 1 row.
        
        if len(corr_df) == 1:
            cluster_df['r_corr'] = corr_df.iloc[0]['r_corr']
            cluster_df['p_val_beh'] = corr_df.iloc[0]['p_val_beh']
            # Update description to include correlation context if needed, or keep cluster desc
            # The task says "description" column. We'll keep the cluster description primarily.
            
            # Ensure the column order matches the schema
            result_df = cluster_df[final_cols].copy()
        else:
            # Fallback if correlation data is multi-row (unexpected)
            logger.warning("Correlation data has multiple rows; attempting to merge by index or defaulting.")
            # Just take the first row of correlation for all clusters as a fallback
            cluster_df['r_corr'] = corr_df.iloc[0]['r_corr']
            cluster_df['p_val_beh'] = corr_df.iloc[0]['p_val_beh']
            result_df = cluster_df[final_cols].copy()
    else:
        # If no clusters survived FDR, we still want to report the correlation if available
        # Create a single row summary
        logger.warning("No clusters found. Generating summary with correlation data only.")
        result_df = pd.DataFrame(columns=final_cols)
        if len(corr_df) > 0:
            result_df = corr_df[final_cols].copy() # This might fail if cols don't match exactly
            # Reconstruct manually
            result_df = pd.DataFrame([{
                'cluster_id': np.nan,
                'x': np.nan,
                'y': np.nan,
                'z': np.nan,
                't': np.nan,
                'p_val_fdr': np.nan,
                'r_corr': corr_df.iloc[0]['r_corr'],
                'p_val_beh': corr_df.iloc[0]['p_val_beh'],
                'description': "No clusters survived FDR; Global Correlation"
            }])
    
    # Ensure numeric columns are numeric
    for col in ['x', 'y', 'z', 't', 'p_val_fdr', 'r_corr', 'p_val_beh']:
        result_df[col] = pd.to_numeric(result_df[col], errors='coerce')
    
    return result_df

def save_report(result_df: pd.DataFrame, logger: logging.Logger) -> Path:
    """
    Save the report summary to docs/report_summary.csv.
    """
    output_dir = PROJECT_ROOT / "docs"
    output_dir.mkdir(exist_ok=True)
    output_path = output_dir / "report_summary.csv"
    
    result_df.to_csv(output_path, index=False)
    logger.info(f"Report summary saved to: {output_path}")
    return output_path

def main():
    """Main entry point for T035."""
    logger = setup_logging()
    logger.info("Starting T035: Generate Report Summary")
    
    try:
        # Load data
        cluster_df = load_cluster_data(logger)
        corr_df = load_correlation_data(logger)
        
        # Generate summary
        summary_df = generate_report_summary(cluster_df, corr_df, logger)
        
        # Save output
        output_path = save_report(summary_df, logger)
        
        logger.info("T035 completed successfully.")
        return 0
    except Exception as e:
        logger.error(f"T035 failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
