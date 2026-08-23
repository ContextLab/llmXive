import os
import sys
import logging
import argparse
import json
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
import pandas as pd
import numpy as np
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import LeaveOneGroupOut
from sklearn.metrics import r2_score
import resource

# Project local imports
from config import get_config, load_environment
from utils.logging_config import get_logger, log_info_with_context, log_warning_with_context, log_error_with_context
from utils.convex_hull import ConvexHullWrapper

# Initialize logger
logger = get_logger(__name__)

def load_encoded_data() -> pd.DataFrame:
    """Load the encoded alloy data from the processed CSV."""
    config = get_config()
    data_path = Path(config.data_processed_dir) / "encoded_alloys.csv"
    
    if not data_path.exists():
        log_error_with_context(f"Encoded data file not found: {data_path}", logger)
        raise FileNotFoundError(f"Encoded data file not found: {data_path}")
    
    log_info_with_context(f"Loading encoded data from {data_path}", logger)
    df = pd.read_csv(data_path)
    
    # Validate required columns
    required_cols = ['composition', 'bulk_modulus', 'shear_modulus', 'system_id']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        log_error_with_context(f"Missing required columns in encoded data: {missing_cols}", logger)
        raise ValueError(f"Missing required columns: {missing_cols}")
    
    log_info_with_context(f"Loaded {len(df)} alloy entries", logger)
    return df

