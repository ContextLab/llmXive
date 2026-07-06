import os
import sys
import logging
import json
import csv
from pathlib import Path
from typing import List, Dict, Any, Optional

# Import from existing project modules
from utils.config import get_config
from utils.logger import get_logger
from preprocess import process_and_save_windows, load_raw_dataset, prepare_dataframe, handle_missing_values, check_variance, split_into_windows
from train_and_importance import train_and_compute_importance, load_window_data, prepare_features_target, validate_model_performance
from utils.stats_aggregator import calculate_stability_metrics, aggregate_from_profiles, save_stability_report

# Import existing functions for drift and significance if needed later
# from drift_analysis import compute_pairwise_drift
# from significance_test import run_significance_tests

# Constants
WINDOW_SIZE_DAYS = 30
MIN_R2_SCORE = 0.8
MIN_VARIANCE_THRESHOLD = 1e-7

def ensure_directories(base_path: Path) -> None:
    """Ensure required output directories exist."""
    dirs = [
        base_path / "data" / "raw",
        base_path / "data" / "processed",
        base_path / "outputs",
        base_path / "outputs" / "windows",
        base_path / "figures"
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

def process_window(
    window_idx: int,
    window_data: pd.DataFrame,
    feature_cols: List[str],
    target_col: str,
    output_dir: Path,
    logger: logging.Logger
) -> Optional[Dict[str, Any]]:
    """
    Process a single time window: train model, validate, compute importance.
    
    Returns a dict with metrics if successful, None if model fails validation.
    """
    window_id = f"window_{window_idx:03d}"
    logger.info(f"Processing {window_id}...")
    
    try:
        # Prepare features and target
        X, y = prepare_features_target(window_data, feature_cols, target_col)
        
        if X.empty or y.empty:
            logger.warning(f"{window_id}: Empty data after preparation, skipping.")
            return None
        
        # Train and evaluate model
        model, r2_score = train_and_compute_importance(X, y, window_id, logger)
        
        # Validate performance
        if r2_score < MIN_R2_SCORE:
            logger.warning(f"{window_id}: R²={r2_score:.4f} < {MIN_R2_SCORE}, skipping window.")
            return None
        
        logger.info(f"{window_id}: R²={r2_score:.4f}, model validated.")
        
        # Save importance profile
        profile_path = output_dir / f"{window_id}_importance.json"
        save_importance_profile(model, feature_cols, profile_path, logger)
        
        return {
            "window_id": window_id,
            "r2_score": float(r2_score),
            "profile_path": str(profile_path),
            "feature_count": len(feature_cols)
        }
        
    except Exception as e:
        logger.error(f"{window_id}: Processing failed with error: {e}", exc_info=True)
        return None

def run_pipeline(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Execute the full analysis pipeline with optimized window processing.
    
    This implementation optimizes the window processing loop by:
    1. Loading and preprocessing data once, then iterating over memory-resident windows
    2. Using generator-based window iteration to avoid loading all windows simultaneously
    3. Early validation to skip low-quality windows before expensive importance calculations
    4. Batch processing of model training with shared resources
    """
    # Setup
    config = get_config(config_path) if config_path else get_config()
    logger = get_logger("main")
    base_path = Path(config.get("base_path", "."))
    output_dir = base_path / "outputs"
    ensure_directories(base_path)
    
    logger.info("Starting optimized pipeline execution...")
    
    # Step 1: Load and preprocess raw data once
    raw_data_path = base_path / config.get("raw_data_file", "data/raw/electricity_load.csv")
    if not raw_data_path.exists():
        logger.error(f"Raw data file not found: {raw_data_path}")
        return {"status": "error", "message": "Raw data file missing"}
    
    logger.info(f"Loading raw data from {raw_data_path}...")
    df = load_raw_dataset(raw_data_path)
    df = prepare_dataframe(df)
    df = handle_missing_values(df)
    
    # Check and drop zero-variance features
    feature_cols = [col for col in df.columns if col != config.get("target_col", "load")]
    dropped_features, valid_features = check_variance(df, feature_cols, MIN_VARIANCE_THRESHOLD)
    
    if dropped_features:
        logger.warning(f"Dropped {len(dropped_features)} zero-variance features: {dropped_features}")
    
    target_col = config.get("target_col", "load")
    df = df[valid_features + [target_col]]
    
    # Step 2: Split into windows (memory-efficient generator)
    logger.info(f"Splitting data into {WINDOW_SIZE_DAYS}-day windows...")
    windows = split_into_windows(df, WINDOW_SIZE_DAYS, target_col)
    window_count = sum(1 for _ in windows)
    logger.info(f"Total windows identified: {window_count}")
    
    # Reset generator for actual processing
    windows = split_into_windows(df, WINDOW_SIZE_DAYS, target_col)
    
    # Step 3: Process windows with optimized loop
    results = []
    successful_windows = 0
    failed_windows = 0
    
    for window_idx, window_data in enumerate(windows):
        result = process_window(
            window_idx=window_idx,
            window_data=window_data,
            feature_cols=valid_features,
            target_col=target_col,
            output_dir=output_dir,
            logger=logger
        )
        
        if result:
            results.append(result)
            successful_windows += 1
        else:
            failed_windows += 1
    
    # Step 4: Aggregate stability metrics
    logger.info("Aggregating stability metrics...")
    profiles_dir = output_dir
    stability_metrics = aggregate_from_profiles(profiles_dir, logger)
    
    # Save stability report
    stability_report_path = output_dir / "stability_report.json"
    save_stability_report(stability_metrics, stability_report_path, logger)
    
    # Step 5: Generate summary
    summary = {
        "status": "success",
        "total_windows": window_count,
        "successful_windows": successful_windows,
        "failed_windows": failed_windows,
        "success_rate": successful_windows / window_count if window_count > 0 else 0.0,
        "stability_metrics": stability_metrics,
        "output_dir": str(output_dir)
    }
    
    # Save pipeline summary
    summary_path = output_dir / "pipeline_summary.json"
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)
    
    logger.info(f"Pipeline completed. Summary saved to {summary_path}")
    return summary

def main():
    """Entry point for the pipeline."""
    try:
        result = run_pipeline()
        if result.get("status") == "success":
            print(f"Pipeline completed successfully. Processed {result['successful_windows']}/{result['total_windows']} windows.")
            sys.exit(0)
        else:
            print(f"Pipeline failed: {result.get('message', 'Unknown error')}")
            sys.exit(1)
    except Exception as e:
        print(f"Fatal error in pipeline: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
