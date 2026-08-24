import json
import os
import time
import platform
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
import random
import numpy as np
import torch

def set_global_seed(seed: int = 42):
    """Set global random seeds for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)

def get_model_param_count(model) -> int:
    """Get the number of parameters in a model."""
    return sum(p.numel() for p in model.parameters())

def calculate_flops(model_params: int, seq_len: int, k: int) -> float:
    """Calculate FLOPs for a given model and sequence length."""
    # Approximate FLOPs calculation: 2 * params * seq_len * k
    return 2 * model_params * seq_len * k

def capture_metrics(mode: str = "default") -> Dict[str, Any]:
    """Capture system metrics."""
    metrics = {
        "timestamp": datetime.now().isoformat(),
        "mode": mode,
        "platform": platform.platform(),
        "python_version": platform.python_version(),
        "cpu_count": os.cpu_count(),
        "timestamp_unix": time.time()
    }
    
    if torch.cuda.is_available():
        metrics["gpu_available"] = True
        metrics["gpu_name"] = torch.cuda.get_device_name(0)
        metrics["gpu_memory_total"] = torch.cuda.get_device_properties(0).total_memory
        metrics["gpu_memory_allocated"] = torch.cuda.memory_allocated(0)
    else:
        metrics["gpu_available"] = False
    
    return metrics

def save_resource_metrics(metrics: Dict[str, Any], output_path: str):
    """Save resource metrics to a JSON file."""
    with open(output_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    print(f"Saved resource metrics to {output_path}")

def main():
    # Example usage
    set_global_seed(42)
    metrics = capture_metrics("test")
    save_resource_metrics(metrics, "data/processed/resource_metrics.json")

if __name__ == "__main__":
    main()
