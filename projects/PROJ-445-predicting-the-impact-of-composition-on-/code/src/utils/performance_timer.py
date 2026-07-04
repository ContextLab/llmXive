import os
import sys
import time
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

# Import existing utilities
from src.utils.manifest_manager import register_artifact, load_manifest, save_manifest, MANIFEST_PATH
from src.utils.cpu_compliance import enforce_cpu_mode, validate_cpu_only_model

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
CI_TIME_LIMIT_HOURS = 6
CI_TIME_LIMIT_SECONDS = CI_TIME_LIMIT_HOURS * 3600
CV_FOLDS = 5

def estimate_training_time(
    n_samples: int,
    n_features: int,
    n_trees: int = 100,
    max_depth: int = 6,
    n_folds: int = CV_FOLDS
) -> Dict[str, Any]:
    """
    Estimate training time for Gradient Boosting based on empirical scaling.
    
    Scaling model: Time ~ k * n_samples * n_trees * max_depth * (n_features^0.8)
    Based on typical scikit-learn GradientBoostingRegressor performance on CPU.
    
    Returns:
        Dict with estimated_seconds, estimated_hours, is_within_limit, recommendation
    """
    # Empirical constant derived from typical free-tier runner performance
    # ~0.0001 seconds per sample per tree per feature unit (approximate)
    k = 1.2e-4 
    
    # Calculate base complexity
    complexity = n_samples * n_trees * max_depth * (n_features ** 0.8)
    estimated_seconds = k * complexity * n_folds
    
    estimated_hours = estimated_seconds / 3600
    is_within_limit = estimated_seconds <= CI_TIME_LIMIT_SECONDS
    
    recommendation = "PASS" if is_within_limit else "OPTIMIZE"
    if not is_within_limit:
        recommendation = "Reduce n_trees or max_depth, or use subsample"
    
    return {
        "estimated_seconds": estimated_seconds,
        "estimated_hours": estimated_hours,
        "is_within_limit": is_within_limit,
        "recommendation": recommendation,
        "n_samples": n_samples,
        "n_features": n_features,
        "n_trees": n_trees,
        "max_depth": max_depth,
        "n_folds": n_folds
    }

