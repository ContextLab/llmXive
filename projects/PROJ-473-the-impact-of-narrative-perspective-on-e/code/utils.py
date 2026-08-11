import re
import hashlib
from typing import Optional, List
import os

def scan_for_pii(text: str) -> List[str]:
    """
    Detect PII in text.
    Returns list of detected PII patterns.
    """
    pii_patterns = [
        r'\b\d{3}-\d{2}-\d{4}\b', # SSN
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', # Email
        r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b' # Phone
    ]
    found = []
    for pattern in pii_patterns:
        matches = re.findall(pattern, text)
        found.extend(matches)
    return found

def compute_artifact_hash(file_path: str) -> str:
    """
    Compute hash of an artifact file for versioning.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()