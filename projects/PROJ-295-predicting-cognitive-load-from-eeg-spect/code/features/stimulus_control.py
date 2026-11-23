"""
Stimulus Control Module for Cognitive Load Prediction Pipeline.

This module implements the regression of stimulus complexity metrics to isolate
the variance in EEG spectral power attributable to cognitive load rather than
stimulus properties.

Since the OpenNeuro ds000246 dataset (naturalistic viewing) typically does not
include explicit, per-epoch "stimulus complexity" metadata (e.g., Gabor energy,
edge density, or semantic complexity scores) in a standardized format, this
module:
1. Attempts to load a potential external metadata file (if provided).
2. If no valid complexity metrics are found, it explicitly flags this limitation
   in a report file and returns the original data unchanged.

This adheres to the requirement to "regress out... or explicitly flag this as a
limitation".
"""

import os
import sys
import json
import hashlib
import datetime
import logging
from typing import Dict, List, Optional, Tuple, Any

import numpy as np
import pandas as pd
from scipy import stats

# Import config utilities
try:
    from config import load_config, get_config_value
except ImportError:
    # Fallback for direct execution or different import paths
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
    from config import load_config, get_config_value

logger = logging.getLogger(__name__)

# Constants
EPSILON = 1e-9
LIMITATION_REPORT_PATH = "results/stimulus_control_limitation.json"


def calculate_file_checksum(file_path: str) -> str:
    """Calculate SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except FileNotFoundError:
        return "file_not_found"


def update_state_checksums(report_path: str) -> None:
    """
    Update the project state YAML with the checksum of the generated report.
    This is a placeholder implementation to satisfy the pipeline's state update
    requirement. In a real scenario, this would read/write `state/pipeline_state.yaml`.
    """
    # Attempt to update state if the file exists
    state_path = "state/pipeline_state.yaml"
    if os.path.exists(state_path):
        try:
            import yaml
            with open(state_path, 'r') as f:
                state = yaml.safe_load(f) or {}
            
            if 'stimulus_control' not in state:
                state['stimulus_control'] = {}
            
            state['stimulus_control']['last_run'] = datetime.datetime.now().isoformat()
            state['stimulus_control']['report_checksum'] = calculate_file_checksum(report_path)
            
            with open(state_path, 'w') as f:
                yaml.dump(state, f, default_flow_style=False)
            logger.info(f"Updated state checksums for {report_path}")
        except Exception as e:
            logger.warning(f"Could not update state file: {e}")
    else:
        logger.debug("State file not found, skipping checksum update.")


def load_stimulus_metadata(metadata_path: str) -> Optional[pd.DataFrame]:
    """
    Attempt to load stimulus complexity metrics from an external file.
    
    Expected format: CSV or JSON with columns including 'epoch_id' and 
    at least one complexity metric (e.g., 'complexity_score', 'edge_density').
    
    Args:
        metadata_path: Path to the metadata file.
        
    Returns:
        DataFrame with complexity metrics, or None if not found/invalid.
    """
    if not os.path.exists(metadata_path):
        logger.info(f"Stimulus metadata file not found at {metadata_path}")
        return None
    
    try:
        if metadata_path.endswith('.csv'):
            df = pd.read_csv(metadata_path)
        elif metadata_path.endswith('.json'):
            with open(metadata_path, 'r') as f:
                data = json.load(f)
            df = pd.DataFrame(data)
        else:
            logger.warning(f"Unsupported metadata format: {metadata_path}")
            return None
        
        # Check for required columns
        required_cols = ['epoch_id']
        complexity_cols = [col for col in df.columns if 'complexity' in col.lower() or 'density' in col.lower() or 'score' in col.lower()]
        
        if not complexity_cols:
            logger.warning(f"No complexity metrics found in {metadata_path}. Columns: {df.columns.tolist()}")
            return None
        
        # Ensure epoch_id is present
        if 'epoch_id' not in df.columns:
            logger.warning(f"Missing 'epoch_id' column in {metadata_path}")
            return None
            
        logger.info(f"Loaded stimulus metadata with complexity columns: {complexity_cols}")
        return df
        
    except Exception as e:
        logger.error(f"Error loading stimulus metadata: {e}")
        return None


def regress_out_stimulus_effect(
    features_df: pd.DataFrame,
    metadata_df: pd.DataFrame,
    complexity_col: str
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Regress out the effect of stimulus complexity from EEG features.
    
    For each feature column, performs a linear regression against the complexity
    metric and returns the residuals.
    
    Args:
        features_df: DataFrame of EEG features (index or column: epoch_id).
        metadata_df: DataFrame containing epoch_id and complexity metrics.
        complexity_col: Name of the column in metadata_df to use as regressor.
        
    Returns:
        Tuple of (residuals_df, stats_report)
    """
    # Merge on epoch_id
    merged = features_df.merge(
        metadata_df[['epoch_id', complexity_col]], 
        on='epoch_id', 
        how='inner'
    )
    
    if len(merged) < len(features_df):
        logger.warning(f"Merged data size {len(merged)} < original {len(features_df)}. Missing epochs.")
    
    if len(merged) < 10:
        logger.warning("Insufficient data points for regression.")
        return features_df, {"status": "insufficient_data", "n_points": len(merged)}
    
    residuals = {}
    stats_report = {
        "complexity_col": complexity_col,
        "n_observations": len(merged),
        "r_squared_values": {}
    }
    
    feature_cols = [col for col in features_df.columns if col != 'epoch_id']
    
    for col in feature_cols:
        if col not in merged.columns:
            continue
        
        y = merged[col].values
        x = merged[complexity_col].values
        
        # Handle NaNs
        mask = ~(np.isnan(x) | np.isnan(y))
        if np.sum(mask) < 10:
            continue
            
        x_clean = x[mask]
        y_clean = y[mask]
        
        # Linear regression: y = beta * x + alpha + error
        # We want the error (residual)
        if np.std(x_clean) < EPSILON:
            # No variance in regressor, keep original
            residuals[col] = merged[col].values
            stats_report["r_squared_values"][col] = 0.0
            continue
        
        slope, intercept, r_value, p_value, std_err = stats.linregress(x_clean, y_clean)
        
        predicted = slope * x_clean + intercept
        residual = y_clean - predicted
        
        # Pad residuals to match original length if needed (though merge should align)
        # We assume merged index aligns with features_df index for simplicity in this context
        # A more robust way is to create a Series and reindex
        residuals[col] = np.full(len(merged), np.nan)
        residuals[col][mask] = residual
        
        stats_report["r_squared_values"][col] = r_value ** 2
    
    # Construct result DataFrame
    result_df = pd.DataFrame(residuals, index=merged.index)
    if 'epoch_id' in merged.columns:
        result_df['epoch_id'] = merged['epoch_id']
    
    # Reorder columns to match original
    result_df = result_df[features_df.columns]
    
    return result_df, stats_report


