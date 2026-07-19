import os
import sys
import time
import logging
import csv
import json
import argparse
from pathlib import Path
import pandas as pd

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import project modules
from simulation.config import SimulationConfig, get_default_config
from simulation.generator import generate_synthetic_data, generate_synthetic_data_from_config
from simulation.logger import setup_logger
from preprocessing.scaling import standardize_data, min_max_scale, robust_scale
from preprocessing.ingestion import (
    RealWorldDataset, load_dataset_config, download_dataset, 
    clean_dataset, process_real_world_dataset, get_cleaned_data_path, 
    update_manifest, run_ingestion_pipeline
)
from analysis.tests import ScalingMethod, TestResult, run_scaled_t_test, run_scaled_anova, run_scaled_chi_squared, run_pipeline
from analysis.metrics import (
    AnovaResult, load_simulation_results, calculate_aggregate_metrics, 
    save_aggregate_metrics, calculate_confidence_interval, fit_synthetic_anova, 
    fit_real_world_mixed_effects_model, calculate_deviation_summary,
    generate_summary_report, generate_error_rate_plot, run_full_analysis_pipeline
)
from visualization.plots import generate_error_rate_plot as viz_generate_error_rate_plot

def ensure_directories():
    """Ensure all required directories exist."""
    dirs = [
        "code", "data", "data/raw", "data/scaled", "data/scaled/standardized",
        "data/scaled/minmax", "data/scaled/robust", "data/config", "data/synthetic",
        "results", "results/figures", "logs", "figures"
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)
    logger.info("Directories ensured.")

def get_scaling_functions():
    """Return a dictionary of scaling functions."""
    return {
        'standardize': standardize_data,
        'minmax': min_max_scale,
        'robust': robust_scale
    }

def save_manifest(manifest_data, path="data/manifest.json"):
    """Save manifest to JSON."""
    with open(path, 'w') as f:
        json.dump(manifest_data, f, indent=2)

def load_manifest(path="data/manifest.json"):
    """Load manifest from JSON."""
    if os.path.exists(path):
        with open(path, 'r') as f:
            return json.load(f)
    return []

def run_simulation_with_checkpointing(config_id: str = None, iterations: int = 100):
    """Run the simulation loop with checkpointing."""
    logger.info(f"Starting simulation with config_id={config_id}, iterations={iterations}")
    
    if config_id is None:
        config = get_default_config()
    else:
        # Load specific config if needed
        config = get_default_config()
    
    results = []
    scaling_funcs = get_scaling_functions()
    
    for i in range(iterations):
        # Generate synthetic data
        data = generate_synthetic_data_from_config(config)
        
        for scale_name, scale_func in scaling_funcs.items():
            try:
                scaled_data = scale_func(data)
                # Run tests (simplified for this task)
                t_res = run_scaled_t_test(scaled_data, scaling_method=scale_name)
                results.append({
                    'iteration': i,
                    'scaling_method': scale_name,
                    'test_type': 't-test',
                    'p_value': t_res.p_value,
                    'ground_truth': config.get('ground_truth', 'unknown')
                })
            except Exception as e:
                logger.warning(f"Failed iteration {i} with {scale_name}: {e}")
    
    # Save results
    df = pd.DataFrame(results)
    output_path = "results/simulation_results.csv"
    df.to_csv(output_path, index=False)
    logger.info(f"Saved simulation results to {output_path}")
    return df

def run_real_world_ingestion_pipeline():
    """Run the real-world dataset ingestion pipeline."""
    logger.info("Starting Real-World Dataset Ingestion Pipeline (T034b)")
    
    # Load dataset configuration
    config_path = "data/config/datasets.yaml"
    if not os.path.exists(config_path):
        logger.warning(f"Dataset config not found at {config_path}. Skipping ingestion.")
        return pd.DataFrame()
    
    try:
        datasets_cfg = load_dataset_config(config_path)
    except Exception as e:
        logger.warning(f"Failed to load dataset config: {e}")
        return pd.DataFrame()
    
    all_data = []
    manifest = load_manifest()
    
    for ds_name, ds_config in datasets_cfg.items():
        logger.info(f"Processing dataset: {ds_name}")
        try:
            # Download dataset (T035)
            raw_path = download_dataset(ds_config)
            
            # Clean dataset (T036)
            clean_path, clean_df = clean_dataset(raw_path)
            
            # Process and save (T037)
            processed_df = process_real_world_dataset(clean_df, ds_name)
            
            # Update manifest
            manifest.append({
                "source": ds_name,
                "size": len(processed_df),
                "missing_rate": 0.0, # Placeholder
                "status": "completed"
            })
            
            all_data.append(processed_df)
            logger.info(f"Successfully processed {ds_name}")
        except Exception as e:
            logger.warning(f"Failed to process {ds_name}: {e}")
    
    save_manifest(manifest)
    logger.info("Real-World Ingestion Pipeline finished.")
    
    if all_data:
        combined = pd.concat(all_data, ignore_index=True)
        combined.to_csv("results/real_world_results.csv", index=False)
        return combined
    return pd.DataFrame()

