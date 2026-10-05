"""
Main entry point for the pain sensitivity prediction pipeline.
Orchestrates data loading, preprocessing, feature extraction, modeling, and diagnostics.
"""
import os
import sys
import logging
import json
from pathlib import Path
import pandas as pd
import numpy as np

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from utils import (
    set_global_seed, 
    setup_logging, 
    measure_duration, 
    assert_duration_limit, 
    record_artifact_hash,
    get_current_timestamp
)
from data_loader import EEGDataLoader
from preprocessing import preprocess_all_participants
from modeling import run_modeling_pipeline
from diagnostics import run_diagnostics_pipeline
from checksums import scan_raw_data_directory, record_checksums_to_state

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
    
    logger.info("Starting Pain Sensitivity Prediction Pipeline (T035: Full Orchestration)")
    
    # Define paths
    raw_data_dir = project_root / "data" / "raw"
    processed_dir = project_root / "data" / "processed"
    artifacts_dir = project_root / "artifacts"
    state_dir = project_root / "state"
    
    feature_matrix_path = processed_dir / "feature_matrix.csv"
    model_result_path = artifacts_dir / "model_result.json"
    diagnostics_report_path = artifacts_dir / "diagnostics_report.md"
    state_file_path = state_dir / "projects" / "PROJ-712-predicting-individual-pain-sensitivity-f.yaml"
    
    # Ensure directories exist
    for p in [processed_dir, artifacts_dir, state_dir, state_dir / "projects"]:
        p.mkdir(parents=True, exist_ok=True)

    # 1. Verify/Record Raw Data Checksums (T004b)
    if raw_data_dir.exists():
        logger.info("Scanning raw data directory for checksums...")
        record_checksums_to_state(raw_data_dir, state_file_path)
    else:
        logger.warning(f"Raw data directory not found: {raw_data_dir}. Skipping checksums.")

    # 2. Preprocessing & Feature Extraction (US1)
    logger.info("Step 1: Preprocessing and Feature Extraction...")
    if not raw_data_dir.exists():
        raise FileNotFoundError(f"Raw data directory not found: {raw_data_dir}. "
                                "Please run data ingestion tasks first.")
            
    loader = EEGDataLoader(raw_data_dir)
    participant_ids = loader.get_participant_ids()
    
    if not participant_ids:
        raise ValueError("No participants found in raw data directory.")
    
    logger.info(f"Found {len(participant_ids)} participants to process.")
    participant_features = preprocess_all_participants(participant_ids, loader)
    
    # Aggregate features
    df = aggregate_features(participant_features, feature_matrix_path)
    
    # Record artifact hash for feature matrix
    record_artifact_hash(feature_matrix_path, "feature_matrix")

    # 3. Modeling (US2)
    logger.info("Step 2: Running Modeling Pipeline (Elastic Net + Permutation + Bootstrap)...")
    model_results = run_modeling_pipeline(feature_matrix_path, model_result_path)
    
    # Record artifact hash for model results
    record_artifact_hash(model_result_path, "model_result")

    # 4. Diagnostics (US3)
    logger.info("Step 3: Running Diagnostics Pipeline (FDR, VIF, Sensitivity)...")
    diagnostics_results = run_diagnostics_pipeline(
        feature_matrix_path, 
        model_result_path, 
        diagnostics_report_path
    )
    
    # Record artifact hash for diagnostics report
    record_artifact_hash(diagnostics_report_path, "diagnostics_report")

    # 5. Final Timing Check
    # The @measure_duration decorator on main() captures the start time.
    # We call assert_duration_limit at the very end to enforce SC-005.
    assert_duration_limit(6 * 3600)  # 6 hours in seconds
    
    logger.info("Pipeline completed successfully. All artifacts generated.")
    
    # Log summary
    summary = {
        "participants_processed": len(participant_ids),
        "features_extracted": 30,
        "model_r": model_results.get("r"),
        "model_p_value": model_results.get("p_value"),
        "diagnostics_report": str(diagnostics_report_path)
    }
    logger.info(f"Execution Summary: {summary}")
    
    return summary

if __name__ == "__main__":
    main()