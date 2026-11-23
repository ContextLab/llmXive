"""
Performance Profiler for Training Loop Memory Footprint.

This script profiles the memory usage of the GNN training loop to identify
memory bottlenecks and verify optimization effectiveness. It uses the
`resource` module for cross-platform memory tracking and integrates with
the existing `performance_optimizer` module to run optimized training.

Outputs:
- code/evaluation/results/memory_profile.json: Detailed memory metrics.
"""

import os
import sys
import json
import time
import logging
import resource
import gc
from typing import Dict, Any, List, Optional

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from data.utils import set_seed, get_seed, setup_logging
from models.gnn import create_gnn_model, polymer_graph_to_pyg_data
from models.trainer import Trainer, create_trainer, EarlyStopping
from data.preprocessing import load_processed_dataset_hdf5, murcko_scaffold_split
from models.baselines import RandomForestBaseline, LinearRegressionBaseline, RandomizedTopologyControlBaseline
from evaluation.metrics import compute_r2, compute_mae, compute_pearson_correlation
from performance_optimizer import run_optimized_training, optimize_environment, FeatureCache

# Setup logging
log_path = os.path.join(project_root, 'logs', 'profiler.log')
os.makedirs(os.path.dirname(log_path), exist_ok=True)
logger = setup_logging(log_path, level=logging.INFO)

RESULTS_DIR = os.path.join(project_root, 'code', 'evaluation', 'results')
os.makedirs(RESULTS_DIR, exist_ok=True)
PROFILE_OUTPUT = os.path.join(RESULTS_DIR, 'memory_profile.json')

def get_memory_usage_mb() -> float:
    """Get current RSS memory usage in MB."""
    usage = resource.getrusage(resource.RUSAGE_SELF)
    # ru_maxrss is in KB on Linux/macOS
    return usage.ru_maxrss / 1024.0

def profile_training_loop(
    use_optimized: bool = False,
    num_epochs: int = 5,
    batch_size: int = 32,
    logger: Optional[logging.Logger] = None
) -> Dict[str, Any]:
    """
    Run a short training loop and profile memory usage.

    Args:
        use_optimized: If True, use the optimized training path from performance_optimizer.
        num_epochs: Number of epochs to run for profiling.
        batch_size: Batch size for DataLoader.
        logger: Logger instance.

    Returns:
        Dictionary containing memory metrics.
    """
    if logger is None:
        logger = logging.getLogger(__name__)

    logger.info(f"Starting {'Optimized' if use_optimized else 'Standard'} training profile...")

    # Load data
    data_path = os.path.join(project_root, 'code', 'data', 'processed', 'polymers.h5')
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Processed dataset not found at {data_path}. Run ingestion/preprocessing first.")

    logger.info(f"Loading dataset from {data_path}")
    dataset = load_processed_dataset_hdf5(data_path)

    # Split data (using scaffold split from T020 if available, otherwise random)
    split_path = os.path.join(project_root, 'code', 'data', 'processed', 'scaffold_split_indices.json')
    if os.path.exists(split_path):
        with open(split_path, 'r') as f:
            splits = json.load(f)
        train_indices = splits['train']
        val_indices = splits['val']
        test_indices = splits['test']
    else:
        logger.warning("Scaffold split not found. Using random split for profiling.")
        import numpy as np
        indices = list(range(len(dataset)))
        np.random.shuffle(indices)
        split_point = int(len(indices) * 0.8)
        train_indices = indices[:split_point]
        val_indices = indices[split_point:split_point + int(len(indices) * 0.1)]
        test_indices = indices[split_point + int(len(indices) * 0.1):]

    logger.info(f"Train: {len(train_indices)}, Val: {len(val_indices)}, Test: {len(test_indices)}")

    # Initialize model
    model = create_gnn_model()
    logger.info(f"Model created. Parameters: {sum(p.numel() for p in model.parameters())}")

    # Memory before training
    gc.collect()
    torch_empty_cache = False
    try:
        import torch
        if hasattr(torch.cuda, 'empty_cache'):
            torch.cuda.empty_cache()
            torch_empty_cache = True
    except ImportError:
        pass

    mem_before = get_memory_usage_mb()
    logger.info(f"Memory before training: {mem_before:.2f} MB")

    # Training loop
    start_time = time.time()

    if use_optimized:
        # Use optimized training path
        logger.info("Running optimized training loop...")
        # Note: run_optimized_training expects specific arguments
        # We wrap it to capture memory
        try:
            metrics = run_optimized_training(
                dataset=dataset,
                train_indices=train_indices,
                val_indices=val_indices,
                test_indices=test_indices,
                epochs=num_epochs,
                batch_size=batch_size,
                logger=logger
            )
        except Exception as e:
            logger.error(f"Optimized training failed: {e}. Falling back to standard.")
            use_optimized = False
            metrics = None

    if not use_optimized:
        logger.info("Running standard training loop...")
        trainer = create_trainer(model, epochs=num_epochs, batch_size=batch_size, logger=logger)
        metrics = trainer.train(
            train_data=dataset,
            train_indices=train_indices,
            val_data=dataset,
            val_indices=val_indices
        )

    end_time = time.time()
    elapsed_time = end_time - start_time

    # Memory after training
    gc.collect()
    if torch_empty_cache:
        try:
            import torch
            torch.cuda.empty_cache()
        except:
            pass

    mem_after = get_memory_usage_mb()
    peak_mem = mem_after  # In simple cases, peak is after training
    mem_delta = mem_after - mem_before

    logger.info(f"Training completed in {elapsed_time:.2f} seconds.")
    logger.info(f"Memory after training: {mem_after:.2f} MB")
    logger.info(f"Memory delta: {mem_delta:.2f} MB")

    return {
        "mode": "optimized" if use_optimized else "standard",
        "epochs": num_epochs,
        "batch_size": batch_size,
        "elapsed_time_seconds": elapsed_time,
        "memory_before_mb": mem_before,
        "memory_after_mb": mem_after,
        "memory_delta_mb": mem_delta,
        "peak_memory_mb": peak_mem,
        "metrics": metrics
    }

