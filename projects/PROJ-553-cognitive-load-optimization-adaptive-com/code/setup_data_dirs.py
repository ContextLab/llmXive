"""
Ensure that all required data sub‑directories exist.

This script is a lightweight helper that can be called independently of
`setup_structure.py`. It guarantees that the `data/` hierarchy is present,
which is useful for downstream scripts that assume these folders exist.
"""
import sys
from pathlib import Path
import logging

def main() -> None:
    """
    Create the data sub‑directories if they are missing.
    """
    project_root = Path(__file__).resolve().parent.parent
    data_root = project_root / "data"

    subdirs = [
        data_root / "raw",
        data_root / "processed",
        data_root / "explanation_tiers",
        data_root / "simulation_results",
    ]

    for sub in subdirs:
        sub.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    logger = logging.getLogger(__name__)
    logger.info("Data directories verified/created successfully.")

if __name__ == "__main__":
    main()