import hashlib
import logging
import os
import random
import sys
from pathlib import Path
from typing import Optional

# Configure a basic logger if one isn't already set up
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DataInsufficiencyError(Exception):
    """
    Custom exception raised when the retrieved data count is below the required threshold.
    
    Attributes:
        retrieved_count (int): The number of records actually retrieved.
        required_count (int): The minimum number of records required.
        missing_features (list): Optional list of features that caused the insufficiency.
    """
    def __init__(self, retrieved_count: int, required_count: int, missing_features: Optional[list] = None):
        self.retrieved_count = retrieved_count
        self.required_count = required_count
        self.missing_features = missing_features or []
        
        if missing_features:
            features_str = ", ".join(missing_features)
            self.message = (
                f"Data Insufficiency: Retrieved {retrieved_count} < {required_count}. "
                f"Missing features: {features_str}"
            )
        else:
            self.message = f"Data Insufficiency: Retrieved {retrieved_count} < {required_count}"
        
        super().__init__(self.message)


def compute_sha256(file_path: str) -> str:
    """Compute SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def setup_logging(log_file: Optional[str] = None) -> logging.Logger:
    """Setup logging to both console and optionally a file."""
    loggers = logging.getLogger()
    loggers.setLevel(logging.INFO)
    
    if not loggers.handlers:
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        ch.setFormatter(formatter)
        loggers.addHandler(ch)
        
        if log_file:
            fh = logging.FileHandler(log_file)
            fh.setLevel(logging.INFO)
            fh.setFormatter(formatter)
            loggers.addHandler(fh)
    
    return logging.getLogger(__name__)


def set_random_seed(seed: int = 42) -> None:
    """Set random seed for reproducibility."""
    random.seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)
    try:
        import numpy as np
        np.random.seed(seed)
    except ImportError:
        pass


def raise_data_insufficiency(retrieved_count: int, required_count: int, missing_features: Optional[list] = None) -> None:
    """
    Log the data insufficiency error and raise an exception to halt execution.
    
    This function implements the error handling infrastructure for T007.
    It logs the exact count of retrieved vs. required records and exits with code 1.
    
    Args:
        retrieved_count (int): The number of records actually retrieved.
        required_count (int): The minimum number of records required.
        missing_features (list): Optional list of features that caused the insufficiency.
    
    Raises:
        DataInsufficiencyError: Always raised with the formatted message.
    """
    error = DataInsufficiencyError(retrieved_count, required_count, missing_features)
    logger.error(error.message)
    raise error
