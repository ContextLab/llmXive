"""
Registry Wrapper for EvoPolicyGym Environment Discovery (T001)

This script imports the EvoPolicyGym environment registry, discovers all
registered environment IDs, writes them to the standard data artifacts:
    - data/discovered_envs.json  (JSON array of IDs)
    - data/discovered_envs.log   (human‑readable log)

It raises a RuntimeError if the number of discovered environments is not
exactly 16, as required by the verification criteria.
"""

import os
import sys

# Ensure the project root is on the Python path when this script is run directly
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from utils.logging import setup_logging, get_logger
from utils.env_discovery import discover_environments, write_discovered_envs

def main() -> None:
    """Execute the discovery workflow, write artifacts, and enforce count == 16."""
    setup_logging()
    logger = get_logger(__name__)
    logger.info("Starting environment discovery via registry_wrapper.")

    # Discover environment IDs
    env_ids = discover_environments()
    count = len(env_ids)
    logger.info(f"Discovery complete – {count} environments found.")

    # Enforce the exact count requirement
    if count != 16:
        error_msg = (
            f"Expected 16 environments, but discovered {count}. "
            "The study requires exactly 16 environments."
        )
        logger.error(error_msg)
        raise RuntimeError(error_msg)

    # Write JSON and log files
    json_path = write_discovered_envs(env_ids)
    logger.info(f"Discovered environments written to {json_path}")

if __name__ == "__main__":
    main()
