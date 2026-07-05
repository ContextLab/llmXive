import os
import csv
import logging
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import yaml
import pandas as pd

from src.utils.config import get_project_root, get_interim_data_dir, get_processed_data_dir

logger = logging.getLogger(__name__)

def load_csv(file_path: Path) -> pd.DataFrame:
    """Load a CSV file into a pandas DataFrame."""
    if not file_path.exists():
        raise FileNotFoundError(f"CSV file not found: {file_path}")
    return pd.read_csv(file_path)

def save_csv(df: pd.DataFrame, file_path: Path) -> None:
    """Save a DataFrame to a CSV file."""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(file_path, index=False)
    logger.info(f"Saved CSV to {file_path} with {len(df)} rows")

def validate_against_schema(df: pd.DataFrame, schema_path: Path) -> bool:
    """Validate a DataFrame against a YAML schema definition."""
    if not schema_path.exists():
        logger.warning(f"Schema file not found: {schema_path}. Skipping validation.")
        return True
    
    with open(schema_path, 'r') as f:
        schema = yaml.safe_load(f)
    
    required_columns = schema.get('required_columns', [])
    for col in required_columns:
        if col not in df.columns:
            logger.error(f"Missing required column: {col}")
            return False
    return True

def combine_datasets(dfs: List[pd.DataFrame]) -> pd.DataFrame:
    """Combine multiple DataFrames vertically."""
    if not dfs:
        return pd.DataFrame()
    return pd.concat(dfs, ignore_index=True)

def filter_by_snr_threshold(
    df: pd.DataFrame, 
    threshold_db: float, 
    snr_column: str = 'snr_db',
    output_path: Optional[Path] = None,
    dropped_path: Optional[Path] = None
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Filter records based on SNR threshold.
    
    Args:
        df: Input DataFrame containing SNR data
        threshold_db: Minimum SNR threshold in dB
        snr_column: Name of the SNR column
        output_path: Path to save filtered records
        dropped_path: Path to save dropped records
        
    Returns:
        Tuple of (filtered_df, dropped_df)
    """
    if snr_column not in df.columns:
        raise ValueError(f"SNR column '{snr_column}' not found in DataFrame")
    
    # Filter records where SNR > threshold
    filtered_df = df[df[snr_column] > threshold_db].copy()
    dropped_df = df[df[snr_column] <= threshold_db].copy()
    
    # Add reason for dropping if dropped_df is not empty
    if not dropped_df.empty:
        dropped_df['drop_reason'] = f'snr_below_{threshold_db}db'
    
    # Save outputs if paths provided
    if output_path:
        save_csv(filtered_df, output_path)
    if dropped_path:
        dropped_path.parent.mkdir(parents=True, exist_ok=True)
        save_csv(dropped_df, dropped_path)
        
    logger.info(f"Filtered at {threshold_db}dB: kept {len(filtered_df)}, dropped {len(dropped_df)}")
    return filtered_df, dropped_df

def run_sensitivity_analysis(
    input_path: Path,
    thresholds: List[float],
    output_dir: Path,
    counts_path: Path
) -> None:
    """
    Execute sensitivity analysis by running SNR filter with multiple thresholds.
    
    Args:
        input_path: Path to the input dataset (filtered_snr.csv)
        thresholds: List of SNR thresholds to test
        output_dir: Directory to save sensitivity output files
        counts_path: Path to save the sensitivity counts summary
    """
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    df = load_csv(input_path)
    logger.info(f"Loaded input dataset with {len(df)} records")
    
    results = []
    
    for threshold in thresholds:
        output_filename = f"sensitivity_{int(threshold)}db.csv"
        dropped_filename = f"filtered_records_{int(threshold)}db.csv"
        
        output_path = output_dir / output_filename
        dropped_path = output_dir / dropped_filename
        
        filtered_df, dropped_df = filter_by_snr_threshold(
            df=df,
            threshold_db=threshold,
            snr_column='snr_db',
            output_path=output_path,
            dropped_path=dropped_path
        )
        
        results.append({
            'threshold': threshold,
            'sample_size': len(filtered_df),
            'dropped_count': len(dropped_df)
        })
        
        logger.info(f"Threshold {threshold}dB: {len(filtered_df)} records retained")
    
    # Save sensitivity counts summary
    counts_df = pd.DataFrame(results)
    counts_path.parent.mkdir(parents=True, exist_ok=True)
    save_csv(counts_df, counts_path)
    logger.info(f"Saved sensitivity counts to {counts_path}")

def main():
    """Main entry point for sensitivity analysis execution."""
    project_root = get_project_root()
    interim_dir = get_interim_data_dir()
    processed_dir = get_processed_data_dir()
    
    # Input file from T017b
    input_path = interim_dir / "filtered_snr.csv"
    
    # Output directories and files
    output_dir = processed_dir
    counts_path = interim_dir / "sensitivity_counts.csv"
    
    # Thresholds to test (including 10 and 15 dB as required)
    thresholds = [5.0, 10.0, 15.0]
    
    logger.info(f"Starting sensitivity analysis with thresholds: {thresholds}")
    logger.info(f"Input: {input_path}")
    logger.info(f"Output dir: {output_dir}")
    
    try:
        run_sensitivity_analysis(
            input_path=input_path,
            thresholds=thresholds,
            output_dir=output_dir,
            counts_path=counts_path
        )
        logger.info("Sensitivity analysis completed successfully")
    except Exception as e:
        logger.error(f"Sensitivity analysis failed: {e}")
        raise

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
