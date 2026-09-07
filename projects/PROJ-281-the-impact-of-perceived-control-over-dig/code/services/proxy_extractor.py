"""
Proxy Extractor Service for US2 - Control Proxy Extraction.

This module extracts metadata-based proxies representing "perceived control"
from social media data. It strictly enforces data independence by ensuring
no access to the 'text' column during processing.
"""
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Custom Exception for Data Independence Violations
class DataIndependenceError(Exception):
    """Raised when the text column is accessed during proxy extraction."""
    pass

def load_analysis_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load analysis configuration from contracts/analysis.schema.yaml.
    
    Args:
        config_path: Path to the config file. Defaults to contracts/analysis.schema.yaml.
        
    Returns:
        Dictionary containing configuration parameters.
    """
    if config_path is None:
        config_path = "contracts/analysis.schema.yaml"
    
    try:
        with open(config_path, 'r') as f:
            # Simple YAML-like parsing for flat structure
            # In production, use a proper YAML parser like pyyaml
            config = {}
            current_section = None
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                if line.endswith(':') and not ':' in line.split(':')[0]:
                    # Section header
                    current_section = line[:-1]
                    config[current_section] = {}
                elif ':' in line and current_section:
                    key, value = line.split(':', 1)
                    key = key.strip()
                    value = value.strip()
                    # Parse value types
                    if value.lower() == 'false':
                        value = False
                    elif value.lower() == 'true':
                        value = True
                    elif value.replace('.', '', 1).isdigit():
                        value = float(value) if '.' in value else int(value)
                    config[current_section][key] = value
            return config
    except FileNotFoundError:
        logger.warning(f"Config file {config_path} not found. Using defaults.")
        return {
            "weights": {
                "weight_filter": 0.5,
                "weight_regularity": 0.5
            }
        }

def calculate_filter_applied_contribution(row: pd.Series, weight: float) -> float:
    """
    Calculate the contribution of filter_applied to the control proxy.
    
    Args:
        row: DataFrame row containing metadata.
        weight: Weight for the filter_applied component.
        
    Returns:
        Weighted contribution value (0.0 or weight).
    """
    # Defensive: Ensure we are not accessing text
    if 'text' in row.index:
        raise DataIndependenceError("Attempted to access 'text' column in filter_applied calculation!")
    
    filter_val = row.get('filter_applied', 0)
    if pd.isna(filter_val):
        filter_val = 0
    
    return float(filter_val) * weight

def calculate_timestamp_regularity(user_timestamps: List[Any]) -> float:
    """
    Calculate timestamp regularity metric for a user's posts.
    
    Args:
        user_timestamps: List of timestamp strings or datetime objects.
        
    Returns:
        Regularity score between 0.0 and 1.0.
    """
    if not user_timestamps or len(user_timestamps) < 2:
        return 0.0
    
    try:
        # Convert to datetime if strings
        datetimes = []
        for ts in user_timestamps:
            if isinstance(ts, str):
                # Try common formats
                for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%d']:
                    try:
                        datetimes.append(datetime.strptime(ts, fmt))
                        break
                    except ValueError:
                        continue
                else:
                    # If all formats fail, try pandas
                    datetimes.append(pd.to_datetime(ts))
            else:
                datetimes.append(ts)
        
        # Sort timestamps
        datetimes.sort()
        
        # Calculate time differences in seconds
        diffs = []
        for i in range(1, len(datetimes)):
            delta = (datetimes[i] - datetimes[i-1]).total_seconds()
            if delta > 0:
                diffs.append(delta)
        
        if not diffs:
            return 0.0
        
        # Calculate coefficient of variation (CV) of time differences
        # Lower CV means more regular posting
        mean_diff = np.mean(diffs)
        std_diff = np.std(diffs)
        
        if mean_diff == 0:
            return 1.0  # Perfectly regular (all same time)
        
        cv = std_diff / mean_diff
        
        # Convert CV to a 0-1 score (lower CV = higher regularity)
        # Using exponential decay: score = e^(-cv)
        regularity = np.exp(-cv)
        
        return float(regularity)
        
    except Exception as e:
        logger.warning(f"Error calculating timestamp regularity: {e}")
        return 0.0

def calculate_control_proxy(row: pd.Series, config: Dict[str, Any]) -> float:
    """
    Calculate the overall control proxy score for a single post.
    
    Args:
        row: DataFrame row containing metadata.
        config: Configuration dictionary with weights.
        
    Returns:
        Control proxy score.
    """
    weights = config.get('weights', {})
    weight_filter = weights.get('weight_filter', 0.5)
    weight_regularity = weights.get('weight_regularity', 0.5)
    
    # Defensive check: Ensure text is not accessed
    if 'text' in row.index:
        raise DataIndependenceError("Attempted to access 'text' column in control proxy calculation!")
    
    # Get filter contribution
    filter_contribution = calculate_filter_applied_contribution(row, weight_filter)
    
    # Get regularity contribution (needs user-level aggregation)
    # This is handled in the pipeline function
    regularity_contribution = row.get('_timestamp_regularity', 0.0)
    regularity_contribution *= weight_regularity
    
    return filter_contribution + regularity_contribution

def run_proxy_extraction_pipeline(
    input_path: str,
    output_path: str,
    config_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Run the full proxy extraction pipeline.
    
    Args:
        input_path: Path to the raw social media CSV.
        output_path: Path to save the proxy results CSV.
        config_path: Path to the analysis config file.
        
    Returns:
        Dictionary with pipeline statistics.
    """
    logger.info(f"Starting proxy extraction pipeline. Input: {input_path}")
    
    # Load config
    config = load_analysis_config(config_path)
    
    # Load data - STRICTLY EXCLUDE TEXT COLUMN
    try:
        # Read only necessary columns
        required_cols = ['post_id', 'user_id', 'timestamp', 'filter_applied']
        
        # Try to load with specific columns to ensure text is not in memory
        df = pd.read_csv(input_path, usecols=required_cols, on_bad_lines='skip')
        
        logger.info(f"Loaded {len(df)} rows. Columns: {list(df.columns)}")
        
        # Double-check: Verify 'text' is not in the dataframe
        if 'text' in df.columns:
            raise DataIndependenceError("Text column was loaded into memory! This violates data independence.")
        
    except Exception as e:
        logger.error(f"Error loading data: {e}")
        return {"status": "error", "message": str(e)}
    
    # Calculate timestamp regularity per user
    logger.info("Calculating timestamp regularity per user...")
    user_regularity = {}
    for user_id, group in df.groupby('user_id'):
        timestamps = group['timestamp'].tolist()
        regularity = calculate_timestamp_regularity(timestamps)
        user_regularity[user_id] = regularity
    
    # Map regularity back to rows
    df['_timestamp_regularity'] = df['user_id'].map(user_regularity)
    
    # Calculate control proxy for each row
    logger.info("Calculating control proxy scores...")
    df['control_proxy'] = df.apply(lambda row: calculate_control_proxy(row, config), axis=1)
    
    # Prepare output dataframe
    output_df = df[['post_id', 'user_id', 'control_proxy', '_timestamp_regularity']].copy()
    output_df.rename(columns={'_timestamp_regularity': 'timestamp_regularity'}, inplace=True)
    
    # Save results
    output_path_obj = Path(output_path)
    output_path_obj.parent.mkdir(parents=True, exist_ok=True)
    output_df.to_csv(output_path, index=False)
    
    logger.info(f"Saved proxy results to {output_path}")
    
    return {
        "status": "success",
        "rows_processed": len(df),
        "output_file": str(output_path)
    }