def run_performance_benchmark(
    data_path: Path,
    output_path: Path,
    n_trees: int = 100,
    max_depth: int = 6,
    n_folds: int = CV_FOLDS
) -> Dict[str, Any]:
    """
    Run a benchmark to measure actual training time for the pipeline.
    
    This function:
    1. Loads the preprocessed data
    2. Runs a timed 5-fold CV training simulation
    3. Records the actual time taken
    4. Compares against the 6-hour limit
    5. Writes results to artifacts/performance_benchmark.json
    
    Args:
        data_path: Path to the preprocessed CSV data
        output_path: Path to write the benchmark results JSON
        n_trees: Number of trees in Gradient Boosting
        max_depth: Maximum depth of trees
        n_folds: Number of CV folds
        
    Returns:
        Dict containing benchmark results
    """
    logger.info(f"Starting performance benchmark for 5-fold CV (limit: {CI_TIME_LIMIT_HOURS}h)")
    
    # Enforce CPU mode
    enforce_cpu_mode()
    
    try:
        import pandas as pd
        import numpy as np
        from sklearn.ensemble import GradientBoostingRegressor
        from sklearn.model_selection import cross_val_time_series_split, KFold
        from sklearn.metrics import mean_squared_error, r2_score
        
        # Load data
        logger.info(f"Loading data from {data_path}")
        if not data_path.exists():
            raise FileNotFoundError(f"Data file not found: {data_path}")
        
        df = pd.read_csv(data_path)
        
        # Identify features and target
        # Expected columns from preprocess.py: mean_coordination_number, 
        # electronegativity_variance, atomic_radius_variance, Tg
        feature_cols = ['mean_coordination_number', 'electronegativity_variance', 'atomic_radius_variance']
        target_col = 'Tg'
        
        # Check if residualized features exist (from T023)
        residualized_cols = [c for c in df.columns if 'residualized' in c.lower()]
        if residualized_cols:
            feature_cols = residualized_cols + feature_cols
            # Remove duplicates while preserving order
            seen = set()
            feature_cols = [x for x in feature_cols if not (x in seen or seen.add(x))]
        
        X = df[feature_cols].dropna().values
        y = df.loc[X.index, target_col].values if hasattr(df, 'loc') else df[target_col].values
          
        # Handle any NaNs that might have slipped through
        mask = ~np.isnan(X).any(axis=1) & ~np.isnan(y)
        X = X[mask]
        y = y[mask]
        
        n_samples = len(X)
        n_features = X.shape[1]
        
        logger.info(f"Dataset: {n_samples} samples, {n_features} features")
        
        # Estimate time first
        estimation = estimate_training_time(n_samples, n_features, n_trees, max_depth, n_folds)
        logger.info(f"Estimated time: {estimation['estimated_hours']:.2f} hours ({estimation['recommendation']})")
        
        # Run actual timed training
        logger.info("Running timed 5-fold CV training...")
        start_time = time.time()
        
        model = GradientBoostingRegressor(
            n_estimators=n_trees,
            max_depth=max_depth,
            random_state=42,
            n_jobs=1  # Force single core for accurate timing
        )
        
        # Perform cross-validation (just fit to measure time, don't store predictions)
        kf = KFold(n_splits=n_folds, shuffle=True, random_state=42)
        
        for train_idx, val_idx in kf.split(X):
            X_train, X_val = X[train_idx], X[val_idx]
            y_train, y_val = y[train_idx], y[val_idx]
            model.fit(X_train, y_train)
            # Optional: quick validation to ensure model works
            # _ = model.score(X_val, y_val)
        
        end_time = time.time()
        actual_time_seconds = end_time - start_time
        actual_time_hours = actual_time_seconds / 3600
        
        is_within_limit = actual_time_seconds <= CI_TIME_LIMIT_SECONDS
        
        # Prepare results
        results = {
            "timestamp": datetime.now().isoformat(),
            "limit_hours": CI_TIME_LIMIT_HOURS,
            "limit_seconds": CI_TIME_LIMIT_SECONDS,
            "actual_seconds": actual_time_seconds,
            "actual_hours": actual_time_hours,
            "is_within_limit": is_within_limit,
            "dataset_stats": {
                "n_samples": n_samples,
                "n_features": n_features
            },
            "model_params": {
                "n_trees": n_trees,
                "max_depth": max_depth,
                "n_folds": n_folds
            },
            "estimation": estimation,
            "status": "PASS" if is_within_limit else "FAIL",
            "message": "Training completed within 6-hour limit." if is_within_limit 
                       else f"Training took {actual_time_hours:.2f}h, exceeding {CI_TIME_LIMIT_HOURS}h limit."
        }
        
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write results
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"Benchmark results written to {output_path}")
        logger.info(f"Status: {results['status']} - {results['message']}")
        
        # Register in manifest
        if MANIFEST_PATH.exists():
            register_artifact(str(output_path), "performance_benchmark")
        
        return results
        
    except Exception as e:
        logger.error(f"Benchmark failed: {str(e)}", exc_info=True)
        error_result = {
            "timestamp": datetime.now().isoformat(),
            "status": "ERROR",
            "error": str(e),
            "message": f"Benchmark failed: {str(e)}"
        }
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(error_result, f, indent=2)
        raise

def main():
    """Main entry point for performance timing task."""
    project_root = Path(__file__).resolve().parent.parent.parent.parent
    data_path = project_root / "data" / "processed" / "preprocessed_data.csv"
    output_path = project_root / "artifacts" / "performance_benchmark.json"
    
    # Allow override via environment variable
    if os.environ.get("DATA_PATH"):
        data_path = Path(os.environ["DATA_PATH"])
    if os.environ.get("OUTPUT_PATH"):
        output_path = Path(os.environ["OUTPUT_PATH"])
        
    logger.info(f"Project root: {project_root}")
    logger.info(f"Data path: {data_path}")
    logger.info(f"Output path: {output_path}")
    
    try:
        results = run_performance_benchmark(data_path, output_path)
        
        if not results["is_within_limit"]:
            logger.warning("Performance limit exceeded. Review recommendations.")
            print("\n" + "="*60)
            print("PERFORMANCE WARNING")
            print("="*60)
            print(f"Estimated: {results['estimation']['estimated_hours']:.2f}h")
            print(f"Actual:    {results['actual_hours']:.2f}h")
            print(f"Limit:     {CI_TIME_LIMIT_HOURS}h")
            print(f"Recommendation: {results['estimation']['recommendation']}")
            print("="*60)
            sys.exit(1)
        
        print("\n" + "="*60)
        print("PERFORMANCE BENCHMARK: PASSED")
        print("="*60)
        print(f"Training time: {results['actual_hours']:.2f}h (Limit: {CI_TIME_LIMIT_HOURS}h)")
        print(f"Status: {results['status']}")
        print("="*60)
        sys.exit(0)
        
    except Exception as e:
        logger.critical(f"Pipeline performance check failed: {e}")
        sys.exit(2)

if __name__ == "__main__":
    main()
