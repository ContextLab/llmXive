import os
import hashlib
import logging
import numpy as np
import scipy
from typing import Optional

logger = logging.getLogger(__name__)

def pin_random_seed(seed: int = 42):
    """
    Pin random seed for numpy and scipy to ensure reproducibility.
    """
    np.random.seed(seed)
    # Note: scipy does not have a global seed setting in older versions, 
    # but random generation in scipy often relies on numpy's RNG.
    # For newer scipy, one might use scipy.random.seed if available, 
    # but standard practice is setting numpy seed.
    os.environ['PYTHONHASHSEED'] = str(seed)
    logger.info(f"Random seed pinned to {seed}")

def compute_file_checksum(filepath: str) -> str:
    """
    Compute SHA256 checksum of a file.
    """
    sha256_hash = hashlib.sha256()
    try:
        with open(filepath, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except FileNotFoundError:
        logger.error(f"File not found for checksum: {filepath}")
        return ""

def setup_logging(log_level: str = "INFO"):
    """
    Initialize logging infrastructure.
    """
    level = getattr(logging, log_level.upper(), logging.INFO)
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    # Silence overly verbose libraries
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('matplotlib').setLevel(logging.WARNING)
    logger.info(f"Logging initialized at level {log_level}")
