"""
Reference-Validator Agent Wrapper.

Implements FR-010: Validates citations found in `state/citations.yaml` against
primary sources. Returns exit code 0 on success, non-zero on failure.

This script is designed to be the first step in the pipeline (T007b).
It ensures that all research claims have valid, verifiable primary sources
before proceeding to data acquisition or analysis.
"""

import os
import sys
import logging
import yaml
import re
from typing import List, Dict, Optional, Tuple, Any

from utils import get_logger, set_task_id, get_task_id

# Constants
CITATIONS_FILE = "state/citations.yaml"
VALIDATION_LOG = "state/validation_log.txt"

# Regex patterns for common URL validation (basic)
URL_PATTERN = re.compile(
    r'^https?://'  # http:// or https://
    r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
    r'localhost|'  # localhost...
    r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})' # ...or ip
    r'(?::\d+)?'  # optional port
    r'(?:/?|[/?]\S+)$', re.IGNORECASE)

DOI_PATTERN = re.compile(
    r'^10\.\d{4,9}/[-._;()/:A-Z0-9]+$', re.IGNORECASE)

class CitationValidator:
    """
    Validates citations against primary sources.
    """

    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def _validate_url(self, url: str) -> bool:
        """Basic structural validation of a URL."""
        if not url:
            return False
        return bool(URL_PATTERN.match(url))

    def _validate_doi(self, doi: str) -> bool:
        """Basic structural validation of a DOI."""
        if not doi:
            return False
        return bool(DOI_PATTERN.match(doi))

    def _verify_source_availability(self, source: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Verifies if a source is structurally valid.
        Note: Without network access in this specific check, we validate
        the structure and format. In a full implementation with network,
        we would ping the URL or DOI resolver.
        """
        source_type = source.get("type", "").lower()
        identifier = source.get("id") or source.get("url") or source.get("doi")

        if not identifier:
            return False, "Missing identifier (id, url, or doi)"

        if source_type == "url":
            if not self._validate_url(identifier):
                return False, f"Invalid URL format: {identifier}"
        elif source_type == "doi":
            if not self._validate_doi(identifier):
                return False, f"Invalid DOI format: {identifier}"
        elif source_type == "book":
            isbn = source.get("isbn")
            if not isbn:
                return False, "Book source missing ISBN"
        elif source_type == "paper":
            if not identifier:
                return False, "Paper source missing DOI or URL"
        else:
            self.warnings.append(f"Unknown source type '{source_type}' for citation: {source.get('claim')}")
            # We don't fail on unknown types, just warn, unless specific format is required
            if not identifier:
                return False, "Source missing identifier"

        return True, "OK"

    def validate_citations_file(self, file_path: str) -> bool:
        """
        Reads the citations file and validates each entry.
        Returns True if all citations are valid, False otherwise.
        """
        if not os.path.exists(file_path):
            self.errors.append(f"Citations file not found: {file_path}")
            return False

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            self.errors.append(f"Failed to parse YAML: {e}")
            return False
        except Exception as e:
            self.errors.append(f"Failed to read file: {e}")
            return False

        if not isinstance(data, list):
            self.errors.append("Citations file must contain a list of citation objects")
            return False

        if not data:
            self.warnings.append("Citations file is empty. No citations to validate.")
            return True # Technically valid, but empty

        valid_count = 0
        for i, citation in enumerate(data):
            if not isinstance(citation, dict):
                self.errors.append(f"Citation {i} is not a dictionary object")
                continue

            claim = citation.get("claim", "Unknown Claim")
            source = citation.get("source")

            if not source:
                self.errors.append(f"Citation for '{claim}' is missing a 'source' block")
                continue

            is_valid, message = self._verify_source_availability(source)
            if is_valid:
                valid_count += 1
                self.logger.debug(f"Citation {i} ({claim}): Valid")
            else:
                self.errors.append(f"Citation {i} ('{claim}'): {message}")

        self.logger.info(f"Validation complete. {valid_count}/{len(data)} citations valid.")

        if self.errors:
            self.logger.error(f"Found {len(self.errors)} validation errors.")
            return False

        return True

    def write_log(self, log_path: str):
        """Writes validation results to a log file."""
        with open(log_path, 'w', encoding='utf-8') as f:
            f.write(f"Validation Log - Task ID: {get_task_id()}\n")
            f.write(f"Timestamp: {get_timestamp()}\n")
            f.write("-" * 40 + "\n")

            if self.warnings:
                f.write("WARNINGS:\n")
                for w in self.warnings:
                    f.write(f"  - {w}\n")
                f.write("\n")

            if self.errors:
                f.write("ERRORS:\n")
                for e in self.errors:
                    f.write(f"  - {e}\n")
                f.write("\n")

            if not self.errors and not self.warnings:
                f.write("No issues found.\n")


def validate_citations():
    """
    Main entry point for citation validation.
    Reads from state/citations.yaml, validates, and exits with appropriate code.
    """
    set_task_id("T007a")
    logger = get_logger("validate_citations")
    logger.info("Starting Citation Validation (T007a)")

    validator = CitationValidator(logger)
    is_valid = validator.validate_citations_file(CITATIONS_FILE)

    # Always write the log for auditability
    validator.write_log(VALIDATION_LOG)
    logger.info(f"Validation log written to {VALIDATION_LOG}")

    if not is_valid:
        logger.error("Citation validation FAILED.")
        for err in validator.errors:
            print(f"ERROR: {err}", file=sys.stderr)
        return False

    logger.info("Citation validation PASSED.")
    return True


def main():
    """
    CLI entry point. Returns 0 on success, 1 on failure.
    """
    try:
        success = validate_citations()
        if success:
            sys.exit(0)
        else:
            sys.exit(1)
    except Exception as e:
        logging.error(f"Unexpected error during validation: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()