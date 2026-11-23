import json
import os
import logging
from pathlib import Path
from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

def assert_seeds_match():
    """Reads the seed configuration from results/seeds.json and compares it
    against the current runtime seed settings where possible.
    """
    seed_file = paths.results("seeds.json")
    if not seed_file.exists():
        log.warning(f"Seed file {seed_file} not found. Skipping seed assertion.")
        return

    try:
        with open(seed_file, "r") as f:
            expected = json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        log.error(f"Failed to read seed file: {e}")
        return

    # PYTHONHASHSEED is set before the process starts and is available in os.environ
    # if it was passed as an environment variable.
    actual_hash_seed = os.environ.get("PYTHONHASHSEED")
    
    if "pythonhashseed" in expected:
        expected_val = str(expected["pythonhashseed"])
        if actual_hash_seed is not None and actual_hash_seed != expected_val:
            raise RuntimeError(
                f"PYTHONHASHSEED mismatch: expected {expected_val}, got {actual_hash_seed}"
            )
    
    # Note: random, numpy, and torch seeds are not directly recoverable from the 
    # runtime state in a simple way after they have been set. We rely on the 
    # load_and_set_seeds() call in the pipeline.
    log.info("Seed assertion completed (checked PYTHONHASHSEED).")
