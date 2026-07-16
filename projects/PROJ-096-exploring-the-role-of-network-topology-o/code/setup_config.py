"""
Script to initialize the project configuration with deterministic seeds and
ODE solver settings.

This script creates the data/processed/config.json file with default values
that ensure reproducible simulations across runs.
"""

import sys
from pathlib import Path

# Add code directory to path for imports
code_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(code_dir))

from utils.config import init_config, DEFAULT_GLOBAL_SEED, DEFAULT_T_EVAL_START, DEFAULT_T_EVAL_STOP, DEFAULT_T_EVAL_NUM

def main():
    """Initialize configuration with default deterministic settings."""
    print("Initializing project configuration...")
    
    # Initialize with defaults (can be overridden via CLI args in future)
    config = init_config(
        seed=DEFAULT_GLOBAL_SEED,
        t_eval_start=DEFAULT_T_EVAL_START,
        t_eval_stop=DEFAULT_T_EVAL_STOP,
        t_eval_num=DEFAULT_T_EVAL_NUM
    )
    
    print(f"Configuration saved to data/processed/config.json:")
    print(f"  - Global seed: {config['seed']}")
    print(f"  - ODE t_eval: [{config['t_eval_start']}, {config['t_eval_stop']}] with {config['t_eval_num']} points")
    print("Done.")

if __name__ == "__main__":
    main()
