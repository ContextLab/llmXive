"""
Verification module for research.md to ensure it contains only verified static URLs/IDs.
Implements Constitution II: No dynamic search logic for data sources.
"""
import os
import sys
import json
import re
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Import logging utilities from existing project API
from logging_config import get_logger, raise_on_missing_data

# Constants
RESEARCH_MD_PATH = Path("specs/001-predict-lst-wear/research.md")
VALIDATION_OUTPUT_PATH = Path("state/research_validation.json")
STATE_DIR = Path("state")

# Patterns to detect dynamic search logic (Constitution II violations)
DYNAMIC_SEARCH_PATTERNS = [
    r"search\(",
    r"query\(",
    r"find\(",
    r"browse\(",
    r"discover\(",
    r"explore\(",
    r"lookup\(",
    r"google\(",
    r"baidu\(",
    r"duckduckgo\(",
    r"bing\(",
    r"arxiv.org/search",
    r"scopus.com/search",
    r"web of science",
    r"dynamic.*source",
    r"runtime.*lookup",
    r"api.*search",
    r"endpoint.*query",
    r"filter.*results",
    r"sort.*results",
    r"page.*results",
    r"next.*page",
    r"load.*more",
    r"fetch.*dynamic",
    r"get.*search",
    r"perform.*search",
    r"execute.*query",
    r"run.*search",
    r"trigger.*search",
    r"initiate.*search",
    r"start.*search",
    r"begin.*search",
    r"launch.*search",
    r"conduct.*search",
    r"carry.*out.*search",
    r"make.*search",
    r"do.*search",
    r"run.*query",
    r"perform.*query",
    r"execute.*search",
]

# Patterns to detect static URLs/IDs (expected valid content)
STATIC_URL_PATTERNS = [
    r"https?://[^\s]+",  # Generic URL
    r"openml.org/d/\d+",  # OpenML dataset ID
    r"huggingface.co/datasets/[^\s]+",  # HuggingFace dataset
    r"doi.org/[^\s]+",  # DOI
    r"arxiv.org/abs/\d+.\d+",  # ArXiv ID
    r"pmc.ncbi.nlm.nih.gov/articles/PMC\d+",  # PubMed Central
    r"sciencedirect.com/science/article/[^\s]+",  # ScienceDirect
    r"wiley.com/doi/[^\s]+",  # Wiley
]

# Required schema structure (from T009 spec)
REQUIRED_KEYS = ["source_name", "url", "dataset_id", "verified"]

logger = get_logger(__name__)