def run_full_proxy_pipeline(
    input_path: Optional[str] = None,
    output_path: Optional[str] = None,
    config_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Run the full proxy pipeline with default paths.
    
    Args:
        input_path: Path to raw data. Defaults to data/raw/social_media.csv.
        output_path: Path to output file. Defaults to data/processed/proxy_results.csv.
        config_path: Path to config file. Defaults to contracts/analysis.schema.yaml.
        
    Returns:
        Pipeline execution result.
    """
    if input_path is None:
        input_path = "data/raw/social_media.csv"
    if output_path is None:
        output_path = "data/processed/proxy_results.csv"
    if config_path is None:
        config_path = "contracts/analysis.schema.yaml"
        
    return run_proxy_extraction_pipeline(input_path, output_path, config_path)

def main():
    """Main entry point for the proxy extractor."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Extract control proxies from social media data")
    parser.add_argument("--input", type=str, help="Input CSV path")
    parser.add_argument("--output", type=str, help="Output CSV path")
    parser.add_argument("--config", type=str, help="Config file path")
    
    args = parser.parse_args()
    
    result = run_full_proxy_pipeline(
        input_path=args.input,
        output_path=args.output,
        config_path=args.config
    )
    
    print(json.dumps(result, indent=2))
    return result

if __name__ == "__main__":
    main()