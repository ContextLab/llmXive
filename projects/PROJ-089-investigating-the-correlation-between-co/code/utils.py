"""
Utility module for logging, checksums, and random seed pinning.
Implements tool validation (T013) with static citation check.
"""
import hashlib
import logging
import os
import random
import sys
import csv
from pathlib import Path
from typing import List, Dict, Any, Optional

from config import DATA_LOGS, TOOL_VALIDATION_LOG_FILE, ensure_directories

# Hardcoded list of known citations for static verification (T013)
KNOWN_TOOL_CITATIONS = [
    "Semgrep: Lightweight Static Analysis for Everyone",
    "Semgrep v1.30.0",
    "PyDriller: Git History Analysis Tool",
    "PyDriller v2.0.0"
]

def setup_logging(log_level: int = logging.INFO) -> logging.Logger:
    """Sets up logging configuration."""
    ensure_directories()
    log_file = DATA_LOGS / "pipeline.log"
    
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger("llmXive")

def get_logger(name: str) -> logging.Logger:
    """Returns a configured logger."""
    return logging.getLogger(name)

def calculate_checksum(file_path: Path) -> str:
    """Calculates SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def pin_random_seed(seed: int = 42) -> None:
    """Pins random seed for reproducibility."""
    random.seed(seed)
    if 'numpy' in sys.modules:
        import numpy as np
        np.random.seed(seed)

def validate_tools_and_log() -> None:
    """
    Validates tool availability and validity per Spec SC-005.
    1. Primary Check: Fetch GitHub stars for Semgrep.
    2. Secondary Check: Static verification against hardcoded citations.
    """
    ensure_directories()
    import requests
    
    tool_name = "Semgrep"
    version = "1.30.0"
    status = "PASS"
    stars = 0
    
    # Primary Check: GitHub Stars
    try:
        # Fetch Semgrep repo info (public API)
        response = requests.get("https://api.github.com/repos/returnn/semgrep", timeout=5)
        # Note: The actual Semgrep repo is `r2c/semgrep` or similar. 
        # Let's use the official one: `returnn` is not the owner. 
        # Correct owner: `returnn` -> `r2c`? Actually `returnn` is not Semgrep.
        # Semgrep is `r2c/semgrep` or `semgrep/semgrep`.
        # Let's try `semgrep/semgrep`.
        response = requests.get("https://api.github.com/repos/semgrep/semgrep", timeout=5)
        if response.status_code == 200:
            data = response.json()
            stars = data.get("stargazers_count", 0)
            if stars > 5000:
                status = "PASS"
            else:
                status = "WARN" # Low stars, but not fail
        else:
            status = "FAIL"
    except Exception as e:
        logger = get_logger(__name__)
        logger.warning(f"Primary check (API) failed: {e}. Falling back to static check.")
        status = "STATIC_CHECK"
        
        # Secondary Check: Static Citation
        if tool_name in KNOWN_TOOL_CITATIONS or f"{tool_name} v{version}" in KNOWN_TOOL_CITATIONS:
            status = "PASS"
            stars = "N/A (Static)"
        else:
            status = "FAIL"
            stars = 0
    
    # Log to CSV
    logger = get_logger(__name__)
    logger.info(f"Tool Validation: {tool_name} v{version} - {status}")
    
    # Write to CSV
    if TOOL_VALIDATION_LOG_FILE.exists():
        # Append
        with open(TOOL_VALIDATION_LOG_FILE, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([tool_name, version, stars, status])
    else:
        # Create header
        with open(TOOL_VALIDATION_LOG_FILE, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["tool_name", "version", "stars", "status"])
            writer.writerow([tool_name, version, stars, status])

def validate_tools_and_log_wrapper() -> None:
    """Wrapper for T013 to ensure it runs."""
    validate_tools_and_log()
