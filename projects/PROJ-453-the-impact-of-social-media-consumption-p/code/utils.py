import hashlib
import logging
import re
from pathlib import Path
from typing import List

def log_setup(level: int = logging.INFO, destination: str = 'stdout') -> logging.Logger:
    """
    Configure and return a logger with the specified level and destination.
    
    Args:
        level: Logging level (e.g., logging.INFO, logging.DEBUG)
        destination: 'stdout' or 'file' (if file, writes to logs/app.log)
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger('llmXive_pipeline')
    logger.setLevel(level)
    
    # Clear existing handlers to avoid duplicates in interactive environments
    if logger.handlers:
        logger.handlers.clear()
    
    # Create formatter
    # Format: [%(asctime)s] %(levelname)s: %(message)s
    formatter = logging.Formatter('[%(asctime)s] %(levelname)s: %(message)s')
    
    # Create handler
    if destination == 'stdout':
        handler = logging.StreamHandler(sys.stdout)
    elif destination == 'file':
        logs_dir = Path('logs')
        logs_dir.mkdir(exist_ok=True)
        handler = logging.FileHandler(logs_dir / 'app.log')
    else:
        raise ValueError(f"Invalid destination: {destination}. Must be 'stdout' or 'file'.")
    
    handler.setLevel(level)
    handler.setFormatter(formatter)
    
    logger.addHandler(handler)
    
    return logger

def checksum_file(path: str) -> str:
    """Calculate SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    try:
        with open(path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except FileNotFoundError:
        raise FileNotFoundError(f"File not found: {path}")

def causal_language_scanner(text: str, forbidden_words: List[str]) -> List[str]:
    """
    Scan text for forbidden causal language terms.
    
    Args:
        text: The text to scan
        forbidden_words: List of forbidden words/phrases (case-insensitive)
    
    Returns:
        List of matches found in the text
    """
    if not text:
        return []
    
    text_lower = text.lower()
    matches = []
    
    for word in forbidden_words:
        if word.lower() in text_lower:
            matches.append(word)
    
    return matches

# Re-export for convenience if imported directly
__all__ = ['log_setup', 'checksum_file', 'causal_language_scanner']
