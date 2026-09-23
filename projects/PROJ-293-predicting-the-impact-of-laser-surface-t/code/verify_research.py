import os
import sys
import json
import re
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

# Import logging setup from existing project module
from logging_config import get_logger, setup_logging

# Define patterns for dynamic search logic
DYNAMIC_SEARCH_PATTERNS = [
    r'\bsearch\b',
    r'\bquery\b',
    r'\bfind\b',
    r'\blookup\b',
    r'\bscrape\b',
    r'\bcrawl\b',
    r'\bfetch.*\?',
    r'\bapi.*\?',
    r'\bgoogle\b',
    r'\bbing\b',
    r'\bdatabase.*search',
    r'\bweb.*search',
    r'\bliterature.*search',
    r'\bmeta.*search',
    r'\bsystematic.*review.*search',
    r'\bfilter.*by',
    r'\bsort.*by',
]

# Define patterns for static data sources (allowed)
STATIC_SOURCE_PATTERNS = [
    r'https?://',
    r'ftp://',
    r'www\.',
    r'\.csv$',
    r'\.json$',
    r'\.xlsx?$',
    r'\.parquet$',
    r'\.h5$',
    r'\.hdf5$',
    r'\.joblib$',
    r'\.pkl$',
    r'openml\.org',
    r'huggingface\.co',
    r'github\.com',
    r'doi\.org',
    r'arxiv\.org',
    r'pubmed\.nlm\.nih\.gov',
    r'sciencedirect\.com',
    r'wiley\.com',
    r'tandfonline\.com',
]

def parse_research_md(file_path: Path) -> Tuple[List[str], List[str]]:
    """
    Parse research.md and extract URLs/IDs and potential dynamic search logic.

    Args:
        file_path: Path to research.md

    Returns:
        Tuple of (static_sources, dynamic_search_mentions)
    """
    static_sources = []
    dynamic_search_mentions = []

    if not file_path.exists():
        raise FileNotFoundError(f"research.md not found at {file_path}")

    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    for line_num, line in enumerate(lines, 1):
        # Check for static sources (URLs, file paths, DOIs)
        if any(re.search(pattern, line, re.IGNORECASE) for pattern in STATIC_SOURCE_PATTERNS):
            # Extract the specific URL/ID
            urls = re.findall(r'(https?://[^\s\'"<>\)]+|www\.[^\s\'"<>\)]+|ftp://[^\s\'"<>\)]+)', line)
            if urls:
                static_sources.extend([(url, line_num) for url in urls])
            file_refs = re.findall(r'([^\s\'"<>\)]+\.(csv|json|xlsx?|parquet|h5|hdf5|joblib|pkl))', line)
            if file_refs:
                static_sources.extend([(ref[0], line_num) for ref in file_refs])
            doi_refs = re.findall(r'(10\.\d{4,9}/[-._;()/:A-Z0-9]+)', line, re.IGNORECASE)
            if doi_refs:
                static_sources.extend([(doi, line_num) for doi in doi_refs])

        # Check for dynamic search logic
        for pattern in DYNAMIC_SEARCH_PATTERNS:
            if re.search(pattern, line, re.IGNORECASE):
                # Avoid false positives on static URLs that happen to contain "search" in the path
                if not re.search(r'(search\.php|search\.asp|search\.cgi|\.search\.)', line):
                    dynamic_search_mentions.append((line.strip(), line_num, pattern))

    return static_sources, dynamic_search_mentions

def validate_research_file(file_path: Path, logger: Optional[logging.Logger] = None) -> Dict[str, Any]:
    """
    Validate research.md for compliance with static data source requirements.

    Args:
        file_path: Path to research.md
        logger: Optional logger instance

    Returns:
        Validation results dictionary
    """
    if logger is None:
        logger = get_logger(__name__)

    result = {
        "file_path": str(file_path),
        "validation_timestamp": datetime.now().isoformat(),
        "is_valid": True,
        "static_sources_found": [],
        "dynamic_search_logic_found": [],
        "warnings": [],
        "errors": [],
    }

    try:
        static_sources, dynamic_search_mentions = parse_research_md(file_path)

        # Log static sources
        for source, line_num in static_sources:
            result["static_sources_found"].append({
                "source": source,
                "line_number": line_num
            })
            logger.info(f"Found static source: {source} at line {line_num}")

        # Check for dynamic search logic
        if dynamic_search_mentions:
            result["is_valid"] = False
            result["errors"].append("Dynamic search logic detected in research.md")
            logger.error(f"Dynamic search logic detected: {len(dynamic_search_mentions)} occurrences")

            for text, line_num, pattern in dynamic_search_mentions:
                result["dynamic_search_logic_found"].append({
                    "line_content": text,
                    "line_number": line_num,
                    "pattern_matched": pattern
                })
                logger.warning(f"Line {line_num} contains dynamic search pattern: {pattern}")
        else:
            logger.info("No dynamic search logic detected in research.md")

        # Check if file is empty or has no sources
        if not static_sources and not dynamic_search_mentions:
            result["warnings"].append("No data sources found in research.md")
            logger.warning("No data sources found in research.md")

        # Add summary
        result["summary"] = {
            "total_static_sources": len(static_sources),
            "total_dynamic_search_mentions": len(dynamic_search_mentions),
            "validation_passed": result["is_valid"]
        }

    except Exception as e:
        result["is_valid"] = False
        result["errors"].append(f"Validation failed with exception: {str(e)}")
        logger.error(f"Validation failed: {str(e)}")
        raise

    return result

def main():
    """
    Main entry point for research validation.
    Scans research.md for dynamic search logic and writes results to state/research_validation.json
    """
    # Setup logging
    setup_logging()
    logger = get_logger(__name__)

    # Define paths
    project_root = Path(__file__).parent.parent
    research_md_path = project_root / "research.md"
    output_path = project_root / "state" / "research_validation.json"

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Starting research validation for {research_md_path}")

    try:
        # Validate the research file
        validation_result = validate_research_file(research_md_path, logger)

        # Write results to JSON
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(validation_result, f, indent=2, default=str)

        logger.info(f"Validation results written to {output_path}")

        # Exit with appropriate code
        if validation_result["is_valid"]:
            logger.info("Research validation PASSED - no dynamic search logic found")
            sys.exit(0)
        else:
            logger.error("Research validation FAILED - dynamic search logic detected")
            sys.exit(1)

    except FileNotFoundError as e:
        logger.error(f"research.md not found: {str(e)}")
        error_result = {
            "file_path": str(research_md_path),
            "validation_timestamp": datetime.now().isoformat(),
            "is_valid": False,
            "errors": [f"research.md not found: {str(e)}"],
            "static_sources_found": [],
            "dynamic_search_logic_found": []
        }
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(error_result, f, indent=2)
        sys.exit(1)

    except Exception as e:
        logger.error(f"Unexpected error during validation: {str(e)}")
        error_result = {
            "file_path": str(research_md_path),
            "validation_timestamp": datetime.now().isoformat(),
            "is_valid": False,
            "errors": [f"Unexpected error: {str(e)}"],
            "static_sources_found": [],
            "dynamic_search_logic_found": []
        }
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(error_result, f, indent=2)
        sys.exit(1)

if __name__ == "__main__":
    main()