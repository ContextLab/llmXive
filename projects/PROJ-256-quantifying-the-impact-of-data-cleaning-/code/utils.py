import os
import hashlib
import logging
import numpy as np
import scipy
from typing import Optional

logger = logging.getLogger(__name__)

def pin_random_seed(seed: int) -> None:
    """Pin random seeds for numpy and scipy to ensure reproducibility."""
    np.random.seed(seed)
    # Note: scipy doesn't have a global seed function, but numpy's seed affects many scipy operations
    os.environ['PYTHONHASHSEED'] = str(seed)

def compute_file_checksum(filepath: str) -> str:
    """Compute SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def setup_logging(log_level: str = "INFO") -> None:
    """Initialize logging infrastructure."""
    log_level = log_level.upper()
    logging.basicConfig(
        level=getattr(logging, log_level, logging.INFO),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('project.log')
        ]
    )

def main():
    """CLI for utils testing."""
    setup_logging("INFO")
    logger.info("Utils module loaded.")

if __name__ == "__main__":
    main()
