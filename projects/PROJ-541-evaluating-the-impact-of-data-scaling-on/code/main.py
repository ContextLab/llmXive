"""
Main entry point for the project.
Orchestrates the full pipeline: Ingestion, Scaling, Testing, and Analysis.
"""
import os
import sys
import time
import logging
import csv
import json
from pathlib import Path
from typing import List, Dict, Any, Optional

# Project root path
PROJECT_ROOT = Path(__file__).parent.parent
RESULTS_DIR = PROJECT_ROOT / "results"
DATA_DIR = PROJECT_ROOT / "data"
LOGS_DIR = PROJECT_ROOT / "logs"

# Ensure directories exist
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# Import project modules
from simulation.config import SimulationConfig, get_default_config
from simulation.logger import setup_logger
from simulation.generator import generate_synthetic_data
from preprocessing.ingestion import load_dataset_config, download_dataset, clean_dataset, process_real_world_dataset, get_cleaned_data_path, update_manifest
from preprocessing.scaling import standardize_data, min_max_scale, robust_scale
from analysis.tests import ScalingMethod, TestResult, run_scaled_t_test, run_scaled_anova, run_scaled_chi_squared, run_pipeline
from analysis.metrics import calculate_aggregate_metrics, save_aggregate_metrics, calculate_deviation_summary, fit_synthetic_mixed_effects_model, fit_real_world_mixed_effects_model, generate_summary_report, run_full_analysis_pipeline, generate_comparison_report
from visualization.plots import generate_error_rate_plot

logger = setup_logger("main")


def ensure_directories():
    """Ensures all required project directories exist."""
    dirs = [
        RESULTS_DIR,
        DATA_DIR / "raw",
        DATA_DIR / "scaled",
        DATA_DIR / "scaled" / "standardized",
        DATA_DIR / "scaled" / "minmax",
        DATA_DIR / "scaled" / "robust",
        DATA_DIR / "synthetic",
        DATA_DIR / "metadata",
        LOGS_DIR,
        RESULTS_DIR / "figures"
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
    logger.info("Directories ensured.")


def save_manifest(manifest_data: List[Dict], path: Path):
    """Saves the manifest JSON."""
    with open(path, 'w') as f:
        json.dump(manifest_data, f, indent=2)


def load_manifest(path: Path) -> List[Dict]:
    """Loads the manifest JSON."""
    if not path.exists():
        return []
    with open(path, 'r') as f:
        return json.load(f)


def get_scaling_functions() -> Dict[str, callable]:
    """Returns available scaling functions."""
    return {
        "standardize": standardize_data,
        "min_max": min_max_scale,
        "robust": robust_scale
    }


def run_real_world_ingestion_pipeline():
    """
    Orchestrates the ingestion of real-world datasets as per T034b.
    Reads config from data/config/datasets.yaml, downloads, cleans, and updates manifest.
    """
    logger.info("Starting Real-World Dataset Ingestion Pipeline (T034b)")
    
    config_path = DATA_DIR / "config" / "datasets.yaml"
    manifest_path = DATA_DIR / "metadata" / "manifest.json"
    
    if not config_path.exists():
        logger.error(f"Dataset config not found at {config_path}")
        return
    
    datasets_config = load_dataset_config(str(config_path))
    manifest = load_manifest(manifest_path)
    existing_ids = {item.get('dataset_id') for item in manifest}
    
    for ds_id, metadata in datasets_config.items():
        if ds_id in existing_ids:
            logger.info(f"Skipping {ds_id}: already in manifest.")
            continue
        
        logger.info(f"Processing dataset: {ds_id}")
        try:
            # Download
            raw_path = download_dataset(ds_id, metadata)
            
            # Clean
            cleaned_df, clean_path = clean_dataset(raw_path, ds_id)
            
            # Update manifest
            update_manifest(manifest, ds_id, metadata, raw_path, clean_path, cleaned_df)
            save_manifest(manifest, manifest_path)
            
            logger.info(f"Successfully processed {ds_id}")
        except Exception as e:
            logger.warning(f"Failed to process {ds_id}: {e}")
            # Skip missing datasets with warnings as per T034b
            continue
    
    logger.info("Real-World Ingestion Pipeline finished.")


def run_real_world_scaling_and_testing():
    """
    Reuses scaling and testing pipeline (US2) on real data (T038).
    """
    logger.info("Starting Real-World Scaling and Testing Pipeline (T038)")
    
    manifest_path = DATA_DIR / "metadata" / "manifest.json"
    if not manifest_path.exists():
        logger.error("No manifest found. Run ingestion first.")
        return
    
    manifest = load_manifest(manifest_path)
    scaling_funcs = get_scaling_functions()
    
    results = []
    
    for item in manifest:
        ds_id = item['dataset_id']
        clean_path = Path(item['clean_path'])
        
        if not clean_path.exists():
            logger.warning(f"Clean data not found for {ds_id}")
            continue
        
        df = pd.read_csv(clean_path)
        
        # Assume numeric columns for scaling
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        if len(numeric_cols) < 2:
            logger.warning(f"Not enough numeric columns for {ds_id}")
            continue
        
        # Simple split for testing (first col vs rest)
        target_col = numeric_cols[0]
        features = numeric_cols[1:]
        
        for scale_name, scale_func in scaling_funcs.items():
            try:
                # Prepare data
                X = df[features].values
                y = df[target_col].values
                
                # Scale
                scaled_X = scale_func(X)
                
                # Run test (t-test for simplicity)
                # Note: This is a simplified test for real data
                # In a full pipeline, we might test specific hypotheses
                res = run_scaled_t_test(scaled_X[:, 0], y, scale_name, "t-test")
                results.append(res)
            except Exception as e:
                logger.warning(f"Error testing {ds_id} with {scale_name}: {e}")
    
    # Save results
    results_path = RESULTS_DIR / "real_world_results.csv"
    if results:
        with open(results_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(list(asdict(results[0]).keys()))
            for r in results:
                writer.writerow(list(asdict(r).values()))
        logger.info(f"Real-world results saved to {results_path}")


def main():
    """
    Main entry point.
    Runs the full pipeline:
    1. Ensure directories
    2. Run Real-World Ingestion (T034b)
    3. Run Real-World Scaling & Testing (T038)
    4. Run Analysis (T029, T031, T032)
    """
    logger.info("Starting Main Pipeline")
    ensure_directories()
    
    # T034b: Ingestion
    run_real_world_ingestion_pipeline()
    
    # T038: Scaling & Testing
    run_real_world_scaling_and_testing()
    
    # T029, T031, T032: Analysis
    # These functions are defined in analysis.metrics
    # They expect data in results/ or data/
    run_full_analysis_pipeline()
    
    logger.info("Main Pipeline finished.")


if __name__ == "__main__":
    main()
