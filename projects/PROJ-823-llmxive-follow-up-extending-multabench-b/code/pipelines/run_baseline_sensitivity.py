"""
Sensitivity analysis script for User Story 1.
Generates frozen embeddings for ALL available datasets using multiple seeds
to assess stability of the baseline generation process.
"""
import os
import sys
import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
import random
import numpy as np
import torch

# Project imports
from config import get_config
from utils.logging import get_logger, log_info, log_warning, log_error, log_debug
from utils.memory_monitor import get_process_memory_mb, memory_limit_context
from embeddings.generator import EmbeddingGenerator
from embeddings.utils import batch_process_embeddings
from embeddings.serializer import serialize_embeddings_to_parquet, generate_run_id
from pipelines.run_baseline import load_dataset_list

logger = get_logger(__name__)

# Configuration for sensitivity analysis
# We use 5 seeds total: the primary seed (42) + 4 additional seeds
ADDITIONAL_SEEDS = [123, 456, 789, 101]
ALL_SEEDS = [42] + ADDITIONAL_SEEDS

def process_dataset_with_seed(
    dataset_info: Dict[str, Any],
    seed: int,
    output_dir: Path,
    generator: EmbeddingGenerator
) -> Dict[str, Any]:
    """
    Process a single dataset with a specific random seed.
    Returns metadata about the processing run.
    """
    dataset_id = dataset_info.get('dataset_id', 'unknown')
    dataset_path = dataset_info.get('path', '')
    
    log_info(logger, f"Processing dataset {dataset_id} with seed {seed}")
    
    # Set seeds for reproducibility
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    
    try:
        # Load data using the existing pipeline logic
        # We assume the generator can handle the loading or we load here
        # For this implementation, we delegate loading to the generator's process method
        # or use a helper similar to run_baseline.py
        
        # Check memory before processing
        mem_before = get_process_memory_mb()
        
        # Process embeddings
        embeddings, metadata = batch_process_embeddings(
            dataset_path=dataset_path,
            generator=generator,
            dataset_id=dataset_id
        )
        
        mem_after = get_process_memory_mb()
        mem_delta = mem_after - mem_before
        
        if embeddings is None or len(embeddings) == 0:
            log_warning(logger, f"No embeddings generated for {dataset_id} with seed {seed}")
            return {
                'dataset_id': dataset_id,
                'seed': seed,
                'status': 'skipped',
                'reason': 'no_data',
                'embeddings_count': 0
            }
        
        # Serialize to parquet
        output_filename = f"embeddings_{dataset_id}_seed_{seed}.parquet"
        output_path = output_dir / output_filename
        
        # Create a unique run_id for this specific seed+dataset combination
        # to ensure deterministic re-computation
        run_id_suffix = f"{seed}_{dataset_id}"
        seed_run_id = generate_run_id(run_id_suffix)
        
        serialize_embeddings_to_parquet(
            embeddings=embeddings,
            metadata=metadata,
            output_path=str(output_path),
            run_id=seed_run_id,
            dataset_id=dataset_id,
            seed=seed
        )
        
        log_info(logger, f"Saved embeddings for {dataset_id} (seed {seed}) to {output_path}")
        
        return {
            'dataset_id': dataset_id,
            'seed': seed,
            'status': 'success',
            'output_file': str(output_path),
            'run_id': seed_run_id,
            'embeddings_count': len(embeddings),
            'memory_delta_mb': mem_delta
        }
        
    except Exception as e:
        log_error(logger, f"Error processing {dataset_id} with seed {seed}: {str(e)}")
        return {
            'dataset_id': dataset_id,
            'seed': seed,
            'status': 'failed',
            'error': str(e)
        }

def main():
    """
    Main entry point for sensitivity analysis.
    Generates embeddings for all datasets using multiple seeds.
    """
    config = get_config()
    output_base_dir = Path(config.get('output_dir', 'data/processed'))
    output_dir = output_base_dir / "sensitivity"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    log_info(logger, f"Sensitivity analysis starting. Output directory: {output_dir}")
    log_info(logger, f"Using seeds: {ALL_SEEDS}")
    
    # Load list of all available datasets
    datasets = load_dataset_list()
    
    if not datasets:
        log_error(logger, "No datasets found to process. Exiting.")
        return 1
    
    log_info(logger, f"Found {len(datasets)} datasets to process")
    
    # Initialize the embedding generator
    # This uses CPU-only mode as per US1 requirements
    generator = EmbeddingGenerator(device='cpu')
    
    results = []
    summary_path = output_dir / "sensitivity_summary.json"
    
    for seed in ALL_SEEDS:
        log_info(logger, f"Starting processing with seed {seed}")
        seed_results = []
        
        for dataset_info in datasets:
            dataset_id = dataset_info.get('dataset_id', 'unknown')
            result = process_dataset_with_seed(
                dataset_info=dataset_info,
                seed=seed,
                output_dir=output_dir,
                generator=generator
            )
            seed_results.append(result)
            results.append(result)
        
        # Save intermediate summary for this seed
        seed_summary = {
            'seed': seed,
            'timestamp': datetime.now().isoformat(),
            'total_datasets': len(datasets),
            'successful': sum(1 for r in seed_results if r['status'] == 'success'),
            'failed': sum(1 for r in seed_results if r['status'] == 'failed'),
            'skipped': sum(1 for r in seed_results if r['status'] == 'skipped'),
            'results': seed_results
        }
        
        seed_summary_path = output_dir / f"sensitivity_summary_seed_{seed}.json"
        with open(seed_summary_path, 'w') as f:
            json.dump(seed_summary, f, indent=2)
        
        log_info(logger, f"Completed seed {seed}: {seed_summary['successful']} success, {seed_summary['failed']} failed, {seed_summary['skipped']} skipped")
    
    # Final summary
    final_summary = {
        'analysis_id': generate_run_id('sensitivity_analysis'),
        'timestamp': datetime.now().isoformat(),
        'seeds_used': ALL_SEEDS,
        'total_datasets': len(datasets),
        'total_runs': len(results),
        'overall_success': sum(1 for r in results if r['status'] == 'success'),
        'overall_failed': sum(1 for r in results if r['status'] == 'failed'),
        'overall_skipped': sum(1 for r in results if r['status'] == 'skipped'),
        'results_by_seed': {}
    }
    
    # Group results by seed for easier consumption by merge script
    for seed in ALL_SEEDS:
        seed_results = [r for r in results if r['seed'] == seed]
        final_summary['results_by_seed'][str(seed)] = seed_results
    
    with open(summary_path, 'w') as f:
        json.dump(final_summary, f, indent=2)
    
    log_info(logger, f"Sensitivity analysis complete. Summary saved to {summary_path}")
    log_info(logger, f"Total successful runs: {final_summary['overall_success']}")
    log_info(logger, f"Total failed runs: {final_summary['overall_failed']}")
    log_info(logger, f"Total skipped runs: {final_summary['overall_skipped']}")
    
    return 0 if final_summary['overall_failed'] == 0 else 1

if __name__ == '__main__':
    sys.exit(main())
