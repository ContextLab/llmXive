"""
Reference Validator Module for llmXive.

This module provides utilities to validate citations and enforce title overlap constraints
as per the Constitution Principle II and project specifications.
"""
import os
import re
import logging
import json
from typing import Dict, List, Optional, Tuple, Any
from urllib.parse import quote

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
TITLE_OVERLAP_THRESHOLD = 0.7
VALIDATION_REPORT_PATH = "data/processed/reference_validation_report.json"


def normalize_text(text: str) -> str:
    """
    Normalize text for comparison by lowercasing and removing punctuation/extra whitespace.

    Args:
        text: The input string to normalize.

    Returns:
        A normalized string suitable for token comparison.
    """
    if not text:
        return ""
    # Lowercase
    text = text.lower()
    # Remove punctuation and non-alphanumeric characters (keeping spaces)
    text = re.sub(r'[^\w\s]', '', text)
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def calculate_title_overlap(title1: str, title2: str) -> float:
    """
    Calculate the Jaccard similarity (overlap) between two titles.

    Args:
        title1: First title string.
        title2: Second title string.

    Returns:
        A float between 0.0 and 1.0 representing the overlap ratio.
    """
    if not title1 or not title2:
        return 0.0

    norm1 = normalize_text(title1)
    norm2 = normalize_text(title2)

    set1 = set(norm1.split())
    set2 = set(norm2.split())

    if not set1 or not set2:
        return 0.0

    intersection = set1.intersection(set2)
    union = set1.union(set2)

    return len(intersection) / len(union) if union else 0.0


def fetch_citation_metadata(doi: str) -> Optional[Dict[str, Any]]:
    """
    Fetch citation metadata for a given DOI.
    In a full implementation, this would query Crossref or similar APIs.
    For this implementation, we simulate the fetch or use a local cache if available.
    Since we cannot guarantee external network access in all environments,
    we attempt to fetch from a mock source or raise if strictly required.

    NOTE: In a real pipeline, this would use `requests.get(f"https://api.crossref.org/works/{doi}")`.
    Here we implement a robust structure that expects a real source or fails loudly.
    """
    # Attempt to fetch from Crossref API
    try:
        import urllib.request
        import urllib.error
        
        url = f"https://api.crossref.org/works/{quote(doi)}"
        req = urllib.request.Request(url, headers={'User-Agent': 'llmXive-Research-Agent'})
        
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))
            
            if data.get("status") == "ok":
                message = data.get("message", {})
                title = message.get("title", [None])[0]
                authors = message.get("author", [])
                published = message.get("published-print", {}).get("date-parts", [[None]])[0][0]
                
                return {
                    "doi": doi,
                    "title": title,
                    "authors": authors,
                    "published_year": published,
                    "source": "crossref"
                }
    except (urllib.error.URLError, json.JSONDecodeError, KeyError, IndexError) as e:
        logger.warning(f"Failed to fetch metadata for DOI {doi} from Crossref: {e}")
    
    # If Crossref fails, we cannot fabricate data.
    # In a real scenario, we might check a local cache file if it exists.
    cache_path = "data/raw/citation_cache.json"
    if os.path.exists(cache_path):
        try:
            with open(cache_path, 'r') as f:
                cache = json.load(f)
                if doi in cache:
                    return cache[doi]
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Failed to read citation cache: {e}")
    
    # If no source is found, return None to indicate failure to validate
    return None


def validate_reference(reference: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate a single reference against the Constitution Principle II.
    Checks if the provided title overlaps sufficiently with the fetched metadata.

    Args:
        reference: A dict containing 'doi', 'title', and optionally 'expected_title'.

    Returns:
        A validation result dict with status, overlap score, and details.
    """
    doi = reference.get("doi")
    provided_title = reference.get("title")
    expected_title = reference.get("expected_title", provided_title)

    if not doi:
        return {
            "doi": doi,
            "status": "failed",
            "reason": "Missing DOI",
            "overlap_score": 0.0
        }

    metadata = fetch_citation_metadata(doi)

    if not metadata:
        return {
            "doi": doi,
            "status": "failed",
            "reason": "Could not fetch metadata from real source",
            "overlap_score": 0.0
        }

    fetched_title = metadata.get("title", "")
    
    if not fetched_title:
        return {
            "doi": doi,
            "status": "failed",
            "reason": "Fetched metadata has no title",
            "overlap_score": 0.0
        }

    overlap = calculate_title_overlap(provided_title, fetched_title)
    
    is_valid = overlap >= TITLE_OVERLAP_THRESHOLD

    return {
        "doi": doi,
        "status": "valid" if is_valid else "invalid",
        "overlap_score": round(overlap, 4),
        "threshold": TITLE_OVERLAP_THRESHOLD,
        "provided_title": provided_title,
        "fetched_title": fetched_title,
        "reason": "Title overlap insufficient" if not is_valid else "Validated successfully"
    }


def validate_references_list(references: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Validate a list of references.

    Args:
        references: List of reference dictionaries.

    Returns:
        List of validation results.
    """
    results = []
    for ref in references:
        result = validate_reference(ref)
        results.append(result)
        status_str = "PASS" if result["status"] == "valid" else "FAIL"
        logger.info(f"Reference {result['doi']}: {status_str} (Overlap: {result['overlap_score']:.2f})")
    return results


def load_references_from_file(file_path: str) -> List[Dict[str, Any]]:
    """
    Load references from a JSON file.

    Args:
        file_path: Path to the JSON file.

    Returns:
        List of reference dictionaries.
    """
    if not os.path.exists(file_path):
        logger.warning(f"References file not found: {file_path}. Returning empty list.")
        return []

    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
            elif isinstance(data, dict) and "references" in data:
                return data["references"]
            else:
                logger.error(f"Invalid format in {file_path}. Expected list or dict with 'references' key.")
                return []
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON in {file_path}: {e}")
        return []


def save_validation_report(results: List[Dict[str, Any]], output_path: str = None) -> str:
    """
    Save the validation report to a JSON file.

    Args:
        results: List of validation result dictionaries.
        output_path: Optional path to save the report. Defaults to VALIDATION_REPORT_PATH.

    Returns:
        The path where the report was saved.
    """
    if output_path is None:
        output_path = VALIDATION_REPORT_PATH

    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Calculate summary stats
    total = len(results)
    valid_count = sum(1 for r in results if r["status"] == "valid")
    failed_count = total - valid_count

    report = {
        "summary": {
            "total_references": total,
            "valid_references": valid_count,
            "failed_references": failed_count,
            "success_rate": valid_count / total if total > 0 else 0.0
        },
        "details": results
    }

    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)

    logger.info(f"Validation report saved to {output_path}")
    return output_path


def main():
    """
    Main entry point for the reference validator.
    Expects a JSON file path as argument or uses a default location.
    """
    import sys

    input_file = sys.argv[1] if len(sys.argv) > 1 else "data/raw/references.json"
    
    logger.info(f"Loading references from {input_file}")
    references = load_references_from_file(input_file)

    if not references:
        logger.warning("No references found to validate.")
        # Create an empty report
        save_validation_report([])
        return

    logger.info(f"Validating {len(references)} references...")
    results = validate_references_list(references)
    
    report_path = save_validation_report(results)
    
    # Check overall pass/fail
    passed = all(r["status"] == "valid" for r in results)
    if passed:
        logger.info("All references validated successfully.")
    else:
        logger.error("Some references failed validation.")
        sys.exit(1)


if __name__ == "__main__":
    main()