def main():
    """Main entry point for profiling."""
    set_seed(42)
    logger.info("Starting Memory Profiler for T062c")

    results = []

    # Profile standard training
    logger.info("--- Profiling Standard Training ---")
    try:
        standard_results = profile_training_loop(
            use_optimized=False,
            num_epochs=5,
            batch_size=32,
            logger=logger
        )
        results.append(standard_results)
    except Exception as e:
        logger.error(f"Standard profiling failed: {e}")
        results.append({"mode": "standard", "error": str(e)})

    # Profile optimized training
    logger.info("--- Profiling Optimized Training ---")
    try:
        optimized_results = profile_training_loop(
            use_optimized=True,
            num_epochs=5,
            batch_size=32,
            logger=logger
        )
        results.append(optimized_results)
    except Exception as e:
        logger.error(f"Optimized profiling failed: {e}")
        results.append({"mode": "optimized", "error": str(e)})

    # Save results
    output_data = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "profiling_runs": results,
        "summary": {
            "standard_memory_mb": next((r.get("memory_after_mb") for r in results if r.get("mode") == "standard"), None),
            "optimized_memory_mb": next((r.get("memory_after_mb") for r in results if r.get("mode") == "optimized"), None),
            "reduction_percent": None
        }
    }

    # Calculate reduction
    std_mem = output_data["summary"]["standard_memory_mb"]
    opt_mem = output_data["summary"]["optimized_memory_mb"]
    if std_mem and opt_mem and std_mem > 0:
        reduction = ((std_mem - opt_mem) / std_mem) * 100
        output_data["summary"]["reduction_percent"] = round(reduction, 2)
        logger.info(f"Memory reduction: {reduction:.2f}%")

    with open(PROFILE_OUTPUT, 'w') as f:
        json.dump(output_data, f, indent=2)

    logger.info(f"Profile results saved to {PROFILE_OUTPUT}")
    print(f"Profile results saved to {PROFILE_OUTPUT}")
    return output_data

if __name__ == "__main__":
    main()
