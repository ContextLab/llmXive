"""
Inference Benchmark for T036: Verify inference time constraint (SC-003).

Measures latency per material on CPU, detects CPU model, and updates
data/results/generalization_metrics.json with inference_time_ms, cpu_model,
and a pass/fail status against the 100ms threshold.

Dependency: T018b (produces data/processed/model_v1.pt and predictions.json)
Dependency: T017 (produces data/processed/split_indices.json)
"""
from __future__ import annotations

import argparse
import gc
import json
import logging
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import numpy as np
import torch
from torch_geometric.data import Data

# Import project utilities
# Note: Using relative imports to ensure compatibility with project structure
try:
    from model.gnn import LightweightGNN, create_model
    from utils.config import enforce_reproducibility
except ImportError:
    # Fallback for execution environment where sys.path might be different
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
    from model.gnn import LightweightGNN, create_model
    from utils.config import enforce_reproducibility

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
NUM_RUNS = 10  # Number of inference runs to average
WARMUP_RUNS = 3
THRESHOLD_MS = 100.0
OUTPUT_PATH = Path("data/results/generalization_metrics.json")
MODEL_PATH = Path("data/processed/model_v1.pt")
SPLIT_PATH = Path("data/processed/split_indices.json")
PARQUET_PATH = Path("data/processed/graphs_v1.parquet")


