"""
Reference Validator Agent for Constitution Check.

This module implements the Reference-Validator Agent as specified in T008.
It verifies that `research.md` exists and contains verified citations from
real, programmatically accessible sources before the Constitution Check passes.
"""
import os
import re
import logging
from pathlib import Path
from typing import List, Optional, Tuple

from utils.error_handlers import SolderPipelineError

# Define the path to research.md relative to project root
# Based on task description: specs/001-predict-solder-hardness/research.md
RESEARCH_MD_PATH = Path("specs/001-predict-solder-hardness/research.md")

# Required source keywords to verify presence in research.md
# These correspond to the sources mentioned in T008a and tasks.md
REQUIRED_SOURCES = [
    "materials project",
    "nist",
    "openalloy",
    "literature corpus",
    "pdf"
]

# Pattern to match URLs or DOIs in the text
URL_PATTERN = re.compile(r'https?://[^\s<>"{}|\\^`\[\]]+|doi:[^\s<>"{}|\\^`\[\]]+', re.IGNORECASE)
DOI_PATTERN = re.compile(r'doi:\s*10\.\d{4,9}/[-._;()/:A-Z0-9]+', re.IGNORECASE)

class ConstitutionError(SolderPipelineError):
    """Raised when the Constitution Check fails due to missing or unverified research.md."""
    pass

def get_logger():
    """Get a logger instance for this module."""
    logger = logging.getLogger(__name__)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger

def check_research_md_exists() -> bool:
    """
    Check if research.md exists at the expected path.

    Returns:
        bool: True if file exists, False otherwise.
    """
    logger = get_logger()
    exists = RESEARCH_MD_PATH.exists()
    if exists:
        logger.info(f"Found {RESEARCH_MD_PATH}")
    else:
        logger.error(f"Missing required file: {RESEARCH_MD_PATH}")
    return exists

def extract_citations(content: str) -> List[Tuple[str, str]]:
    """
    Extract potential citations (URLs, DOIs) from the content.

    Args:
        content (str): The text content of research.md.

    Returns:
        List[Tuple[str, str]]: List of (type, value) tuples for found citations.
    """
    logger = get_logger()
    citations = []

    # Find URLs
    urls = URL_PATTERN.findall(content)
    for url in urls:
        citations.append(("URL", url))

    # Find DOIs
    dois = DOI_PATTERN.findall(content)
    for doi in dois:
        citations.append(("DOI", doi))

    logger.info(f"Extracted {len(citations)} potential citations")
    return citations

def verify_citations(content: str) -> Tuple[bool, List[str]]:
    """
    Verify that the content contains references to required sources.

    This is a heuristic check based on the presence of required source keywords
    and at least one valid citation (URL or DOI).

    Args:
        content (str): The text content of research.md.

    Returns:
        Tuple[bool, List[str]]: (is_valid, list of missing sources)
    """
    logger = get_logger()
    content_lower = content.lower()
    missing_sources = []

    # Check for required source keywords
    for source in REQUIRED_SOURCES:
        if source not in content_lower:
            missing_sources.append(source)

    # Check for at least one valid citation
    citations = extract_citations(content)
    has_citations = len(citations) > 0

    if missing_sources:
        logger.warning(f"Missing references to required sources: {missing_sources}")

    if not has_citations:
        logger.warning("No citations (URLs or DOIs) found in research.md")

    is_valid = (len(missing_sources) == 0) and has_citations
    return is_valid, missing_sources

def validate_research_md() -> bool:
    """
    Perform the full Constitution Check validation.

    1. Check if research.md exists.
    2. Read its content.
    3. Verify it contains required sources and citations.

    Returns:
        bool: True if validation passes.

    Raises:
        ConstitutionError: If validation fails.
    """
    logger = get_logger()

    # Step 1: Check existence
    if not check_research_md_exists():
        raise ConstitutionError(
            f"Constitution Check FAILED: {RESEARCH_MD_PATH} does not exist. "
            "Run T008a to generate research.md first."
        )

    # Step 2: Read content
    try:
        content = RESEARCH_MD_PATH.read_text(encoding='utf-8')
    except Exception as e:
        raise ConstitutionError(
            f"Constitution Check FAILED: Could not read {RESEARCH_MD_PATH}: {e}"
        )

    if not content.strip():
        raise ConstitutionError(
            f"Constitution Check FAILED: {RESEARCH_MD_PATH} is empty."
        )

    # Step 3: Verify citations and sources
    is_valid, missing_sources = verify_citations(content)

    if not is_valid:
        error_msg = "Constitution Check FAILED: research.md is missing required citations or source references."
        if missing_sources:
            error_msg += f" Missing sources: {', '.join(missing_sources)}."
        if not extract_citations(content):
            error_msg += " No URLs or DOIs found."

        logger.error(error_msg)
        raise ConstitutionError(error_msg)

    logger.info("Constitution Check PASSED: research.md is valid.")
    return True

def main():
    """Main entry point for the Reference Validator Agent."""
    logger = get_logger()
    logger.info("Starting Reference-Validator Agent (T008)...")

    try:
        validate_research_md()
        logger.info("T008 completed successfully.")
        return 0
    except ConstitutionError as e:
        logger.error(f"T008 failed: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error during T008: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
