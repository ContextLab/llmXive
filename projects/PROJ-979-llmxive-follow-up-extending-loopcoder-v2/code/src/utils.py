import json
import os
import time
import platform
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
import subprocess
import psutil

def get_model_param_count(model) -> int:
    """
    Calculate the number of trainable parameters in a Hugging Face model.
    
    Args:
        model: A Hugging Face transformers model object.
        
    Returns:
        int: Total number of trainable parameters.
    """
    return sum(p.numel() for p in model.parameters() if p.requires_grad)


def calculate_flops(
    parameters: int,
    sequence_length: int,
    k: int,
    layers: Optional[int] = None
) -> float:
    """
    Calculate FLOPs for a forward pass using the formula:
    FLOPs = parameters * sequence_length * k
    
    Args:
        parameters (int): Number of model parameters.
        sequence_length (int): Length of the input sequence.
        k (int): Number of passes/iterations (default 1).
        
    Returns:
        float: Estimated FLOPs.
    """
    return float(parameters * sequence_length * k)


def capture_metrics(output_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Capture system resource metrics including CPU, RAM, and GPU usage.
    
    Uses psutil for CPU/RAM and torch.cuda/nvidia-smi for GPU metrics.
    
    Args:
        output_path (str, optional): Path to save the metrics JSON. If None, 
                                   metrics are not written to disk.
                                   
    Returns:
        Dict[str, Any]: Dictionary containing:
            - runtime_s (float): Execution time in seconds.
            - ram_gb (float): RAM usage in GB.
            - gpu_util_pct (float): GPU utilization percentage.
            - gpu_memory_gb (float): GPU memory usage in GB.
    """
    start_time = time.time()
    
    # CPU/RAM metrics via psutil
    process = psutil.Process(os.getpid())
    cpu_percent = process.cpu_percent(interval=0.1)
    ram_info = process.memory_info()
    ram_gb = ram_info.rss / (1024 ** 3)  # Convert bytes to GB
    
    # GPU metrics
    gpu_util_pct = 0.0
    gpu_memory_gb = 0.0
    
    # Check if CUDA is available
    try:
        import torch
        if torch.cuda.is_available():
            # Get GPU utilization and memory via torch
            gpu_count = torch.cuda.device_count()
            if gpu_count > 0:
                # Use the first GPU for metrics
                gpu_util_pct = float(torch.cuda.utilization(0)) * 100
                gpu_memory_allocated = torch.cuda.memory_allocated(0) / (1024 ** 3)
                gpu_memory_reserved = torch.cuda.memory_reserved(0) / (1024 ** 3)
                # Use allocated memory as primary metric, or total if allocated is 0
                gpu_memory_gb = max(gpu_memory_allocated, gpu_memory_reserved)
            else:
                gpu_util_pct = 0.0
                gpu_memory_gb = 0.0
        else:
            # Fallback: try nvidia-smi via subprocess if torch.cuda not available
            try:
                result = subprocess.run(
                    ['nvidia-smi', '--query-gpu=utilization.gpu,memory.used', 
                     '--format=csv,noheader,nounits'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    lines = result.stdout.strip().split('\n')
                    if lines:
                        parts = lines[0].split(',')
                        if len(parts) >= 2:
                            gpu_util_pct = float(parts[0].strip())
                            gpu_memory_gb = float(parts[1].strip()) / 1024.0
            except (subprocess.TimeoutExpired, FileNotFoundError, ValueError):
                # nvidia-smi not available or failed
                pass
    except ImportError:
        # torch not installed
        pass
    
    runtime_s = time.time() - start_time
    
    metrics = {
        "runtime_s": round(runtime_s, 4),
        "ram_gb": round(ram_gb, 4),
        "gpu_util_pct": round(gpu_util_pct, 2),
        "gpu_memory_gb": round(gpu_memory_gb, 4)
    }
    
    # Write to file if path provided
    if output_path:
        output_dir = os.path.dirname(output_path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(metrics, f, indent=2)
    
    return metrics


def save_resource_metrics(metrics: Dict[str, Any], output_path: str) -> None:
    """
    Save resource metrics to a JSON file.
    
    Args:
        metrics (Dict[str, Any]): Metrics dictionary.
        output_path (str): Path to save the JSON file.
    """
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(metrics, f, indent=2)


def main():
    """
    Main entry point for resource monitoring utility.
    Captures metrics and saves to data/processed/resource_metrics.json.
    """
    output_path = "data/processed/resource_metrics.json"
    print(f"Capturing resource metrics...")
    metrics = capture_metrics(output_path)
    print(f"Metrics captured and saved to {output_path}")
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
