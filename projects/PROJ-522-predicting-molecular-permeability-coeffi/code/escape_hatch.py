"""
GPU Escape Hatch Module for llmXive Project

Implements a fallback mechanism to trigger GPU training on Kaggle when CPU training
exceeds timeout or fails. Uses the Kaggle API to submit a job to a pre-configured
kernel.
"""
import os
import sys
import subprocess
import logging
from pathlib import Path
from typing import Optional, Dict, Any

# Import from existing project modules
from config import load_config
from utils.logger import setup_logging

# Configure logging
logger = logging.getLogger(__name__)

# Constants
KAGGLE_DOCKER_IMAGE = "pytorch/pytorch:2.0.1-cuda11.7-cudnn8-runtime"
KAGGLE_KERAS_SCRIPT_PATH = "code/training.py"
KAGGLE_CONFIG_DIR = Path(os.environ.get("KAGGLE_CONFIG_DIR", "~/.kaggle")).expanduser()
KAGGLE_CREDS_FILE = KAGGLE_CONFIG_DIR / "kaggle.json"

class KaggleGPUEscapeHatch:
    """
    Handles the logic to trigger a GPU training run on Kaggle as a fallback
    when CPU training fails or times out.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or load_config()
        self.kaggle_username = os.environ.get("KAGGLE_USERNAME")
        self.kaggle_key = os.environ.get("KAGGLE_KEY")
        self.kernel_id = self.config.get("kaggle", {}).get("kernel_id")
        
        if not self.kernel_id:
            logger.warning("Kaggle kernel ID not configured. GPU escape hatch will be disabled.")
            self.kernel_id = None

    def _validate_credentials(self) -> bool:
        """
        Validates that Kaggle credentials are available.
        """
        if not self.kaggle_username or not self.kaggle_key:
            logger.error("Kaggle credentials (KAGGLE_USERNAME, KAGGLE_KEY) not found in environment.")
            return False
        
        if not self.kaggle_key:
            logger.error("Kaggle key not found.")
            return False

        return True

    def _prepare_kaggle_json(self) -> bool:
        """
        Prepares the kaggle.json file for the Kaggle API if it doesn't exist.
        """
        KAGGLE_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        
        if not KAGGLE_CREDS_FILE.exists():
            logger.info(f"Creating Kaggle credentials file at {KAGGLE_CREDS_FILE}")
            try:
                creds = {
                    "username": self.kaggle_username,
                    "key": self.kaggle_key
                }
                import json
                with open(KAGGLE_CREDS_FILE, 'w') as f:
                    json.dump(creds, f)
                os.chmod(KAGGLE_CREDS_FILE, 0o600)
                logger.info("Kaggle credentials file created successfully.")
            except Exception as e:
                logger.error(f"Failed to create Kaggle credentials file: {e}")
                return False
        else:
            logger.info("Kaggle credentials file already exists.")

        return True

    def _trigger_kaggle_kernel(self) -> bool:
        """
        Triggers the Kaggle kernel using the Kaggle CLI.
        """
        if not self.kernel_id:
            logger.error("No Kaggle kernel ID configured. Cannot trigger GPU run.")
            return False

        logger.info(f"Triggering Kaggle kernel: {self.kernel_id}")

        try:
            # Ensure kaggle CLI is available
            result = subprocess.run(
                ["kaggle", "-v"],
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                logger.error("Kaggle CLI not found. Please install it via 'pip install kaggle'.")
                return False

            # Trigger the kernel
            cmd = [
                "kaggle", "kernels", "run",
                "-k", self.kernel_id,
                "--quiet"
            ]

            logger.info(f"Executing command: {' '.join(cmd)}")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60  # Timeout for the API call itself
            )

            if result.returncode == 0:
                logger.info("Kaggle kernel triggered successfully.")
                return True
            else:
                logger.error(f"Failed to trigger Kaggle kernel: {result.stderr}")
                return False

        except subprocess.TimeoutExpired:
            logger.error("Timeout while triggering Kaggle kernel.")
            return False
        except Exception as e:
            logger.error(f"Unexpected error triggering Kaggle kernel: {e}")
            return False

    def activate(self, failure_reason: str) -> bool:
        """
        Main entry point to activate the GPU escape hatch.
        
        Args:
            failure_reason: Description of why the CPU training failed.
        
        Returns:
            bool: True if the GPU run was successfully triggered, False otherwise.
        """
        logger.info(f"Activating GPU escape hatch due to: {failure_reason}")

        if not self._validate_credentials():
            logger.error("Aborting GPU escape hatch: Invalid credentials.")
            return False

        if not self._prepare_kaggle_json():
            logger.error("Aborting GPU escape hatch: Failed to prepare credentials.")
            return False

        success = self._trigger_kaggle_kernel()
        
        if success:
            logger.info("GPU escape hatch activation successful.")
        else:
            logger.error("GPU escape hatch activation failed.")

        return success


def main():
    """
    CLI entry point for testing the escape hatch mechanism.
    """
    setup_logging()
    logger.info("Testing GPU Escape Hatch mechanism...")

    try:
        escape_hatch = KaggleGPUEscapeHatch()
        success = escape_hatch.activate(failure_reason="Manual test trigger")
        
        if success:
            print("GPU Escape Hatch triggered successfully.")
            sys.exit(0)
        else:
            print("GPU Escape Hatch failed to trigger.")
            sys.exit(1)
            
    except Exception as e:
        logger.exception(f"Unhandled exception in main: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
