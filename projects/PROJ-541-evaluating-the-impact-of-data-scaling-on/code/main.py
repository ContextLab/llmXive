import os
import sys
import time
import logging
import csv
import json
import argparse
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import project modules
from simulation.config import get_default_config
from simulation.generator import generate_synthetic_data
from simulation.logger import setup_logger
from preprocessing.scaling import standardize_data, min_max_scale, robust_scale
from preprocessing.ingestion import (
    load_dataset_config, download_dataset, clean_dataset, 
    process_real_world_dataset, get_cleaned_data_path, update_manifest,
    run_ingestion_pipeline
)
from analysis.tests import run_scaled_t_test, run_scaled_anova, run_scaled_chi_squared, run_pipeline
from analysis.metrics import (
    load_simulation_results, calculate_aggregate_metrics, save_aggregate_metrics,
    fit_synthetic_anova, calculate_deviation_summary, generate_summary_report,
    generate_error_rate_plot, run_full_analysis_pipeline
)
from simulation.persistence import save_synthetic_data

def ensure_directories():
    """Ensure all required directories exist."""
    dirs = [
        "code", "data", "results", "logs",
        "code/simulation", "code/preprocessing", "code/analysis", "code/visualization",
        "data/raw", "data/scaled", "data/config", "data/synthetic", "data/metadata",
        "results/figures", "data/scaled/standardized", "data/scaled/minmax", "data/scaled/robust"
    ]
    for d in dirs:
        Path(d).mkdir(parents=True, exist_ok=True)
    logger.info("Directories ensured.")

def save_manifest(manifest: Dict[str, Any], filepath: str = "data/metadata/manifest.json"):
    """Save manifest to JSON file."""
    with open(filepath, 'w') as f:
        json.dump(manifest, f, indent=2)
    logger.info(f"Manifest saved to {filepath}")

def load_manifest(filepath: str = "data/metadata/manifest.json") -> Dict[str, Any]:
    """Load manifest from JSON file."""
    if os.path.exists(filepath):
        with open(filepath, 'r') as f:
            return json.load(f)
    return {}

def get_scaling_functions() -> Dict[str, callable]:
    """Return dictionary of scaling functions."""
    return {
        'standardize': standardize_data,
        'minmax': min_max_scale,
        'robust': robust_scale
    }

def run_simulation_with_checkpointing(
    config_id: str = "default",
    iterations: int = 10000,
    batch_size: int = 100
):
    """
    Run simulation loop with checkpointing.
    
    Args:
        config_id: Identifier for the configuration
        iterations: Number of iterations to run
        batch_size: Number of iterations per batch
    """
    logger.info(f"Starting simulation with {iterations} iterations...")
    
    config = get_default_config()
    config['batch_id'] = config_id
    config['seed'] = 42  # Fixed seed for reproducibility
    
    results = []
    start_time = time.time()
    max_runtime = 5.5 * 3600  # 5.5 hours in seconds
    
    for i in range(iterations):
        # Check runtime
        if time.time() - start_time > max_runtime:
            logger.warning(f"Runtime exceeded {max_runtime}s. Saving checkpoint and stopping.")
            break
        
        # Generate synthetic data
        try:
            data, ground_truth = generate_synthetic_data(config)
            
            # Run tests
            for scaling_name, scale_func in get_scaling_functions().items():
                try:
                    scaled_data = scale_func(data)
                    test_results = run_pipeline(scaled_data, ground_truth)
                    
                    for test_type, result in test_results.items():
                        results.append({
                            'iteration_id': i,
                            'seed': config['seed'],
                            'scaling_method': scaling_name,
                            'test_type': test_type,
                            'p_value': result['p_value'],
                            't_statistic': result.get('t_statistic'),
                            'f_statistic': result.get('f_statistic'),
                            'chi2_statistic': result.get('chi2_statistic'),
                            'ground_truth_label': ground_truth
                        })
                except Exception as e:
                    logger.warning(f"Error in scaling {scaling_name}: {e}")
                    continue
                    
        except Exception as e:
            logger.warning(f"Error in generation iteration {i}: {e}")
            continue
        
        # Checkpoint every batch_size iterations
        if (i + 1) % batch_size == 0:
            # Save partial results
            df = pd.DataFrame(results)
            df.to_csv(f"results/simulation_results_{config_id}_partial.csv", index=False)
            logger.info(f"Checkpoint saved at iteration {i + 1}")
    
    # Save final results
    if results:
        df = pd.DataFrame(results)
        df.to_csv("results/simulation_results.csv", index=False)
        logger.info(f"Simulation completed. {len(results)} results saved.")
    else:
        logger.warning("No results generated.")

