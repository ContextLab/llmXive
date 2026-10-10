"""
Registry Wrapper for EvoPolicyGym Environment Discovery (T001)

This script imports the EvoPolicyGym environment registry, discovers all
registered environment IDs, and writes them to the standard data artifacts:
    - data/discovered_envs.json  (JSON array of IDs)
    - data/discovered_envs.log   (human‑readable log)

It re‑uses the implementation in ``code.utils.env_discovery`` so that the
discovery logic is centralized and testable.
"""

import os
import sys

# Ensure the project root is on the Python path when this script is run directly
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from utils.logging import setup_logging, get_logger
from utils.env_discovery import run_discovery

def main() -> None:
    """Execute the discovery workflow and emit log messages."""
    setup_logging()
    logger = get_logger(__name__)
    logger.info("Starting environment discovery via registry_wrapper.")
    discovered = run_discovery()
    logger.info(f"Discovery complete – {len(discovered)} environments found.")

if __name__ == "__main__":
    main()