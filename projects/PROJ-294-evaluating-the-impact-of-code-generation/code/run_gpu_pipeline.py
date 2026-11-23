"""
GPU Execution Wrapper for llmXive Project PROJ-294.

This script orchestrates GPU-dependent tasks (T051, T052) and handles
environment detection for the execution stage.

Constraints:
- Must exit cleanly if no GPU is detected, signaling the execution stage
  to provision a GPU runner.
- Does not perform generation itself; delegates to T051 (codegen) and T052 (llama).
"""

import os
import sys
import subprocess
import logging
import time

# Add project root to path if running from elsewhere
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Import shared utilities from utils (contract: setup_logging, get_logger)
try:
    from utils import setup_logging, get_logger, set_task_id
except ImportError:
    # Fallback if utils is not importable (should not happen in valid env)
    logging.basicConfig(level=logging.INFO, format='%(asctime)s [GPU-WRAPPER] %(message)s')
    logger = logging.getLogger("GPU-WRAPPER")
else:
    # Use the project's logging setup
    set_task_id("T055-GPU-ORCHESTRATOR")
    logger = get_logger("GPU-WRAPPER")

def check_gpu_availability() -> bool:
    """
    Check if a CUDA-compatible GPU is available.

    Returns:
        bool: True if GPU is available, False otherwise.
    """
    try:
        import torch
        if torch.cuda.is_available():
            device_count = torch.cuda.device_count()
            logger.info(f"GPU available: {device_count} device(s). {torch.cuda.get_device_name(0)}")
            return True
        else:
            logger.warning("CUDA is not available in this environment.")
            return False
    except ImportError:
        logger.warning("PyTorch is not installed. Cannot detect GPU.")
        return False
    except Exception as e:
        logger.error(f"Error checking GPU availability: {e}")
        return False

def run_gpu_task(script_name: str, args: list = None) -> int:
    """
    Execute a GPU-dependent script.

    Args:
        script_name: Name of the script in code/ directory.
        args: Optional list of arguments to pass to the script.

    Returns:
        int: Return code of the subprocess.
    """
    script_path = os.path.join(PROJECT_ROOT, "code", script_name)
    if not os.path.exists(script_path):
        logger.error(f"Script not found: {script_path}")
        return 1

    cmd = [sys.executable, script_path]
    if args:
        cmd.extend(args)

    logger.info(f"Executing GPU task: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, check=False)
        return result.returncode
    except Exception as e:
        logger.error(f"Failed to execute subprocess: {e}")
        return 1

def main():
    """
    Main entry point for the GPU pipeline wrapper.
    """
    logger.info("Starting GPU Pipeline Wrapper (T055)")

    # 1. Check GPU Availability
    if not check_gpu_availability():
        logger.critical("No GPU detected. Exiting cleanly to signal execution stage to provision a GPU runner.")
        # Exit with code 0 to indicate 'clean exit' rather than a crash,
        # but the execution stage interprets this specific exit condition
        # as a signal to switch runners if it supports that protocol.
        # However, standard convention for 'provision needed' is often a specific non-zero code
        # or a clean 0 with a specific log message. The task says "exit cleanly".
        # We will exit 0 but log the critical signal.
        # If the execution stage expects a non-zero to retry, we might need to adjust,
        # but "exit cleanly" usually implies 0.
        # Re-reading: "signal the execution stage to provision a GPU runner".
        # If this is a local run, it might just exit. If it's an orchestrator,
        # it might need to return a specific code. Assuming standard 0 for 'done'
        # but the log message is the signal.
        # To be safe and explicit as per "signal", we can exit 0.
        sys.exit(0)

    # 2. Run T051: GPU Inference (CodeGen)
    # Note: T051 is codegen-350M on GPU.
    logger.info("Triggering T051: CodeGen GPU Inference")
    rc_codegen = run_gpu_task("generate_code_gpu.py")
    if rc_codegen != 0:
        logger.error(f"T051 (generate_code_gpu.py) failed with code {rc_codegen}")
        # Do not exit immediately; attempt T052 if possible, or fail all.
        # Given the dependency chain, if T051 fails, T053 might fail later.
        # We will continue to T052 to gather as much data as possible,
        # but mark the overall status.

    # 3. Run T052: CodeLlama Sensitivity (LLaMA)
    # Note: T052 is CodeLlama-7b on GPU.
    logger.info("Triggering T052: CodeLlama GPU Inference")
    rc_llama = run_gpu_task("generate_code_llama.py")
    if rc_llama != 0:
        logger.error(f"T052 (generate_code_llama.py) failed with code {rc_llama}")

    # 4. Final Status
    if rc_codegen == 0 and rc_llama == 0:
        logger.info("GPU Pipeline completed successfully.")
        sys.exit(0)
    else:
        logger.warning("GPU Pipeline completed with errors.")
        sys.exit(1)

if __name__ == "__main__":
    main()