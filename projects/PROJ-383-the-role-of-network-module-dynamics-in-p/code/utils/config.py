import random
import numpy as np
import os

# Pinned random seeds for reproducibility
RANDOM_SEED = 42
NUMPY_SEED = 42
NETWORKX_SEED = 42
LEIDEN_SEED = 42

# Window length parameters (in seconds)
WINDOW_LENGTHS = [30, 60, 90]
DEFAULT_WINDOW_LENGTH = 60
WINDOW_STEP = 15  # Step size in seconds

def set_all_seeds(seed: int = RANDOM_SEED) -> None:
    """
    Set global random seeds for reproducibility.
    """
    random.seed(seed)
    np.random.seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)
    # Note: NetworkX and LeidenAlg seeds are set where they are instantiated,
    # using this global seed constant.

def get_window_params():
    """
    Returns a dictionary of window parameters.
    """
    return {
        "lengths": WINDOW_LENGTHS,
        "default": DEFAULT_WINDOW_LENGTH,
        "step": WINDOW_STEP
    }

def main():
    """CLI test for config."""
    set_all_seeds()
    print("Seeds set.")
    print(f"Window Params: {get_window_params()}")

if __name__ == "__main__":
    main()
