import hashlib
import logging
import os
import random
from pathlib import Path
from typing import Any, Dict, Optional, Union

def set_global_seed(seed: int = 42) -> None:
    """
    Sets the global random seed for reproducibility.
    """
    random.seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)
    # Note: numpy and torch seeds are handled in their respective modules if needed

def setup_logging(log_level: int = logging.INFO, log_file: Optional[str] = None) -> logging.Logger:
    """
    Configures the root logger and returns it.
    """
    logger = logging.getLogger()
    logger.setLevel(log_level)
    
    if logger.handlers:
        logger.handlers.clear()
    
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

def compute_file_hash(file_path: Union[str, Path]) -> str:
    """
    Computes the SHA-256 hash of a file.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    
    sha256_hash = hashlib.sha256()
    with open(path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def record_artifact_hash(artifact_path: Union[str, Path], hash_map: Dict[str, str]) -> None:
    """
    Records the hash of an artifact into a dictionary.
    This supports Constitution Principle V (Traceability).
    """
    path = Path(artifact_path)
    if not path.exists():
        raise FileNotFoundError(f"Cannot record hash for non-existent file: {path}")
    
    hash_val = compute_file_hash(path)
    hash_map[str(path)] = hash_val
    logging.info(f"Recorded hash for {path}: {hash_val}")