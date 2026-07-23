"""
Citation Validation Wrapper for Reference-Validator Agent.

This script reads citations from `state/citations.yaml`, attempts to verify
them against primary sources (simulated for this phase via URL reachability
and format validation), and returns exit code 0 on success or non-zero on failure.

Dependency: T006a (must have generated state/citations.yaml)
"""
import os
import sys
import logging
import yaml
import re
from typing import List, Dict, Optional, Tuple, Any
import urllib.request
import urllib.error
import socket

# Configure logging to match project standards
from utils import setup_logging, get_logger, set_task_id, get_task_id

# Set task ID for this specific module
set_task_id("T007a")
logger = get_logger("validate_citations")

CITATIONS_FILE_PATH = "state/citations.yaml"

class CitationValidator:
    """
    Validates a list of citations by checking URL accessibility and format.
    """
    
    def __init__(self, citations: List[Dict[str, Any]]):
        self.citations = citations
        self.validation_results: List[Dict[str, Any]] = []
        self.valid_count = 0
        self.invalid_count = 0

    def _validate_url_format(self, url: str) -> bool:
        """Basic regex check for URL format."""
        pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        return pattern.match(url) is not None

    def _check_url_reachability(self, url: str, timeout: int = 10) -> bool:
        """
        Checks if the URL is reachable by sending a HEAD request.
        Returns True if status code is 2xx or 3xx, False otherwise.
        """
        try:
            req = urllib.request.Request(url, method='HEAD')
            # Add a generic User-Agent to avoid being blocked by some servers
            req.add_header('User-Agent', 'Mozilla/5.0 (compatible; CitationValidator/1.0)')
            with urllib.request.urlopen(req, timeout=timeout) as response:
                status = response.getcode()
                return 200 <= status < 400
        except (urllib.error.HTTPError, urllib.error.URLError, socket.timeout) as e:
            logger.warning(f"URL {url} failed reachability check: {e}")
            return False
        except Exception as e:
            logger.warning(f"Unexpected error checking {url}: {e}")
            return False

    def validate(self) -> bool:
        """
        Validates all citations in the list.
        Returns True if ALL citations are valid, False otherwise.
        Populates self.validation_results with details.
        """
        if not self.citations:
            logger.warning("No citations found to validate.")
            return False

        all_valid = True

        for idx, citation in enumerate(self.citations):
            url = citation.get('url', '')
            title = citation.get('title', 'Unknown Title')
            source_file = citation.get('source_file', 'Unknown')
            
            is_valid = True
            reason = ""

            # 1. Check if URL exists
            if not url:
                is_valid = False
                reason = "Missing URL"
            elif not self._validate_url_format(url):
                is_valid = False
                reason = "Invalid URL format"
            else:
                # 2. Check reachability
                if not self._check_url_reachability(url):
                    is_valid = False
                    reason = "URL unreachable (404, timeout, or network error)"
                else:
                    reason = "Valid"

            result = {
                "index": idx,
                "title": title,
                "url": url,
                "source_file": source_file,
                "is_valid": is_valid,
                "reason": reason
            }
            
            self.validation_results.append(result)
            
            if is_valid:
                self.valid_count += 1
            else:
                self.invalid_count += 1
                all_valid = False
                logger.error(f"Citation validation failed: {title} ({url}) - {reason}")
        
        return all_valid

def validate_citations() -> bool:
    """
    Main entry point to validate citations from state/citations.yaml.
    Returns True if all citations are valid, False otherwise.
    """
    logger.info(f"Starting citation validation for task {get_task_id()}")
    
    if not os.path.exists(CITATIONS_FILE_PATH):
        logger.error(f"Critical: Citation file not found at {CITATIONS_FILE_PATH}")
        logger.error("Dependency T006a has not completed or failed. Please run T006a first.")
        return False

    try:
        with open(CITATIONS_FILE_PATH, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        logger.error(f"Failed to parse YAML file {CITATIONS_FILE_PATH}: {e}")
        return False
    except Exception as e:
        logger.error(f"Failed to read file {CITATIONS_FILE_PATH}: {e}")
        return False

    if not isinstance(data, list):
        logger.error(f"Expected {CITATIONS_FILE_PATH} to contain a list of citations, got {type(data)}")
        return False

    logger.info(f"Found {len(data)} citations to validate.")
    
    validator = CitationValidator(data)
    success = validator.validate()

    # Log summary
    logger.info(f"Validation Summary: {validator.valid_count} valid, {validator.invalid_count} invalid")
    
    if success:
        logger.info("All citations validated successfully.")
    else:
        logger.error("One or more citations failed validation. Check logs for details.")
    
    return success

def main():
    """
    CLI entry point. Returns exit code 0 on success, 1 on failure.
    """
    success = validate_citations()
    if success:
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