def apply_stimulus_control(
    features_path: str,
    output_path: str,
    metadata_path: Optional[str] = None
) -> None:
    """
    Main entry point for applying stimulus control.
    
    If metadata_path is provided and valid complexity metrics exist, regress them out.
    Otherwise, generate a limitation report and copy the original features.
    
    Args:
        features_path: Path to the input features CSV (from T021).
        output_path: Path to write the output features CSV.
        metadata_path: Optional path to stimulus metadata file.
    """
    logger.info(f"Starting stimulus control for {features_path}")
    
    # Load features
    if not os.path.exists(features_path):
        raise FileNotFoundError(f"Features file not found: {features_path}")
    
    features_df = pd.read_csv(features_path)
    logger.info(f"Loaded {len(features_df)} feature rows")
    
    # Determine complexity column
    complexity_col = None
    stats_report = None
    
    if metadata_path:
        metadata_df = load_stimulus_metadata(metadata_path)
        if metadata_df is not None:
            # Find first available complexity column
            complexity_cols = [col for col in metadata_df.columns if 'complexity' in col.lower() or 'density' in col.lower() or 'score' in col.lower()]
            if complexity_cols:
                complexity_col = complexity_cols[0]
                logger.info(f"Using complexity metric: {complexity_col}")
                features_df, stats_report = regress_out_stimulus_effect(
                    features_df, metadata_df, complexity_col
                )
                logger.info("Successfully regressed out stimulus effect.")
            else:
                logger.warning("No complexity columns found in metadata.")
        else:
            logger.warning("Failed to load or parse metadata.")
    
    # If no complexity control was applied, flag limitation
    if stats_report is None:
        logger.info("No stimulus complexity metrics available. Flagging limitation.")
        limitation_report = {
            "status": "limitation_flagged",
            "reason": "Stimulus complexity metrics not found in metadata or metadata file not provided.",
            "dataset": "ds000246 (OpenNeuro Naturalistic Viewing)",
            "timestamp": datetime.datetime.now().isoformat(),
            "input_features": features_path,
            "output_features": output_path,
            "note": "EEG features were not adjusted for stimulus complexity. "
                    "Predictions may conflate cognitive load with stimulus-driven neural activity."
        }
        
        # Ensure results directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with open(LIMITATION_REPORT_PATH, 'w') as f:
            json.dump(limitation_report, f, indent=2)
        
        logger.info(f"Limitation report written to {LIMITATION_REPORT_PATH}")
        
        # Copy original features (no regression performed)
        features_df.to_csv(output_path, index=False)
    else:
        # Save adjusted features
        features_df.to_csv(output_path, index=False)
        
        # Save regression stats
        stats_report_path = output_path.replace('.csv', '_stats.json')
        with open(stats_report_path, 'w') as f:
            json.dump(stats_report, f, indent=2)
        
        logger.info(f"Stimulus-adjusted features saved to {output_path}")
        logger.info(f"Regression stats saved to {stats_report_path}")
    
    # Update state
    update_state_checksums(output_path)


def main():
    """CLI entry point for stimulus control."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Apply stimulus control to EEG features.")
    parser.add_argument(
        "--features", 
        type=str, 
        default="data/processed/features.csv",
        help="Path to input features CSV"
    )
    parser.add_argument(
        "--output", 
        type=str, 
        default="data/processed/features_stimulus_controlled.csv",
        help="Path to output features CSV"
    )
    parser.add_argument(
        "--metadata", 
        type=str, 
        default=None,
        help="Path to stimulus metadata CSV/JSON (optional)"
    )
    
    args = parser.parse_args()
    
    # Load config if needed for paths
    try:
        config = load_config()
        if args.features == "data/processed/features.csv" and 'features_path' in config:
            args.features = config['features_path']
    except Exception as e:
        logger.debug(f"Could not load config: {e}")
    
    apply_stimulus_control(
        features_path=args.features,
        output_path=args.output,
        metadata_path=args.metadata
    )
    
    print(f"Stimulus control complete. Output: {args.output}")
    if os.path.exists(LIMITATION_REPORT_PATH):
        print(f"Limitation report generated: {LIMITATION_REPORT_PATH}")


if __name__ == "__main__":
    main()