import hashlib
import logging
import re
import sys
from pathlib import Path
from typing import List, Optional, Dict, Any

def log_setup() -> None:
    """
    Initialize logging configuration.
    
    This function ensures that logging is properly configured before
    any other modules attempt to log messages.
    """
    from logging_config import setup_logging
    setup_logging()

def checksum_file(path: str) -> str:
    """
    Calculate the SHA-256 checksum of a file.
    
    Args:
        path: Path to the file.
    
    Returns:
        Hexadecimal string of the SHA-256 checksum.
    
    Raises:
        FileNotFoundError: If the file does not exist.
        IOError: If the file cannot be read.
    """
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except IOError as e:
        raise IOError(f"Error reading file {path}: {e}")

def causal_language_scanner(text: str, forbidden_words: List[str]) -> bool:
    """
    Scan text for forbidden causal language terms.
    
    Args:
        text: The text to scan.
        forbidden_words: List of forbidden words/phrases (case-insensitive).
    
    Returns:
        True if any forbidden word is found, False otherwise.
    """
    text_lower = text.lower()
    for word in forbidden_words:
        if word.lower() in text_lower:
            return True
    return False