def prepare_features_targets(df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Separate features and targets for Bulk and Shear moduli."""
    feature_cols = [col for col in df.columns if col not in ['composition', 'bulk_modulus', 'shear_modulus', 'system_id']]
    X = df[feature_cols].values
    y_bulk = df['bulk_modulus'].values
    y_shear = df['shear_modulus'].values
    groups = df['system_id'].values
    return X, y_bulk, y_shear, groups

def train_model(X: np.ndarray, y: np.ndarray, n_jobs: int = 2) -> GradientBoostingRegressor:
    """Train a GradientBoostingRegressor with memory-safe parameters."""
    # Memory-safe parameters: limit depth and subsample to control memory usage
    model = GradientBoostingRegressor(
        n_estimators=100,
        max_depth=5,
        subsample=0.8,
        learning_rate=0.1,
        random_state=42,
        n_jobs=n_jobs
    )
    model.fit(X, y)
    
    # Monitor memory usage
    mem_usage = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024  # Convert to MB
    log_info_with_context(f"Model trained. Peak memory usage: {mem_usage:.2f} MB", logger)
    
    if mem_usage > 7000:  # 7GB limit
        log_warning_with_context(f"Memory usage ({mem_usage:.2f} MB) exceeds recommended limit (7000 MB)", logger)
    
    return model

def run_loso_cv(X: np.ndarray, y_bulk: np.ndarray, y_shear: np.ndarray, groups: np.ndarray) -> Dict[str, Any]:
    """
    Perform Leave-One-System-Out Cross-Validation.
    Returns metrics, held-out test data, and system-level statistics.
    """
    logo = LeaveOneGroupOut()
    bulk_scores = []
    shear_scores = []
    test_indices = []
    test_data_list = []
    system_coverage = {}
    
    log_info_with_context("Starting Leave-One-System-Out Cross-Validation", logger)
    
    for train_idx, test_idx in logo.split(X, y_bulk, groups):
        system_id = groups[test_idx][0]
        
        X_train, X_test = X[train_idx], X[test_idx]
        y_bulk_train, y_bulk_test = y_bulk[train_idx], y_bulk[test_idx]
        y_shear_train, y_shear_test = y_shear[train_idx], y_shear[test_idx]
        
        # Train models
        bulk_model = train_model(X_train, y_bulk_train, n_jobs=2)
        shear_model = train_model(X_train, y_shear_train, n_jobs=2)
        
        # Predict and score
        y_bulk_pred = bulk_model.predict(X_test)
        y_shear_pred = shear_model.predict(X_test)
        
        r2_bulk = r2_score(y_bulk_test, y_bulk_pred)
        r2_shear = r2_score(y_shear_test, y_shear_pred)
        
        bulk_scores.append(r2_bulk)
        shear_scores.append(r2_shear)
        test_indices.append(test_idx)
        
        # Store test data for this fold
        test_data = {
            'system_id': system_id,
            'composition': X[test_idx],
            'bulk_modulus_true': y_bulk_test,
            'bulk_modulus_pred': y_bulk_pred,
            'shear_modulus_true': y_shear_test,
            'shear_modulus_pred': y_shear_pred,
            'r2_bulk': r2_bulk,
            'r2_shear': r2_shear
        }
        test_data_list.append(test_data)
        
        # Track system coverage
        if system_id not in system_coverage:
            system_coverage[system_id] = {'seen': False, 'held_out': True}
        else:
            system_coverage[system_id]['seen'] = False  # This system was held out in this fold
    
    # Calculate aggregate metrics
    mean_r2_bulk = np.mean(bulk_scores)
    mean_r2_shear = np.mean(shear_scores)
    std_r2_bulk = np.std(bulk_scores)
    std_r2_shear = np.std(shear_scores)
    
    log_info_with_context(f"LOSO-CV Results - Bulk R²: {mean_r2_bulk:.4f} (±{std_r2_bulk:.4f})", logger)
    log_info_with_context(f"LOSO-CV Results - Shear R²: {mean_r2_shear:.4f} (±{std_r2_shear:.4f})", logger)
    
    return {
        'mean_r2_bulk': mean_r2_bulk,
        'mean_r2_shear': mean_r2_shear,
        'std_r2_bulk': std_r2_bulk,
        'std_r2_shear': std_r2_shear,
        'bulk_scores': bulk_scores,
        'shear_scores': shear_scores,
        'test_data': test_data_list,
        'system_coverage': system_coverage,
        'total_systems': len(set(groups))
    }

def calculate_uncertainty(loso_results: Dict[str, Any]) -> Dict[str, float]:
    """Calculate uncertainty metrics from LOSO-CV results."""
    uncertainty = {
        'bulk_variance': np.var(loso_results['bulk_scores']),
        'shear_variance': np.var(loso_results['shear_scores']),
        'bulk_std': loso_results['std_r2_bulk'],
        'shear_std': loso_results['std_r2_shear']
    }
    return uncertainty

def save_metrics(metrics: Dict[str, Any], output_path: Path):
    """Save validation metrics to JSON."""
    # Convert numpy types to Python types for JSON serialization
    serializable_metrics = {}
    for key, value in metrics.items():
        if isinstance(value, (np.integer, np.floating)):
            serializable_metrics[key] = float(value)
        elif isinstance(value, np.ndarray):
            serializable_metrics[key] = value.tolist()
        elif isinstance(value, dict):
            serializable_metrics[key] = {
                k: float(v) if isinstance(v, (np.integer, np.floating)) else v 
                for k, v in value.items()
            }
        else:
            serializable_metrics[key] = value
    
    with open(output_path, 'w') as f:
        json.dump(serializable_metrics, f, indent=2)
    
    log_info_with_context(f"Validation metrics saved to {output_path}", logger)

def save_models(bulk_model: GradientBoostingRegressor, shear_model: GradientBoostingRegressor, output_dir: Path):
    """Save trained models using joblib (not included in requirements, so we'll save as pickle-compatible format)."""
    import pickle
    
    bulk_path = output_dir / "bulk_modulus_model.pkl"
    shear_path = output_dir / "shear_modulus_model.pkl"
    
    with open(bulk_path, 'wb') as f:
        pickle.dump(bulk_model, f)
    with open(shear_path, 'wb') as f:
        pickle.dump(shear_model, f)
    
    log_info_with_context(f"Models saved to {output_dir}", logger)

def generate_loso_test_points_csv(test_data: List[Dict[str, Any]], output_path: Path):
    """Generate CSV file containing held-out test data from LOSO-CV."""
    rows = []
    for fold_data in test_data:
        system_id = fold_data['system_id']
        for i in range(len(fold_data['composition'])):
            row = {
                'system_id': system_id,
                'bulk_modulus_true': float(fold_data['bulk_modulus_true'][i]),
                'bulk_modulus_pred': float(fold_data['bulk_modulus_pred'][i]),
                'shear_modulus_true': float(fold_data['shear_modulus_true'][i]),
                'shear_modulus_pred': float(fold_data['shear_modulus_pred'][i]),
                'r2_bulk': float(fold_data['r2_bulk']),
                'r2_shear': float(fold_data['r2_shear'])
            }
            rows.append(row)
    
    df = pd.DataFrame(rows)
    df.to_csv(output_path, index=False)
    log_info_with_context(f"LOSO test points saved to {output_path}", logger)

def generate_validation_report(loso_results: Dict[str, Any], uncertainty: Dict[str, float]) -> Dict[str, Any]:
    """Generate comprehensive validation report."""
    # Determine if regions are unreliable based on R² threshold (0.6 as per spec)
    mean_r2_bulk = loso_results['mean_r2_bulk']
    mean_r2_shear = loso_results['mean_r2_shear']
    
    unreliable_bulk = mean_r2_bulk < 0.6
    unreliable_shear = mean_r2_shear < 0.6
    unreliable = unreliable_bulk or unreliable_shear
    
    # Calculate coverage stats
    total_systems = loso_results['total_systems']
    covered_systems = len(loso_results['system_coverage'])
    
    report = {
        'validation_method': 'Leave-One-System-Out Cross-Validation',
        'total_systems_evaluated': total_systems,
        'mean_r2_bulk': float(mean_r2_bulk),
        'mean_r2_shear': float(mean_r2_shear),
        'std_r2_bulk': float(loso_results['std_r2_bulk']),
        'std_r2_shear': float(loso_results['std_r2_shear']),
        'variance_bulk': float(uncertainty['bulk_variance']),
        'variance_shear': float(uncertainty['shear_variance']),
        'system_coverage_rate': float(covered_systems / total_systems) if total_systems > 0 else 0.0,
        'unreliable_regions_flag': unreliable,
        'unreliable_bulk': unreliable_bulk,
        'unreliable_shear': unreliable_shear,
        'r2_threshold': 0.6,
        'gating_passed': not unreliable
    }
    
    return report

def save_validation_report(report: Dict[str, Any], output_path: Path):
    """Save validation report to JSON."""
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    log_info_with_context(f"Validation report saved to {output_path}", logger)

def run_training_pipeline(config: Dict[str, Any]):
    """Run the full training pipeline including LOSO-CV validation."""
    # Load data
    df = load_encoded_data()
    X, y_bulk, y_shear, groups = prepare_features_targets(df)
    
    log_info_with_context(f"Training on {len(X)} samples across {len(set(groups))} systems", logger)
    
    # Run LOSO-CV
    loso_results = run_loso_cv(X, y_bulk, y_shear, groups)
    
    # Calculate uncertainty
    uncertainty = calculate_uncertainty(loso_results)
    
    # Generate outputs
    output_dir = Path(config.data_processed_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save LOSO test points CSV
    loso_test_points_path = output_dir / "loso_test_points.csv"
    generate_loso_test_points_csv(loso_results['test_data'], loso_test_points_path)
    
    # Generate and save validation report
    validation_report = generate_validation_report(loso_results, uncertainty)
    validation_report_path = output_dir / "model_validation_report.json"
    save_validation_report(validation_report, validation_report_path)
    
    # Train final models on full dataset
    log_info_with_context("Training final models on full dataset", logger)
    bulk_model = train_model(X, y_bulk, n_jobs=2)
    shear_model = train_model(X, y_shear, n_jobs=2)
    
    # Save final models
    save_models(bulk_model, shear_model, output_dir)
    
    # Save metrics
    metrics_path = output_dir / "training_metrics.json"
    save_metrics(loso_results, metrics_path)
    
    # Check gating condition (R² > 0.6)
    if not validation_report['gating_passed']:
        log_error_with_context(
            f"LOSO-CV R² score ({validation_report['mean_r2_bulk']:.4f} bulk, {validation_report['mean_r2_shear']:.4f} shear) "
            f"is below threshold (0.6). Pipeline halted.", 
            logger
        )
        raise RuntimeError("Gating condition failed: R² score below 0.6")
    
    log_info_with_context("Training pipeline completed successfully", logger)
    return validation_report

def main():
    """Main entry point for model training script."""
    # Load environment
    load_environment()
    
    # Parse arguments
    parser = argparse.ArgumentParser(description="Train alloy property models with LOSO-CV validation")
    parser.add_argument("--config", type=str, default="config_default.yaml", help="Path to config file")
    args = parser.parse_args()
    
    # Load config
    config = get_config()
    
    try:
        validation_report = run_training_pipeline(config)
        print(json.dumps(validation_report, indent=2))
    except Exception as e:
        log_error_with_context(f"Training pipeline failed: {str(e)}", logger)
        raise

if __name__ == "__main__":
    main()
