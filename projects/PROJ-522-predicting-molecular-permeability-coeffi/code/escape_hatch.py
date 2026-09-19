import os
import sys
import subprocess
import logging
from pathlib import Path
from typing import Optional, Dict, Any
import json
import time

# Import config to read environment settings
from config import load_config

# Configure logging to match project standards
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('data/processed/escape_hatch.log')
    ]
)
logger = logging.getLogger(__name__)

class GPUComputeEscapeHatch:
    """
    Implements a 'GPU Escape Hatch' strategy.
    Detects if the current runner lacks GPU resources or if ingestion is failing
    due to resource constraints, and triggers a re-run on a generic GPU-enabled runner
    if environment variables permit.

    This class does NOT use Kaggle API or kernel IDs as per constraints.
    It relies on environment variables to define the target runner context.
    """

    def __init__(self, config_path: Optional[Path] = None):
        self.config = load_config(config_path) if config_path else load_config()
        self.log_path = Path("data/processed/escape_hatch_log.json")
        self.ensure_data_dirs()

    def ensure_data_dirs(self):
        """Ensure output directories exist."""
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def _check_current_environment(self) -> Dict[str, Any]:
        """
        Checks the current environment for GPU availability and memory constraints.
        Returns a status dict.
        """
        has_gpu = False
        gpu_name = None
        memory_limit_exceeded = False

        try:
            # Attempt to import torch to check GPU
            import torch
            if torch.cuda.is_available():
                has_gpu = True
                gpu_name = torch.cuda.get_device_name(0)
            else:
                has_gpu = False
        except ImportError:
            logger.warning("PyTorch not installed. Assuming no GPU available for acceleration.")
            has_gpu = False
        except Exception as e:
            logger.warning(f"Error checking CUDA: {e}")
            has_gpu = False

        # Check environment variable for forced trigger (e.g., if ingestion failed previously)
        force_trigger = os.getenv("ESCAPE_HATCH_FORCE_TRIGGER", "false").lower() == "true"
        if force_trigger:
            logger.info("ESCAPE_HATCH_FORCE_TRIGGER is set. Preparing to offload.")
            # Even if we have a GPU locally, we might want to offload to a dedicated large-memory runner
            # based on project config.
            if self.config.get("GPU_ESCAPE_HATCH", {}).get("always_offload", False):
                has_gpu = False # Pretend we don't have it to trigger the logic

        return {
            "has_gpu": has_gpu,
            "gpu_name": gpu_name,
            "force_trigger": force_trigger,
            "needs_gpu": not has_gpu or force_trigger
        }

    def _trigger_external_runner(self) -> bool:
        """
        Triggers the ingestion process on a generic GPU runner.
        In a real CI/CD context, this would dispatch a job to a GPU node.
        Here, we simulate the trigger by checking for a specific environment variable
        that indicates we are *on* the GPU runner, or by attempting to re-run the ingestion
        script with specific flags if we are in a local emulation mode.

        Since we cannot actually spin up a new container in this environment,
        we verify if the environment variables indicate we are *already* on the GPU runner.
        If not, we log the intent and return False (simulating a trigger to an external system).
        If the environment variable ESCAPE_HATCH_IS_GPU_RUNNER is set, we execute the ingestion.
        """
        is_gpu_runner = os.getenv("ESCAPE_HATCH_IS_GPU_RUNNER", "false").lower() == "true"

        if not is_gpu_runner:
            logger.info("Not running on a GPU runner. Triggering external dispatch (simulated).")
            logger.info("In a real deployment, this would call: kubectl run, AWS Batch, or similar.")
            # We cannot actually spawn a new process here that survives this container,
            # so we log the request and return False to indicate we didn't complete the work locally.
            return False

        # If we are on the GPU runner, execute the ingestion
        logger.info("Detected GPU runner environment. Executing ingestion script.")
        
        ingestion_script = Path("code/ingestion.py")
        if not ingestion_script.exists():
            logger.error(f"Ingestion script not found at {ingestion_script}")
            return False

        try:
            # Re-run ingestion with GPU-specific flags if any, or standard flags
            # We assume the ingestion script handles its own logic
            cmd = [sys.executable, str(ingestion_script), "--source", "nist,pubchem,mtr"]
            
            # Run with timeout to prevent hanging
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600  # 10 minutes timeout for the escape hatch run
            )

            if result.returncode == 0:
                logger.info("Ingestion completed successfully on GPU runner.")
                return True
            else:
                logger.error(f"Ingestion failed on GPU runner: {result.stderr}")
                return False

        except subprocess.TimeoutExpired:
            logger.error("Ingestion timed out on GPU runner.")
            return False
        except Exception as e:
            logger.error(f"Failed to execute ingestion on GPU runner: {e}")
            return False

    def run(self) -> Dict[str, Any]:
        """
        Main entry point to execute the escape hatch logic.
        Returns a status dictionary to be saved to escape_hatch_log.json.
        """
        logger.info("Starting GPU Escape Hatch check...")
        
        env_status = self._check_current_environment()
        triggered = False
        status = "fail"
        runner_type = "cpu" # Default

        if env_status["needs_gpu"]:
            logger.info("GPU resources missing or forced trigger active. Attempting escape hatch.")
            runner_type = "gpu"
            triggered = self._trigger_external_runner()
            if triggered:
                status = "success"
            else:
                status = "fail"
        else:
            logger.info("Current environment has sufficient GPU resources. No escape hatch needed.")
            triggered = False
            status = "not_needed"
            runner_type = "gpu" if env_status["has_gpu"] else "cpu"

        result = {
            "triggered": triggered,
            "runner_type": runner_type,
            "status": status,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "details": {
                "has_gpu_local": env_status["has_gpu"],
                "gpu_name_local": env_status["gpu_name"],
                "force_triggered": env_status["force_trigger"]
            }
        }

        # Write result to file
        try:
            with open(self.log_path, 'w') as f:
                json.dump(result, f, indent=2)
            logger.info(f"Escape hatch log written to {self.log_path}")
        except Exception as e:
            logger.error(f"Failed to write escape hatch log: {e}")

        return result

def main():
    """CLI entry point for the escape hatch module."""
    hatch = GPUComputeEscapeHatch()
    result = hatch.run()
    print(json.dumps(result, indent=2))
    sys.exit(0 if result["status"] in ["success", "not_needed"] else 1)

if __name__ == "__main__":
    main()