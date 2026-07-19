import os
import sys
import csv
import json
import logging
import gc
import math
from typing import List, Dict, Any, Optional, Tuple

# Import from local utils
from utils.masking import (
    load_model_layer_by_layer,
    apply_mask_to_layer,
    run_inference_with_masking,
    calculate_sensitivity,
    get_memory_usage_gb
)
from utils.faithfulness_score import (
    compute_batch_faithfulness,
    aggregate_faithfulness_metrics
)
from utils.dataset_loader import load_and_cache_dataset, verify_checksum
from code_00_config import Config, validate_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('data/processed/sensitivity_analysis.log')
    ]
)
logger = logging.getLogger(__name__)

# Constants
DATA_DIR = "data"
PROCESSED_DIR = os.path.join(DATA_DIR, "processed")
RAW_DIR = os.path.join(DATA_DIR, "raw")

def load_sensitivity_results(filepath: str) -> List[Dict[str, Any]]:
    """Load sensitivity results from CSV."""
    results = []
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Sensitivity results file not found: {filepath}")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            results.append({
                'layer_id': int(row['layer_id']),
                'param_id': row['param_id'],
                'sensitivity_score': float(row['sensitivity_score']),
                'original_score': float(row['original_score'])
            })
    return results

def generate_random_mask_indices(total_params: int, mask_fraction: float, seed: int) -> List[int]:
    """Generate random indices for masking."""
    import random
    random.seed(seed)
    num_to_mask = int(total_params * mask_fraction)
    indices = random.sample(range(total_params), num_to_mask)
    return sorted(indices)

def run_single_random_baseline_iteration(
    model, 
    dataset, 
    mask_fraction: float, 
    seed: int,
    iteration_id: int
) -> List[Dict[str, Any]]:
    """Run a single random masking iteration and return faithfulness scores."""
    logger.info(f"Running random baseline iteration {iteration_id}")
    
    # Get total parameter count for this layer
    param_map = {}
    for layer_id, layer in enumerate(model.layers):
        param_count = 0
        for name, param in layer.named_parameters():
            param_count += param.numel()
        param_map[layer_id] = param_count

    results = []
    
    # For each layer, apply random mask
    for layer_id, param_count in param_map.items():
        mask_indices = generate_random_mask_indices(param_count, mask_fraction, seed + layer_id)
        
        # Apply mask and run inference
        masked_score = run_inference_with_masking(
            model, 
            dataset, 
            layer_id, 
            mask_indices,
            param_count
        )
        
        # Record result for each masked parameter
        for idx in mask_indices:
            results.append({
                'iteration_id': iteration_id,
                'layer_id': layer_id,
                'param_id': f"{layer_id}.random.{idx}",
                'faithfulness_score': masked_score
            })
    
    return results

def execute_random_baseline(
    model, 
    dataset, 
    mask_fraction: float, 
    num_iterations: int,
    seed: int
) -> List[List[Dict[str, Any]]]:
    """Execute multiple random baseline iterations."""
    all_results = []
    
    for i in range(num_iterations):
        iteration_results = run_single_random_baseline_iteration(
            model, dataset, mask_fraction, seed, i
        )
        all_results.append(iteration_results)
        logger.info(f"Completed random baseline iteration {i+1}/{num_iterations}")
    
    return all_results

