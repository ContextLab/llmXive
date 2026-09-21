import hashlib
import logging
import os
import random
import sys
import csv
import requests
from pathlib import Path
from typing import Optional, Dict, Any, List

from config import get_config_summary

# --- Logging Setup ---

def setup_logging(log_file: str = "data/logs/pipeline.log", level: int = logging.INFO) -> logging.Logger:
    """Configure root logger to write to a file and console."""
    logger = logging.getLogger()
    logger.setLevel(level)

    # Clear existing handlers to avoid duplicates
    if logger.handlers:
        logger.handlers.clear()

    # File handler
    Path(log_file).parent.mkdir(parents=True, exist_ok=True)
    fh = logging.FileHandler(log_file)
    fh.setLevel(level)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    # Console handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(level)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    return logger

def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Get a logger instance, optionally named."""
    if name:
        return logging.getLogger(name)
    return logging.getLogger()

# --- Utility Functions ---

def calculate_checksum(file_path: str) -> str:
    """Calculate SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def pin_random_seed(seed: int = 42) -> None:
    """Pin random seed for reproducibility."""
    random.seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)

# --- Tool Validation Logic (T013b) ---

def validate_tools_and_log(
    repo_owner: str,
    repo_name: str,
    log_path: str = "data/logs/tool_validation_log.csv",
    citations_path: str = "data/logs/citations.csv"
) -> Dict[str, Any]:
    """
    Validate tool validity per SC-005.
    
    Action: 
    1. Call GitHub API /repos/{owner}/{repo} to fetch star count.
    2. If stars > 5000, log "PASS".
    3. Else, search data/logs/citations.csv for a matching paper title.
       - If found, log "PASS".
       - If not found, log "FAIL".
    
    Deviation Note: This simplified check does not satisfy Constitution Principle II 
    (Reference-Validator Agent) but is required by Spec SC-005. Log as DEVIATION: Principle II.
    
    Deliverable: data/logs/tool_validation_log.csv
    """
    logger = get_logger("ToolValidation")
    
    # Ensure log directory exists
    Path(log_path).parent.mkdir(parents=True, exist_ok=True)
    
    # Prepare result structure
    result = {
        "repo_id": f"{repo_owner}/{repo_name}",
        "owner": repo_owner,
        "name": repo_name,
        "stars": 0,
        "citation_found": False,
        "status": "FAIL",
        "deviation_logged": True
    }
    
    # 1. Fetch Star Count from GitHub API
    url = f"https://api.github.com/repos/{repo_owner}/{repo_name}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        stars = data.get('stargazers_count', 0)
        result["stars"] = stars
        logger.info(f"Fetched stars for {repo_owner}/{repo_name}: {stars}")
    except requests.RequestException as e:
        logger.error(f"Failed to fetch repo info for {repo_owner}/{repo_name}: {e}")
        # If we can't fetch stars, we can't pass the star check. 
        # We proceed to citation check if possible, but default to FAIL if no citation.
        stars = 0
    
    # Check Star Threshold
    if stars > 5000:
        result["status"] = "PASS"
        logger.info(f"Tool validation PASS for {repo_owner}/{repo_name} (Stars: {stars} > 5000)")
    else:
        # 2. Search Citations
        citation_found = False
        if Path(citations_path).exists():
            try:
                with open(citations_path, 'r', newline='', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        # Check if repo name or owner matches a paper title or related field
                        # Assuming 'paper_title' or similar column exists in citations.csv
                        # Since spec doesn't define schema, we check generic string match on title
                        title = row.get('paper_title', '') or row.get('title', '')
                        if repo_name.lower() in title.lower() or repo_owner.lower() in title.lower():
                            citation_found = True
                            break
            except Exception as e:
                logger.error(f"Error reading citations file {citations_path}: {e}")
        
        result["citation_found"] = citation_found
        if citation_found:
            result["status"] = "PASS"
            logger.info(f"Tool validation PASS for {repo_owner}/{repo_name} (Citation found)")
        else:
            result["status"] = "FAIL"
            logger.warning(f"Tool validation FAIL for {repo_owner}/{repo_name} (Stars <= 5000, No Citation)")
    
    # Log Deviation
    if result["deviation_logged"]:
        logger.info(f"DEVIATION: Principle II - Simplified validation used for {repo_owner}/{repo_name}")
    
    # Write to Log File (Append mode)
    file_exists = os.path.isfile(log_path)
    fieldnames = ["repo_id", "owner", "name", "stars", "citation_found", "status", "deviation_logged"]
    
    with open(log_path, 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow(result)
    
    return result

def validate_tools_and_log_wrapper() -> None:
    """
    Wrapper to run validation on a list of repos if needed, or placeholder for orchestration.
    Currently, this task focuses on the logic function `validate_tools_and_log`.
    This wrapper can be called from main.py to iterate over selected repos.
    """
    logger = get_logger("ToolValidationWrapper")
    logger.info("Tool validation wrapper called. Please provide repo list or call validate_tools_and_log directly.")

# --- Main Entry Point (for testing) ---
if __name__ == "__main__":
    setup_logging()
    # Example usage for testing
    validate_tools_and_log("torvalds", "linux")
    validate_tools_and_log("psf", "black")
