import re
import hashlib
from typing import Optional, List
import os

def scan_for_pii(text: str) -> List[str]:
    """
    Detect potential PII (Personally Identifiable Information) in text.
    
    Args:
        text: The text to scan.
        
    Returns:
        List of detected PII patterns.
    """
    patterns = {
        'email': r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
        'phone': r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
        'ssn': r'\b\d{3}-\d{2}-\d{4}\b',
        'credit_card': r'\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b'
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
    
    Args:
        file_path: Path to the file.
        
    Returns:
        Hex digest of the file hash.
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def normalize_story_id(text: str) -> str:
    """
    Generate a consistent story_id (SHA-256 hash of the first 50 chars).
    
    Args:
        text: The story text.
        
    Returns:
        SHA-256 hash of the first 50 characters.
    """
    if not text:
        return hashlib.sha256(b"").hexdigest()
    
    truncated = text[:50]
    return hashlib.sha256(truncated.encode('utf-8')).hexdigest()
