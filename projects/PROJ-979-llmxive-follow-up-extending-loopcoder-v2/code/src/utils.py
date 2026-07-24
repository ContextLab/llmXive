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

# Configure logging
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
PROCESSED_DATA_DIR = Path("data/processed")

def get_model_param_count(model: Any) -> int:
    """
    Get the number of parameters in a model.
    
    Args:
        model: Model object
        
    Returns:
        Number of parameters
    """
    return sum(p.numel() for p in model.parameters())

def calculate_flops(parameters: int, sequence_length: int, k: int = 1) -> float:
    """
    Calculate FLOPs for a given scenario.
    
    Formula: FLOPs = parameters * sequence_length * k
    
    Args:
        parameters: Number of model parameters
        sequence_length: Sequence length
        k: Number of loops/iterations
        
    Returns:
        Estimated FLOPs
    """
    return parameters * sequence_length * k

def capture_metrics() -> Dict[str, float]:
    """
    Capture runtime metrics (runtime, RAM, GPU usage).
    
    This function measures the actual resource usage of the current process.
    It attempts to use nvidia-smi for GPU metrics if available, falling back
    to torch.cuda if torch is available, otherwise reporting 0.0 for GPU metrics.
    
    Returns:
        Dictionary with metrics: runtime_s, ram_gb, gpu_util_pct
    """
    start_time = time.time()
    
    metrics = {
        "runtime_s": 0.0,
        "ram_gb": 0.0,
        "gpu_util_pct": 0.0,
        "timestamp": datetime.now().isoformat()
    }
    
    # Get RAM usage using psutil
    try:
        import psutil
        process = psutil.Process(os.getpid())
        mem_info = process.memory_info()
        metrics["ram_gb"] = mem_info.rss / (1024 ** 3)
    except ImportError:
        logger.warning("psutil not available, RAM usage not captured. Installing psutil is recommended.")
    except Exception as e:
        logger.warning(f"Failed to capture RAM usage: {e}")
    
    # Get GPU usage
    # Priority 1: nvidia-smi (system level, no torch dependency)
    gpu_detected = False
    try:
        import subprocess
        # Run nvidia-smi to get GPU utilization
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=utilization.gpu", "--format=csv,noheader,nounits"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0 and result.stdout.strip():
            # Parse the output (might have multiple GPUs, take the first one or average)
            util_values = [float(x.strip()) for x in result.stdout.strip().split('\n') if x.strip()]
            if util_values:
                metrics["gpu_util_pct"] = sum(util_values) / len(util_values)
                gpu_detected = True
            else:
                metrics["gpu_util_pct"] = 0.0
        else:
            metrics["gpu_util_pct"] = 0.0
    except FileNotFoundError:
        logger.debug("nvidia-smi not found in PATH. GPU metrics will be 0.0 unless torch is available.")
    except subprocess.TimeoutExpired:
        logger.warning("nvidia-smi timed out.")
    except Exception as e:
        logger.warning(f"Failed to capture GPU usage via nvidia-smi: {e}")
    
    # Priority 2: torch.cuda (if torch is available and nvidia-smi failed or wasn't used)
    if not gpu_detected:
        try:
            import torch
            if torch.cuda.is_available():
                # torch.cuda.utilization() gives GPU utilization percentage
                # Note: This might be 0.0 if the GPU is idle or the metric isn't exposed
                try:
                    util = torch.cuda.utilization()
                    metrics["gpu_util_pct"] = float(util)
                    gpu_detected = True
                except AttributeError:
                    # Older torch versions might not have this
                    pass
                
                # Fallback: check if any memory is allocated as a proxy for GPU activity
                allocated_memory = torch.cuda.memory_allocated()
                if allocated_memory > 0:
                    # If memory is allocated, assume some GPU usage, but we can't know the exact %
                    # We leave it as is from nvidia-smi or 0.0 if torch.utilization failed
                    pass
            else:
                metrics["gpu_util_pct"] = 0.0
        except ImportError:
            logger.debug("torch not available, GPU usage not captured via torch.")
        except Exception as e:
            logger.warning(f"Failed to capture GPU usage via torch: {e}")
    
    # Calculate runtime
    metrics["runtime_s"] = time.time() - start_time
    
    return metrics

def save_resource_metrics(metrics: Dict[str, float], output_path: str = None):
    """
    Save resource metrics to JSON file.
    
    Args:
        metrics: Metrics dictionary
        output_path: Output file path
    """
    if output_path is None:
        output_path = str(PROCESSED_DATA_DIR / "resource_metrics.json")
    
    # Ensure directory exists
    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    
    logger.info(f"Saved resource metrics to {output_path}")

def main():
    """Main entry point for utility functions."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Utility functions for resource monitoring")
    parser.add_argument("--capture", action="store_true", help="Capture and save metrics")
    parser.add_argument("--output", type=str, default=None, help="Output file path for metrics")
    parser.add_argument("--duration", type=float, default=0.0, help="Duration to simulate work (seconds)")
    
    args = parser.parse_args()
    
    if args.capture:
        # Simulate some work if duration is specified
        if args.duration > 0:
            logger.info(f"Simulating work for {args.duration} seconds...")
            time.sleep(args.duration)
        
        metrics = capture_metrics()
        save_resource_metrics(metrics, args.output)
        logger.info(f"Metrics captured and saved: {metrics}")
    else:
        parser.print_help()

if __name__ == "__main__":
    main()