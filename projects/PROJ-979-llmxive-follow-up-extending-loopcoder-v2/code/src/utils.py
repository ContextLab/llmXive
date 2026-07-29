"""
Utility functions for FLOPs calculation and resource monitoring.

This module provides utilities for:
- Calculating FLOPs based on model parameters and sequence length
- Capturing runtime resource metrics (CPU, RAM, GPU)
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

# Configure logging
import logging
logger = logging.getLogger(__name__)

def get_model_param_count(model) -> int:
    """
    Get the number of parameters in a model.
    
    Args:
        model: PyTorch model
        
    Returns:
        Number of parameters
    """
    return sum(p.numel() for p in model.parameters())

def calculate_flops(
    parameters: int,
    sequence_length: int,
    k: int,
    factor: float = 2.0
) -> float:
    """
    Calculate FLOPs for a given computation.
    
    Formula: FLOPs = parameters * sequence_length * k * factor
    Factor accounts for forward/backward pass (2.0 for training, 1.0 for inference)
    
    Args:
        parameters: Number of model parameters
        sequence_length: Input sequence length
        k: Number of iterations/loops
        factor: FLOPs factor (default 2.0 for training)
        
    Returns:
        Calculated FLOPs
    """
    return parameters * sequence_length * k * factor

def capture_metrics() -> Dict[str, Any]:
    """
    Capture runtime resource metrics.
    
    Returns:
        Dictionary with runtime, RAM, and GPU metrics
    """
    start_time = time.perf_counter()
    
    # CPU/RAM metrics
    process = psutil.Process(os.getpid())
    ram_gb = process.memory_info().rss / (1024 ** 3)
    
    # GPU metrics
    gpu_util_pct = None
    gpu_memory_gb = None
    
    if torch.cuda.is_available():
        gpu_util_pct = torch.cuda.utilization()
        gpu_memory_gb = torch.cuda.memory_allocated() / (1024 ** 3)
    else:
        # Try nvidia-smi via subprocess
        try:
            import subprocess
            result = subprocess.run(
                ['nvidia-smi', '--query-gpu=utilization.gpu,memory.used', '--format=csv,noheader,nounits'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                if lines:
                    parts = lines[0].split(',')
                    gpu_util_pct = float(parts[0].strip())
                    gpu_memory_gb = float(parts[1].strip()) / 1024
        except Exception as e:
            logger.warning(f"Could not get GPU metrics: {e}")
    
    runtime_s = time.perf_counter() - start_time
    
    metrics = {
        "runtime_s": runtime_s,
        "ram_gb": ram_gb,
        "gpu_util_pct": gpu_util_pct,
        "gpu_memory_gb": gpu_memory_gb,
        "timestamp": datetime.now().isoformat(),
        "platform": platform.system(),
        "python_version": platform.python_version()
    }
    
    return metrics

def save_resource_metrics(
    metrics: Dict[str, Any],
    output_path: str = "data/processed/resource_metrics.json"
) -> None:
    """
    Save resource metrics to JSON file.
    
    Args:
        metrics: Metrics dictionary
        output_path: Output file path
    """
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    
    logger.info(f"Resource metrics saved to {output_path}")

def main():
    """Main entry point for resource monitoring."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Capture and save resource metrics")
    parser.add_argument("--output", type=str, default="data/processed/resource_metrics.json",
                      help="Output path for metrics JSON")
    
    args = parser.parse_args()
    
    metrics = capture_metrics()
    save_resource_metrics(metrics, args.output)
    
    print(f"Metrics captured: {metrics}")

if __name__ == "__main__":
    main()
