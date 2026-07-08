"""
Reference Validator Module for llmXive Pipeline.

This module validates academic citations by fetching metadata from external sources (Crossref API)
and enforcing a title overlap threshold (>= 0.7) between the claimed reference and the retrieved source.
"""
import os
import re
import logging
import json
from typing import Dict, List, Optional, Tuple, Any
from urllib.parse import quote
import requests

# Import existing utilities from utils.py
from utils import setup_logging, log_info, log_warning, log_error, log_critical, compute_sha256

# Constants
CROSSREF_API_URL = "https://api.crossref.org/works"
DEFAULT_TITLE_OVERLAP_THRESHOLD = 0.7
REQUEST_TIMEOUT = 10  # seconds

# Configure logging if not already done
logger = setup_logging("reference_validator")


def normalize_text(text: str) -> str:
    """
    Normalize a string for comparison: lowercase, remove punctuation, collapse whitespace.
    """
    if not text:
        return ""
    text = text.lower()
    # Remove non-alphanumeric characters except spaces
    text = re.sub(r'[^a-z0-9\s]', '', text)
    # Collapse multiple spaces into one
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def calculate_title_overlap(title_a: str, title_b: str) -> float:
    """
    Calculate the Jaccard similarity (overlap) between two titles.
    Returns a float between 0.0 and 1.0.
    """
    if not title_a or not title_b:
        return 0.0

    set_a = set(normalize_text(title_a).split())
    set_b = set(normalize_text(title_b).split())

    if not set_a or not set_b:
        return 0.0

    intersection = set_a.intersection(set_b)
    union = set_a.union(set_b)

    if not union:
        return 0.0

    return len(intersection) / len(union)


def fetch_citation_metadata(identifier: str, identifier_type: str = "doi") -> Optional[Dict[str, Any]]:
    """
    Fetch metadata for a citation from Crossref API.

    Args:
        identifier: The DOI or other identifier.
        identifier_type: Type of identifier (currently only 'doi' is supported).

    Returns:
        A dictionary containing the metadata if found, None otherwise.
    """
    if identifier_type.lower() != "doi":
        log_warning(f"Identifier type '{identifier_type}' not supported. Only 'doi' is supported.")
        return None

    if not identifier.startswith("10."):
        # Attempt to normalize DOI if it doesn't start with 10.
        # Some inputs might be just the number part or have prefixes.
        log_warning(f"DOI '{identifier}' does not appear to be in standard format. Attempting to fetch anyway.")

    url = f"{CROSSREF_API_URL}/{quote(identifier)}"
    params = {"mailto": "research@example.com"}  # Required by Crossref for rate limiting compliance

    try:
        response = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        data = response.json()

        if data.get("status") == "failed":
            log_error(f"Crossref API returned failure status for DOI: {identifier}")
            return None

        item = data.get("message", {})
        if not item:
            log_error(f"No message content found in Crossref response for DOI: {identifier}")
            return None

        return item

    except requests.exceptions.RequestException as e:
        log_error(f"Network error fetching metadata for DOI {identifier}: {str(e)}")
        return None
    except json.JSONDecodeError as e:
        log_error(f"JSON decode error for DOI {identifier}: {str(e)}")
        return None


def validate_reference(
    claimed_title: str,
    claimed_doi: str,
    threshold: float = DEFAULT_TITLE_OVERLAP_THRESHOLD
) -> Dict[str, Any]:
    """
    Validate a single reference against the Crossref database.

    Args:
        claimed_title: The title as claimed in the document.
        claimed_doi: The DOI of the reference.
        threshold: Minimum required title overlap (0.0 to 1.0).

    Returns:
        A dictionary with validation results.
    """
    result = {
        "doi": claimed_doi,
        "claimed_title": claimed_title,
        "found": False,
        "matched_title": None,
        "overlap_score": 0.0,
        "valid": False,
        "error": None
    }

    if not claimed_doi:
        result["error"] = "No DOI provided"
        log_error(f"Validation failed for title '{claimed_title}': No DOI provided")
        return result

    metadata = fetch_citation_metadata(claimed_doi)

    if not metadata:
        result["error"] = "Could not retrieve metadata from Crossref"
        log_error(f"Validation failed for DOI {claimed_doi}: Metadata retrieval failed")
        return result

    # Extract title from metadata (Crossref returns a list of titles)
    retrieved_titles = metadata.get("title", [])
    if not retrieved_titles:
        result["error"] = "No title found in retrieved metadata"
        log_warning(f"Validation skipped for DOI {claimed_doi}: No title in metadata")
        result["found"] = True
        return result

    # Use the first title for comparison
    retrieved_title = retrieved_titles[0]
    result["found"] = True
    result["matched_title"] = retrieved_title

    overlap = calculate_title_overlap(claimed_title, retrieved_title)
    result["overlap_score"] = overlap

    if overlap >= threshold:
        result["valid"] = True
        log_info(f"Reference validation PASSED for DOI {claimed_doi} (Overlap: {overlap:.2f})")
    else:
        result["valid"] = False
        log_warning(f"Reference validation FAILED for DOI {claimed_doi} (Overlap: {overlap:.2f} < {threshold})")

    return result


