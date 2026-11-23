"""
T016b: Enforce N>=80 Gate.
Reads modeling_config.json and exits if abort_flag is true.
"""
import json
import sys
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def enforce_sample_gate(config_path: str = "data/processed/modeling_config.json"):
    """Check the abort flag in modeling_config.json."""
    if not Path(config_path).exists():
        logger.error(f"Config file not found: {config_path}. Run power analysis first.")
        return False
    
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    abort_flag = config.get("abort_flag", False)
    n_samples = config.get("n_samples", 0)
    
    if abort_flag:
        logger.error(f"Analysis aborted: Insufficient sample size (N < 80). N={n_samples}")
        return False
    
    logger.info(f"Sample size check passed. N={n_samples}")
    return True

def main():
    if not enforce_sample_gate():
        return 1
    return 0

if __name__ == "__main__":
    sys.exit(main())