def parse_research_md(file_path: Path) -> Tuple[bool, List[str], Dict[str, Any]]:
    """
    Parse research.md and extract structured data.

    Args:
        file_path: Path to research.md file

    Returns:
        Tuple of (is_valid, list of errors, parsed data dict)
    """
    errors = []
    parsed_data = {}

    if not file_path.exists():
        errors.append(f"File not found: {file_path}")
        return False, errors, parsed_data

    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception as e:
        errors.append(f"Error reading file: {str(e)}")
        return False, errors, parsed_data

    lines = content.split("\n")
    current_source = None

    # Simple parser for the expected schema format
    # Expected format: {source_name: str, url: str, dataset_id: str, verified: bool}
    # Could be JSON, YAML, or structured text

    # Try to parse as JSON first
    try:
        # Look for JSON block
        json_match = re.search(r'(\{.*\})', content, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
            parsed_data = json.loads(json_str)
            if isinstance(parsed_data, dict):
                logger.info("Successfully parsed research.md as JSON")
                return True, errors, parsed_data
    except (json.JSONDecodeError, AttributeError):
        pass

    # Try to parse as structured text (key-value pairs)
    source_entries = []
    current_entry = {}

    for line in lines:
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        # Check for key-value pairs
        if ":" in line:
            key, value = line.split(":", 1)
            key = key.strip()
            value = value.strip()

            # Remove quotes if present
            value = value.strip('"\'')

            # Convert boolean strings
            if value.lower() == "true":
                value = True
            elif value.lower() == "false":
                value = False

            current_entry[key] = value

            # If we have all required keys, save the entry
            if all(key in current_entry for key in REQUIRED_KEYS):
                source_entries.append(current_entry)
                current_entry = {}

    if source_entries:
        # Convert list to dict keyed by source_name if possible
        if all("source_name" in entry for entry in source_entries):
            parsed_data = {entry["source_name"]: entry for entry in source_entries}
        else:
            parsed_data = {"sources": source_entries}

        logger.info(f"Parsed {len(source_entries)} entries from research.md")
        return True, errors, parsed_data

    errors.append("Could not parse research.md in any expected format")
    return False, errors, parsed_data


def check_static_urls(content: str) -> Tuple[bool, List[str]]:
    """
    Check that research.md contains only static URLs/IDs and no dynamic search logic.

    Args:
        content: String content of research.md

    Returns:
        Tuple of (is_valid, list of issues)
    """
    issues = []

    # Check for dynamic search patterns (Constitution II violation)
    for pattern in DYNAMIC_SEARCH_PATTERNS:
        matches = re.findall(pattern, content, re.IGNORECASE)
        if matches:
            issues.append(f"Dynamic search logic detected: pattern '{pattern}' matched {len(matches)} times")

    # Check for presence of static URLs/IDs
    has_static_urls = False
    for pattern in STATIC_URL_PATTERNS:
        if re.search(pattern, content, re.IGNORECASE):
            has_static_urls = True
            break

    if not has_static_urls:
        issues.append("No static URLs or dataset IDs found in research.md")

    # Check for placeholder or example text
    placeholder_patterns = [
        r"example\.com",
        r"sample\.com",
        r"placeholder",
        r"TODO",
        r"FIXME",
        r"HACK",
        r"XXX",
        r"insert.*here",
        r"add.*here",
        r"replace.*with",
        r"your.*here",
        r"change.*to",
        r"update.*to",
        r"modify.*to",
        r"edit.*to",
        r"fill.*in",
    ]

    for pattern in placeholder_patterns:
        if re.search(pattern, content, re.IGNORECASE):
            issues.append(f"Placeholder text detected: pattern '{pattern}'")

    return len(issues) == 0, issues


def validate_research_file(file_path: Path) -> Dict[str, Any]:
    """
    Validate research.md according to Constitution II requirements.

    Args:
        file_path: Path to research.md file

    Returns:
        Validation result dictionary
    """
    result = {
        "file_path": str(file_path),
        "exists": file_path.exists(),
        "parse_success": False,
        "static_url_check": False,
        "schema_validation": False,
        "is_valid": False,
        "issues": [],
        "sources_found": 0,
        "timestamp": None,
    }

    if not result["exists"]:
        result["issues"].append(f"File not found: {file_path}")
        return result

    # Parse the file
    parse_success, parse_errors, parsed_data = parse_research_md(file_path)
    result["parse_success"] = parse_success
    result["issues"].extend(parse_errors)

    if not parse_success:
        return result

    # Check for static URLs
    try:
        content = file_path.read_text(encoding="utf-8")
        static_check_passed, static_issues = check_static_urls(content)
        result["static_url_check"] = static_check_passed
        result["issues"].extend(static_issues)
    except Exception as e:
        result["issues"].append(f"Error checking static URLs: {str(e)}")

    # Validate schema
    schema_valid = True
    if isinstance(parsed_data, dict):
        # Check if it's a dict of sources
        if "sources" in parsed_data:
            sources = parsed_data["sources"]
            if isinstance(sources, list) and len(sources) > 0:
                result["sources_found"] = len(sources)
                for i, source in enumerate(sources):
                    if not isinstance(source, dict):
                        schema_valid = False
                        result["issues"].append(f"Source {i} is not a dict")
                        continue
                    for key in REQUIRED_KEYS:
                        if key not in source:
                            schema_valid = False
                            result["issues"].append(f"Source {i} missing required key: {key}")
        else:
            # Check if top-level dict values are sources
            source_count = 0
            for key, value in parsed_data.items():
                if isinstance(value, dict):
                    missing_keys = [k for k in REQUIRED_KEYS if k not in value]
                    if missing_keys:
                        schema_valid = False
                        result["issues"].append(f"Source '{key}' missing keys: {missing_keys}")
                    else:
                        source_count += 1
            result["sources_found"] = source_count
    elif isinstance(parsed_data, list):
        if len(parsed_data) > 0:
            result["sources_found"] = len(parsed_data)
            for i, item in enumerate(parsed_data):
                if not isinstance(item, dict):
                    schema_valid = False
                    result["issues"].append(f"Item {i} is not a dict")
                    continue
                missing_keys = [k for k in REQUIRED_KEYS if k not in item]
                if missing_keys:
                    schema_valid = False
                    result["issues"].append(f"Item {i} missing keys: {missing_keys}")

    result["schema_validation"] = schema_valid

    # Overall validity
    result["is_valid"] = (
        result["parse_success"] and
        result["static_url_check"] and
        result["schema_validation"] and
        result["sources_found"] > 0
    )

    # Add timestamp
    from datetime import datetime
    result["timestamp"] = datetime.utcnow().isoformat()

    return result


def main():
    """
    Main entry point for research.md verification.
    Validates research.md and writes results to state/research_validation.json
    """
    logger.info("Starting research.md verification (T039a)")

    # Ensure state directory exists
    STATE_DIR.mkdir(parents=True, exist_ok=True)

    # Validate the research file
    validation_result = validate_research_file(RESEARCH_MD_PATH)

    # Write results to output file
    try:
        with open(VALIDATION_OUTPUT_PATH, "w", encoding="utf-8") as f:
            json.dump(validation_result, f, indent=2)
        logger.info(f"Validation results written to {VALIDATION_OUTPUT_PATH}")
    except Exception as e:
        logger.error(f"Failed to write validation results: {str(e)}")
        raise_on_missing_data(f"Failed to write validation results: {str(e)}")

    # Print summary
    print(f"\n=== Research.md Validation Summary ===")
    print(f"File exists: {validation_result['exists']}")
    print(f"Parse success: {validation_result['parse_success']}")
    print(f"Static URL check: {validation_result['static_url_check']}")
    print(f"Schema validation: {validation_result['schema_validation']}")
    print(f"Sources found: {validation_result['sources_found']}")
    print(f"Overall valid: {validation_result['is_valid']}")

    if validation_result["issues"]:
        print(f"\nIssues found ({len(validation_result['issues'])}):")
        for issue in validation_result["issues"]:
            print(f"  - {issue}")

    # Exit with appropriate code
    if validation_result["is_valid"]:
        logger.info("Research.md validation PASSED")
        sys.exit(0)
    else:
        logger.error("Research.md validation FAILED")
        sys.exit(1)


if __name__ == "__main__":
    main()
