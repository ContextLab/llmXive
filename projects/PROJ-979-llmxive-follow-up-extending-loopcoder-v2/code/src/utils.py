"""
Utility functions for seed management, metrics, and flops calculation.
"""
import os
import random
import time
import platform
from datetime import datetime
from pathlib import Path
import json
import numpy as np

try:
    import torch
except ImportError:
    torch = None

def set_global_seed(seed: int = 42):
    """Set random seed for reproducibility across libraries."""
    random.seed(seed)
    np.random.seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)
    
    if torch is not None:
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)

def get_model_param_count(model) -> int:
    """Get the number of parameters in a model."""
    if model is None:
        return 0
    return sum(p.numel() for p in model.parameters())

def calculate_flops(model_params: int, seq_len: int, k: int) -> float:
    """
    Calculate approximate FLOPs for inference.
    Formula: 2 * params * seq_len * k (simplified)
    """
    return 2.0 * model_params * seq_len * k

def capture_metrics(mode: str = "default") -> dict:
    """
    Capture system metrics (CPU, Memory, Time).
    Returns a dictionary of metrics.
    """
    metrics = {
        "timestamp": datetime.now().isoformat(),
        "mode": mode,
        "platform": platform.platform(),
        "python_version": platform.python_version(),
        "cpu_count": os.cpu_count(),
    }
    
    try:
        import psutil
        process = psutil.Process()
        metrics["memory_mb"] = process.memory_info().rss / (1024 * 1024)
        metrics["cpu_percent"] = process.cpu_percent()
    except ImportError:
        metrics["memory_mb"] = None
        metrics["cpu_percent"] = None
        metrics["psutil_note"] = "psutil not installed"

    return metrics

def save_resource_metrics(metrics: dict, output_path: str):
    """Save resource metrics to a JSON file."""
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(metrics, f, indent=2)

def main():
    # Example usage for testing
    set_global_seed(42)
    print(f"Seed set to 42. CPU Count: {os.cpu_count()}")

if __name__ == "__main__":
    main()