def run_real_world_ingestion_pipeline():
    """Run the real-world dataset ingestion pipeline."""
    logger.info("Starting Real-World Dataset Ingestion Pipeline (T034b)")
    
    # Load dataset configuration
    config_path = "data/config/datasets.yaml"
    if not os.path.exists(config_path):
        logger.error(f"Dataset config not found: {config_path}")
        return
    
    dataset_configs = load_dataset_config(config_path)
    manifest = load_manifest()
    
    for dataset_info in dataset_configs:
        dataset_id = dataset_info.get('id', 'unknown')
        logger.info(f"Processing dataset: {dataset_id}")
        
        try:
            # Download and clean dataset
            raw_data = download_dataset(dataset_info)
            if raw_data is None:
                logger.warning(f"Failed to download dataset: {dataset_id}")
                manifest[dataset_id] = {
                    'source': dataset_info.get('source', 'unknown'),
                    'size': 0,
                    'missing_rate': 0.0,
                    'status': 'skipped'
                }
                continue
            
            cleaned_data = clean_dataset(raw_data)
            
            # Process and save
            processed_data = process_real_world_dataset(cleaned_data, dataset_id)
            output_path = get_cleaned_data_path(dataset_id)
            processed_data.to_csv(output_path, index=False)
            
            # Update manifest
            manifest[dataset_id] = {
                'source': dataset_info.get('source', 'unknown'),
                'size': len(processed_data),
                'missing_rate': float(processed_data.isnull().sum().sum() / processed_data.size),
                'status': 'success'
            }
            logger.info(f"Successfully processed dataset: {dataset_id}")
            
        except Exception as e:
            logger.warning(f"Failed to process dataset {dataset_id}: {e}")
            if dataset_id not in manifest:
                manifest[dataset_id] = {
                    'source': dataset_info.get('source', 'unknown'),
                    'size': 0,
                    'missing_rate': 0.0,
                    'status': 'skipped'
                }
    
    # Save manifest
    save_manifest(manifest)
    logger.info("Real-World Ingestion Pipeline finished.")

def run_real_world_scaling_and_testing():
    """
    Run scaling and testing on real-world datasets (T038).
    
    This function:
    1. Loads cleaned real-world datasets
    2. Applies scaling methods
    3. Runs statistical tests
    4. Saves results to results/real_world_results.csv
    """
    logger.info("Starting Real-World Scaling and Testing Pipeline (T038)")
    
    # Get manifest of processed datasets
    manifest = load_manifest()
    results = []
    
    for dataset_id, meta in manifest.items():
        if meta.get('status') != 'success':
            continue
        
        # Load cleaned dataset
        input_path = get_cleaned_data_path(dataset_id)
        if not os.path.exists(input_path):
            logger.warning(f"Cleaned data not found for {dataset_id}")
            continue
        
        try:
            df = pd.read_csv(input_path)
            
            # Identify numeric columns for testing
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            if len(numeric_cols) < 2:
                logger.warning(f"Not enough numeric columns for {dataset_id}")
                continue
            
            # Use first two numeric columns for t-test, all for ANOVA
            col1, col2 = numeric_cols[0], numeric_cols[1]
            
            # Prepare data for testing
            group1 = df[col1].dropna()
            group2 = df[col2].dropna()
            
            if len(group1) < 2 or len(group2) < 2:
                logger.warning(f"Insufficient data for {dataset_id}")
                continue
            
            # Test data as a simple DataFrame
            test_data = pd.DataFrame({col1: group1, col2: group2})
            
            # Apply scaling and tests
            for scaling_name, scale_func in get_scaling_functions().items():
                try:
                    scaled_data = scale_func(test_data)
                    
                    # Run t-test
                    t_result = run_scaled_t_test(scaled_data, col1, col2)
                    results.append({
                        'dataset_id': dataset_id,
                        'scaling_method': scaling_name,
                        'test_type': 't-test',
                        'p_value': t_result['p_value'],
                        't_statistic': t_result.get('t_statistic'),
                        'ground_truth_label': 'real_world'
                    })
                    
                    # Run ANOVA if more than 2 columns
                    if len(numeric_cols) > 2:
                        anova_data = scaled_data[numeric_cols[:3]]  # Use first 3 columns
                        anova_result = run_scaled_anova(anova_data)
                        results.append({
                            'dataset_id': dataset_id,
                            'scaling_method': scaling_name,
                            'test_type': 'anova',
                            'p_value': anova_result['p_value'],
                            'f_statistic': anova_result.get('f_statistic'),
                            'ground_truth_label': 'real_world'
                        })
                        
                except Exception as e:
                    logger.warning(f"Error in scaling {scaling_name} for {dataset_id}: {e}")
                    continue
                    
        except Exception as e:
            logger.warning(f"Error processing dataset {dataset_id}: {e}")
            continue
    
    # Save results
    if results:
        df_results = pd.DataFrame(results)
        df_results.to_csv("results/real_world_results.csv", index=False)
        logger.info(f"Real-world results saved: {len(results)} rows")
    else:
        logger.warning("No real-world results generated.")

def main():
    """Main entry point for the pipeline."""
    parser = argparse.ArgumentParser(description="Statistical Test Scaling Analysis Pipeline")
    parser.add_argument('--mode', type=str, default='simulation', 
                      choices=['simulation', 'real_world', 'analyze', 'visualize', 'verify-checksums'],
                      help='Pipeline mode')
    parser.add_argument('--config-id', type=str, default='default', help='Configuration ID')
    parser.add_argument('--iterations', type=int, default=10000, help='Number of iterations')
    
    args = parser.parse_args()
    
    logger.info("Starting Main Pipeline")
    ensure_directories()
    
    if args.mode == 'simulation':
        run_simulation_with_checkpointing(args.config_id, args.iterations)
    elif args.mode == 'real_world':
        run_real_world_ingestion_pipeline()
        run_real_world_scaling_and_testing()
    elif args.mode == 'analyze':
        # Run full analysis pipeline
        run_full_analysis_pipeline(mode='full')
    elif args.mode == 'visualize':
        # Load results and generate plots
        try:
            results_df = load_simulation_results("results/simulation_results.csv")
            metrics_df = calculate_aggregate_metrics(results_df)
            generate_error_rate_plot(metrics_df)
        except FileNotFoundError:
            logger.warning("No results found for visualization")
    elif args.mode == 'verify-checksums':
        # Placeholder for checksum verification
        logger.info("Checksum verification not implemented")
    
    logger.info("Main Pipeline finished")

if __name__ == "__main__":
    main()