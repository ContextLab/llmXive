"""
Logging module for Random Forest baseline training operations.

This module provides functionality to log training metrics, exclusion counts,
and other operational details to the data/logs directory.

It integrates with the existing logging infrastructure from setup_logging.py
and ensures all baseline training operations are properly recorded.
"""

import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

# Add the code directory to the path for imports
code_dir = Path(__file__).parent.parent
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from setup_logging import setup_logger, log_exclusion_counts, log_training_metrics

# Constants
LOG_DIR = Path("data/logs")
METRICS_FILE = "data/logs/baseline_training_metrics.json"

def ensure_log_directory():
    """Ensure the log directory exists."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)

def log_smiles_exclusion_count(count: int, reason: str = "Invalid SMILES"):
    """
    Log the count of molecules excluded due to invalid SMILES.
    
    Args:
        count: Number of molecules excluded
        reason: Reason for exclusion (default: "Invalid SMILES")
    """
    ensure_log_directory()
    logger = setup_logger("baseline_training")
    
    exclusion_data = {
        "type": "smiles_exclusion",
        "count": count,
        "reason": reason,
        "timestamp": datetime.now().isoformat()
    }
    
    logger.info(f"Excluded {count} molecules due to {reason}")
    
    # Append to exclusion log file
    exclusion_log_path = LOG_DIR / "exclusion_counts.json"
    
    if exclusion_log_path.exists():
        with open(exclusion_log_path, 'r') as f:
            try:
                exclusions = json.load(f)
            except json.JSONDecodeError:
                exclusions = []
    else:
        exclusions = []
    
    exclusions.append(exclusion_data)
    
    with open(exclusion_log_path, 'w') as f:
        json.dump(exclusions, f, indent=2)

def log_data_preprocessing_stats(stats: Dict[str, Any]):
    """
    Log statistics about data preprocessing.
    
    Args:
        stats: Dictionary containing preprocessing statistics
    """
    ensure_log_directory()
    logger = setup_logger("baseline_training")
    
    stats["timestamp"] = datetime.now().isoformat()
    
    log_path = LOG_DIR / "preprocessing_stats.json"
    
    if log_path.exists():
        with open(log_path, 'r') as f:
            try:
                all_stats = json.load(f)
            except json.JSONDecodeError:
                all_stats = []
    else:
        all_stats = []
    
    all_stats.append(stats)
    
    with open(log_path, 'w') as f:
        json.dump(all_stats, f, indent=2)
    
    logger.info(f"Logged preprocessing stats: {stats}")

def log_split_statistics(train_size: int, val_size: int, test_size: int):
    """
    Log the sizes of train, validation, and test splits.
    
    Args:
        train_size: Number of samples in training set
        val_size: Number of samples in validation set
        test_size: Number of samples in test set
    """
    ensure_log_directory()
    logger = setup_logger("baseline_training")
    
    split_data = {
        "type": "split_statistics",
        "train_size": train_size,
        "val_size": val_size,
        "test_size": test_size,
        "total_size": train_size + val_size + test_size,
        "timestamp": datetime.now().isoformat()
    }
    
    logger.info(f"Split statistics - Train: {train_size}, Val: {val_size}, Test: {test_size}")
    
    log_path = LOG_DIR / "split_statistics.json"
    
    if log_path.exists():
        with open(log_path, 'r') as f:
            try:
                splits = json.load(f)
            except json.JSONDecodeError:
                splits = []
    else:
        splits = []
    
    splits.append(split_data)
    
    with open(log_path, 'w') as f:
        json.dump(splits, f, indent=2)

def log_baseline_training_metrics(
    r_squared: float,
    rmse: float,
    mae: Optional[float] = None,
    training_time_seconds: Optional[float] = None,
    n_estimators: int = 100,
    fingerprint_bits: int = 2048,
    fingerprint_radius: int = 2
):
    """
    Log comprehensive metrics from Random Forest baseline training.
    
    Args:
        r_squared: R-squared value on test set
        rmse: Root Mean Square Error on test set
        mae: Mean Absolute Error on test set (optional)
        training_time_seconds: Time taken for training in seconds
        n_estimators: Number of trees in the forest
        fingerprint_bits: Number of bits in Morgan fingerprint
        fingerprint_radius: Radius of Morgan fingerprint
    """
    ensure_log_directory()
    logger = setup_logger("baseline_training")
    
    metrics = {
        "r_squared": r_squared,
        "rmse": rmse,
        "mae": mae,
        "training_time_seconds": training_time_seconds,
        "hyperparameters": {
            "n_estimators": n_estimators,
            "fingerprint_bits": fingerprint_bits,
            "fingerprint_radius": fingerprint_radius
        },
        "timestamp": datetime.now().isoformat()
    }
    
    # Remove None values
    metrics = {k: v for k, v in metrics.items() if v is not None}
    
    logger.info(f"Baseline training completed - R²: {r_squared:.4f}, RMSE: {rmse:.4f}")
    
    # Save to metrics file
    with open(METRICS_FILE, 'w') as f:
        json.dump(metrics, f, indent=2)
    
    # Also log via the standard training metrics function
    log_training_metrics("baseline_rf", metrics)

def log_model_save_operation(model_path: str, model_size_bytes: int):
    """
    Log the model save operation.
    
    Args:
        model_path: Path where model was saved
        model_size_bytes: Size of the saved model file in bytes
    """
    ensure_log_directory()
    logger = setup_logger("baseline_training")
    
    save_data = {
        "type": "model_save",
        "model_path": model_path,
        "model_size_bytes": model_size_bytes,
        "model_size_mb": model_size_bytes / (1024 * 1024),
        "timestamp": datetime.now().isoformat()
    }
    
    logger.info(f"Model saved to {model_path} ({save_data['model_size_mb']:.2f} MB)")
    
    log_path = LOG_DIR / "model_operations.json"
    
    if log_path.exists():
        with open(log_path, 'r') as f:
            try:
                operations = json.load(f)
            except json.JSONDecodeError:
                operations = []
    else:
        operations = []
    
    operations.append(save_data)
    
    with open(log_path, 'w') as f:
        json.dump(operations, f, indent=2)

def main():
    """
    Main function to demonstrate logging operations.
    
    This function can be called to test the logging functionality
    and ensure all log files are properly created.
    """
    print("Testing baseline training logging operations...")
    
    # Test exclusion logging
    log_smiles_exclusion_count(5, "Invalid SMILES")
    log_smiles_exclusion_count(2, "Missing logS value")
    
    # Test preprocessing stats
    log_data_preprocessing_stats({
        "total_molecules": 1128,
        "valid_molecules": 1120,
        "features_extracted": 2048,
        "processing_time_seconds": 12.5
    })
    
    # Test split statistics
    log_split_statistics(800, 160, 168)
    
    # Test training metrics
    log_baseline_training_metrics(
        r_squared=0.85,
        rmse=0.65,
        mae=0.52,
        training_time_seconds=45.3,
        n_estimators=100,
        fingerprint_bits=2048,
        fingerprint_radius=2
    )
    
    # Test model save operation
    log_model_save_operation("models/baseline_rf.pkl", 2500000)
    
    print("All logging operations completed successfully.")
    print(f"Logs written to: {LOG_DIR}")

if __name__ == "__main__":
    main()
