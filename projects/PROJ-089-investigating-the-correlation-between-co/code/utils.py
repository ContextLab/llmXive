"""
Utility functions for the Code Churn vs Technical Debt correlation study.
"""
import hashlib
import logging
import os
import random
import sys
import csv
import requests
from pathlib import Path
from typing import List, Dict, Any, Optional

from config import DATA_LOGS, SEMGREP_VERSION, TOOL_VALIDATION_LOG_FILE

# Configure root logger if not already configured
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)

def setup_logging(log_file: Optional[Path] = None) -> logging.Logger:
    """
    Sets up a logger that writes to a file and console.
    If log_file is provided, adds a file handler.
    """
    logger = logging.getLogger("utils")
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        if log_file:
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(logging.INFO)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
    return logger

def get_logger(name: str = "utils") -> logging.Logger:
    """
    Returns a logger with the specified name.
    """
    return logging.getLogger(name)

def calculate_checksum(file_path: Path) -> str:
    """
    Calculates the SHA256 checksum of a file.
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def pin_random_seed(seed: int = 42) -> None:
    """
    Pins the random seed for reproducibility.
    """
    random.seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)
    # Note: numpy seed pinning is handled in analysis.py if numpy is imported there

def validate_tools_and_log(tool_name: str, version: str) -> Dict[str, Any]:
    """
    Validates a tool's availability and validity per Spec SC-005.
    Checks a hardcoded list of known, cited papers/sources first.
    If not found, fetches GitHub star count via API.
    Returns a dictionary with validation results.
    """
    logger = get_logger("utils")
    
    # Hardcoded list of known, cited papers/tools that are exempt from API check
    # Based on Spec SC-005: "First, check code/config.py for a hardcoded list..."
    # Since config.py doesn't have this list explicitly, we define it here as per task instruction
    # to check "code/config.py" logic. The task implies we should check if the tool is 
    # in a list of known papers. Semgrep is a tool, not a paper, so we check if it's 
    # in a "known tools" list.
    # The task says: "check code/config.py for a hardcoded list of known, cited papers (e.g., 'Wheeler, 2015')"
    # Since 'Semgrep' is not a paper, it won't be in a list of papers.
    # We assume the "known list" is for academic citations. Tools like Semgrep are validated via API.
    
    known_papers_citations = [
        "Wheeler, 2015",
        "Fowler, 2018",
        "Hassan, 2009"
    ]
    
    result = {
        "tool_name": tool_name,
        "version": version,
        "stars": None,
        "status": "FAIL"
    }
    
    # Check if tool name matches a known citation (unlikely for tools, but per spec logic)
    # The spec says "If the tool (Semgrep) is in the list, log PASS".
    # Semgrep is not a paper, so it won't be in the list.
    if tool_name in known_papers_citations or version in known_papers_citations:
        logger.info(f"Tool {tool_name} ({version}) found in known citations list. PASS")
        result["status"] = "PASS"
        result["stars"] = "N/A (Citation)"
        return result

    # If not in the citation list, fetch GitHub stars
    logger.info(f"Tool {tool_name} not in citation list. Fetching GitHub stars...")
    
    try:
        # Map tool name to GitHub repo. Semgrep is 'semgrep/semgrep'
        github_repo_map = {
            "Semgrep": "semgrep/semgrep",
            "PyDriller": "whiteseven/pydriller",
            "Radon": "rpyc/radon"
        }
        
        repo_path = github_repo_map.get(tool_name, f"{tool_name}/{tool_name}")
        api_url = f"https://api.github.com/repos/{repo_path}"
        
        response = requests.get(api_url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        stars = data.get("stargazers_count", 0)
        result["stars"] = stars
        
        if stars > 5000:
            logger.info(f"Tool {tool_name} has {stars} stars (>5000). PASS")
            result["status"] = "PASS"
        else:
            logger.warning(f"Tool {tool_name} has {stars} stars (<=5000). FAIL")
            result["status"] = "FAIL"
    
    except Exception as e:
        logger.error(f"Failed to validate tool {tool_name}: {e}")
        result["status"] = "FAIL"
        result["stars"] = "Error"
    
    return result

def validate_tools_and_log_wrapper() -> None:
    """
    Wrapper function to run tool validation for the primary tool (Semgrep)
    and write the results to the CSV log file.
    """
    logger = get_logger("utils")
    logger.info("Starting tool validation...")
    
    # Ensure log directory exists
    DATA_LOGS.mkdir(parents=True, exist_ok=True)
    
    tool_name = "Semgrep"
    version = SEMGREP_VERSION
    
    validation_result = validate_tools_and_log(tool_name, version)
    
    # Write to CSV
    csv_path = TOOL_VALIDATION_LOG_FILE
    # If file doesn't exist, write header
    if not csv_path.exists():
        with open(csv_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['tool_name', 'version', 'stars', 'status'])
    
    with open(csv_path, 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            validation_result['tool_name'],
            validation_result['version'],
            validation_result['stars'],
            validation_result['status']
        ])
    
    logger.info(f"Tool validation log written to {csv_path}")