import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np

from code.config import CONFIG

logger = logging.getLogger(__name__)

def load_analysis_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """Load analysis configuration parameters from contracts/analysis.schema.yaml."""
    if config_path is None:
        config_path = str(CONFIG.PROJECT_ROOT / "contracts" / "analysis.schema.yaml")
    
    path = Path(config_path)
    if not path.exists():
        logger.warning(f"Configuration file not found at {config_path}. Using defaults.")
        return {
            "filter_applied_weight": 0.5,
            "timestamp_regularity_weight": 0.5,
            "missing_metadata_default": 0.0
        }
    
    with open(path, 'r') as f:
        # Simple YAML parser for flat structure or use yaml if available
        # Assuming simple key: value format for this task
        config = {}
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                if ':' in line:
                    key, value = line.split(':', 1)
                    key = key.strip()
                    value = value.strip()
                    try:
                        config[key] = float(value)
                    except ValueError:
                        config[key] = value
        return config

def calculate_filter_applied_contribution(filter_applied: Optional[bool], config: Dict[str, Any]) -> float:
    """Calculate contribution of filter_applied to control proxy."""
    weight = config.get("filter_applied_weight", 0.5)
    default_val = config.get("missing_metadata_default", 0.0)
    
    if filter_applied is None:
        logger.warning("Missing filter_applied metadata, defaulting to 0.0")
        return default_val
    
    return float(filter_applied) * weight

def calculate_timestamp_regularity(timestamps: List[Any]) -> float:
    """Calculate timestamp regularity metric for a user's posts."""
    if not timestamps or len(timestamps) < 2:
        return 0.0
    
    try:
        # Convert to datetime if strings
        if isinstance(timestamps[0], str):
            ts = pd.to_datetime(timestamps)
        else:
            ts = pd.Series(timestamps)
        
        # Calculate time differences
        diffs = ts.diff().dropna().abs()
        if len(diffs) == 0:
            return 0.0
        
        # Regularity: inverse of coefficient of variation of time differences
        mean_diff = diffs.mean()
        std_diff = diffs.std()
        
        if mean_diff == 0:
            return 1.0  # Perfectly regular if all same time
        
        cv = std_diff / mean_diff
        regularity = 1.0 / (1.0 + cv)  # Normalize to [0, 1]
        return float(regularity)
    except Exception as e:
        logger.warning(f"Error calculating timestamp regularity: {e}")
        return 0.0

def calculate_control_proxy(filter_applied_contribution: float, timestamp_regularity: float, config: Dict[str, Any]) -> float:
    """Calculate final control proxy score."""
    timestamp_weight = config.get("timestamp_regularity_weight", 0.5)
    filter_weight = config.get("filter_applied_weight", 0.5)
    
    # Normalize weights to sum to 1 if needed
    total_weight = filter_weight + timestamp_weight
    if total_weight > 0:
        filter_weight = filter_weight / total_weight
        timestamp_weight = timestamp_weight / total_weight
    
    return (filter_applied_contribution * filter_weight) + (timestamp_regularity * timestamp_weight)

def run_proxy_extraction_pipeline(input_path: Optional[str] = None, config_path: Optional[str] = None) -> pd.DataFrame:
    """
    Run the proxy extraction pipeline.
    Reads metadata from input CSV (excluding text column) and calculates control proxies.
    """
    if input_path is None:
        input_path = str(CONFIG.RAW_DATA_PATH / "social_media.csv")
    
    input_file = Path(input_path)
    if not input_file.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    logger.info(f"Loading data from {input_path}")
    df = pd.read_csv(input_file)
    
    # Ensure required columns exist, handle missing with defaults
    required_cols = ['post_id', 'user_id']
    optional_cols = ['filter_applied', 'timestamp']
    
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Required column '{col}' not found in input data")
    
    # Handle optional columns with defaults (T025 implementation)
    config = load_analysis_config(config_path)
    default_val = config.get("missing_metadata_default", 0.0)
    
    for col in optional_cols:
        if col not in df.columns:
            logger.warning(f"Missing optional column '{col}', defaulting all rows to {default_val}")
            df[col] = default_val
        else:
            # Check for null values and log warnings
            null_count = df[col].isnull().sum()
            if null_count > 0:
                logger.warning(f"Column '{col}' has {null_count} missing values, defaulting to {default_val}")
                df[col] = df[col].fillna(default_val)
    
    # Extract only metadata columns (no text access - Constitution Principle VI)
    metadata_cols = ['post_id', 'user_id'] + [c for c in optional_cols if c in df.columns]
    df_metadata = df[metadata_cols].copy()
    
    # Calculate filter_applied contribution
    df_metadata['filter_applied_contribution'] = df_metadata['filter_applied'].apply(
        lambda x: calculate_filter_applied_contribution(x, config)
    )
    
    # Calculate timestamp regularity per user
    def get_user_regularity(group):
        return calculate_timestamp_regularity(group['timestamp'])
    
    user_regularity = df_metadata.groupby('user_id').apply(get_user_regularity).reset_index()
    user_regularity.columns = ['user_id', 'timestamp_regularity']
    
    # Merge back
    df_metadata = df_metadata.merge(user_regularity, on='user_id', how='left')
    
    # Calculate final control proxy
    df_metadata['control_proxy'] = df_metadata.apply(
        lambda row: calculate_control_proxy(
            row['filter_applied_contribution'],
            row['timestamp_regularity'],
            config
        ),
        axis=1
    )
    
    # Select final output columns
    result = df_metadata[['post_id', 'user_id', 'control_proxy', 'timestamp_regularity']]
    
    logger.info(f"Proxy extraction complete. Processed {len(result)} rows.")
    return result

def run_full_proxy_pipeline(input_path: Optional[str] = None, 
                            output_path: Optional[str] = None,
                            config_path: Optional[str] = None) -> str:
    """
    Run full proxy extraction pipeline including saving results.
    Returns path to output file.
    """
    if output_path is None:
        output_path = str(CONFIG.PROCESSED_DATA_PATH / "proxy_results.csv")
    
    results_df = run_proxy_extraction_pipeline(input_path, config_path)
    
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    results_df.to_csv(output_file, index=False)
    logger.info(f"Proxy results saved to {output_path}")
    
    return output_path

def main():
    """CLI entry point for proxy extraction."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Extract control proxies from social media metadata")
    parser.add_argument("--input", type=str, default=None, help="Input CSV path")
    parser.add_argument("--output", type=str, default=None, help="Output CSV path")
    parser.add_argument("--config", type=str, default=None, help="Config YAML path")
    
    args = parser.parse_args()
    
    output = run_full_proxy_pipeline(args.input, args.output, args.config)
    print(f"Completed. Output: {output}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()