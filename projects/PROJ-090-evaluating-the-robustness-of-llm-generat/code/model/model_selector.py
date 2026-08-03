"""
Model Selector Module for PROJ-090

Implements the Plan's override of FR-004:
- Selects 'bigcode/starcoder2-1.5b' for CPU runs (Plan feasibility fallback)
- Selects 'bigcode/starcoder2-3b' for GPU runs (Spec FR-004 primary)

Logs the selection rationale to the standard logging infrastructure.
"""
import argparse
import logging
import sys
from pathlib import Path

# Add project root to path for imports if running as script
if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

from utils.logging import init_logging, get_inference_logger

# Model IDs
MODEL_CPU = "bigcode/starcoder2-1.5b"
MODEL_GPU = "bigcode/starcoder2-3b"

def select_model(is_cpu: bool = True) -> str:
    """
    Select the appropriate model ID based on the execution environment.

    Args:
        is_cpu (bool): If True, select the CPU-optimized model (1.5B).
                       If False, select the GPU-optimized model (3B).

    Returns:
        str: The selected model ID string.

    Logs:
        Selection rationale including the specific model ID and the reason
        (CPU memory constraints vs. GPU capability).
    """
    logger = get_inference_logger()
    
    if is_cpu:
        selected_model = MODEL_CPU
        rationale = (
            f"CPU environment detected. "
            f"Selecting '{selected_model}' (1.5B) per Plan.md feasibility override "
            f"to avoid OOM errors and ensure runtime within SC-003 limits. "
            f"Overrides Spec FR-004 (which prefers 3B) for CPU execution."
        )
    else:
        selected_model = MODEL_GPU
        rationale = (
            f"GPU environment detected. "
            f"Selecting '{selected_model}' (3B) per Spec FR-004 primary requirement "
            f"for maximum code generation quality."
        )

    logger.info(rationale)
    print(rationale) # Also print to stdout for CLI verification
    return selected_model

def main():
    """
    CLI entry point for model selection verification.
    
    Usage:
        python code/model/model_selector.py --cpu
        python code/model/model_selector.py --gpu
    """
    # Initialize logging to ensure logs are captured
    init_logging()
    
    parser = argparse.ArgumentParser(
        description="Select model based on hardware constraints (Plan override of FR-004)."
    )
    parser.add_argument(
        "--cpu",
        action="store_true",
        help="Select the CPU-optimized model (bigcode/starcoder2-1.5b)."
    )
    parser.add_argument(
        "--gpu",
        action="store_true",
        help="Select the GPU-optimized model (bigcode/starcoder2-3b)."
    )
    
    args = parser.parse_args()
    
    # Default to CPU if no flag provided (safe default)
    is_cpu = not args.gpu
    if args.cpu:
        is_cpu = True
    
    model_id = select_model(is_cpu=is_cpu)
    return model_id

if __name__ == "__main__":
    main()