def get_cpu_model() -> str:
    """Detect the specific CPU model using lscpu or psutil."""
    try:
        # Try lscpu first (common on Linux)
        result = subprocess.run(
            ["lscpu"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            for line in result.stdout.split('\n'):
                if line.startswith("Model name:"):
                    return line.split(":", 1)[1].strip()
    except Exception:
        pass

    try:
        # Fallback to psutil if available
        import psutil
        # psutil doesn't directly give model name, but we can try /proc/cpuinfo
        if os.path.exists('/proc/cpuinfo'):
            with open('/proc/cpuinfo', 'r') as f:
                for line in f:
                    if 'model name' in line:
                        return line.split(":", 1)[1].strip()
    except ImportError:
        pass
    except Exception:
        pass

    # Ultimate fallback
    return "Unknown CPU Model"


def load_test_data_and_indices(
    parquet_path: Path,
    split_path: Path
) -> Tuple[List[Dict[str, Any]], List[int]]:
    """
    Load test data from parquet and test indices from split_indices.json.

    Returns:
        Tuple of (list of graph dicts, list of test indices)
    """
    if not parquet_path.exists():
        raise FileNotFoundError(f"Parquet file not found: {parquet_path}")
    if not split_path.exists():
        raise FileNotFoundError(f"Split indices file not found: {split_path}")

    try:
        import pandas as pd
        df = pd.read_parquet(parquet_path)
    except Exception as e:
        raise RuntimeError(f"Failed to read parquet file: {e}")

    with open(split_path, 'r') as f:
        split_data = json.load(f)

    test_indices = split_data.get('test_indices', [])
    if not test_indices:
        raise ValueError("No test indices found in split file")

    # Extract test samples
    test_samples = df.iloc[test_indices].to_dict('records')
    logger.info(f"Loaded {len(test_samples)} test samples for benchmarking")

    return test_samples, test_indices


def convert_graphs_to_pyg(graph_dicts: List[Dict[str, Any]]) -> List[Data]:
    """
    Convert list of graph dictionaries to PyTorch Geometric Data objects.

    Expected dict keys:
        - node_features: np.ndarray or list
        - edge_index: np.ndarray or list (2, num_edges)
        - edge_features: np.ndarray or list (optional)
        - target_moduli: dict or list (optional)
    """
    pyg_graphs = []
    for graph_dict in graph_dicts:
        try:
            node_features = torch.tensor(graph_dict['node_features'], dtype=torch.float32)
            edge_index = torch.tensor(graph_dict['edge_index'], dtype=torch.long)

            # Handle optional edge features
            edge_attr = None
            if 'edge_features' in graph_dict and graph_dict['edge_features'] is not None:
                edge_attr = torch.tensor(graph_dict['edge_features'], dtype=torch.float32)

            # Create PyG Data object
            data = Data(
                x=node_features,
                edge_index=edge_index,
                edge_attr=edge_attr
            )
            pyg_graphs.append(data)
        except Exception as e:
            logger.warning(f"Failed to convert graph: {e}")
            continue

    return pyg_graphs


def load_model_and_config(model_path: Path) -> LightweightGNN:
    """Load the trained model from checkpoint."""
    if not model_path.exists():
        raise FileNotFoundError(f"Model checkpoint not found: {model_path}")

    # Load config from the checkpoint or use defaults
    # Assuming the model was saved with a specific architecture
    # We need to reconstruct the model based on the saved state dict
    checkpoint = torch.load(model_path, map_location='cpu', weights_only=True)

    # Extract input/output dimensions from the state dict if possible
    # This is a heuristic; in a real scenario, we'd store config with the model
    input_dim = 128  # Default assumption, adjust if needed
    hidden_dim = 64  # Default assumption
    output_dim = 3   # Young's, Shear, Poisson

    if 'input_dim' in checkpoint:
        input_dim = checkpoint['input_dim']
    if 'hidden_dim' in checkpoint:
        hidden_dim = checkpoint['hidden_dim']
    if 'output_dim' in checkpoint:
        output_dim = checkpoint['output_dim']

    model = create_model(input_dim=input_dim, hidden_dim=hidden_dim, output_dim=output_dim)

    # Load state dict
    model.load_state_dict(checkpoint['model_state_dict'])
    model.eval()

    logger.info(f"Model loaded from {model_path}")
    return model


def run_benchmark(
    model: LightweightGNN,
    graphs: List[Data],
    num_runs: int = NUM_RUNS,
    warmup_runs: int = WARMUP_RUNS
) -> float:
    """
    Run inference benchmark on the provided graphs.

    Returns:
        Average inference time per graph in milliseconds.
    """
    model.eval()
    device = torch.device('cpu')
    model.to(device)

    times = []

    # Warmup runs
    logger.info(f"Running {warmup_runs} warmup iterations...")
    with torch.no_grad():
        for _ in range(warmup_runs):
            for graph in graphs:
                graph = graph.to(device)
                _ = model(graph)
            torch.cuda.empty_cache() if torch.cuda.is_available() else None
            gc.collect()

    # Actual benchmark runs
    logger.info(f"Running {num_runs} benchmark iterations...")
    for run in range(num_runs):
        start = time.perf_counter()
        with torch.no_grad():
            for graph in graphs:
                graph = graph.to(device)
                _ = model(graph)
        end = time.perf_counter()
        elapsed = (end - start) * 1000  # Convert to ms
        times.append(elapsed)
        logger.debug(f"Run {run + 1}/{num_runs}: {elapsed:.4f} ms total for {len(graphs)} graphs")

    # Calculate average time per graph
    total_time = sum(times)
    avg_time_per_graph = (total_time / num_runs) / len(graphs)

    logger.info(f"Average inference time per graph: {avg_time_per_graph:.4f} ms")
    return avg_time_per_graph


def update_generalization_metrics(
    output_path: Path,
    inference_time_ms: float,
    cpu_model: str,
    threshold_ms: float = THRESHOLD_MS
) -> Dict[str, Any]:
    """
    Update or create the generalization metrics file with inference benchmark results.

    Args:
        output_path: Path to the generalization metrics JSON file
        inference_time_ms: Measured average inference time per graph
        cpu_model: Detected CPU model string
        threshold_ms: Threshold for passing the constraint

    Returns:
        Updated metrics dictionary
    """
    metrics = {}

    # Load existing metrics if file exists
    if output_path.exists():
        try:
            with open(output_path, 'r') as f:
                metrics = json.load(f)
            logger.info(f"Loaded existing metrics from {output_path}")
        except Exception as e:
            logger.warning(f"Failed to load existing metrics: {e}. Starting fresh.")

    # Update with benchmark results
    metrics['inference_time_ms'] = round(inference_time_ms, 4)
    metrics['cpu_model'] = cpu_model
    metrics['inference_threshold_ms'] = threshold_ms
    metrics['inference_constraint_met'] = inference_time_ms < threshold_ms

    # Ensure disclaimer is present (from T046)
    if 'disclaimer' not in metrics:
        metrics['disclaimer'] = (
            "These results are derived from a machine learning surrogate model "
            "interpolating pre-computed DFT data. They do not represent first-principles "
            "calculations or solutions to the Schrödinger equation."
        )

    # Save updated metrics
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(metrics, f, indent=2)

    logger.info(f"Updated generalization metrics saved to {output_path}")
    return metrics


def main():
    """Main entry point for the inference benchmark."""
    parser = argparse.ArgumentParser(description="Inference Benchmark for SC-003")
    parser.add_argument(
        '--model-path',
        type=str,
        default=str(MODEL_PATH),
        help=f"Path to the trained model checkpoint (default: {MODEL_PATH})"
    )
    parser.add_argument(
        '--split-path',
        type=str,
        default=str(SPLIT_PATH),
        help=f"Path to the split indices file (default: {SPLIT_PATH})"
    )
    parser.add_argument(
        '--parquet-path',
        type=str,
        default=str(PARQUET_PATH),
        help=f"Path to the graphs parquet file (default: {PARQUET_PATH})"
    )
    parser.add_argument(
        '--output-path',
        type=str,
        default=str(OUTPUT_PATH),
        help=f"Path to the output generalization metrics file (default: {OUTPUT_PATH})"
    )
    parser.add_argument(
        '--num-runs',
        type=int,
        default=NUM_RUNS,
        help=f"Number of benchmark runs (default: {NUM_RUNS})"
    )
    parser.add_argument(
        '--warmup-runs',
        type=int,
        default=WARMUP_RUNS,
        help=f"Number of warmup runs (default: {WARMUP_RUNS})"
    )

    args = parser.parse_args()

    # Enforce reproducibility
    enforce_reproducibility()

    logger.info("Starting inference benchmark...")

    # Detect CPU model
    cpu_model = get_cpu_model()
    logger.info(f"Detected CPU: {cpu_model}")

    # Load data
    try:
        test_samples, test_indices = load_test_data_and_indices(
            Path(args.parquet_path),
            Path(args.split_path)
        )
    except Exception as e:
        logger.error(f"Failed to load data: {e}")
        sys.exit(1)

    # Convert to PyG graphs
    pyg_graphs = convert_graphs_to_pyg(test_samples)
    if not pyg_graphs:
        logger.error("No valid graphs converted for benchmarking")
        sys.exit(1)

    logger.info(f"Converted {len(pyg_graphs)} graphs for benchmarking")

    # Load model
    try:
        model = load_model_and_config(Path(args.model_path))
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        sys.exit(1)

    # Run benchmark
    try:
        avg_time_ms = run_benchmark(
            model,
            pyg_graphs,
            num_runs=args.num_runs,
            warmup_runs=args.warmup_runs
        )
    except Exception as e:
        logger.error(f"Benchmark failed: {e}")
        sys.exit(1)

    # Update metrics
    try:
        metrics = update_generalization_metrics(
            Path(args.output_path),
            avg_time_ms,
            cpu_model
        )
    except Exception as e:
        logger.error(f"Failed to update metrics: {e}")
        sys.exit(1)

    # Report results
    logger.info("=" * 50)
    logger.info("INFERENCE BENCHMARK RESULTS")
    logger.info("=" * 50)
    logger.info(f"CPU Model: {metrics['cpu_model']}")
    logger.info(f"Average Inference Time: {metrics['inference_time_ms']:.4f} ms/graph")
    logger.info(f"Threshold: {metrics['inference_threshold_ms']} ms")
    logger.info(f"Constraint Met: {'YES' if metrics['inference_constraint_met'] else 'NO'}")
    logger.info("=" * 50)

    if not metrics['inference_constraint_met']:
        logger.warning("WARNING: Inference time exceeds the 100ms threshold!")
        sys.exit(0)  # Exit 0 even if constraint not met, as this is a measurement task

    logger.info("Benchmark completed successfully.")


if __name__ == "__main__":
    main()