import os
import hashlib
import logging
import numpy as np
import scipy
from typing import Optional

logger = logging.getLogger(__name__)

def pin_random_seed(seed: int) -> None:
    """Pin random seed for numpy and scipy to ensure reproducibility."""
    np.random.seed(seed)
    # scipy respects numpy's seed
    logger.info(f"Random seed pinned to {seed}")


def compute_file_checksum(filepath: str) -> str:
    """Compute SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    try:
        with open(filepath, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except Exception as e:
        logger.error(f"Failed to compute checksum for {filepath}: {e}", exc_info=True)
        return ""


def setup_logging(log_level: str = "INFO") -> None:
    """Initialize the logging infrastructure."""
    level = getattr(logging, log_level.upper(), logging.INFO)
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger.info(f"Logging initialized at level {log_level}")


def main():
    """Main entry point for direct execution."""
    setup_logging()
    pin_random_seed(42)
    print("Utils module loaded.")

if __name__ == "__main__":
    main()