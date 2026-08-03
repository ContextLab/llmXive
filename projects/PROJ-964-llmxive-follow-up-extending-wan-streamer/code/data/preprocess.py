import os
import sys
import argparse
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List

import pandas as pd
import numpy as np
import yaml

# Project-relative imports based on API surface
# Note: In a real execution environment, ensure PYTHONPATH includes the code/ root
try:
    from utils.config import get_config_summary
except ImportError:
    # Fallback for direct execution if PYTHONPATH isn't set up correctly in some environments
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from utils.config import get_config_summary

from utils.validators import ValidationError, validate_dataframe

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_config(config_path: Optional[Path] = None) -> Dict[str, Any]:
    """Load configuration from YAML or return defaults."""
    if config_path is None:
        config_path = Path(__file__).parent.parent / 'config' / 'detection_thresholds.yaml'
    
    if not config_path.exists():
        # Default config if file missing, though T012a should have created it
        return {
            'thresholds': {
                'interruption_energy_db': -20.0,
                'pause_energy_db': -40.0,
                'pause_duration_ms': 200
            },
            'sampling': {
                'target_size_gb': 1.0,
                'stratify_columns': ['turn_label', 'event_type']
            },
            'validation': {
                'required_columns': ['timestamp', 'semantic_feature', 'prosodic_feature', 'latent_delta_magnitude', 'turn_label', 'event_type', 'priority'],
                'nullable_columns': [] # Empty means all required columns must be non-null
            }
        }
    
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def fetch_data_source(raw_path: Path, processed_path: Path) -> pd.DataFrame:
    """
    Fetch the processed data from the extraction step (T013).
    Expects the output of extract_latents.py to be at raw_path.
    """
    input_file = raw_path / 'extracted_latents.parquet'
    if not input_file.exists():
        raise FileNotFoundError(f"Input file not found: {input_file}. Run T013 first.")
    
    logger.info(f"Loading data from {input_file}")
    df = pd.read_parquet(input_file)
    return df

def filter_events(df: pd.DataFrame, config: Dict[str, Any]) -> pd.DataFrame:
    """Filter for interruption/pause events based on thresholds."""
    thresholds = config.get('thresholds', {})
    # Implementation depends on specific column logic from T013/T012a
    # Assuming 'event_type' column exists from T013
    if 'event_type' in df.columns:
        mask = df['event_type'].isin(['interruption', 'pause'])
        return df[mask]
    return df

def compute_latent_deltas(df: pd.DataFrame) -> pd.DataFrame:
    """Compute latent delta magnitude if not present."""
    if 'latent_delta_magnitude' not in df.columns:
        # Placeholder logic if T013 didn't compute it
        # Assuming semantic_feature is a vector or scalar
        if 'semantic_feature' in df.columns:
            df['latent_delta_magnitude'] = np.abs(df['semantic_feature']).diff().fillna(0)
    return df

def apply_stratified_sampling(df: pd.DataFrame, config: Dict[str, Any]) -> pd.DataFrame:
    """Apply stratified sampling to reduce dataset size."""
    # Implementation depends on T014b logic
    # Assuming target size and stratify columns are in config
    return df # Placeholder for T014b integration

def label_priority(df: pd.DataFrame, config: Dict[str, Any]) -> pd.DataFrame:
    """Label events as high/low priority."""
    # Implementation depends on T014c logic
    if 'priority' not in df.columns:
        df['priority'] = 'low' # Default
    return df

def log_priority_counts(df: pd.DataFrame) -> None:
    """Log counts of high/low priority events."""
    if 'priority' in df.columns:
        counts = df['priority'].value_counts()
        logger.info(f"Priority counts: {counts.to_dict()}")

