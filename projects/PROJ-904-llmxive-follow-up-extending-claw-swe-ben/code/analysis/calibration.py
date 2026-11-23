"""
Quantization Calibration Module.

Implements a pilot inference run to calibrate the quantization penalty for Q4_K_M
on CPU. Enforces a strict 60‑minute timeout and writes the result to
state/quantization_penalty.json.
"""

import json
import logging
import os
import signal
import sys
import time
from pathlib import Path
from typing import Optional, Dict, Any

# Ensure project root is in path for imports if run as script
if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

from models.quantization import load_model_q4_k_m
from utils.logger import setup_logger, log_error

# Additional import for real data
from datasets import load_dataset

# Constants
PROJECT_ROOT = Path(__file__).resolve().parent.parent
STATE_DIR = PROJECT_ROOT / "state"
OUTPUT_FILE = STATE_DIR / "quantization_penalty.json"
TIMEOUT_SECONDS = 60 * 60  # 60 minutes
LOG_FILE = PROJECT_ROOT / "state" / "calibration.log"

# Configure logger
logger = setup_logger("calibration", log_file=str(LOG_FILE))

class TimeoutError(Exception):
    """Custom timeout exception for the calibration pilot."""
    pass

def timeout_handler(signum, frame):
    """Signal handler for timeout."""
    raise TimeoutError("Pilot run exceeded 60‑minute timeout.")

class QuantizationCalibration:
    """
    Runs a pilot inference to estimate the performance penalty of Q4_K_M quantization
    on CPU.
    """

    def __init__(self, model_path: Optional[str] = None):
        """
        Initialize the calibration runner.

        Args:
            model_path: Path to the model. If None, uses default from config.
        """
        self.model_path = model_path
        self.device = "cpu"
        self.quantization_type = "Q4_K_M"
        self.logger = logger

    def _load_real_sample(self) -> Dict[str, Any]:
        """
        Loads a single real instance from the Claw‑SWE‑Bench dataset to use as a
        calibration prompt. The dataset is streamed to avoid loading the whole
        collection into memory.

        Returns:
            A dictionary representing one dataset example. Expected to contain at
            least the key ``problem_statement`` which will be fed to the model.
        """
        self.logger.info("Fetching a real sample from the Claw‑SWE‑Bench dataset...")
        # The official dataset identifier on Hugging Face Hub
        ds = load_dataset(
            "princeton-nlp/Claw-SWE-Bench",
            split="train",
            streaming=True,
            trust_remote_code=True,
        )
        for example in ds:
            # Return the first example that has a non‑empty problem statement
            if example.get("problem_statement"):
                self.logger.info("Sample fetched successfully.")
                return example
        raise ValueError("Unable to fetch a valid sample from the dataset.")

    def _run_pilot_inference(self, sample: Dict[str, Any]) -> float:
        """
        Runs a minimal inference pass using the loaded quantized model.

        Args:
            sample: A dataset example containing at least ``problem_statement``.

        Returns:
            float: Measured penalty. For this calibration we define the penalty as
            the elapsed time (seconds) of loading + a single token generation.
            The value is returned directly; downstream scripts may normalise it.
        """
        self.logger.info("Loading model with Q4_K_M quantization on CPU...")
        self.logger.info(f"Device: {self.device}")
        self.logger.info(f"Quantization: {self.quantization_type}")

        start_time = time.time()
        try:
            # Load the quantized model; the helper handles device placement.
            model = load_model_q4_k_m(self.model_path, device=self.device)

            self.logger.info("Model loaded successfully. Running minimal inference...")

            prompt = sample["problem_statement"]
            # Attempt a very small generation; many models expose a ``generate`` method.
            if hasattr(model, "generate"):
                # For Transformers models we also need a tokenizer.
                # The quantization loader typically returns a tuple (model, tokenizer)
                # but we guard against different return signatures.
                if isinstance(model, tuple) and len(model) == 2:
                    model_obj, tokenizer = model
                else:
                    model_obj = model
                    tokenizer = None

                if tokenizer is not None:
                    inputs = tokenizer(prompt, return_tensors="pt")
                    # Ensure tensors are on CPU
                    inputs = {k: v.to(self.device) for k, v in inputs.items()}
                    # Generate a single token
                    output = model_obj.generate(**inputs, max_new_tokens=1)
                else:
                    # Fallback: assume model can accept raw strings (e.g., a pipeline)
                    output = model.generate(prompt, max_new_tokens=1)
            else:
                self.logger.warning(
                    "Model object lacks a 'generate' method; skipping generation step."
                )
            end_time = time.time()
            duration = end_time - start_time
            self.logger.info(f"Pilot inference completed in {duration:.2f} seconds.")
            # Here the "penalty" is simply the duration; callers can interpret as needed.
            return duration
        except Exception as e:
            self.logger.error(f"Pilot inference failed: {str(e)}")
            raise

    def run(self) -> Dict[str, Any]:
        """
        Execute the calibration process.

        Returns:
            dict: Result containing the measured penalty and metadata.
        """
        self.logger.info("Starting Quantization Calibration...")

        # Set up the timeout
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(TIMEOUT_SECONDS)

        try:
            sample = self._load_real_sample()
            penalty = self._run_pilot_inference(sample)

            # Cancel the alarm
            signal.alarm(0)

            result = {
                "penalty": penalty,
                "reason": "calibrated",
                "model_path": self.model_path,
                "device": self.device,
                "quantization_type": self.quantization_type,
            }

            self.logger.info(f"Calibration successful. Penalty: {penalty:.2f}s")
            return result

        except TimeoutError as e:
            signal.alarm(0)
            self.logger.error(f"TIMEOUT: {str(e)}")
            return {
                "penalty": None,
                "reason": "timeout",
                "model_path": self.model_path,
                "device": self.device,
                "quantization_type": self.quantization_type,
            }
        except Exception as e:
            signal.alarm(0)
            self.logger.error(f"Calibration failed with error: {str(e)}")
            raise

    def write_output(self, result: Dict[str, Any]) -> None:
        """
        Persist the calibration result to ``state/quantization_penalty.json``.
        """
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        with open(OUTPUT_FILE, "w") as f:
            json.dump(result, f, indent=2)
        self.logger.info(f"Result written to {OUTPUT_FILE}")

def main():
    """
    Main entry point for the calibration script.
    """
    try:
        calibration = QuantizationCalibration()
        result = calibration.run()
        calibration.write_output(result)

        # Verify the output file exists
        if OUTPUT_FILE.exists():
            logger.info("Verification: Output file exists.")
            with open(OUTPUT_FILE, "r") as f:
                data = json.load(f)
                logger.info(f"Output content: {data}")
        else:
            logger.error("Verification failed: Output file does not exist.")
            sys.exit(1)

    except Exception as e:
        log_error(logger, "Calibration execution failed", e)
        sys.exit(1)

if __name__ == "__main__":
    main()
