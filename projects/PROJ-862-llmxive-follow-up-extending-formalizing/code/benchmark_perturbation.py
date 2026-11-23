"""
Benchmark script for perturbation logic - uses REAL data from dataset, not synthetic.
"""
import torch
import time
import json
import os
import logging
import numpy as np
from typing import Tuple, List, Dict

from config import load_config, ModelConfig
from data_loader import load_reasoning_dataset
from model_utils import load_frozen_model
from perturbation import inject_and_project

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def generate_small_sample_data(config) -> Tuple[torch.Tensor, torch.Tensor]:
    """
    Load a SMALL SAMPLE of the REAL dataset for benchmarking.
    Returns input_ids and embeddings from the actual model.
    """
    logger.info("Loading real dataset sample for benchmarking...")
    
    # Load dataset with streaming to get a small sample
    dataset = load_reasoning_dataset(config)
    
    # Take first 100 samples
    sample_size = min(100, len(dataset))
    sample_data = dataset.select(range(sample_size))
    
    # Load model
    model, tokenizer = load_frozen_model(config.model)
    
    # Get embeddings for sample
    input_ids_list = []
    for item in sample_data:
        input_ids = item['input_token_ids']
        input_ids_list.append(torch.tensor([input_ids], dtype=torch.long))
    
    # Batch process
    batch_input = torch.cat(input_ids_list, dim=0)
    
    with torch.no_grad():
        embeddings = model.get_input_embeddings()(batch_input)
    
    logger.info(f"Generated {embeddings.shape[0]} real samples for benchmarking")
    return batch_input, embeddings

def run_benchmark(config) -> Dict:
    """
    Run benchmark on real data sample.
    Measures time and memory for perturbation at various sigma levels.
    """
    logger.info("Starting perturbation benchmark on real data...")
    
    input_ids, embeddings = generate_small_sample_data(config)
    embedding_matrix = model.get_input_embeddings().weight
    
    results = {
        'sample_size': embeddings.shape[0],
        'dimensions': embeddings.shape[1],
        'benchmarks': []
    }
    
    sigmas = [0.01, 0.05, 0.10, 0.15, 0.20]
    
    for sigma in sigmas:
        logger.info(f"Benchmarking sigma={sigma:.2f}")
        start_time = time.time()
        
        try:
            perturbed_ids, perturbed_embeddings = inject_and_project(
                embeddings, 
                sigma, 
                embedding_matrix
            )
            elapsed = time.time() - start_time
            
            results['benchmarks'].append({
                'sigma': sigma,
                'elapsed_seconds': elapsed,
                'samples_processed': embeddings.shape[0],
                'status': 'success'
            })
            
            logger.info(f"  Completed in {elapsed:.2f}s")
            
        except Exception as e:
            elapsed = time.time() - start_time
            results['benchmarks'].append({
                'sigma': sigma,
                'elapsed_seconds': elapsed,
                'status': 'failed',
                'error': str(e)
            })
            logger.error(f"  Failed: {e}")
    
    return results

def main():
    """Main entry point for benchmark."""
    config = load_config('config/pipeline_config.json')
    
    results = run_benchmark(config)
    
    output_path = 'data/processed/benchmark_results.json'
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Benchmark results saved to {output_path}")

if __name__ == '__main__':
    main()