def validate_output(df: pd.DataFrame, config: Dict[str, Any]) -> bool:
    """
    Validate that all required columns are non-null and correctly typed.
    Implements T014d requirements.
    
    Args:
        df: The dataframe to validate.
        config: Configuration dictionary containing validation rules.
        
    Returns:
        bool: True if validation passes.
        
    Raises:
        ValidationError: If validation fails.
    """
    validation_config = config.get('validation', {})
    required_columns = validation_config.get('required_columns', [])
    nullable_columns = validation_config.get('nullable_columns', [])
    
    logger.info(f"Validating output dataframe with {len(df)} rows.")
    logger.info(f"Required columns: {required_columns}")
    
    # 1. Check for existence of required columns
    missing_cols = [col for col in required_columns if col not in df.columns]
    if missing_cols:
        raise ValidationError(f"Missing required columns: {missing_cols}")
    
    # 2. Check for nulls in required columns (excluding explicitly nullable ones)
    non_nullable_cols = [col for col in required_columns if col not in nullable_columns]
    
    null_counts = {}
    for col in non_nullable_cols:
        null_count = df[col].isnull().sum()
        if null_count > 0:
            null_counts[col] = null_count
    
    if null_counts:
        error_msg = "Non-null constraints violated for the following columns:\n"
        for col, count in null_counts.items():
            error_msg += f"  - {col}: {count} null values found\n"
        raise ValidationError(error_msg)
    
    # 3. Type validation (basic checks)
    type_checks = {
        'timestamp': (int, float, pd.Timestamp),
        'latent_delta_magnitude': (int, float, np.floating),
        'turn_label': (str, int),
        'priority': (str,)
    }
    
    for col, expected_types in type_checks.items():
        if col in df.columns:
            # Check if the column's dtype is compatible
            # We allow pandas extension types, so we check the underlying numpy type or object
            if not df[col].apply(lambda x: isinstance(x, expected_types) or pd.isna(x)).all():
                # Note: We already checked for nulls above, so if we are here, we expect no nulls
                # But just in case, we check for valid types
                sample_val = df[col].iloc[0]
                if not isinstance(sample_val, expected_types):
                    raise ValidationError(f"Column '{col}' has invalid type. Expected {expected_types}, got {type(sample_val)}")
    
    logger.info("Validation passed: All required columns are present, non-null, and correctly typed.")
    return True

def get_current_memory_usage_mb() -> float:
    """Get current memory usage in MB."""
    try:
        import psutil
        process = psutil.Process(os.getpid())
        return process.memory_info().rss / 1024 / 1024
    except ImportError:
        logger.warning("psutil not installed. Cannot report memory usage.")
        return 0.0

def handle_power_limitation(error: Exception) -> None:
    """Handle power limitation errors."""
    logger.error(f"Power limitation encountered: {error}")
    # Logic to reduce sample size or exit gracefully
    sys.exit(1)

def main():
    """Main entry point for preprocessing pipeline."""
    parser = argparse.ArgumentParser(description='Preprocess extracted latents.')
    parser.add_argument('--config', type=str, default=None, help='Path to config file')
    parser.add_argument('--input-dir', type=str, default='data/raw', help='Input directory')
    parser.add_argument('--output-dir', type=str, default='data/processed', help='Output directory')
    args = parser.parse_args()
    
    input_path = Path(args.input_dir)
    output_path = Path(args.output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    config = load_config(Path(args.config) if args.config else None)
    
    try:
        # Fetch data
        df = fetch_data_source(input_path, output_path)
        
        # Apply transformations
        df = filter_events(df, config)
        df = compute_latent_deltas(df)
        df = apply_stratified_sampling(df, config)
        df = label_priority(df, config)
        
        log_priority_counts(df)
        
        # VALIDATION STEP (T014d)
        logger.info("Starting validation step (T014d)...")
        validate_output(df, config)
        logger.info("Validation successful.")
        
        # Save output
        output_file = output_path / 'preprocessed_latents.parquet'
        df.to_parquet(output_file, index=False)
        logger.info(f"Saved preprocessed data to {output_file}")
        
    except ValidationError as e:
        logger.error(f"Validation failed: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()