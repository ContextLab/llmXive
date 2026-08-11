"""
Reference Validator Agent for Constitution Check.

This module implements the Reference-Validator Agent required by Task T008.
It verifies that research.md exists, contains valid citations, and is not a placeholder.
"""
import os
import re
import logging
from pathlib import Path
from typing import List, Optional, Tuple

from utils.error_handlers import SolderPipelineError

# Define the path to the research document relative to the project root
# The project root is typically the parent of 'code/'
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
RESEARCH_DOC_PATH = PROJECT_ROOT / "docs" / "research.md"

class ConstitutionError(SolderPipelineError):
    """Raised when the Constitution Check (research.md verification) fails."""
    pass

def get_logger():
    """Get a logger instance for the reference validator."""
    logger = logging.getLogger("ReferenceValidator")
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger

def check_research_md_exists() -> bool:
    """Check if research.md exists at the expected path."""
    return RESEARCH_DOC_PATH.exists()

def extract_citations(content: str) -> List[str]:
    """
    Extract potential citations from the markdown content.
    Looks for patterns like [Author, Year], DOIs, or URLs.
    """
    # Pattern for [Author, Year] style
    author_year_pattern = r'\[([A-Z][a-z]+(?:,?\s+[A-Z][a-z]+)*),\s*(\d{4})\]'
    # Pattern for DOIs
    doi_pattern = r'10\.\d{4,9}/[-._;()/:A-Z0-9]+'
    # Pattern for URLs
    url_pattern = r'https?://[^\s]+'

    citations = []
    citations.extend(re.findall(author_year_pattern, content))
    citations.extend(re.findall(doi_pattern, content))
    citations.extend(re.findall(url_pattern, content))
    return citations

def verify_citations(content: str) -> Tuple[bool, List[str]]:
    """
    Verify that the content contains substantive citations.
    Returns (is_valid, list_of_citations).
    """
    citations = extract_citations(content)
    
    # Check for placeholder text that indicates fabrication
    placeholder_indicators = [
        "placeholder",
        "todo",
        "insert citation here",
        "fake data",
        "sample text",
        "example only"
    ]
    
    lower_content = content.lower()
    has_placeholders = any(indicator in lower_content for indicator in placeholder_indicators)
    
    if has_placeholders:
        return False, ["Content contains placeholder text."]
    
    if not citations:
        return False, ["No citations found in research.md."]
    
    # We expect a reasonable number of citations for a research document
    if len(citations) < 3:
        return False, [f"Insufficient citations found ({len(citations)}). Expected at least 3."]
    
    return True, citations

def validate_research_md() -> bool:
    """
    Main validation function for Task T008.
    Checks existence, content validity, and citation presence.
    
    Raises:
        ConstitutionError: If validation fails.
    """
    logger = get_logger()
    
    if not check_research_md_exists():
        error_msg = f"Constitution Check FAILED: {RESEARCH_DOC_PATH} does not exist."
        logger.error(error_msg)
        raise ConstitutionError(error_msg)
    
    try:
        content = RESEARCH_DOC_PATH.read_text(encoding='utf-8')
    except Exception as e:
        error_msg = f"Failed to read {RESEARCH_DOC_PATH}: {e}"
        logger.error(error_msg)
        raise ConstitutionError(error_msg)
    
    # Check for empty file
    if not content.strip():
        error_msg = f"Constitution Check FAILED: {RESEARCH_DOC_PATH} is empty."
        logger.error(error_msg)
        raise ConstitutionError(error_msg)
    
    is_valid, citations = verify_citations(content)
    
    if not is_valid:
        error_msg = f"Constitution Check FAILED: Invalid citations in {RESEARCH_DOC_PATH}. Details: {citations}"
        logger.error(error_msg)
        raise ConstitutionError(error_msg)
    
    logger.info(f"Constitution Check PASSED: {RESEARCH_DOC_PATH} is valid with {len(citations)} citations.")
    return True

def main():
    """Entry point for running the validator."""
    logger = get_logger()
    try:
        validate_research_md()
        logger.info("Reference-Validator Agent: SUCCESS")
        return 0
    except ConstitutionError as e:
        logger.error(f"Reference-Validator Agent: FAILED - {e}")
        return 1
    except Exception as e:
        logger.error(f"Reference-Validator Agent: UNEXPECTED ERROR - {e}")
        return 1

if __name__ == "__main__":
    exit(main())
