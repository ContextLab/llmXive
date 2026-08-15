import json
import os
import time
import platform
from datetime import datetime
from pathlib import Path
import random
import numpy as np
import torch
import psutil

def set_global_seed(seed: int = 42):
    """
    Set global random seed for reproducibility.
    """
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)

def get_model_param_count(model) -> int:
    """
    Get the number of parameters in a model.
    """
    return sum(p.numel() for p in model.parameters())

def calculate_flops(model_params: int, seq_len: int, k: int) -> float:
    """
    Calculate FLOPs for a given model and sequence length.
    Formula: FLOPs = parameters * sequence_length * k
    """
    return model_params * seq_len * k

def capture_metrics(mode: str = "validation") -> Dict[str, Any]:
    """
    Capture resource metrics.
    """
    start_time = time.perf_counter()
    
    # CPU/RAM metrics
    cpu_percent = psutil.cpu_percent(interval=1)
    ram_gb = psutil.virtual_memory().used / (1024 ** 3)
    
    # GPU metrics
    gpu_util_pct = None
    gpu_memory_gb = None
    
    if torch.cuda.is_available():
        try:
            result = subprocess.run(
                ["nvidia-smi", "--query-gpu=utilization.gpu,memory.used", "--format=csv,noheader"],
                capture_output=True,
                text=True,
                timeout=5
            )
            lines = result.stdout.strip().split("\n")
            if lines:
                parts = lines[0].split(",")
                gpu_util_pct = float(parts[0].strip().replace("%", ""))
                gpu_memory_gb = float(parts[1].strip().replace(" MiB", "")) / 1024
        except Exception as e:
            logger.warning(f"Failed to get GPU metrics: {e}")
    
    runtime_s = time.perf_counter() - start_time
    
    metrics = {
        "runtime_s": runtime_s,
        "ram_gb": ram_gb,
        "gpu_util_pct": gpu_util_pct,
        "gpu_memory_gb": gpu_memory_gb,
        "mode": mode
    }
    
    # Save metrics
    save_resource_metrics(metrics)
    
    return metrics

def save_resource_metrics(metrics: Dict[str, Any], output_path: str = "data/processed/resource_metrics.json"):
    """
    Save resource metrics to JSON.
    """
    with open(output_path, "w") as f:
        json.dump(metrics, f, indent=2)
    logger.info(f"Resource metrics saved to {output_path}")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Utils")
    parser.add_argument("--mode", type=str, default="validation", help="Mode for metric capture")
    
    args = parser.parse_args()
    
    metrics = capture_metrics(args.mode)
    print(json.dumps(metrics, indent=2))

if __name__ == "__main__":
    main()