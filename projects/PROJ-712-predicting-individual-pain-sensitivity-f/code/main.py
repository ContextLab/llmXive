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

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from utils import (
    set_global_seed,
    setup_logging,
    measure_duration,
    assert_duration_limit,
)
from data_loader import EEGDataLoader
from preprocessing import preprocess_all_participants
from modeling import run_modeling_pipeline
from diagnostics import run_diagnostics_pipeline
from config import EXPECTED_FEATURE_COLUMNS

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

    # Ensure 'participant_id' is first column
    cols = ["participant_id"] + [c for c in df.columns if c != "participant_id"]
    df = df[cols]

    # ----------------------------------------------------------------------
    # Validation against the canonical feature list defined in config
    # ----------------------------------------------------------------------
    feature_cols = [c for c in df.columns if c != "participant_id"]
    expected_len = len(EXPECTED_FEATURE_COLUMNS)
    if len(feature_cols) != expected_len:
        raise AssertionError(
            f"Feature matrix must have exactly {expected_len} columns. "
            f"Found {len(feature_cols)} columns: {feature_cols}"
        )

    missing = set(EXPECTED_FEATURE_COLUMNS) - set(feature_cols)
    extra = set(feature_cols) - set(EXPECTED_FEATURE_COLUMNS)
    if missing or extra:
        raise AssertionError(
            f"Feature columns mismatch. Missing: {missing}. Unexpected: {extra}."
        )

    ordered_features = [col for col in EXPECTED_FEATURE_COLUMNS if col in df.columns]
    df = df[["participant_id"] + ordered_features]

    assert list(df.columns) == ["participant_id"] + EXPECTED_FEATURE_COLUMNS, (
        "Column order after reordering does not match EXPECTED_FEATURE_COLUMNS."
    )

    total_nans = df.isna().sum().sum()
    if total_nans > 0:
        nan_counts = df.isna().sum()
        raise ValueError(
            f"Feature matrix contains {total_nans} NaN values. "
            f"Details: {nan_counts[nan_counts > 0].to_dict()}"
        )

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

    logger.info("Starting Pain Sensitivity Prediction Pipeline (T014)")

    # Define key directories
    raw_data_dir = project_root / "data" / "raw"
    processed_dir = project_root / "data" / "processed"
    artifacts_dir = project_root / "artifacts"

    feature_matrix_path = processed_dir / "feature_matrix.csv"
    model_result_path = artifacts_dir / "model_result.json"
    diagnostics_report_path = artifacts_dir / "diagnostics_report.md"

    # Ensure required directories exist
    for p in [processed_dir, artifacts_dir]:
        p.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # 1. Preprocessing & Feature Extraction
    # ------------------------------------------------------------------
    logger.info("Step 1: Preprocessing and Feature Extraction")
    if not raw_data_dir.exists():
        raise FileNotFoundError(
            f"Raw data directory not found: {raw_data_dir}. "
            "Please place the OpenNeuro dataset under this path."
        )

    loader = EEGDataLoader(raw_data_dir)
    participant_ids = loader.get_participant_ids()
    if not participant_ids:
        raise ValueError("No participants found in raw data directory.")

    logger.info(f"Found {len(participant_ids)} participants to process.")
    participant_features = preprocess_all_participants(participant_ids, loader)

    # Aggregate and write feature matrix
    df = aggregate_features(participant_features, feature_matrix_path)

    # ------------------------------------------------------------------
    # 2. Modeling (Elastic Net + Nested CV + Permutation + Bootstrap)
    # ------------------------------------------------------------------
    logger.info("Step 2: Running Modeling Pipeline")
    model_results = run_modeling_pipeline(feature_matrix_path, model_result_path)

    # ------------------------------------------------------------------
    # 3. Diagnostics (VIF, Permutation Importance, Sensitivity Analyses)
    # ------------------------------------------------------------------
    logger.info("Step 3: Running Diagnostics Pipeline")
    diagnostics_results = run_diagnostics_pipeline(
        feature_matrix_path,
        model_result_path,
        diagnostics_report_path,
    )

    # ------------------------------------------------------------------
    # 4. Duration Check (SC-005)
    # ------------------------------------------------------------------
    assert_duration_limit(6 * 3600)  # 6 hours in seconds

    logger.info("Pipeline completed successfully.")
    summary = {
        "participants_processed": len(participant_ids),
        "features_extracted": len(EXPECTED_FEATURE_COLUMNS),
        "model_r": model_results.get("r"),
        "model_p_value": model_results.get("p_value"),
        "diagnostics_report": str(diagnostics_report_path),
    }
    logger.info(f"Execution Summary: {summary}")

    # Return summary for potential downstream use
    return summary

if __name__ == "__main__":
    main()
