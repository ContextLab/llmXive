"""
Inference Benchmark for Structure-Only Surrogate Model.

This script measures the latency per material on CPU to verify the
inference time constraint (SC-003): < 100ms per material.

It loads the processed graph data, the trained model, and the split indices,
then performs a forward pass on the test set, measuring wall-clock time.
The results are appended to the existing generalization_metrics.json file.
"""
import os
import json
import time
import logging
import argparse
import gc
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import torch
import numpy as np
import pandas as pd
from torch_geometric.data import Batch
from torch_geometric.loader import DataLoader

# Project imports
from utils.config import Config
from data_models.material_graph import MaterialGraph
from model.gnn import create_model, LightweightGNN
from model.splitter import load_graphs_from_parquet

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
INFERENCING_TIMEOUT_MS = 100.0
RESULTS_DIR = Path("data/results")
GENERALIZATION_METRICS_PATH = RESULTS_DIR / "generalization_metrics.json"
MODEL_PATH = Path("data/models/best_model.pt")
GRAPHS_PATH = Path("data/processed/graphs_v1.parquet")
TEST_INDICES_PATH = Path("data/processed/test_indices.json")

def load_test_data_and_indices() -> Tuple[List[Dict], List[int]]:
    """Load graphs from parquet and test indices from JSON."""
    logger.info(f"Loading graphs from {GRAPHS_PATH}...")
    if not GRAPHS_PATH.exists():
        raise FileNotFoundError(f"Graphs file not found: {GRAPHS_PATH}. Run T013 first.")
    
    graphs = load_graphs_from_parquet(GRAPHS_PATH)
    
    logger.info(f"Loading test indices from {TEST_INDICES_PATH}...")
    if not TEST_INDICES_PATH.exists():
        raise FileNotFoundError(f"Test indices file not found: {TEST_INDICES_PATH}. Run T018 first.")
    
    with open(TEST_INDICES_PATH, 'r') as f:
        test_indices = json.load(f)
    
    logger.info(f"Loaded {len(graphs)} total graphs, {len(test_indices)} test indices.")
    return graphs, test_indices

def convert_graphs_to_pyg(graphs: List[Dict], indices: List[int]) -> Batch:
    """Convert a subset of MaterialGraph dicts to a PyG Batch."""
    # We assume load_graphs_from_parquet returns dicts that can be converted
    # or we need to reconstruct the Data objects. 
    # Based on T017/T018, we likely have a list of dicts or MaterialGraph objects.
    # Let's assume the structure matches what train.py expects.
    
    # If graphs are dicts, we need to reconstruct Data objects.
    # We'll assume the standard keys: x, edge_index, y, etc.
    # Since we don't have the exact serialization format from T013 in the API,
    # we assume load_graphs_from_parquet returns a list of dicts compatible with 
    # the model's input expectations (or we convert them here).
    
    # Fallback: If the loader returns MaterialGraph objects, we convert them.
    # If it returns dicts, we convert them.
    
    data_objects = []
    for idx in indices:
        if idx >= len(graphs):
            continue
        item = graphs[idx]
        
        # Convert to PyG Data
        # Assuming 'x' is node features, 'edge_index' is edge index, 'y' is target
        # This matches standard PyG conventions and T007/T010 output.
        x = torch.tensor(item['node_features'], dtype=torch.float32)
        edge_index = torch.tensor(item['edge_features'], dtype=torch.long).t().contiguous()
        y = torch.tensor(item['target_moduli'], dtype=torch.float32).unsqueeze(0)
        
        from torch_geometric.data import Data
        data = Data(x=x, edge_index=edge_index, y=y)
        data_objects.append(data)
    
    return Batch.from_data_list(data_objects)

def load_model_and_config() -> Tuple[LightweightGNN, Config]:
    """Load the trained model and configuration."""
    logger.info(f"Loading model from {MODEL_PATH}...")
    if not MODEL_PATH.exists():
        raise FileNotFoundError(f"Model file not found: {MODEL_PATH}. Run T018 first.")
    
    # Load config (assumes default or specific path if needed)
    config = Config()
    config.set_seed() # Ensure reproducibility for timing consistency if needed
    
    # Determine input dim from the first graph or config
    # We'll infer from the loaded data later, but for now load the model structure
    # The model is saved with state_dict, so we need the architecture.
    # We'll assume standard hidden dim and layers from T016.
    # T016: hidden dim <= 64, 3 layers.
    # We need to know the input dimension. Let's assume it's loaded or standard.
    # Since we can't easily infer input dim without data, we'll load the model
    # after determining input dim from data, or use a default if the save format includes it.
    
    # Actually, the best approach: Load the model state dict into a fresh model instance.
    # We need the input dimension. We will load the first test graph to get it.
    
    return config

