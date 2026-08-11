import re
import hashlib
from typing import Optional, List

def scan_for_pii(text: str) -> List[str]:
    """
    Scan text for potential PII (emails, phone numbers, SSNs).
    Returns a list of detected patterns.
    """
    patterns = {
        'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        'phone': r'\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b',
        'ssn': r'\b\d{3}-\d{2}-\d{4}\b'
    }
    
    found = []
    for name, pattern in patterns.items():
        matches = re.findall(pattern, text)
        if matches:
            found.extend([f"{name}: {m}" for m in matches])
    return found

def compute_artifact_hash(file_path: str) -> str:
    """
    Compute SHA-256 hash of a file for versioning.
    """
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except FileNotFoundError:
        return "file_not_found"
