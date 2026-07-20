import json
import os
import time
import platform
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False


def get_model_param_count(model) -> int:
    """
    Calculate the total number of parameters in a PyTorch model.

    Args:
        model: A PyTorch nn.Module instance.

    Returns:
        Total number of parameters as an integer.
    """
    if not TORCH_AVAILABLE:
        raise RuntimeError("PyTorch is required to count model parameters.")
    return sum(p.numel() for p in model.parameters())


def calculate_flops(
    parameters: int,
    sequence_length: int,
    k: int,
    multiplier: float = 2.0
) -> float:
    """
    Calculate approximate FLOPs for a transformer inference pass.

    Formula: FLOPs = parameters * sequence_length * k * multiplier
    (multiplier accounts for forward/backward or specific architecture factors,
     defaulting to 2.0 for standard FLOP estimation per spec T005d).

    Args:
        parameters: Number of model parameters.
        sequence_length: Input sequence length.
        k: Number of loop iterations or samples.
        multiplier: FLOP multiplier constant.

    Returns:
        Estimated FLOPs as a float.
    """
    return parameters * sequence_length * k * multiplier


def capture_metrics(
    output_path: Optional[str] = None,
    include_gpu: bool = True
) -> Dict[str, Any]:
    """
    Capture runtime system metrics including time, RAM, and GPU usage.

    This function logs:
    - Timestamp
    - Platform info
    - CPU count
    - Available and used RAM (in GB)
    - GPU memory usage and utilization (if GPU available and include_gpu=True)

    It writes the collected metrics to a JSON file at the specified output path.
    If no path is provided, it defaults to 'data/processed/resource_metrics.json'
    relative to the project root.

    Args:
        output_path: Optional path to save the JSON metrics file.
        include_gpu: Whether to attempt to capture GPU metrics.

    Returns:
        A dictionary containing the captured metrics.
    """
    metrics: Dict[str, Any] = {
        "timestamp": datetime.now().isoformat(),
        "platform": {
            "system": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "python_version": platform.python_version()
        },
        "cpu": {
            "count": os.cpu_count()
        }
    }

    # RAM Metrics
    if PSUTIL_AVAILABLE:
        mem = psutil.virtual_memory()
        metrics["memory"] = {
            "total_gb": round(mem.total / (1024 ** 3), 2),
            "available_gb": round(mem.available / (1024 ** 3), 2),
            "used_gb": round(mem.used / (1024 ** 3), 2),
            "percent": round(mem.percent, 2)
        }
    else:
        metrics["memory"] = {
            "status": "psutil not installed",
            "note": "Install psutil for detailed memory metrics."
        }

    # GPU Metrics
    if include_gpu and TORCH_AVAILABLE:
        if torch.cuda.is_available():
            gpu_metrics = []
            for i in range(torch.cuda.device_count()):
                gpu_metrics.append({
                    "device_id": i,
                    "name": torch.cuda.get_device_name(i),
                    "total_memory_gb": round(torch.cuda.get_device_properties(i).total_memory / (1024 ** 3), 2),
                    "allocated_memory_gb": round(torch.cuda.memory_allocated(i) / (1024 ** 3), 2),
                    "reserved_memory_gb": round(torch.cuda.memory_reserved(i) / (1024 ** 3), 2),
                    "utilization_percent": torch.cuda.utilization(i)
                })
            metrics["gpu"] = {
                "available": True,
                "device_count": torch.cuda.device_count(),
                "devices": gpu_metrics
            }
        else:
            metrics["gpu"] = {
                "available": False,
                "reason": "CUDA not available in PyTorch"
            }
    elif include_gpu:
        metrics["gpu"] = {
            "available": False,
            "reason": "PyTorch not installed or GPU support missing"
        }
    else:
        metrics["gpu"] = {
            "skipped": True,
            "reason": "include_gpu flag set to False"
        }

    # Ensure output directory exists
    if output_path is None:
        # Default to project root relative path
        output_path = "data/processed/resource_metrics.json"

    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # Write to file
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

    return metrics


def main():
    """
    CLI entry point for capturing resource metrics.
    Usage: python -m src.utils capture
    """
    print("Capturing resource metrics...")
    metrics = capture_metrics()
    print(f"Metrics saved to {Path('data/processed/resource_metrics.json').resolve()}")
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()