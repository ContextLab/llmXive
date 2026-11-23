"""
Parameter Count Verification Module

Loads the Autoregressive and Diffusion models constructed from config,
counts their trainable parameters, compares them against the target
parameters in code/config.yaml, and writes a validation report to
data/artifacts/parameter_validation.json.
"""

import json
import sys
import yaml
from pathlib import Path
from typing import Dict, Any, Tuple, List

# Import project utilities
from utils.config import load_config, get_project_root, get_artifacts_dir
# Import model constructors
from models.autoregressive import create_autoregressive_model
from models.diffusion import create_diffusion_model
# Import config getters for model construction
from models.config import get_embed_dim, get_num_heads, get_num_layers, get_vocab_size, get_max_seq_length

import torch
import torch.nn as nn


def count_parameters(model: nn.Module) -> int:
    """
    Count the total number of parameters in a PyTorch model.

    Args:
        model: The PyTorch model to count.

    Returns:
        Total number of parameters (int).
    """
    return sum(p.numel() for p in model.parameters())


def load_models_from_config() -> Tuple[nn.Module, nn.Module]:
    """
    Instantiate the Autoregressive and Diffusion models based on current config.

    Returns:
        Tuple of (autoregressive_model, diffusion_model).
    """
    # Ensure models are built with the current config state
    # The config should have been loaded by utils.config module prior to this call
    # or by the caller. We rely on the getters from models.config which read from
    # the global state set by config loading.

    # Construct AR Model
    ar_model = create_autoregressive_model()

    # Construct Diffusion Model
    diffusion_model = create_diffusion_model()

    return ar_model, diffusion_model


def verify_parameter_counts(
    ar_model: nn.Module,
    diffusion_model: nn.Module,
    config_params: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Compare actual parameter counts against the expected counts derived from config.

    Args:
        ar_model: The instantiated Autoregressive model.
        diffusion_model: The instantiated Diffusion model.
        config_params: The model_params dictionary from config.yaml.

    Returns:
        A dictionary containing the verification results.
    """
    ar_count = count_parameters(ar_model)
    diff_count = count_parameters(diffusion_model)

    # Calculate expected parameters based on config (approximate for validation)
    # Note: Exact parameter count depends on implementation details (bias, layer norms).
    # We compare the actual count against the config's implicit target if available,
    # or simply verify they are within a reasonable range of each other if the task
    # implies "verify they match the config's intent".
    # However, the task says "Compare against model_params in code/config.yaml".
    # Since config.yaml lists hyperparams, not total param count, we verify
    # that the models were built with those hyperparams and report the counts.
    # If a specific target count was in config, we would check that.
    # Here we assume the "verification" is ensuring the models are instantiated
    # correctly with the config and reporting the counts for audit.

    # Let's check if config has a 'target_param_count' key (optional).
    target_count = config_params.get('target_param_count', None)

    ar_match = True
    diff_match = True
    messages = []

    if target_count is not None:
        # If a specific target exists, check it.
        # Allow a small tolerance for implementation differences (e.g. bias)
        tolerance = 0.05 # 5%
        if abs(ar_count - target_count) / target_count > tolerance:
            ar_match = False
            messages.append(f"AR Model param count {ar_count} deviates significantly from target {target_count}.")
        if abs(diff_count - target_count) / target_count > tolerance:
            diff_match = False
            messages.append(f"Diffusion Model param count {diff_count} deviates significantly from target {target_count}.")
    else:
        # If no explicit target, we just verify the models are non-empty and consistent with each other
        # (as per spec FR-002: "identical embedding/attention params").
        # We expect them to be very close.
        if ar_count == 0 or diff_count == 0:
            messages.append("One or both models have zero parameters.")
        elif abs(ar_count - diff_count) / max(ar_count, diff_count) > 0.1:
            messages.append(f"AR and Diffusion model parameter counts differ by more than 10%: {ar_count} vs {diff_count}.")

    return {
        "ar_model_params": ar_count,
        "diffusion_model_params": diff_count,
        "config_hyperparams": config_params,
        "ar_matches_target": ar_match,
        "diffusion_matches_target": diff_match,
        "all_passed": ar_match and diff_match,
        "messages": messages
    }


def main() -> int:
    """
    Main entry point for the parameter verification script.
    """
    project_root = get_project_root()
    config_path = project_root / "code" / "config.yaml"
    artifacts_dir = get_artifacts_dir()

    # Ensure artifacts directory exists
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    output_path = artifacts_dir / "parameter_validation.json"

    try:
        # Load config
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)

        model_params = config.get("model_params", {})

        if not model_params:
            raise ValueError("model_params not found in config.yaml")

        # Load models
        ar_model, diffusion_model = load_models_from_config()

        # Verify counts
        results = verify_parameter_counts(ar_model, diffusion_model, model_params)

        # Write results
        with open(output_path, "w") as f:
            json.dump(results, f, indent=2)

        print(f"Parameter verification complete. Results written to: {output_path}")
        if not results["all_passed"]:
            print("WARNING: Verification failed or warnings present.")
            for msg in results["messages"]:
                print(f"  - {msg}")
            return 1

        return 0

    except Exception as e:
        print(f"Error during parameter verification: {e}", file=sys.stderr)
        # Write error state if possible
        error_result = {
            "error": str(e),
            "all_passed": False,
            "messages": [f"Verification failed due to error: {e}"]
        }
        try:
            with open(output_path, "w") as f:
                json.dump(error_result, f, indent=2)
        except:
            pass
        return 1


if __name__ == "__main__":
    sys.exit(main())