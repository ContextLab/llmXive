"""
Main orchestration entry point for the Plant Stress Resilience pipeline.
Executes the full workflow: Data Generation -> Preprocessing -> Training -> Validation -> Results.
"""
import os
import sys
import argparse
import json
import time
import random
from datetime import datetime

# Add project root to path for imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from data.generator import generate_synthetic_data
from data.ingest import MockAdapter, validate_and_handle_rejection, DataRejectionError
from data.preprocess import (
    check_missing_threshold,
    impute_half_min,
    normalize_tic_and_log,
    aggregate_population
)
from models.train import train_random_forest, train_svm, get_top_features, calculate_metric
from models.validate import (
    lodo_cv,
    cross_stress_eval,
    permutation_test,
    baseline_null_model,
    check_sample_size
)
from utils.logging import get_logger, DataRejectionError as LoggingDataRejectionError
from utils.reproducibility import audit_seed_propagation

logger = get_logger(__name__)


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Plant Stress Resilience Prediction Pipeline")
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility (default: 42)"
    )
    parser.add_argument(
        "--stress-type",
        type=str,
        default="drought",
        choices=["drought", "salinity", "heat", "cold"],
        help="Type of stress to simulate"
    )
    parser.add_argument(
        "--n-samples",
        type=int,
        default=200,
        help="Number of synthetic samples to generate"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/results",
        help="Directory to write results"
    )
    return parser.parse_args()


def run_pipeline(args):
    """
    Execute the full research pipeline.
    1. Generate synthetic data
    2. Preprocess (filter, impute, normalize)
    3. Train models (RF, SVM)
    4. Validate (LODO, Cross-Stress, Permutation)
    5. Write results to JSON
    """
    start_time = time.time()
    logger.info(f"Starting pipeline with seed={args.seed}, stress={args.stress_type}")

    # 1. Reproducibility Audit
    audit_seed_propagation({"seed": args.seed})
    random.seed(args.seed)
    os.environ['PYTHONHASHSEED'] = str(args.seed)

    # Ensure output directories exist
    os.makedirs(args.output_dir, exist_ok=True)
    processed_dir = os.path.join(project_root, "data", "processed")
    os.makedirs(processed_dir, exist_ok=True)

    # 2. Data Generation
    logger.info("Step 1: Generating synthetic data...")
    synthetic_file = generate_synthetic_data(
        n_samples=args.n_samples,
        stress_type=args.stress_type,
        missing_rate=0.05,  # Keep below 10% threshold for success
        seed=args.seed
    )
    logger.info(f"Generated data: {synthetic_file}")

    # 3. Data Ingestion & Validation
    logger.info("Step 2: Ingesting and validating data...")
    adapter = MockAdapter()
    df = adapter.fetch(synthetic_file)

    # Validate missing threshold (must be < 10%)
    try:
        check_missing_threshold(df, threshold=0.10)
    except (DataRejectionError, LoggingDataRejectionError) as e:
        logger.error(f"Data rejected: {e}")
        raise

    # 4. Preprocessing
    logger.info("Step 3: Preprocessing data...")
    # Impute missing values
    df = impute_half_min(df)
    # Normalize TIC and Log transform
    df = normalize_tic_and_log(df)
    # Aggregate if needed (population level)
    df = aggregate_population(df)

    logger.info(f"Preprocessing complete. Shape: {df.shape}")

    # Prepare features (X) and target (y)
    # Assuming 'recovery_index' is the target and other columns are features
    target_col = 'recovery_index'
    if target_col not in df.columns:
        raise ValueError(f"Target column '{target_col}' not found in data. Columns: {df.columns.tolist()}")

    feature_cols = [c for c in df.columns if c not in [target_col, 'sample_id', 'stress_type']]
    X = df[feature_cols].values
    y = df[target_col].values

    logger.info(f"Features: {len(feature_cols)}, Samples: {len(y)}")

    # 5. Model Training
    logger.info("Step 4: Training models...")
    rf_model, rf_metrics = train_random_forest(X, y, cv=5, seed=args.seed)
    svm_model, svm_metrics = train_svm(X, y, cv=5, seed=args.seed)

    # Extract top features
    rf_top_features = get_top_features(rf_model, n=20)
    svm_top_features = get_top_features(svm_model, n=20)

    logger.info(f"RF Metrics: {rf_metrics}")
    logger.info(f"SVM Metrics: {svm_metrics}")

    # 6. Validation
    logger.info("Step 5: Running validation...")
    
    # Check sample size
    check_sample_size(len(y))

    # Baseline Null Model
    baseline_score = baseline_null_model(y)
    
    # Permutation Test (RF)
    logger.info("Running permutation test...")
    p_value = permutation_test(rf_model, X, y, n=100) # Reduced n=100 for speed in quickstart, usually 1000
    
    # Cross-Stress Eval (Simulated with single dataset split for this run)
    # In a real LODO scenario, we would have multiple datasets. 
    # Here we simulate a train/test split by stress vector if available, 
    # or just report that LODO requires multiple datasets.
    lodo_results = None
    cross_stress_results = None
    
    # Since we generated a single dataset, we cannot do true LODO without T009.3 datasets.
    # We log a warning if only one dataset is present.
    logger.warning("Single dataset detected. Skipping full LODO and Cross-Stress validation. "
                   "Requires multiple distinct datasets (T009.3).")

    # 7. Compile Results
    logger.info("Step 6: Compiling results...")
    results = {
        "pipeline_run": {
            "timestamp": datetime.now().isoformat(),
            "seed": args.seed,
            "stress_type": args.stress_type,
            "n_samples": args.n_samples,
            "execution_time_seconds": time.time() - start_time
        },
        "data_summary": {
            "n_features": len(feature_cols),
            "n_samples": int(len(y)),
            "missing_threshold_passed": True
        },
        "models": {
            "random_forest": {
                "metrics": rf_metrics,
                "top_features": [{"feature": f, "importance": float(i)} for f, i in rf_top_features]
            },
            "svm": {
                "metrics": svm_metrics,
                "top_features": [{"feature": f, "importance": float(i)} for f, i in svm_top_features]
            },
            "baseline_null": {
                "r_squared": float(baseline_score)
            }
        },
        "validation": {
            "permutation_test": {
                "p_value": float(p_value),
                "n_permutations": 100
            },
            "lodo_cv": "Skipped (Single Dataset)",
            "cross_stress_eval": "Skipped (Single Dataset)"
        }
    }

    # 8. Write Output
    output_file = os.path.join(args.output_dir, "model_metrics.json")
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

    logger.info(f"Pipeline completed successfully. Results written to: {output_file}")
    return results


def main():
    """Main entry point."""
    args = parse_args()
    try:
        run_pipeline(args)
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
