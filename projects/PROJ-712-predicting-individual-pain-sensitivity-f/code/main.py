"""
Main entry point for the pain sensitivity prediction pipeline.
Orchestrates data loading, preprocessing, feature extraction, and aggregation.
"""
import os
import sys
import logging
from pathlib import Path
import pandas as pd
import numpy as np

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from utils import set_global_seed, setup_logging, measure_duration, assert_duration_limit, record_artifact_hash
from data_loader import EEGDataLoader
from preprocessing import preprocess_all_participants

logger = logging.getLogger(__name__)

def aggregate_features(participant_data: dict, output_path: Path) -> pd.DataFrame:
    """
    Aggregates feature dictionaries from all participants into a single DataFrame.
    
    Args:
        participant_data: Dictionary mapping participant IDs to feature dicts.
        output_path: Path where the final CSV will be saved.
        
    Returns:
        DataFrame containing the aggregated feature matrix.
        
    Raises:
        AssertionError: If the number of columns is not exactly 30.
        ValueError: If NaN values are present in the data.
    """
    if not participant_data:
        raise ValueError("No participant data provided for aggregation.")

    rows = []
    for pid, features in participant_data.items():
        row = {"participant_id": pid}
        row.update(features)
        rows.append(row)

    df = pd.DataFrame(rows)
    
    # Ensure 'participant_id' is first
    cols = ["participant_id"] + [c for c in df.columns if c != "participant_id"]
    df = df[cols]

    # Validate column count
    feature_cols = [c for c in df.columns if c != "participant_id"]
    logger.info(f"Total feature columns detected: {len(feature_cols)}")
    
    # Explicit assertion as per task requirement
    assert len(feature_cols) == 30, (
        f"Feature matrix must have exactly 30 columns. "
        f"Found {len(feature_cols)} columns: {feature_cols}"
    )

    # Ensure column order: mean durations, occurrence rates, transition probs, spectral power
    # Based on T016 definition:
    # 4 mean durations (A, B, C, D)
    # 4 occurrence rates (A, B, C, D)
    # 16 transition probabilities (4x4 flattened)
    # 6 spectral power features (delta, theta, alpha, beta, low-gamma, high-gamma)
    
    expected_order = []
    # Mean Durations
    for map_label in ["A", "B", "C", "D"]:
        expected_order.append(f"mean_duration_{map_label}")
    # Occurrence Rates
    for map_label in ["A", "B", "C", "D"]:
        expected_order.append(f"occurrence_rate_{map_label}")
    # Transition Probabilities (4x4 flattened: row-major)
    for from_map in ["A", "B", "C", "D"]:
        for to_map in ["A", "B", "C", "D"]:
            expected_order.append(f"trans_prob_{from_map}_{to_map}")
    # Spectral Power
    for band in ["delta", "theta", "alpha", "beta", "low_gamma", "high_gamma"]:
        expected_order.append(f"spectral_power_{band}")

    # Verify actual columns match expected
    actual_features = [c for c in df.columns if c != "participant_id"]
    if actual_features != expected_order:
        logger.warning("Column order does not match expected specification. Reordering...")
        # Reorder columns to match expected
        # Ensure all expected columns exist before reordering
        missing_cols = set(expected_order) - set(actual_features)
        if missing_cols:
            raise ValueError(f"Missing expected columns: {missing_cols}")
        
        df = df[["participant_id"] + expected_order]

    # Final check after reordering
    assert list(df.columns) == ["participant_id"] + expected_order, \
        "Column order mismatch after reordering attempt."

    # Check for NaNs
    nan_counts = df.isna().sum()
    total_nans = nan_counts.sum()
    if total_nans > 0:
        raise ValueError(f"Feature matrix contains {total_nans} NaN values: {nan_counts[nan_counts > 0].to_dict()}")

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Save to CSV
    df.to_csv(output_path, index=False)
    logger.info(f"Feature matrix saved to {output_path} with shape {df.shape}")
    
    return df

@measure_duration
def main():
    """Main execution pipeline."""
    set_global_seed(42)
    setup_logging()
    
    logger.info("Starting Pain Sensitivity Prediction Pipeline (T017: Feature Aggregation)")
    
    # Define paths
    raw_data_dir = project_root / "data" / "raw"
    processed_dir = project_root / "data" / "processed"
    output_file = processed_dir / "feature_matrix.csv"
    
    if not raw_data_dir.exists():
        raise FileNotFoundError(f"Raw data directory not found: {raw_data_dir}. "
                                "Please run data ingestion tasks first.")
            
    # Initialize loader
    loader = EEGDataLoader(raw_data_dir)
    
    # Get list of participants (assumes standard BIDS-like or MNE structure)
    # This relies on the data_loader implementation to identify valid subjects
    participant_ids = loader.get_participant_ids()
    
    if not participant_ids:
        raise ValueError("No participants found in raw data directory.")
    
    logger.info(f"Found {len(participant_ids)} participants to process.")
    
    # Preprocess all participants and extract features
    # This function returns a dict: {pid: features_dict}
    participant_features = preprocess_all_participants(participant_ids, loader)
    
    # Aggregate features
    df = aggregate_features(participant_features, output_file)
    
    # Record artifact hash for reproducibility (Constitution Principle III)
    record_artifact_hash(output_file, "feature_matrix")
    
    assert_duration_limit(6 * 3600) # SC-005: < 6 hours
    
    logger.info("Pipeline completed successfully.")
    return df

if __name__ == "__main__":
    main()
