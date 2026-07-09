"""
Reference Validator Script for llmXive Project PROJ-275.

This script verifies dataset URLs defined in `research.md` against
actual accessibility (HTTP 200 or valid redirect). It enforces
Constitution Principle II by halting the pipeline if any URL fails.
"""

import os
import sys
import re
import logging
from urllib.parse import urlparse
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

# Configuration
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESEARCH_MD_PATH = os.path.join(PROJECT_ROOT, "research.md")
LOG_DIR = os.path.join(PROJECT_ROOT, "data", "logs")
LOG_FILE = os.path.join(LOG_DIR, "validation_error.log")

# Ensure log directory exists
os.makedirs(LOG_DIR, exist_ok=True)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, mode='a'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Regex to extract URLs from markdown. Matches http/https URLs.
URL_PATTERN = re.compile(r'https?://[^\s<>"{}|\\^`\[\]]+')

def extract_urls_from_file(filepath: str) -> list[str]:
    """Extract all URLs from a markdown file."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Reference file not found: {filepath}")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    urls = URL_PATTERN.findall(content)
    # Filter out potential markdown artifacts or non-dataset links if necessary,
    # but for now, we validate all found URLs to be safe.
    return list(set(urls))

def validate_url(url: str, timeout: int = 10) -> tuple[bool, str]:
    """
    Validate a single URL by attempting to open it.
    Returns (is_valid, message).
    """
    try:
        # Create a request with a standard User-Agent to avoid being blocked by some servers
        req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urlopen(req, timeout=timeout) as response:
            status = response.getcode()
            if status == 200:
                return True, "OK"
            else:
                return False, f"HTTP Error: {status}"
    except HTTPError as e:
        return False, f"HTTP Error: {e.code} {e.reason}"
    except URLError as e:
        return False, f"URL Error: {e.reason}"
    except Exception as e:
        return False, f"Unexpected Error: {str(e)}"

def main():
    logger.info(f"Starting Reference Validator for {RESEARCH_MD_PATH}")
    
    if not os.path.exists(RESEARCH_MD_PATH):
        logger.error(f"Critical: {RESEARCH_MD_PATH} not found. Cannot proceed.")
        sys.exit(1)

    urls = extract_urls_from_file(RESEARCH_MD_PATH)
    
    if not urls:
        logger.warning("No URLs found in research.md. Validation skipped.")
        return

    logger.info(f"Found {len(urls)} URLs to validate.")
    
    failed_urls = []
    
    for url in urls:
        is_valid, message = validate_url(url)
        if is_valid:
            logger.info(f"✓ Valid: {url}")
        else:
            logger.error(f"✗ Invalid: {url} -> {message}")
            failed_urls.append((url, message))

    if failed_urls:
        logger.critical(f"Validation FAILED for {len(failed_urls)} URL(s).")
        logger.critical("Halting pipeline as per Constitution Principle II.")
        
        # Log specific failures to the error log file explicitly
        with open(LOG_FILE, 'a') as f:
            f.write(f"\n--- Validation Failure Report at {os.popen('date').read().strip()} ---\n")
            for url, reason in failed_urls:
                f.write(f"URL: {url}\nReason: {reason}\n")
            f.write("--- End Report ---\n")
        
        sys.exit(1)
    else:
        logger.info("All URLs validated successfully. Pipeline can proceed.")
        sys.exit(0)

if __name__ == "__main__":
    main()
