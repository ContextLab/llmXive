"""
Utility functions for the project.
"""
import hashlib
import logging
import re
import sys
from pathlib import Path
from typing import List, Optional, Dict, Any

from logging_config import get_logger

logger = get_logger(__name__)

def log_setup() -> None:
    """
    Setup logging for the module.
    """
    pass # Handled by logging_config

def checksum_file(path: Path) -> str:
    """
    Calculate MD5 checksum of a file.

    Args:
        path: Path to the file.

    Returns:
        str: Hexadecimal MD5 checksum.
    """
    hash_md5 = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def causal_language_scanner(text: str, forbidden_words: List[str]) -> bool:
    """
    Scan text for forbidden causal language terms.

    Args:
        text: The text to scan.
        forbidden_words: List of forbidden words/phrases.

    Returns:
        bool: True if any forbidden term is found.
    """
    text_lower = text.lower()
    for word in forbidden_words:
        if word.lower() in text_lower:
            logger.warning(f"Causal language detected: '{word}'")
            return True
    return False
