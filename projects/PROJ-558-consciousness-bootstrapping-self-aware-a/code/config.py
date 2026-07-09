"""
Configuration management for the Consciousness Bootstrapping project.

This module defines hyperparameters and constraints for the project.
It is created as part of task T005, but T004 requires it to be present.
We implement the minimal required interface here to support T004 execution.
"""

import os

# Hyperparameters
SEED = 42
BATCH_SIZE = 8
RECURSION_DEPTH = 2
LEARNING_RATE = 1e-4
TOKEN_LIMIT = 100000  # Default limit for T004

# Execution constraints
# Enforce CPU-only execution
FORCE_CPU = True

def validate_config():
    """
    Validates that the configuration meets project constraints.
    """
    if FORCE_CPU:
        # Check if torch is available and force CPU
        try:
            import torch
            if torch.cuda.is_available():
                print("Warning: CUDA detected, but FORCE_CPU is enabled. Forcing CPU.")
                torch.set_num_threads(1) # Limit threads to simulate constrained env
            # Set device to CPU
            os.environ["CUDA_VISIBLE_DEVICES"] = ""
        except ImportError:
            pass
    return True


if __name__ == "__main__":
    validate_config()
    print(f"Config loaded: TOKEN_LIMIT={TOKEN_LIMIT}, SEED={SEED}")
