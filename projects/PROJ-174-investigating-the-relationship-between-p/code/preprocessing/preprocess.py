"""
Preprocessing pipeline for pupil dilation data.
Refactored to reduce cyclomatic complexity (< 15 per function).
"""
import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
import numpy as np
import pandas as pd

# Import existing utilities
from preprocessing.filter import process_pupil_data, write_quality_report
from preprocessing.features import extract_features

# Configure logging
logger = logging.getLogger(__name__)

def load_raw_data(input_path: str) -> pd.DataFrame:
    """Load raw data from CSV or similar format."""
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    ext = Path(input_path).suffix.lower()
    if ext == '.csv':
        return pd.read_csv(input_path)
    elif ext == '.parquet':
        return pd.read_parquet(input_path)
    else:
        raise ValueError(f"Unsupported file format: {ext}")

def validate_data_columns(df: pd.DataFrame) -> bool:
    """Check if required columns exist in the dataframe."""
    required = ['timestamp', 'pupil_diameter']
    return all(col in df.columns for col in required)

def preprocess_single_subject(
    df: pd.DataFrame,
    config: Dict[str, Any]
) -> Tuple[pd.DataFrame, Dict[str, int]]:
    """
    Preprocess data for a single subject.
    Returns processed dataframe and exclusion counts.
    """
    if not validate_data_columns(df):
        raise ValueError("Missing required columns in input data")
    
    # Apply filtering (blink interpolation, low-pass)
    filtered_df, exclusion_counts = process_pupil_data(df, config)
    
    # Extract features (search time, fixation count, salience)
    feature_df = extract_features(filtered_df, config)
    
    return feature_df, exclusion_counts

def run_preprocessing_pipeline(
    input_dir: str,
    output_dir: str,
    config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Run the full preprocessing pipeline on all subjects in input_dir.
    Returns summary statistics.
    """
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    results = {
        'total_files': 0,
        'processed_files': 0,
        'failed_files': 0,
        'total_exclusions': {}
    }
    
    # Find all data files
    data_files = list(input_path.glob("*.csv"))
    results['total_files'] = len(data_files)
    
    quality_reports = []
    
    for file_path in data_files:
        try:
            logger.info(f"Processing: {file_path.name}")
            df = load_raw_data(str(file_path))
            processed_df, exclusions = preprocess_single_subject(df, config)
            
            # Save processed data
            output_file = output_path / f"processed_{file_path.name}"
            processed_df.to_csv(output_file, index=False)
            
            results['processed_files'] += 1
            quality_reports.append(exclusions)
            
            # Aggregate exclusions
            for key, count in exclusions.items():
                results['total_exclusions'][key] = \
                    results['total_exclusions'].get(key, 0) + count
                
        except Exception as e:
            logger.error(f"Failed to process {file_path.name}: {str(e)}")
            results['failed_files'] += 1
    
    # Write aggregated quality report
    if quality_reports:
        write_quality_report(quality_reports, str(output_path / "quality_report.csv"))
    
    return results

def main():
    """Main entry point for preprocessing pipeline."""
    import argparse
    from config import load_config
    
    parser = argparse.ArgumentParser(description="Preprocess pupil dilation data")
    parser.add_argument("--input", required=True, help="Input directory")
    parser.add_argument("--output", required=True, help="Output directory")
    parser.add_argument("--config", default="code/config.yaml", help="Config file path")
    args = parser.parse_args()
    
    # Load configuration
    config = load_config(args.config)
    
    # Run pipeline
    results = run_preprocessing_pipeline(args.input, args.output, config)
    
    # Log summary
    logger.info(f"Preprocessing complete: {results}")
    print(f"Processed {results['processed_files']}/{results['total_files']} files")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
