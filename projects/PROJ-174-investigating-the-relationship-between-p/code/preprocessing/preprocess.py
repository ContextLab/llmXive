import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
import numpy as np

from preprocessing.load_data import load_raw_data_from_dataset, normalize_columns, save_to_csv, process_single_file, run_loading_pipeline
from preprocessing.filter import process_pupil_data, apply_filter_to_dataset, write_quality_report
from preprocessing.features import extract_features, process_dataset_features

logger = logging.getLogger(__name__)

def load_raw_data(input_dir: Path, config: Dict[str, Any]) -> Tuple[List[Path], List[str]]:
    """Load raw data from the input directory."""
    paths = []
    errors = []
    for root, dirs, files in os.walk(input_dir):
        for file in files:
            if file.endswith(('.csv', '.tsv', '.txt')):
                full_path = Path(root) / file
                try:
                    # Simulate validation during loading
                    _ = load_raw_data_from_dataset(full_path, config)
                    paths.append(full_path)
                except Exception as e:
                    errors.append(f"Failed to load {file}: {str(e)}")
    return paths, errors

def validate_data_columns(df: Any, required_cols: List[str]) -> bool:
    """Check if dataframe has required columns."""
    if not hasattr(df, 'columns'):
        return False
    missing = [c for c in required_cols if c not in df.columns]
    return len(missing) == 0

def preprocess_single_subject(subject_id: str, file_path: Path, config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Process data for a single subject."""
    try:
        # 1. Load
        raw_df = load_raw_data_from_dataset(file_path, config)
        if raw_df is None:
            logger.warning(f"Failed to load data for subject {subject_id}")
            return None

        # 2. Validate
        required = ['timestamp', 'pupil_diameter', 'x', 'y']
        if not validate_data_columns(raw_df, required):
            logger.error(f"Missing columns for subject {subject_id}")
            return None

        # 3. Filter (Blink interpolation + Low-pass)
        filtered_df = process_pupil_data(raw_df, config)
        if filtered_df is None:
            logger.warning(f"Filtering failed for subject {subject_id}")
            return None

        # 4. Extract Features
        feature_df = extract_features(filtered_df, config)
        if feature_df is None:
            logger.warning(f"Feature extraction failed for subject {subject_id}")
            return None

        return {
            'subject_id': subject_id,
            'processed_data': feature_df,
            'status': 'success'
        }
    except Exception as e:
        logger.error(f"Error processing subject {subject_id}: {str(e)}", exc_info=True)
        return None

def run_preprocessing_pipeline(input_dir: Path, output_dir: Path, config: Dict[str, Any]) -> Dict[str, Any]:
    """Run the full preprocessing pipeline."""
    logger.info(f"Starting preprocessing pipeline for {input_dir}")

    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load raw paths
    raw_paths, load_errors = load_raw_data(input_dir, config)
    if not raw_paths:
        logger.error("No valid data files found.")
        return {'status': 'fail', 'errors': load_errors}

    results = []
    for file_path in raw_paths:
        subject_id = file_path.stem  # Assume filename is subject ID
        result = preprocess_single_subject(subject_id, file_path, config)
        if result:
            results.append(result)
            # Save processed data
            out_path = output_dir / f"{subject_id}_processed.csv"
            save_to_csv(result['processed_data'], out_path)
        else:
            logger.warning(f"Skipped subject {subject_id} due to processing failure.")

    # Write quality report
    write_quality_report(results, output_dir)

    logger.info(f"Preprocessing complete. {len(results)} subjects processed.")
    return {
        'status': 'success',
        'processed_count': len(results),
        'errors': load_errors
    }

def main():
    """CLI entry point for preprocessing."""
    from config import load_config
    import argparse

    parser = argparse.ArgumentParser(description="Run preprocessing pipeline")
    parser.add_argument("--input", type=str, required=True, help="Input directory")
    parser.add_argument("--output", type=str, required=True, help="Output directory")
    parser.add_argument("--config", type=str, default="code/config.yaml", help="Config file path")
    args = parser.parse_args()

    # Load config
    config = load_config(args.config)

    # Setup logging
    from logging_config import setup_logging
    setup_logging()

    # Run pipeline
    result = run_preprocessing_pipeline(
        Path(args.input),
        Path(args.output),
        config
    )

    if result['status'] == 'fail':
        sys.exit(1)

    logger.info("Pipeline finished successfully.")

if __name__ == "__main__":
    main()
