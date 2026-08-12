import re
import hashlib
from typing import Optional, List
import os

def scan_for_pii(text: str) -> bool:
    """
    Scan text for PII (Personally Identifiable Information).
    Returns True if PII is detected, False otherwise.
    """
    # Simple regex patterns for PII
    patterns = [
        r'\b\d{3}-\d{2}-\d{4}\b',  # SSN
        r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',  # Phone number
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # Email
        r'\b\d{5}(-\d{4})?\b',  # ZIP code (might be too broad)
    ]
    
    for pattern in patterns:
        if re.search(pattern, text):
            return True
    return False

def compute_artifact_hash(file_path: str) -> str:
    """
    Compute SHA-256 hash of a file.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()