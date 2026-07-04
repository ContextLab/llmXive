"""
Main entry point for the Feature Importance Drift Analysis pipeline.

Orchestrates the full workflow:
1. Ensures directory structure exists.
2. Iterates through all available time windows in data/processed.
3. For each window:
   - Loads data.
   - Checks feature variance (drops zero-variance features).
   - Trains model and validates R² >= 0.8.
   - Calculates permutation importance.
   - Saves importance profile.
4. Aggregates stability metrics from all valid windows.
5. Generates final reports (importance_profiles.csv, global_stats.json).
"""
import os
import sys
import logging
import json
import csv
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from code.utils.logger import setup_logger, get_logger
from code.utils.config import get_config
from code.utils.stats_aggregator import calculate_stability_metrics, save_stability_report
from code.preprocess import check_variance, load_raw_dataset, prepare_dataframe, handle_missing_values, split_into_windows
from code.train_and_importance import (
    load_window_data, 
    prepare_features_target, 
    train_model, 
    evaluate_model, 
    validate_model_performance, 
    calculate_importance, 
    save_importance_profile
)

# Setup logging
logger = setup_logger("main_pipeline")

def ensure_directories():
    """Ensure required output directories exist."""
    dirs = [
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        project_root / "outputs"
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
    logger.info("Directory structure verified.")

def process_window(window_id: str, window_path: Path) -> Optional[Dict[str, Any]]:
    """
    Process a single time window:
    1. Load data.
    2. Check variance and drop zero-variance features.
    3. Train model and validate R².
    4. Calculate importance.
    5. Save profile.
    
    Returns metadata dict if successful, None if skipped (e.g., R² < 0.8).
    """
    logger.info(f"Processing window: {window_id}")
    
    try:
        # Load window data
        df = load_window_data(window_path)
        
        if df is None or df.empty:
            logger.warning(f"Window {window_id} is empty. Skipping.")
            return None

        # Check variance and drop zero-variance features
        # check_variance returns (df_clean, dropped_features)
        df_clean, dropped_features = check_variance(df)
        
        if len(dropped_features) > 0:
            logger.info(f"Window {window_id}: Dropped {len(dropped_features)} zero-variance features: {dropped_features}")
        
        if df_clean.empty:
            logger.warning(f"Window {window_id} has no features after variance check. Skipping.")
            return None

        # Prepare features and target
        # Assuming the last column is the target based on typical pipeline design
        # or specific logic in prepare_features_target
        X, y, feature_names = prepare_features_target(df_clean)
        
        if X.empty or y.empty:
            logger.warning(f"Window {window_id}: Invalid features/target. Skipping.")
            return None

        # Train model
        model = train_model(X, y)
        
        # Evaluate model
        r2_score = evaluate_model(model, X, y)
        
        # Validate performance (FR-003b: skip if R² < 0.8)
        is_valid, reason = validate_model_performance(r2_score)
        
        if not is_valid:
            logger.warning(f"Window {window_id}: Model failure - {reason} (R²={r2_score:.4f}). Skipping importance calculation.")
            return None

        # Calculate importance
        importance_result = calculate_importance(model, X, y, feature_names)
        
        # Prepare importance data for saving
        importance_data = {
            "window_id": window_id,
            "r2_score": r2_score,
            "dropped_features": dropped_features,
            "importance_scores": importance_result
        }

        # Save individual profile
        output_file = project_root / "outputs" / f"importance_profile_{window_id}.csv"
        save_importance_profile(importance_result, feature_names, output_file)
        
        logger.info(f"Window {window_id} processed successfully. R²={r2_score:.4f}, Saved: {output_file.name}")
        
        return importance_data

    except Exception as e:
        logger.error(f"Error processing window {window_id}: {str(e)}", exc_info=True)
        return None

def run_pipeline():
    """Main pipeline execution loop."""
    logger.info("Starting Feature Importance Drift Analysis Pipeline...")
    
    # 1. Ensure directories
    ensure_directories()
    
    config = get_config()
    data_dir = project_root / "data" / "processed"
    
    if not data_dir.exists():
        logger.error(f"Data directory {data_dir} not found. Run download.py and preprocess.py first.")
        return False

    # 2. Discover windows
    # We expect files named like window_001.csv, window_002.csv, etc.
    window_files = sorted(data_dir.glob("window_*.csv"))
    
    if not window_files:
        logger.error("No window files found in data/processed. Run preprocess.py first.")
        return False
    
    logger.info(f"Found {len(window_files)} windows to process.")
    
    all_profiles = []
    successful_windows = 0
    failed_windows = 0
    total_r2 = 0.0

    # 3. Iterate and process
    for window_path in window_files:
        window_id = window_path.stem # e.g., "window_001"
        result = process_window(window_id, window_path)
        
        if result:
            all_profiles.append(result)
            successful_windows += 1
            total_r2 += result["r2_score"]
        else:
            failed_windows += 1

    # 4. Aggregate and Save Global Results
    if successful_windows > 0:
        # Aggregate importance profiles into a single CSV
        # Format: window_id, feature_name, importance_score, r2_score (optional context)
        profiles_csv_path = project_root / "outputs" / "importance_profiles.csv"
        
        with open(profiles_csv_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["window_id", "feature_name", "importance_score", "r2_score", "dropped_features"])
            
            for profile in all_profiles:
                window_id = profile["window_id"]
                r2 = profile["r2_score"]
                dropped = ";".join(profile["dropped_features"]) if profile["dropped_features"] else ""
                
                # importance_result is a dict {feature_name: score}
                for feat, score in profile["importance_scores"].items():
                    writer.writerow([window_id, feat, score, r2, dropped])
        
        logger.info(f"Saved aggregated importance profiles to {profiles_csv_path}")
        
        # Calculate stability metrics
        # We need to pass the list of valid results to the aggregator
        # The aggregator expects a list of dicts or similar structure
        stability_metrics = calculate_stability_metrics(all_profiles)
        
        # Save stability report
        stability_report_path = project_root / "outputs" / "stability_report.json"
        save_stability_report(stability_metrics, stability_report_path)
        
        logger.info(f"Saved stability report to {stability_report_path}")
        
        # Generate global stats JSON
        global_stats = {
            "total_windows": len(window_files),
            "successful_windows": successful_windows,
            "failed_windows": failed_windows,
            "average_r2": total_r2 / successful_windows if successful_windows > 0 else 0.0,
            "stability_metrics": stability_metrics
        }
        
        global_stats_path = project_root / "outputs" / "global_stats.json"
        with open(global_stats_path, 'w') as f:
            json.dump(global_stats, f, indent=2)
        
        logger.info(f"Saved global stats to {global_stats_path}")
        
        logger.info(f"Pipeline completed. Success: {successful_windows}, Failed: {failed_windows}")
        return True
    else:
        logger.error("No windows were successfully processed. Check logs for errors.")
        return False

def main():
    """Entry point."""
    success = run_pipeline()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
