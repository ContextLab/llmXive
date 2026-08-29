"""
Model Persistence Module for Moebius-Dynamic

Handles the verification of gate status and the actual saving of model weights
to disk. Ensures that models are only saved if the permutation test gate (T025a)
has passed.
"""
import os
import sys
import json
import argparse
import torch
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

# Local imports matching API surface
from utils.logger import get_logger
from config import is_ci_mode, get_mode
from eval.gate import load_validation_result

logger = get_logger(__name__)

# Constants for paths relative to project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
MODEL_DIR = PROJECT_ROOT / "code" / "models"
RESULTS_DIR = PROJECT_ROOT / "data" / "results"
GATE_STATUS_FILE = RESULTS_DIR / "gate_status.json"
MODEL_WEIGHTS_FILE = MODEL_DIR / "moebius_dynamic.pt"
GATING_WEIGHTS_FILE = RESULTS_DIR / "gating_weights.pt"

def verify_gate_status(gate_file_path: Optional[Path] = None) -> bool:
    """
    Verifies that the permutation test gate (T025a) has passed.

    Reads the validation result from the gate status file.
    - In CI Mode: Always returns True (gate is simulated/pass).
    - In Research Mode: Checks if p-value > 0.05.

    Args:
        gate_file_path: Path to the gate status JSON file. Defaults to GATE_STATUS_FILE.

    Returns:
        bool: True if gate passed, False otherwise.

    Raises:
        FileNotFoundError: If gate file is missing in Research Mode.
        ValueError: If gate status indicates failure (p <= 0.05).
    """
    if gate_file_path is None:
        gate_file_path = GATE_STATUS_FILE

    if is_ci_mode():
        logger.info("[CI_MODE] Gate verification skipped (simulation mode).")
        return True

    logger.info("[RESEARCH_MODE] Verifying permutation test gate...")

    if not gate_file_path.exists():
        error_msg = f"Gate status file missing: {gate_file_path}. " \
                    "Run T025 (Permutation Test) first."
        logger.error(error_msg)
        raise FileNotFoundError(error_msg)

    try:
        with open(gate_file_path, 'r') as f:
            gate_data = json.load(f)
    except json.JSONDecodeError as e:
        error_msg = f"Invalid JSON in gate status file: {e}"
        logger.error(error_msg)
        raise ValueError(error_msg)

    # Expected structure from T025a/T025
    status = gate_data.get("status", "UNKNOWN")
    p_value = gate_data.get("p_value", None)

    if p_value is None:
        error_msg = "p_value missing in gate status file."
        logger.error(error_msg)
        raise ValueError(error_msg)

    if p_value <= 0.05:
        error_msg = f"Gate FAILED: p-value ({p_value:.4f}) <= 0.05. " \
                    "Model has likely overfit shuffled labels. " \
                    "Deployment blocked."
        logger.critical(error_msg)
        raise ValueError(error_msg)

    logger.info(f"Gate PASSED: p-value ({p_value:.4f}) > 0.05. Proceeding to save model.")
    return True

def save_model_weights(
    model: torch.nn.Module,
    gating_head: torch.nn.Module,
    metadata: Optional[Dict[str, Any]] = None,
    output_model_path: Optional[Path] = None,
    output_gating_path: Optional[Path] = None
) -> Dict[str, str]:
    """
    Saves the MoebiusDynamic model and GatingHead weights to disk.

    Args:
        model: The trained MoebiusDynamic model instance.
        gating_head: The trained GatingHead instance.
        metadata: Optional dictionary of training metadata (seed, timestamp, etc.).
        output_model_path: Path to save the full model weights.
        output_gating_path: Path to save the gating head weights.

    Returns:
        Dict[str, str]: Paths to the saved files.

    Raises:
        RuntimeError: If save fails.
    """
    if output_model_path is None:
        output_model_path = MODEL_WEIGHTS_FILE
    if output_gating_path is None:
        output_gating_path = GATING_WEIGHTS_FILE

    # Ensure directories exist
    output_model_path.parent.mkdir(parents=True, exist_ok=True)
    output_gating_path.parent.mkdir(parents=True, exist_ok=True)

    saved_files = {}

    try:
        # Save full model state dict
        state_dict = {
            "model_state_dict": model.state_dict(),
            "gating_head_state_dict": gating_head.state_dict(),
            "metadata": metadata or {}
        }
        torch.save(state_dict, output_model_path)
        saved_files["model"] = str(output_model_path)
        logger.info(f"Model weights saved to: {output_model_path}")

        # Save gating head separately for modularity
        torch.save(gating_head.state_dict(), output_gating_path)
        saved_files["gating"] = str(output_gating_path)
        logger.info(f"Gating head weights saved to: {output_gating_path}")

    except Exception as e:
        error_msg = f"Failed to save model weights: {e}"
        logger.error(error_msg)
        raise RuntimeError(error_msg) from e

    return saved_files

