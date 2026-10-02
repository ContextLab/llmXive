import hashlib
import logging
import re
import sys
from pathlib import Path
from typing import List, Optional, Dict, Any

def log_setup():
    """Legacy alias for setup_logging."""
    from logging_config import setup_logging
    return setup_logging()

def checksum_file(path: str) -> str:
    """Calculate SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def causal_language_scanner(text: str, forbidden_words: List[str] = None) -> bool:
    """Scan text for forbidden causal language."""
    if forbidden_words is None:
        forbidden_words = ["causes", "leads to", "impacts", "determines", "affects"]
    
    text_lower = text.lower()
    for word in forbidden_words:
        if word in text_lower:
            return True
    return False