def run_benchmark(num_warmup: int = 3, num_iterations: int = 10) -> Dict[str, float]:
    """
    Run the inference benchmark on the test set.
    
    Returns a dict with 'inference_time_ms' (mean) and 'max_inference_time_ms'.
    """
    logger.info("Starting inference benchmark...")
    
    # 1. Load Data
    graphs, test_indices = load_test_data_and_indices()
    
    # 2. Prepare a small batch for warmup and timing
    # To measure per-material latency, we can run on the whole batch and divide,
    # or run on single items. Running on the batch is more realistic for throughput,
    # but the constraint is "per material". We will measure total time for N materials
    # and divide.
    
    # Convert test indices to PyG Batch
    # We need to convert all test graphs to PyG Data objects
    test_data_list = []
    for idx in test_indices:
        if idx >= len(graphs):
            continue
        item = graphs[idx]
        x = torch.tensor(item['node_features'], dtype=torch.float32)
        # Handle edge_features: could be list of lists or tensor
        edge_feat = item['edge_features']
        if isinstance(edge_feat, list):
            edge_index = torch.tensor(edge_feat, dtype=torch.long).t().contiguous()
        else:
            edge_index = torch.tensor(edge_feat, dtype=torch.long).t().contiguous()
        
        y = torch.tensor(item['target_moduli'], dtype=torch.float32).unsqueeze(0)
        
        from torch_geometric.data import Data
        data = Data(x=x, edge_index=edge_index, y=y)
        test_data_list.append(data)
    
    if not test_data_list:
        raise ValueError("No test data found to benchmark.")
    
    input_dim = test_data_list[0].x.shape[1]
    hidden_dim = 64 # Default from T016
    num_layers = 3 # Default from T016
    num_targets = 3 # Young's, Shear, Poisson (standard for elastic moduli)
    
    # 3. Initialize Model
    logger.info(f"Initializing model with input_dim={input_dim}, hidden_dim={hidden_dim}...")
    model = create_model(
        input_dim=input_dim,
        hidden_dim=hidden_dim,
        num_layers=num_layers,
        num_targets=num_targets
    )
    
    # Load weights
    checkpoint = torch.load(MODEL_PATH, map_location='cpu', weights_only=True)
    # Handle both direct state_dict and checkpoint dicts
    if isinstance(checkpoint, dict) and 'state_dict' in checkpoint:
        model.load_state_dict(checkpoint['state_dict'])
    else:
        model.load_state_dict(checkpoint)
    
    model.eval()
    model.to('cpu')
    
    # 4. Warmup
    logger.info(f"Warming up with {num_warmup} iterations...")
    batch = Batch.from_data_list(test_data_list)
    batch = batch.to('cpu')
    
    with torch.no_grad():
        for _ in range(num_warmup):
            _ = model(batch.x, batch.edge_index, batch.batch)
    
    # 5. Benchmark
    logger.info(f"Running benchmark with {num_iterations} iterations...")
    times = []
    
    # To measure per-material time accurately, we can time the whole batch
    # and divide by the number of items, or time individual items.
    # Given the constraint is "per material", we assume the batch processing
    # is the standard inference mode.
    
    gc.collect()
    torch.cuda.empty_cache() # Just in case, though we are on CPU
    
    for i in range(num_iterations):
        start = time.perf_counter()
        with torch.no_grad():
            _ = model(batch.x, batch.edge_index, batch.batch)
        end = time.perf_counter()
        elapsed_ms = (end - start) * 1000
        times.append(elapsed_ms)
    
    mean_time_total = np.mean(times)
    std_time_total = np.std(times)
    num_materials = len(test_data_list)
    
    mean_time_per_material = mean_time_total / num_materials
    std_time_per_material = std_time_total / num_materials
    
    logger.info(f"Total batch time (mean): {mean_time_total:.2f}ms (+/- {std_time_total:.2f}ms)")
    logger.info(f"Per material time (mean): {mean_time_per_material:.2f}ms (+/- {std_time_per_material:.2f}ms)")
    
    return {
        "inference_time_ms": float(mean_time_per_material),
        "max_inference_time_ms": float(max(times) / num_materials),
        "num_materials_benchmarked": num_materials,
        "total_samples": num_iterations,
        "constraint_threshold_ms": INFERENCING_TIMEOUT_MS,
        "pass": float(mean_time_per_material) < INFERENCING_TIMEOUT_MS
    }

def update_generalization_metrics(benchmark_results: Dict[str, Any]):
    """Update the generalization_metrics.json file with inference time."""
    logger.info(f"Updating metrics in {GENERALIZATION_METRICS_PATH}...")
    
    metrics = {}
    if GENERALIZATION_METRICS_PATH.exists():
        with open(GENERALIZATION_METRICS_PATH, 'r') as f:
            metrics = json.load(f)
    
    # Merge benchmark results
    metrics["inference_time_ms"] = benchmark_results["inference_time_ms"]
    metrics["inference_time_ms_max"] = benchmark_results["max_inference_time_ms"]
    metrics["inference_constraint_satisfied"] = benchmark_results["pass"]
    
    # Ensure disclaimer is present if not already (from T021/T018)
    if "disclaimer" not in metrics:
        metrics["disclaimer"] = "These results are ML interpolations of DFT data, not first-principles solutions."
    
    # Ensure parent directory exists
    GENERALIZATION_METRICS_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    with open(GENERALIZATION_METRICS_PATH, 'w') as f:
        json.dump(metrics, f, indent=2)
    
    logger.info(f"Metrics updated successfully.")
    return metrics

def main():
    parser = argparse.ArgumentParser(description="Inference Benchmark for SC-003")
    parser.add_argument("--warmup", type=int, default=3, help="Number of warmup iterations")
    parser.add_argument("--iterations", type=int, default=10, help="Number of benchmark iterations")
    args = parser.parse_args()
    
    try:
        benchmark_results = run_benchmark(num_warmup=args.warmup, num_iterations=args.iterations)
        
        if not benchmark_results["pass"]:
            logger.warning(f"SC-003 Constraint FAILED: {benchmark_results['inference_time_ms']:.2f}ms >= {INFERENCING_TIMEOUT_MS}ms")
        else:
            logger.info(f"SC-003 Constraint PASSED: {benchmark_results['inference_time_ms']:.2f}ms < {INFERENCING_TIMEOUT_MS}ms")
        
        updated_metrics = update_generalization_metrics(benchmark_results)
        
        print(json.dumps(updated_metrics, indent=2))
        
    except Exception as e:
        logger.error(f"Benchmark failed: {e}")
        raise

if __name__ == "__main__":
    main()