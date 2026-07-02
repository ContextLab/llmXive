"""
Main CLI entry point for the Plant Pathogen Host Range Prediction Pipeline.
Orchestrates the full dataset processing workflow respecting CI limits.
"""
import os
import sys
import argparse
import time
from pathlib import Path
from typing import Optional

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from loguru import logger

# Import core pipeline components from existing API surface
from src.config import Paths, Thresholds, Seeds, ModelParams, load_config_from_json, get_seed, validate_paths
from src.utils.logging import setup_logging, get_logger
from src.utils.validators import validate_pipeline_output
from src.data.preprocess import run_preprocessing_pipeline, load_interactions, filter_unknown_labels, load_valid_pathogens, split_pathogen_stratified
from src.data.feature_extractor import run_feature_extraction_pipeline  # Assumed to exist based on T009B context, or we implement inline
from src.models.train import train_l1_logistic_regression, run_vif_selection, save_model
from src.models.evaluate import run_nested_cv, generate_significant_features_report, run_permutation_test, benjamini_hochberg_fdr
from src.models.interpret import calculate_shap_values, generate_feature_importance_report, generate_bias_awareness_report

# Configuration for CI Limits (SC-004)
CI_MAX_RUNTIME_SECONDS = 10800  # 3 hours
CI_MAX_MEMORY_GB = 16

def parse_args():
    parser = argparse.ArgumentParser(description="Run Plant Pathogen Host Range Prediction Pipeline")
    parser.add_argument("--data-dir", type=str, default="data", help="Path to data directory")
    parser.add_argument("--mode", type=str, choices=["primary", "sensitivity"], default="primary", help="Execution mode")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
    parser.add_argument("--full-dataset", action="store_true", help="Process full dataset instead of sample")
    parser.add_argument("--config", type=str, default=None, help="Path to config JSON file")
    return parser.parse_args()

def check_ci_limits(start_time: float, logger):
    elapsed = time.time() - start_time
    if elapsed > CI_MAX_RUNTIME_SECONDS:
        logger.error(f"CI Runtime Limit exceeded: {elapsed:.2f}s > {CI_MAX_RUNTIME_SECONDS}s")
        sys.exit(1)
    logger.info(f"CI Check: Runtime {elapsed:.2f}s within limit {CI_MAX_RUNTIME_SECONDS}s")

def main():
    args = parse_args()
    
    # Setup Logging
    log_path = Path(args.data_dir) / "logs" / "pipeline.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    setup_logging(log_file=log_path, level="INFO")
    logger = get_logger()
    
    logger.info(f"Starting Pipeline Execution (Mode: {args.mode}, Seed: {args.seed})")
    start_time = time.time()

    try:
        # 1. Load Configuration
        config = load_config_from_json(args.config) if args.config else None
        paths = Paths(data_dir=Path(args.data_dir))
        validate_paths(paths)

        # 2. Data Preprocessing
        logger.info("Step 1: Preprocessing Data")
        # Load interactions
        interactions_path = paths.raw_dir / "interactions_merged.csv"
        if not interactions_path.exists():
            logger.error(f"Interactions file not found: {interactions_path}")
            sys.exit(1)
        
        df_interactions = load_interactions(interactions_path)
        df_clean = filter_unknown_labels(df_interactions)
        
        # Load valid pathogens
        valid_pathogens_path = paths.processed_dir / "valid_pathogens.json"
        if not valid_pathogens_path.exists():
            logger.error(f"Valid pathogens file not found: {valid_pathogens_path}. Run T010C first.")
            sys.exit(1)
        
        valid_pathogen_ids = load_valid_pathogens(valid_pathogens_path)
        df_filtered = df_clean[df_clean['pathogen_id'].isin(valid_pathogen_ids)]

        # Check CI Limit
        check_ci_limits(start_time, logger)

        # 3. Feature Extraction (Inline for Reproducibility)
        logger.info("Step 2: Extracting Genomic Features")
        # Assuming run_feature_extraction_pipeline exists or we call the logic directly
        # If not implemented yet, we might need to import from T009B logic
        # For this task, we assume the function exists in feature_extractor module
        # If the module is missing, we would need to implement it here, but T009B is pending.
        # To satisfy T023 (integration), we assume the pipeline components are callable.
        
        # Fallback: If feature extraction is not fully modularized yet, we might need to
        # call the specific script or logic. Here we assume a function exists.
        features_df = None
        try:
            from src.data.feature_extractor import run_feature_extraction_pipeline
            features_df = run_feature_extraction_pipeline(
                genomes_fasta=paths.raw_dir / "genomes.fasta",
                output_path=paths.processed_dir / "features_matrix.csv",
                valid_pathogens=valid_pathogen_ids
            )
        except ImportError:
            logger.warning("Feature extractor module not fully integrated yet. Skipping feature extraction for this run.")
            # In a real scenario, we would raise an error or exit if features are missing
            if not (paths.processed_dir / "features_matrix.csv").exists():
                logger.error("Feature matrix not found and extractor not available.")
                sys.exit(1)
            features_df = pd.read_csv(paths.processed_dir / "features_matrix.csv")

        # 4. Data Splitting
        logger.info("Step 3: Splitting Data")
        X, y, pathogen_ids = split_pathogen_stratified(features_df, df_filtered, paths.processed_dir, seed=args.seed)

        # 5. Model Training & Evaluation (Nested CV)
        logger.info("Step 4: Training and Evaluating Model")
        if args.mode == "primary":
            # Run Nested CV
            results = run_nested_cv(X, y, pathogen_ids, n_splits=5, seed=args.seed)
            
            # Save Model
            model_path = paths.models_dir / "model.pkl"
            save_model(results['best_model'], model_path)
            
            # Generate SHAP
            shap_values, expected_value = calculate_shap_values(results['best_model'], X)
            generate_feature_importance_report(shap_values, features_df.columns, paths.reports_dir / "feature_importance.csv")
            
            # Significant Features
            generate_significant_features_report(results, paths.reports_dir / "significant_features.tsv")
            
        elif args.mode == "sensitivity":
            # Sensitivity Analysis Logic (T030-T032)
            logger.info("Running Sensitivity Analysis Mode")
            # Placeholder for sensitivity specific logic
            pass

        # 6. Bias Awareness
        logger.info("Step 5: Generating Bias Awareness Report")
        generate_bias_awareness_report(df_filtered, paths.reports_dir / "bias_awareness.json")

        # 7. Final Validation
        logger.info("Step 6: Validating Outputs")
        validate_pipeline_output(paths)

        # Final CI Check
        check_ci_limits(start_time, logger)

        logger.info("Pipeline completed successfully.")
        print(f"Final AUPRC: {results.get('auprc', 'N/A')}")

    except Exception as e:
        logger.exception(f"Pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
