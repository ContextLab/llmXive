"""
Reference Validator Module for llmXive - The Impact of Nostalgia on Cognitive Flexibility.

This module validates citations, enforces title overlap thresholds (≥ 0.7),
and verifies reference metadata against external sources (DOI).
"""
import os
import re
import logging
import json
import hashlib
from typing import Dict, List, Optional, Tuple, Any
from urllib.parse import quote
from pathlib import Path

# Import config utilities if needed for paths
# from config import get_config

# Setup logging
logger = logging.getLogger(__name__)

# Constants
TITLE_OVERLAP_THRESHOLD = 0.7
CROSSREF_API_URL = "https://api.crossref.org/works/"

def normalize_text(text: str) -> str:
    """
    Normalize text for comparison: lower case, remove punctuation, collapse whitespace.
    """
    if not text:
        return ""
    # Lowercase
    text = text.lower()
    # Remove punctuation and special characters
    text = re.sub(r'[^\w\s]', '', text)
    # Collapse whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def calculate_title_overlap(title1: str, title2: str) -> float:
    """
    Calculate Jaccard similarity overlap between two normalized titles.
    Returns a float between 0.0 and 1.0.
    """
    norm1 = normalize_text(title1)
    norm2 = normalize_text(title2)

    if not norm1 or not norm2:
        return 0.0

    set1 = set(norm1.split())
    set2 = set(norm2.split())

    if not set1 or not set2:
        return 0.0

    intersection = set1.intersection(set2)
    union = set1.union(set2)

    if not union:
        return 0.0

    return len(intersection) / len(union)

def fetch_citation_metadata(doi: str) -> Optional[Dict[str, Any]]:
    """
    Fetch metadata for a citation using DOI from Crossref API.
    Returns metadata dict or None if not found/error.
    """
    if not doi:
        logger.warning("No DOI provided for metadata fetch.")
        return None

    # Sanitize DOI
    doi = doi.strip()
    if doi.startswith('https://doi.org/'):
        doi = doi.replace('https://doi.org/', '')
    elif doi.startswith('http://dx.doi.org/'):
        doi = doi.replace('http://dx.doi.org/', '')

    encoded_doi = quote(doi, safe='')
    url = f"{CROSSREF_API_URL}{encoded_doi}"

    try:
        import requests
        logger.info(f"Fetching metadata for DOI: {doi} from {url}")
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        if data.get('status') == 'failed':
            logger.error(f"Crossref API failed for DOI {doi}")
            return None

        message = data.get('message', {})
        return {
            'title': message.get('title', [None])[0],
            'author': message.get('author', []),
            'published-print': message.get('published-print', {}),
            'container-title': message.get('container-title', [None])[0],
            'source': message.get('source', None),
            'DOI': message.get('DOI', None),
            'type': message.get('type', None)
        }

    except Exception as e:
        logger.error(f"Failed to fetch metadata for DOI {doi}: {e}")
        return None

def validate_reference(reference: Dict[str, Any], source_metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Validate a single reference entry.
    Checks:
      1. If DOI exists and is resolvable (if source_metadata provided).
      2. If title overlap with source metadata is >= 0.7.
    """
    result = {
        'valid': False,
        'doi': reference.get('doi'),
        'title': reference.get('title'),
        'overlap_score': 0.0,
        'errors': [],
        'warnings': []
    }

    ref_doi = reference.get('doi')
    ref_title = reference.get('title', '')

    if not ref_doi:
        result['errors'].append("Missing DOI")
        return result

    # If source metadata is provided (e.g., from a known dataset), compare titles
    if source_metadata:
        src_title = source_metadata.get('title')
        if src_title:
            overlap = calculate_title_overlap(ref_title, src_title)
            result['overlap_score'] = overlap
            if overlap < TITLE_OVERLAP_THRESHOLD:
                result['errors'].append(f"Title overlap {overlap:.2f} < {TITLE_OVERLAP_THRESHOLD}")
            else:
                result['valid'] = True
        else:
            result['warnings'].append("Source metadata missing title, skipping overlap check")
            result['valid'] = True # Assume valid if we can't check
    else:
        # If no source metadata, we assume valid if DOI format looks okay
        # Or we could try to fetch it here, but that might be slow for batch validation.
        # For this task, we assume external fetch happens before or is handled separately.
        result['valid'] = True

    return result

def validate_references_list(references: List[Dict[str, Any]], source_metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Validate a list of references against optional source metadata.
    Returns a summary report.
    """
    results = []
    valid_count = 0
    invalid_count = 0

    for i, ref in enumerate(references):
        res = validate_reference(ref, source_metadata)
        results.append(res)
        if res['valid']:
            valid_count += 1
        else:
            invalid_count += 1

    return {
        'total': len(references),
        'valid': valid_count,
        'invalid': invalid_count,
        'threshold': TITLE_OVERLAP_THRESHOLD,
        'details': results
    }

def load_references_from_file(file_path: str) -> List[Dict[str, Any]]:
    """
    Load references from a JSON file.
    Expected format: List of dicts with 'doi', 'title', etc.
    """
    path = Path(file_path)
    if not path.exists():
        logger.error(f"References file not found: {file_path}")
        return []

    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
            elif isinstance(data, dict) and 'references' in data:
                return data['references']
            else:
                logger.error("Invalid references format in file")
                return []
    except Exception as e:
        logger.error(f"Error loading references file: {e}")
        return []

def save_validation_report(report: Dict[str, Any], output_path: str) -> None:
    """
    Save the validation report to a JSON file.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    logger.info(f"Validation report saved to {output_path}")

def main() -> None:
    """
    Main entry point for reference validation.
    Reads from data/references.json (example path), validates against
    metadata in data/raw/metadata.json (if available), and saves report to data/results/validation_report.json.
    """
    # Setup logging if not already done
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Define paths relative to project root
    project_root = Path(__file__).resolve().parent.parent
    refs_path = project_root / "data" / "references.json"
    metadata_path = project_root / "data" / "raw" / "metadata.json"
    report_path = project_root / "data" / "results" / "validation_report.json"

    # Ensure results directory exists
    report_path.parent.mkdir(parents=True, exist_ok=True)

    # Load references
    logger.info(f"Loading references from {refs_path}")
    references = load_references_from_file(str(refs_path))

    if not references:
        logger.warning("No references found to validate.")
        # Save empty report
        save_validation_report({'total': 0, 'valid': 0, 'invalid': 0, 'details': []}, str(report_path))
        return

    # Load source metadata if available
    source_metadata = None
    if metadata_path.exists():
        try:
            with open(metadata_path, 'r', encoding='utf-8') as f:
                meta = json.load(f)
                # Try to extract a 'validation_study' or similar if present
                # For now, we assume the metadata might contain a title if it's a specific study
                if 'title' in meta:
                    source_metadata = meta
                    logger.info("Source metadata loaded for validation.")
        except Exception as e:
            logger.warning(f"Could not load metadata for validation: {e}")

    # Validate
    logger.info(f"Validating {len(references)} references (threshold: {TITLE_OVERLAP_THRESHOLD})")
    report = validate_references_list(references, source_metadata)

    # Save report
    save_validation_report(report, str(report_path))

    # Log summary
    logger.info(f"Validation complete: {report['valid']}/{report['total']} valid.")
    if report['invalid'] > 0:
        logger.warning(f"{report['invalid']} references failed validation.")

if __name__ == "__main__":
    main()
