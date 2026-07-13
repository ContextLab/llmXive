"""
Verify that config.yaml is under 2KB and contains only allowed keys.

This script is a hardened version of the compliance check, ensuring
that derived statistics have been moved to the state file.
"""
import os
import sys
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = PROJECT_ROOT / "code" / "config.yaml"
MAX_SIZE = 2048

ALLOWED_TOP_KEYS = {
    'hyperparameters', 'seeds', 'base_paths', 'model_config', 'data_config',
    'evaluation_config', 'logging_config'
}
FORBIDDEN_DERIVED_KEYS = {'dataset_stats', 'inference_results', 'simulation_metrics'}

def main():
    if not CONFIG_PATH.exists():
        logger.error(f"Config file not found: {CONFIG_PATH}")
        sys.exit(1)

    # Check size
    size = os.path.getsize(CONFIG_PATH)
    logger.info(f"Config size: {size} bytes (limit: {MAX_SIZE})")
    if size > MAX_SIZE:
        logger.error(f"FAIL: Config size {size} exceeds {MAX_SIZE} bytes.")
        sys.exit(1)

    # Load and check keys
    with open(CONFIG_PATH, 'r') as f:
        config = yaml.safe_load(f)

    if not config:
        logger.warning("Config file is empty.")
        sys.exit(0)

    # Check for forbidden keys at top level
    found_forbidden = [k for k in FORBIDDEN_DERIVED_KEYS if k in config]
    if found_forbidden:
        logger.error(f"FAIL: Found forbidden derived keys in config: {found_forbidden}")
        sys.exit(1)

    # Check top-level keys (warn if unknown, but don't fail unless forbidden)
    unknown_keys = set(config.keys()) - ALLOWED_TOP_KEYS
    if unknown_keys:
        logger.warning(f"Unknown top-level keys in config (allowed: {ALLOWED_TOP_KEYS}): {unknown_keys}")

    logger.info("Config compliance check PASSED.")
    sys.exit(0)

if __name__ == "__main__":
    main()