def validate_references_list(
    references: List[Dict[str, str]],
    threshold: float = DEFAULT_TITLE_OVERLAP_THRESHOLD
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Validate a list of references.

    Args:
        references: List of dictionaries containing 'title' and 'doi' keys.
        threshold: Minimum required title overlap.

    Returns:
        A tuple of (valid_references, invalid_references).
    """
    valid_refs = []
    invalid_refs = []

    for ref in references:
        title = ref.get("title", "")
        doi = ref.get("doi", "")

        if not title or not doi:
            log_error(f"Skipping invalid reference entry: {ref}")
            invalid_refs.append({**ref, "reason": "Missing title or DOI"})
            continue

        validation_result = validate_reference(title, doi, threshold)

        if validation_result["valid"]:
            valid_refs.append(validation_result)
        else:
            invalid_refs.append(validation_result)

    return valid_refs, invalid_refs


def load_references_from_file(file_path: str) -> List[Dict[str, str]]:
    """
    Load references from a JSON file. Expected format:
    [
      {"title": "...", "doi": "..."},
      ...
    ]

    Args:
        file_path: Path to the JSON file.

    Returns:
        List of reference dictionaries.
    """
    if not os.path.exists(file_path):
        log_error(f"References file not found: {file_path}")
        return []

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        if not isinstance(data, list):
            log_error(f"Invalid format in {file_path}: Expected a list of references.")
            return []

        return data

    except json.JSONDecodeError as e:
        log_error(f"JSON decode error in {file_path}: {str(e)}")
        return []
    except Exception as e:
        log_error(f"Error reading {file_path}: {str(e)}")
        return []


def save_validation_report(
    valid_refs: List[Dict[str, Any]],
    invalid_refs: List[Dict[str, Any]],
    output_path: str
) -> None:
    """
    Save the validation report to a JSON file.

    Args:
        valid_refs: List of valid reference validation results.
        invalid_refs: List of invalid reference validation results.
        output_path: Path to the output JSON file.
    """
    report = {
        "summary": {
            "total_validated": len(valid_refs) + len(invalid_refs),
            "valid_count": len(valid_refs),
            "invalid_count": len(invalid_refs),
            "threshold_used": DEFAULT_TITLE_OVERLAP_THRESHOLD
        },
        "valid_references": valid_refs,
        "invalid_references": invalid_refs
    }

    try:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)
        log_info(f"Validation report saved to {output_path}")
    except Exception as e:
        log_error(f"Failed to save validation report to {output_path}: {str(e)}")


def main():
    """
    Main entry point for the reference validator script.
    Expects a reference file path as an argument or uses a default path.
    """
    import sys

    # Default paths
    default_ref_file = "data/raw/references.json"
    default_output_file = "data/results/reference_validation_report.json"

    # Check for command line arguments
    if len(sys.argv) > 1:
        ref_file = sys.argv[1]
    else:
        ref_file = default_ref_file

    if len(sys.argv) > 2:
        output_file = sys.argv[2]
    else:
        output_file = default_output_file

    log_info(f"Starting reference validation for file: {ref_file}")

    # Load references
    references = load_references_from_file(ref_file)

    if not references:
        log_critical("No references found to validate. Exiting.")
        sys.exit(1)

    log_info(f"Loaded {len(references)} references.")

    # Validate
    valid_refs, invalid_refs = validate_references_list(references)

    # Save report
    save_validation_report(valid_refs, invalid_refs, output_file)

    log_info(f"Validation complete. Valid: {len(valid_refs)}, Invalid: {len(invalid_refs)}")

    # Exit with code 1 if any validations failed
    if invalid_refs:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()