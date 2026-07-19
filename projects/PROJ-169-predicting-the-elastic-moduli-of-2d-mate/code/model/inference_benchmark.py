"""
Inference benchmark for the Structure-Only Surrogate Model.

Measures latency per material on CPU to verify SC-003 (inference time < 100ms).
"""

import os
import json
import time
import logging
import argparse
import gc
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import numpy as np
import torch
import psutil
import pandas as pd
from torch_geometric.data import Data

# Project imports
from model.gnn import LightweightGNN, create_model
from model.train_config import TrainingConfig
from data_models.material_graph import MaterialGraph
from utils.config import set_global_config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

NUM_RUNS = 50
INFERENCE_THRESHOLD_MS = 100.0

def load_test_data_and_indices(
    graphs_path: Path,
    indices_path: Path
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Load the full graph dataset and the split indices.
    Returns the raw data as dicts for filtering.
    """
    if not graphs_path.exists():
        raise FileNotFoundError(f"Graphs file not found: {graphs_path}")
    
    if not indices_path.exists():
        raise FileNotFoundError(f"Split indices file not found: {indices_path}")

    df = pd.read_parquet(graphs_path)
    indices_df = pd.read_json(indices_path)

    # Filter for test set
    test_ids = set(indices_df[indices_df['split'] == 'test']['id'])
    test_data = df[df['id'].isin(test_ids)].to_dict('records')

    logger.info(f"Loaded {len(test_data)} test samples for benchmarking.")
    return test_data, indices_df.to_dict('records')

def convert_graphs_to_pyg(graph_data_list: List[Dict[str, Any]]) -> List[Data]:
    """
    Convert dictionary representation of MaterialGraph to PyTorch Geometric Data objects.
    """
    pyg_graphs = []
    for item in graph_data_list:
        # Assuming serialized format from pipeline: node_features, edge_index, edge_features, target_moduli
        node_features = torch.tensor(item['node_features'], dtype=torch.float32)
        edge_index = torch.tensor(item['edge_index'], dtype=torch.long)
        edge_features = torch.tensor(item['edge_features'], dtype=torch.float32)
        
        # Create PyG Data object
        data = Data(
            x=node_features,
            edge_index=edge_index,
            edge_attr=edge_features,
            y=torch.tensor(item['target_moduli'], dtype=torch.float32)
        )
        pyg_graphs.append(data)
    
    return pyg_graphs

def load_model_and_config(
    model_path: Path,
    device: torch.device
) -> LightweightGNN:
    """
    Load the trained GNN model.
    """
    if not model_path.exists():
        raise FileNotFoundError(f"Model file not found: {model_path}")

    # We need to reconstruct the config to instantiate the model correctly.
    # For benchmarking, we assume standard config or load from a sidecar if available.
    # If no sidecar, we use defaults matching the training task.
    config = TrainingConfig()
    
    model = create_model(config)
    model.load_state_dict(torch.load(model_path, map_location=device))
    model.to(device)
    model.eval()
    
    logger.info(f"Model loaded from {model_path}")
    return model

def get_cpu_model() -> str:
    """
    Detect the CPU model string for portability logging.
    """
    try:
        # Try reading from /proc/cpuinfo on Linux
        if os.path.exists('/proc/cpuinfo'):
            with open('/proc/cpuinfo', 'r') as f:
                for line in f:
                    if 'model name' in line:
                        return line.split(':')[1].strip()
        # Fallback to psutil if available
        if hasattr(psutil, 'cpu_freq'):
            # psutil doesn't give model name directly, but we can try to get info
            pass
        return "Unknown CPU"
    except Exception as e:
        logger.warning(f"Could not detect CPU model: {e}")
        return "Unknown CPU"

def run_benchmark(
    model: LightweightGNN,
    graphs: List[Data],
    num_runs: int = NUM_RUNS,
    device: torch.device = torch.device('cpu')
) -> float:
    """
    Run inference benchmark averaging latency over num_runs.
    """
    latencies = []
    
    # Warmup run
    with torch.no_grad():
        for _ in range(5):
            _ = model(graphs[0].x.unsqueeze(0), graphs[0].edge_index.unsqueeze(0))
    
    logger.info(f"Starting benchmark with {num_runs} runs...")
    
    for i in range(num_runs):
        # Pick a random graph to simulate variable load
        sample_idx = np.random.randint(0, len(graphs))
        graph = graphs[sample_idx]
        
        # Ensure graph is on correct device
        x = graph.x.unsqueeze(0).to(device)
        edge_index = graph.edge_index.unsqueeze(0).to(device)
        
        start_time = time.perf_counter()
        with torch.no_grad():
            _ = model(x, edge_index)
        end_time = time.perf_counter()
        
        latency_ms = (end_time - start_time) * 1000
        latencies.append(latency_ms)
        
        if (i + 1) % 10 == 0:
            logger.debug(f"Completed {i+1}/{num_runs} runs")

    avg_latency = np.mean(latencies)
    std_latency = np.std(latencies)
    
    logger.info(f"Benchmark complete. Avg latency: {avg_latency:.2f}ms (std: {std_latency:.2f}ms)")
    return avg_latency

def update_generalization_metrics(
    output_path: Path,
    inference_time_ms: float,
    cpu_model: str,
    threshold_ms: float = INFERENCE_THRESHOLD_MS
) -> Dict[str, Any]:
    """
    Load existing generalization metrics if present, update with inference stats,
    and save back.
    """
    metrics = {}
    
    if output_path.exists():
        with open(output_path, 'r') as f:
            metrics = json.load(f)
    
    metrics['inference_time_ms'] = inference_time_ms
    metrics['cpu_model'] = cpu_model
    metrics['inference_threshold_ms'] = threshold_ms
    metrics['inference_pass'] = inference_time_ms < threshold_ms
    
    # Ensure disclaimer is present if not already
    if 'disclaimer' not in metrics:
        metrics['disclaimer'] = "These results are ML interpolations of DFT data, not first-principles solutions."
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    
    logger.info(f"Updated generalization metrics at {output_path}")
    return metrics

def main():
    parser = argparse.ArgumentParser(description="Benchmark inference latency of the surrogate model.")
    parser.add_argument(
        "--graphs",
        type=str,
        required=True,
        help="Path to the processed graphs parquet file (e.g., data/processed/graphs_v1.parquet)"
    )
    parser.add_argument(
        "--indices",
        type=str,
        required=True,
        help="Path to the split indices JSON file (e.g., data/processed/split_indices.json)"
    )
    parser.add_argument(
        "--model",
        type=str,
        required=True,
        help="Path to the trained model checkpoint (e.g., data/processed/model_v1.pt)"
    )
    parser.add_argument(
        "--output",
        type=str,
        required=True,
        help="Path to the output metrics JSON file (e.g., data/results/generalization_metrics.json)"
    )
    parser.add_argument(
        "--runs",
        type=int,
        default=NUM_RUNS,
        help=f"Number of inference runs to average (default: {NUM_RUNS})"
    )
    
    args = parser.parse_args()
    
    # Set global config for reproducibility
    set_global_config()
    
    device = torch.device('cpu')
    logger.info(f"Running benchmark on {device}")
    
    try:
        # 1. Load data
        test_data, _ = load_test_data_and_indices(Path(args.graphs), Path(args.indices))
        if not test_data:
            logger.error("No test data found for benchmarking.")
            sys.exit(1)
        
        pyg_graphs = convert_graphs_to_pyg(test_data)
        if not pyg_graphs:
            logger.error("Failed to convert graphs to PyG format.")
            sys.exit(1)
        
        # 2. Load model
        model = load_model_and_config(Path(args.model), device)
        
        # 3. Run benchmark
        avg_latency = run_benchmark(model, pyg_graphs, num_runs=args.runs, device=device)
        
        # 4. Detect CPU
        cpu_model = get_cpu_model()
        
        # 5. Update metrics
        output_path = Path(args.output)
        final_metrics = update_generalization_metrics(
            output_path, 
            avg_latency, 
            cpu_model, 
            INFERENCE_THRESHOLD_MS
        )
        
        # 6. Report status
        if final_metrics['inference_pass']:
            logger.info(f"SUCCESS: Inference time ({avg_latency:.2f}ms) is below threshold ({INFERENCE_THRESHOLD_MS}ms).")
        else:
            logger.warning(f"WARNING: Inference time ({avg_latency:.2f}ms) exceeds threshold ({INFERENCE_THRESHOLD_MS}ms).")
            
    except Exception as e:
        logger.error(f"Benchmark failed: {e}")
        raise

if __name__ == "__main__":
    main()