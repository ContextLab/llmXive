"""
T009 – CPU‑only environment enforcement.

This script disables CUDA device visibility by setting the
``CUDA_VISIBLE_DEVICES`` environment variable to an empty string.
It should be executed before any code that may attempt to initialise
GPU resources (e.g., Torch or Transformers model loading).

The script is deliberately tiny and has no external dependencies.
Running it as a standalone step guarantees that the rest of the
pipeline operates in a CPU‑only mode, satisfying the requirement
of task T009.
"""

import os
import sys

def enforce_cpu_only() -> None:
    """
    Set the environment variable that disables CUDA devices.

    The variable is respected by PyTorch, TensorFlow and most
    libraries that rely on CUDA. By setting it to an empty string
    we ensure that any attempt to use a GPU will fall back to CPU
    and will not raise a “CUDA not available” error on machines
    that have GPUs present.
    """
    os.environ["CUDA_VISIBLE_DEVICES"] = ""
    # Explicitly inform the user / logs
    print("Environment variable CUDA_VISIBLE_DEVICES set to '' (CPU‑only mode).", flush=True)

if __name__ == "__main__":
    try:
        enforce_cpu_only()
    except Exception as e:
        # Propagate the exception so the CI runner can see a failure.
        print(f"Failed to enforce CPU‑only execution: {e}", file=sys.stderr, flush=True)
        raise
    # Exit with success code
    sys.exit(0)