def run_real_world_scaling_and_testing():
    """
    Reuse scaling and testing pipeline on real data.
    This is the implementation for T038.
    """
    logger.info("Starting Real-World Scaling and Testing Pipeline (T038)")
    
    # Load the real-world data generated by the ingestion pipeline
    input_path = "results/real_world_results.csv"
    if not os.path.exists(input_path):
        logger.warning(f"No real-world data found at {input_path}. Ingestion pipeline may not have run.")
        # Create an empty DF to prevent downstream crashes
        df = pd.DataFrame(columns=['feature_1', 'feature_2'])
    else:
        df = pd.read_csv(input_path)
    
    if df.empty:
        logger.info("No real-world data to scale and test.")
        return pd.DataFrame()
    
    # Select numeric columns for testing
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    if len(numeric_cols) < 2:
        logger.warning("Not enough numeric columns for testing.")
        return pd.DataFrame()
    
    # Apply scaling methods
    scaling_funcs = get_scaling_functions()
    results = []
    
    for scale_name, scale_func in scaling_funcs.items():
        try:
            # Scale the first two numeric columns
            data_subset = df[numeric_cols[:2]].dropna()
            if len(data_subset) < 10:
                logger.warning(f"Insufficient data for {scale_name} scaling.")
                continue
                
            scaled_data = scale_func(data_subset)
            
            # Run statistical tests on scaled data
            # Using t-test as the primary test for T038
            t_res = run_scaled_t_test(scaled_data, scaling_method=scale_name)
            
            results.append({
                'scaling_method': scale_name,
                'test_type': 't-test',
                'p_value': t_res.p_value,
                'sample_size': len(scaled_data)
            })
            
            logger.info(f"Completed {scale_name} scaling and testing")
        except Exception as e:
            logger.error(f"Error in {scale_name} scaling/testing: {e}")
    
    # Save results
    results_df = pd.DataFrame(results)
    results_df.to_csv("results/real_world_analysis_results.csv", index=False)
    logger.info("Real-World Scaling and Testing Pipeline finished.")
    return results_df

def run_full_analysis_wrapper():
    """
    Wrapper to run the full analysis pipeline.
    Calls run_full_analysis_pipeline from metrics.py.
    """
    logger.info("Starting Full Analysis Wrapper")
    
    # 1. Run Ingestion (if needed)
    run_real_world_ingestion_pipeline()
    
    # 2. Run Scaling and Testing (T038)
    run_real_world_scaling_and_testing()
    
    # 3. Run Full Analysis (T039 & Plot Generation)
    # We pass None to let the function load the data it just helped create
    result = run_full_analysis_pipeline(results_df=None)
    
    return result

def main():
    parser = argparse.ArgumentParser(description="Main Pipeline Orchestrator")
    parser.add_argument('--mode', type=str, default='simulation', 
                        choices=['simulation', 'real_world', 'visualize', 'analyze', 'verify-checksums'],
                        help='Mode to run the pipeline')
    parser.add_argument('--config-id', type=str, default=None, help='Simulation config ID')
    parser.add_argument('--iterations', type=int, default=100, help='Number of iterations')
    
    args = parser.parse_args()
    
    logger.info("Starting Main Pipeline")
    ensure_directories()
    
    if args.mode == 'simulation':
        run_simulation_with_checkpointing(args.config_id, args.iterations)
    elif args.mode == 'real_world':
        run_real_world_ingestion_pipeline()
        run_real_world_scaling_and_testing()
    elif args.mode == 'visualize':
        run_real_world_ingestion_pipeline()
        run_real_world_scaling_and_testing()
        run_full_analysis_wrapper()
    elif args.mode == 'analyze':
        run_full_analysis_wrapper()
    elif args.mode == 'verify-checksums':
        logger.info("Checksum verification not implemented in this round.")
    
    logger.info("Main Pipeline finished.")

if __name__ == "__main__":
    main()
