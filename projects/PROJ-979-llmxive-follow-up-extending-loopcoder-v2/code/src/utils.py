"""
Utility functions for FLOPs calculation and resource monitoring.
"""
import json
import os
import time
import platform
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

import psutil
import torch

def get_model_param_count(model: Any) -> int:
    """
    Get the total number of parameters in a model.
    
    Args:
        model: A PyTorch model.
        
    Returns:
        Total parameter count.
    """
    return sum(p.numel() for p in model.parameters())

def calculate_flops(
    parameters: int,
    sequence_length: int,
    k: int,
    layers: Optional[int] = None
) -> float:
    """
    Calculate FLOPs for a given model configuration.
    Formula: FLOPs = parameters * sequence_length * k
    
    Args:
        parameters: Number of model parameters.
        sequence_length: Input sequence length.
        k: Number of loops/iterations.
        layers: Optional number of layers (for more precise calculation).
        
    Returns:
        Estimated FLOPs.
    """
    base_flops = parameters * sequence_length * k
    
    if layers:
        # More precise: FLOPs per layer * number of layers
        # This is a rough approximation
        return base_flops * layers
    
    return base_flops

def capture_metrics() -> Dict[str, float]:
    """
    Capture system resource metrics: runtime, RAM, GPU usage.
    
    Returns:
        Dict with keys: runtime_s, ram_gb, gpu_util_pct, gpu_memory_gb
    """
    start_time = time.time()
    
    # RAM usage
    process = psutil.Process(os.getpid())
    ram_gb = process.memory_info().rss / (1024 ** 3)
    
    # GPU metrics
    gpu_util_pct = 0.0
    gpu_memory_gb = 0.0
    
    if torch.cuda.is_available():
        gpu_util_pct = torch.cuda.utilization()
        gpu_memory_gb = torch.cuda.memory_allocated() / (1024 ** 3)
    
    runtime_s = time.time() - start_time
    
    return {
        "runtime_s": round(runtime_s, 2),
        "ram_gb": round(ram_gb, 2),
        "gpu_util_pct": round(gpu_util_pct, 2),
        "gpu_memory_gb": round(gpu_memory_gb, 2)
    }

def save_resource_metrics(
    metrics: Dict[str, float],
    output_path: str
) -> None:
    """
    Save resource metrics to a JSON file.
    
    Args:
        metrics: Dict of metrics.
        output_path: Path to output file.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(metrics, f, indent=2)

def main():
    """
    Main entry point for resource monitoring.
    Usage: python code/src/utils.py --output data/processed/resource_metrics.json
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Capture and save resource metrics.")
    parser.add_argument('--output', type=str, default='data/processed/resource_metrics.json',
                        help='Path to output JSON')
    
    args = parser.parse_args()
    
    metrics = capture_metrics()
    save_resource_metrics(metrics, args.output)
    
    print(f"Metrics saved to {args.output}")
    print(json.dumps(metrics, indent=2))

if __name__ == "__main__":
    main()
