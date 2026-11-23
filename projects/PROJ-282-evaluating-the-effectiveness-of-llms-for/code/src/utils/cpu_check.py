"""
CPU-Only Pre-Flight Check for LLM Pipeline.

This script checks for GPU availability using PyTorch.
If a GPU is detected, it writes an abort signal and exits with code 1.
If only CPU is available, it writes a success signal and exits with code 0.
"""
import os
import sys
import json
import torch
from pathlib import Path

# Import project root utility to ensure consistent pathing
from src.utils.config import get_project_root


def check_cpu_only() -> dict:
    """
    Checks if GPU is available via torch.
    
    Returns:
        dict: Status object with 'status' and 'abort' keys.
    """
    gpu_available = torch.cuda.is_available()
    
    if gpu_available:
        return {
            "status": "GPU_DETECTED",
            "abort": True
        }
    else:
        return {
            "status": "CPU_ONLY",
            "abort": False
        }


def main():
    """
    Main entry point for the CPU check script.
    Writes result to data/logs/cpu_check.json and exits with appropriate code.
    """
    project_root = get_project_root()
    logs_dir = project_root / "data" / "logs"
    output_file = logs_dir / "cpu_check.json"
    
    # Ensure logs directory exists
    logs_dir.mkdir(parents=True, exist_ok=True)
    
    # Perform check
    result = check_cpu_only()
    
    # Write result to JSON file
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2)
    
    # Exit with appropriate code
    if result["abort"]:
        print(f"GPU detected ({torch.cuda.get_device_name(0) if torch.cuda.device_count() > 0 else 'unknown'}). Aborting CPU-only pipeline.")
        sys.exit(1)
    else:
        print("CPU-only environment confirmed. Proceeding.")
        sys.exit(0)


if __name__ == "__main__":
    main()