def save_random_baseline_results(results: List[List[Dict[str, Any]]], filepath: str):
    """Save random baseline results to CSV."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['iteration_id', 'layer_id', 'param_id', 'faithfulness_score']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for iteration_results in results:
            for result in iteration_results:
                writer.writerow(result)
    
    logger.info(f"Saved random baseline results to {filepath}")

def load_random_baseline_distribution(baseline_filepath: str) -> Dict[Tuple[int, int], List[float]]:
    """Load random baseline results and compute distribution per layer/param."""
    distribution = {}
    
    if not os.path.exists(baseline_filepath):
        raise FileNotFoundError(f"Random baseline file not found: {baseline_filepath}")
    
    with open(baseline_filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            layer_id = int(row['layer_id'])
            # Extract param_id format: layer_id.param_type.param_index
            param_id_parts = row['param_id'].split('.')
            if len(param_id_parts) >= 3:
                param_type = param_id_parts[1]
                param_index = int(param_id_parts[2])
            else:
                param_index = 0
                param_type = 'unknown'
            
            score = float(row['faithfulness_score'])
            
            key = (layer_id, param_index)
            if key not in distribution:
                distribution[key] = []
            distribution[key].append(score)
    
    return distribution

def calculate_mean(values: List[float]) -> float:
    """Calculate mean of a list of values."""
    if not values:
        return 0.0
    return sum(values) / len(values)

def calculate_std(values: List[float]) -> float:
    """Calculate standard deviation of a list of values."""
    if len(values) < 2:
        return 0.0
    mean = calculate_mean(values)
    variance = sum((x - mean) ** 2 for x in values) / (len(values) - 1)
    return math.sqrt(variance)

def calculate_delta_faithfulness(
    sensitivity_results: List[Dict[str, Any]],
    baseline_distribution: Dict[Tuple[int, int], List[float]]
) -> List[Dict[str, Any]]:
    """
    Calculate delta_faithfulness for each masked configuration relative to 
    the distribution of scores in random_baseline_iterations.csv.
    
    FR-002: Delta is calculated as the difference between the specific masking 
    score and the mean of the random baseline distribution for that parameter.
    """
    updated_results = []
    
    for result in sensitivity_results:
        layer_id = result['layer_id']
        param_id = result['param_id']
        sensitivity_score = result['sensitivity_score']
        
        # Parse param_id to get layer_id and param_index
        param_parts = param_id.split('.')
        if len(param_parts) >= 3:
            param_index = int(param_parts[2])
        else:
            param_index = 0
        
        key = (layer_id, param_index)
        
        if key in baseline_distribution:
            baseline_scores = baseline_distribution[key]
            baseline_mean = calculate_mean(baseline_scores)
            baseline_std = calculate_std(baseline_scores)
            
            # Calculate delta: specific score - mean of random baseline
            delta = sensitivity_score - baseline_mean
            
            updated_results.append({
                'layer_id': layer_id,
                'param_id': param_id,
                'sensitivity_score': sensitivity_score,
                'delta_faithfulness': delta,
                'random_baseline_score': baseline_mean,
                'random_baseline_std': baseline_std,
                'original_score': result.get('original_score', 0.0)
            })
        else:
            # If no baseline distribution found, use original score as fallback
            # This should not happen if baseline was run correctly
            logger.warning(f"No baseline distribution found for {param_id}, using original score")
            updated_results.append({
                'layer_id': layer_id,
                'param_id': param_id,
                'sensitivity_score': sensitivity_score,
                'delta_faithfulness': sensitivity_score - result.get('original_score', 0.0),
                'random_baseline_score': result.get('original_score', 0.0),
                'random_baseline_std': 0.0,
                'original_score': result.get('original_score', 0.0)
            })
    
    return updated_results

def save_delta_results(results: List[Dict[str, Any]], filepath: str):
    """Save delta faithfulness results to CSV."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        fieldnames = [
            'layer_id', 'param_id', 'sensitivity_score', 
            'delta_faithfulness', 'random_baseline_score', 
            'random_baseline_std', 'original_score'
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for result in results:
            writer.writerow(result)
    
    logger.info(f"Saved delta faithfulness results to {filepath}")

def load_model_and_dataset(config: Config):
    """Load model and dataset based on config."""
    logger.info("Loading model and dataset...")
    
    # Load dataset
    dataset_path = os.path.join(RAW_DIR, "occ_rag_corpus.jsonl")
    if not os.path.exists(dataset_path):
        raise FileNotFoundError(f"Dataset not found at {dataset_path}. Please run T004 first.")
    
    dataset = load_and_cache_dataset(dataset_path)
    
    # Load model layer by layer to stay within memory limits
    model_path = config.MODEL_PATH
    model = load_model_layer_by_layer(model_path)
    
    logger.info("Model and dataset loaded successfully")
    return model, dataset

def main():
    """Main function to execute sensitivity analysis with delta calculation."""
    logger.info("Starting sensitivity analysis with delta faithfulness calculation")
    
    # Validate config
    config = Config()
    validate_config(config)
    
    # Load model and dataset
    model, dataset = load_model_and_dataset(config)
    
    # Load sensitivity results from previous run
    sensitivity_results_path = os.path.join(PROCESSED_DIR, "sensitivity_results.csv")
    if not os.path.exists(sensitivity_results_path):
        raise FileNotFoundError(f"Sensitivity results not found at {sensitivity_results_path}. Run T010 first.")
    
    sensitivity_results = load_sensitivity_results(sensitivity_results_path)
    logger.info(f"Loaded {len(sensitivity_results)} sensitivity results")
    
    # Load random baseline distribution
    baseline_filepath = os.path.join(PROCESSED_DIR, "random_baseline_iterations.csv")
    if not os.path.exists(baseline_filepath):
        raise FileNotFoundError(f"Random baseline results not found at {baseline_filepath}. Run T010 first.")
    
    baseline_distribution = load_random_baseline_distribution(baseline_filepath)
    logger.info(f"Loaded baseline distribution for {len(baseline_distribution)} parameters")
    
    # Calculate delta faithfulness
    delta_results = calculate_delta_faithfulness(sensitivity_results, baseline_distribution)
    logger.info(f"Calculated delta faithfulness for {len(delta_results)} parameters")
    
    # Save results
    output_path = os.path.join(PROCESSED_DIR, "sensitivity_results_with_delta.csv")
    save_delta_results(delta_results, output_path)
    
    # Also update the original sensitivity_results.csv with delta column
    final_output_path = os.path.join(PROCESSED_DIR, "sensitivity_results.csv")
    save_delta_results(delta_results, final_output_path)
    
    logger.info("Sensitivity analysis with delta faithfulness calculation completed successfully")
    
    # Clean up
    del model
    del dataset
    gc.collect()
    
    return delta_results

if __name__ == "__main__":
    main()