def main():
    """
    CLI entry point for T026.
    Usage:
      python code/training/save_model.py --model-path <path_to_trained_model>
    """
    parser = argparse.ArgumentParser(description="Save Moebius-Dynamic model weights (T026).")
    parser.add_argument(
        "--model-path",
        type=str,
        required=True,
        help="Path to the checkpoint or state dict produced by training scripts."
    )
    parser.add_argument(
        "--gate-file",
        type=str,
        default=str(GATE_STATUS_FILE),
        help="Path to the gate status JSON file (default: data/results/gate_status.json)."
    )
    parser.add_argument(
        "--output-model",
        type=str,
        default=str(MODEL_WEIGHTS_FILE),
        help="Output path for full model weights."
    )
    parser.add_argument(
        "--output-gating",
        type=str,
        default=str(GATING_WEIGHTS_FILE),
        help="Output path for gating head weights."
    )
    args = parser.parse_args()

    logger.info(f"Starting T026: Model Persistence. Mode: {get_mode()}")

    # 1. Verify Gate
    try:
        gate_path = Path(args.gate_file)
        if not verify_gate_status(gate_path):
            # verify_gate_status raises on failure, but explicit check for safety
            sys.exit(1)
    except (FileNotFoundError, ValueError) as e:
        logger.critical(f"Gate verification failed: {e}")
        sys.exit(1)

    # 2. Load Model (Assuming training script saved a state dict)
    logger.info(f"Loading model from: {args.model_path}")
    try:
        checkpoint = torch.load(args.model_path, map_location="cpu")
    except FileNotFoundError:
        logger.critical(f"Training checkpoint not found: {args.model_path}")
        sys.exit(1)
    except Exception as e:
        logger.critical(f"Failed to load checkpoint: {e}")
        sys.exit(1)

    # 3. Reconstruct Model Architecture (Requires importing model classes)
    # We assume the training script saved the architecture config or we reconstruct from defaults
    # For T026, we assume the model class is available and we load state into a fresh instance
    # In a real pipeline, we would load the config first. Here we instantiate MoebiusDynamic
    # and GatingHead with standard args.
    try:
        from models.moebius_dynamic import create_moebius_dynamic
        from models.gating_head import create_gating_head

        # Create instances
        # Note: These factory functions usually take config or args.
        # We use defaults or try to infer from checkpoint if possible.
        # For robustness, we assume standard initialization.
        model = create_moebius_dynamic()
        gating_head = create_gating_head()

        # Load state dicts
        if "model_state_dict" in checkpoint:
            model.load_state_dict(checkpoint["model_state_dict"])
            logger.info("Loaded model state dict.")
        elif "state_dict" in checkpoint:
            model.load_state_dict(checkpoint["state_dict"])
            logger.info("Loaded state dict (flat).")
        else:
            logger.warning("No 'model_state_dict' found in checkpoint. Attempting direct load.")
            model.load_state_dict(checkpoint)

        if "gating_head_state_dict" in checkpoint:
            gating_head.load_state_dict(checkpoint["gating_head_state_dict"])
            logger.info("Loaded gating head state dict.")
        elif "gating_state_dict" in checkpoint:
            gating_head.load_state_dict(checkpoint["gating_state_dict"])
            logger.info("Loaded gating state dict (flat).")

    except Exception as e:
        logger.critical(f"Failed to reconstruct/load model architecture: {e}")
        sys.exit(1)

    # 4. Save to Final Destination
    metadata = {
        "timestamp": datetime.now().isoformat(),
        "mode": get_mode(),
        "source_checkpoint": args.model_path,
        "task": "T026"
    }

    try:
        saved = save_model_weights(
            model=model,
            gating_head=gating_head,
            metadata=metadata,
            output_model_path=Path(args.output_model),
            output_gating_path=Path(args.output_gating)
        )
        logger.info("T026 Completed Successfully.")
        logger.info(f"Saved artifacts: {saved}")
    except RuntimeError as e:
        logger.critical(f"Failed to save model: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
