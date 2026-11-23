import os
import sys
import subprocess
import logging
import json
from pathlib import Path
from typing import Optional, Dict, Any
from config import load_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class GPUComputeEscapeHatch:
    """
    Handles re-running training on a generic GPU runner if available.
    Uses environment variables to detect GPU availability and triggers
    the training script if conditions are met.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or load_config()
        self.output_path = Path("data/processed/escape_hatch_log.json")
        self.training_script = Path("code/training.py")
        
        # Ensure output directory exists
        self.output_path.parent.mkdir(parents=True, exist_ok=True)

    def is_gpu_available(self) -> bool:
        """
        Check if a GPU is available in the current environment.
        Checks for CUDA availability via PyTorch or nvidia-smi.
        """
        try:
            import torch
            if torch.cuda.is_available():
                logger.info("GPU detected via PyTorch: CUDA is available.")
                return True
        except ImportError:
            logger.warning("PyTorch not installed; cannot check CUDA via torch.")
        
        # Fallback: check nvidia-smi
        try:
            subprocess.run(
                ["nvidia-smi"], 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE, 
                check=True,
                timeout=10
            )
            logger.info("GPU detected via nvidia-smi.")
            return True
        except (subprocess.SubprocessError, FileNotFoundError, subprocess.TimeoutExpired):
            logger.info("No GPU detected via nvidia-smi or CUDA not available.")
            return False

    def trigger_gpu_run(self) -> bool:
        """
        Trigger the training script on the current runner if GPU is available.
        Returns True if the run was triggered successfully, False otherwise.
        """
        if not self.is_gpu_available():
            logger.info("Skipping GPU escape hatch: No GPU available.")
            return False

        logger.info("GPU available. Triggering training script on GPU runner...")
        
        # Prepare environment variables for GPU run
        env = os.environ.copy()
        env["GPU_ESCAPE_HATCH_TRIGGERED"] = "true"
        
        try:
            # Run the training script
            result = subprocess.run(
                [sys.executable, str(self.training_script)],
                env=env,
                capture_output=True,
                text=True,
                timeout=3600  # 1 hour timeout for training
            )
            
            if result.returncode == 0:
                logger.info("Training script completed successfully on GPU runner.")
                return True
            else:
                logger.error(f"Training script failed with return code {result.returncode}")
                logger.error(f"Stderr: {result.stderr}")
                return False

        except subprocess.TimeoutExpired:
            logger.error("Training script timed out on GPU runner.")
            return False
        except Exception as e:
            logger.error(f"Failed to trigger training script: {e}")
            return False

    def log_result(self, triggered: bool, status: str, error: Optional[str] = None):
        """
        Log the result of the escape hatch attempt to a JSON file.
        """
        log_entry = {
            "triggered": triggered,
            "runner_type": "gpu",
            "status": status,
            "timestamp": str(Path(self.output_path).parent.stat().st_mtime) if triggered else None,
            "error": error
        }
        
        # Remove None values for cleaner JSON
        log_entry = {k: v for k, v in log_entry.items() if v is not None}
        
        with open(self.output_path, 'w') as f:
            json.dump(log_entry, f, indent=2)
        
        logger.info(f"Escape hatch result logged to {self.output_path}")

    def run(self) -> Dict[str, Any]:
        """
        Main entry point to execute the GPU escape hatch logic.
        Returns the result dictionary.
        """
        logger.info("Starting GPU Compute Escape Hatch...")
        
        if not self.training_script.exists():
            error_msg = f"Training script not found: {self.training_script}"
            logger.error(error_msg)
            self.log_result(triggered=False, status="fail", error=error_msg)
            return {"success": False, "error": error_msg}

        triggered = self.trigger_gpu_run()
        
        if triggered:
            self.log_result(triggered=True, status="success")
            return {"success": True, "triggered": True, "status": "success"}
        else:
            # Check if it was skipped (no GPU) vs failed
            if not self.is_gpu_available():
                self.log_result(triggered=False, status="skipped")
                return {"success": True, "triggered": False, "status": "skipped", "reason": "No GPU available"}
            else:
                self.log_result(triggered=False, status="fail", error="Training execution failed")
                return {"success": False, "triggered": False, "status": "fail"}


def main():
    """
    CLI entry point for the GPU escape hatch.
    """
    logger.info("Executing GPU Escape Hatch via CLI...")
    
    try:
        escape_hatch = GPUComputeEscapeHatch()
        result = escape_hatch.run()
        
        if result["success"]:
            logger.info(f"GPU Escape Hatch completed: {result['status']}")
            sys.exit(0)
        else:
            logger.error(f"GPU Escape Hatch failed: {result.get('error', 'Unknown error')}")
            sys.exit(1)
            
    except Exception as e:
        logger.exception(f"Unhandled exception in GPU Escape Hatch: {e}")
        # Log a failure entry
        try:
            log_path = Path("data/processed/escape_hatch_log.json")
            log_path.parent.mkdir(parents=True, exist_ok=True)
            with open(log_path, 'w') as f:
                json.dump({
                    "triggered": False,
                    "runner_type": "gpu",
                    "status": "fail",
                    "error": str(e)
                }, f, indent=2)
        except Exception:
            pass
        sys.exit(1)


if __name__ == "__main__":
    main()