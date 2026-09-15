import hashlib
import logging
import re
from pathlib import Path
from typing import List

def log_setup(level=logging.INFO):
    """
    Configure and return a logger with the specified format:
    [%(asctime)s] %(levelname)s: %(message)s
    Destination: stdout
    """
    logger = logging.getLogger("llmXive")
    logger.setLevel(level)

    # Avoid adding duplicate handlers if called multiple times
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(level)
        formatter = logging.Formatter("[%(asctime)s] %(levelname)s: %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger

def checksum_file(path):
    """Calculate SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def causal_language_scanner(text, forbidden_words):
    """
    Scan text for forbidden causal terms.
    Returns a list of matches found.
    """
    matches = []
    text_lower = text.lower()
    for word in forbidden_words:
        if word.lower() in text_lower:
            matches.append(word)
    return matches

# Import sys for StreamHandler usage in log_setup
import sys
