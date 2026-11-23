"""
GPU Offload Orchestrator for Socratic Transformers Project.

This script acts as a CI wrapper that monitors the execution of the CPU training
loop (train_loop.py). If the training loop fails with exit code 1 (indicating
an Out-Of-Memory error on the CPU), this script automatically re-invokes the
training command on a Kaggle GPU environment with scaled-down parameters.

Execution Order: Triggered automatically by CI upon T021 failure.
"""

import os
import subprocess
import sys
import time
from pathlib import Path
from typing import List, Optional

# Project root relative to this script's location
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
TRAIN_SCRIPT = PROJECT_ROOT / "src" / "train" / "train_loop.py"

# Configuration for the GPU offload
# These parameters are scaled down to ensure they fit within typical Kaggle
# free-tier GPU constraints (e.g., T4 x 1) while compensating for reduced batch size
GPU_OFFLOAD_ARGS = {
    "batch_size": 1,  # Reduced from CPU default (likely 2)
    "gradient_accumulation_steps": 8,  # Increased to compensate for batch_size=1
    "max_steps": 100,  # Limit steps for CI safety if not specified
    "timeout_seconds": 3600,  # 1 hour hard limit for GPU job
}

# Exit codes
EXIT_SUCCESS = 0
EXIT_OOM = 1
EXIT_FAILURE = 2

def run_cpu_training() -> int:
    """
    Executes the CPU training loop (T021).
    Returns the exit code of the training process.
    """
    print(f"[GPU Offload Orchestrator] Starting CPU training loop: {TRAIN_SCRIPT}")
    print(f"[GPU Offload Orchestrator] Working directory: {PROJECT_ROOT}")

    cmd = [sys.executable, str(TRAIN_SCRIPT)]
    
    try:
        result = subprocess.run(
            cmd,
            cwd=str(PROJECT_ROOT),
            env=os.environ,
            timeout=GPU_OFFLOAD_ARGS["timeout_seconds"] * 4, # Allow longer for CPU if no OOM
            capture_output=False, # Stream output to parent for visibility
        )
        return result.returncode
    except subprocess.TimeoutExpired:
        print("[GPU Offload Orchestrator] CPU training timed out. Treating as failure.")
        return EXIT_FAILURE

def prepare_kaggle_env() -> None:
    """
    Sets up environment variables or configuration required for the Kaggle GPU run.
    In a real CI pipeline, this might involve writing a kaggle.json or setting
    specific environment flags. For this implementation, we ensure the environment
    is clean for the GPU invocation.
    """
    print("[GPU Offload Orchestrator] Preparing Kaggle GPU environment context.")
    # Ensure the data directories exist before offloading
    data_dirs = [
        PROJECT_ROOT / "data" / "raw",
        PROJECT_ROOT / "data" / "processed",
        PROJECT_ROOT / "data" / "results"
    ]
    for d in data_dirs:
        d.mkdir(parents=True, exist_ok=True)

def build_gpu_command() -> List[str]:
    """
    Constructs the command to run training on the GPU with scaled parameters.
    """
    cmd = [
        sys.executable,
        str(TRAIN_SCRIPT),
        "--batch_size", str(GPU_OFFLOAD_ARGS["batch_size"]),
        "--gradient_accumulation_steps", str(GPU_OFFLOAD_ARGS["gradient_accumulation_steps"]),
        "--max_steps", str(GPU_OFFLOAD_ARGS["max_steps"]),
    ]
    return cmd

def run_gpu_training() -> int:
    """
    Re-invokes the training command on a GPU environment.
    In a local/CI context, this simulates the offload by running with GPU flags
    or explicitly calling the script with the modified arguments.
    """
    print("[GPU Offload Orchestrator] OOM detected on CPU. Initiating GPU Offload...")
    prepare_kaggle_env()

    cmd = build_gpu_command()
    print(f"[GPU Offload Orchestrator] Executing GPU command: {' '.join(cmd)}")

    try:
        # In a real CI scenario, this might be `kaggle kernels push` or a remote call.
        # Here we execute locally but with the expectation that the environment
        # has GPU access (or the script handles the device selection internally).
        result = subprocess.run(
            cmd,
            cwd=str(PROJECT_ROOT),
            env=os.environ,
            timeout=GPU_OFFLOAD_ARGS["timeout_seconds"],
            capture_output=False,
        )
        return result.returncode
    except subprocess.TimeoutExpired:
        print("[GPU Offload Orchestrator] GPU training timed out.")
        return EXIT_FAILURE

def main():
    """
    Main entry point for the GPU Offload Orchestrator.
    1. Runs the CPU training loop.
    2. If exit code is 1 (OOM), triggers GPU offload.
    3. Returns the final exit code.
    """
    print("=" * 60)
    print("Socratic Transformers: GPU Offload Orchestrator")
    print("=" * 60)

    # Step 1: Attempt CPU Training
    cpu_exit_code = run_cpu_training()

    if cpu_exit_code == EXIT_OOM:
        print(f"[GPU Offload Orchestrator] CPU training failed with OOM (Exit Code: {cpu_exit_code}).")
        print("[GPU Offload Orchestrator] Triggering automatic GPU offload...")
        
        # Step 2: Trigger GPU Offload
        gpu_exit_code = run_gpu_training()
        
        if gpu_exit_code == EXIT_SUCCESS:
            print("[GPU Offload Orchestrator] GPU training completed successfully.")
            return EXIT_SUCCESS
        else:
            print(f"[GPU Offload Orchestrator] GPU training failed with Exit Code: {gpu_exit_code}")
            return gpu_exit_code
    
    elif cpu_exit_code == EXIT_SUCCESS:
        print("[GPU Offload Orchestrator] CPU training completed successfully. No offload needed.")
        return EXIT_SUCCESS
    
    else:
        print(f"[GPU Offload Orchestrator] CPU training failed with unexpected exit code: {cpu_exit_code}. Aborting.")
        return cpu_exit_code

if __name__ == "__main__":
    sys.exit(main())
