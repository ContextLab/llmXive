import hashlib
import logging
import re
import sys
from pathlib import Path
from typing import List, Optional

def log_setup():
    """Configure logging to stdout."""
    logging.basicConfig(
        level=logging.INFO,
        format='[%(asctime)s] %(levelname)s: %(message)s',
        stream=sys.stdout
    )

def checksum_file(path: Path) -> str:
    """Calculate SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def causal_language_scanner(text: str, forbidden_words: Optional[List[str]] = None) -> List[str]:
    """Scan text for forbidden causal language."""
    if forbidden_words is None:
        forbidden_words = ['causes', 'leads to', 'impacts', 'affects', 'determines']
    
    text_lower = text.lower()
    matches = []
    for word in forbidden_words:
        if word in text_lower:
            matches.append(word)
    return matches
