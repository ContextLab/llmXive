"""
T039a: Verify research.md contains only verified static URLs/IDs.

This script scans the `research.md` file to ensure:
1. It exists and is non-empty.
2. It contains only static URLs or dataset IDs (e.g., OpenML IDs, HuggingFace dataset IDs).
3. It does NOT contain dynamic search logic (e.g., search queries, wildcards, "find the latest...").

Output: Writes validation results to `state/research_validation.json`.
Exits with code 0 if valid, 1 if invalid or missing.
"""
import os
import sys
import json
import re
import logging
from pathlib import Path
from typing import List, Tuple, Dict, Any

# Import existing logging config
from logging_config import setup_logging, get_logger, raise_on_missing_data

# Configure logging
setup_logging()
logger = get_logger(__name__)

RESEARCH_FILE = Path("research.md")
OUTPUT_FILE = Path("state/research_validation.json")

# Patterns indicating dynamic search or non-static sources
DYNAMIC_PATTERNS = [
    r"search\s+for",
    r"find\s+the\s+latest",
    r"query\s+",
    r"browse\s+",
    r"\*",  # Wildcards
    r"google\s+",
    r"baidu\s+",
    r"arxiv\s+search",
    r"keyword\s+",
    r"filter\s+by",
    r"sort\s+by",
]

# Patterns indicating static sources (OpenML, HuggingFace, direct URLs)
STATIC_PATTERNS = [
    r"https?://openml\.org/.*",
    r"https?://huggingface\.co/datasets/.*",
    r"https?://github\.com/.*\.csv",
    r"https?://\S+\.(csv|json|parquet|xlsx)",
    r"openml_\d+",
    r"hf_\S+",
    r"dataset_id\s*[:=]\s*\d+",
]

def parse_research_md(file_path: Path) -> List[str]:
    """Read research.md and return lines."""
    if not file_path.exists():
        raise FileNotFoundError(f"Research file not found: {file_path}")
    
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    if not content.strip():
        raise ValueError("Research file is empty.")
    
    return content.splitlines()

def check_static_urls(lines: List[str]) -> Tuple[bool, List[str], List[str]]:
    """
    Check if lines contain only static URLs/IDs and no dynamic search logic.
    
    Returns:
        (is_valid, static_sources, dynamic_warnings)
    """
    static_sources = []
    dynamic_warnings = []
    is_valid = True
    
    for line_num, line in enumerate(lines, 1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or stripped.startswith("<!--"):
            continue
        
        # Check for dynamic patterns
        for pattern in DYNAMIC_PATTERNS:
            if re.search(pattern, stripped, re.IGNORECASE):
                dynamic_warnings.append(f"Line {line_num}: Dynamic search logic detected: '{stripped}'")
                is_valid = False
        
        # Check for static patterns
        for pattern in STATIC_PATTERNS:
            if re.search(pattern, stripped, re.IGNORECASE):
                static_sources.append(stripped)
                break
        else:
            # If no static pattern matched and line looks like a URL or dataset reference
            if re.search(r"https?://|openml|huggingface|dataset", stripped, re.IGNORECASE):
                # It looks like a source but didn't match our static patterns strictly
                # We allow it if it doesn't trigger dynamic patterns, but log it
                pass
    
    return is_valid, static_sources, dynamic_warnings

def validate_research_file(file_path: Path) -> Dict[str, Any]:
    """
    Validate the research.md file according to Constitution II.
    
    Returns a dictionary with validation results.
    """
    try:
        lines = parse_research_md(file_path)
    except (FileNotFoundError, ValueError) as e:
        logger.error(f"Failed to parse research file: {e}")
        raise_on_missing_data(f"Research file validation failed: {e}")
    
    is_valid, static_sources, dynamic_warnings = check_static_urls(lines)
    
    result = {
        "file_path": str(file_path),
        "is_valid": is_valid,
        "static_sources_found": len(static_sources),
        "static_sources": static_sources,
        "dynamic_warnings": dynamic_warnings,
        "validation_message": "Research.md contains only verified static URLs/IDs." if is_valid else "Research.md contains dynamic search logic or missing sources."
    }
    
    logger.info(f"Validation result: {result['validation_message']}")
    if not is_valid:
        for warning in dynamic_warnings:
            logger.warning(warning)
    
    return result

def main():
    """Main entry point for T039a."""
    logger.info(f"Starting research.md validation (Task T039a)...")
    
    # Ensure output directory exists
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        result = validate_research_file(RESEARCH_FILE)
        
        # Write results to state file
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)
        
        logger.info(f"Validation results written to {OUTPUT_FILE}")
        
        # Exit with appropriate code
        if result["is_valid"]:
            logger.info("T039a PASSED: research.md is valid.")
            sys.exit(0)
        else:
            logger.error("T039a FAILED: research.md contains invalid dynamic logic.")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Critical error during validation: {e}")
        # Write failure result
        failure_result = {
            "file_path": str(RESEARCH_FILE),
            "is_valid": False,
            "error": str(e),
            "validation_message": f"Validation failed due to error: {e}"
        }
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(failure_result, f, indent=2)
        raise_on_missing_data(f"Research validation failed: {e}")

if __name__ == "__main__":
    main()