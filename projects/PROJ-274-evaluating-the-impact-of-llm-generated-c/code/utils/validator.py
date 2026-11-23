"""
Reference Validator Agent Logic (T071a implementation).

This module implements the logic to validate citations found in research documents.
It fetches metadata via DOI/URL, calculates Jaccard similarity, and logs results.
"""
import json
import os
import sys
import hashlib
import logging
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
import yaml

# Import requests if available, otherwise we simulate the fetch logic structure
# For the purpose of this task, we assume requests is installed (per requirements.txt)
try:
    import requests
except ImportError:
    requests = None
    logging.warning("requests library not found. Validation will fail if real fetch is needed.")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ReferenceValidator")

def tokenize_title(title: str) -> List[str]:
    """Tokenize a title into a set of lowercase words."""
    if not title:
        return []
    # Simple tokenization: lowercase, remove punctuation, split
    tokens = re.sub(r'[^\w\s]', '', title.lower()).split()
    return list(set(tokens))

def calculate_jaccard_similarity(set1: List[str], set2: List[str]) -> float:
    """Calculate Jaccard similarity between two token lists."""
    if not set1 or not set2:
        return 0.0
    s1 = set(set1)
    s2 = set(set2)
    intersection = len(s1.intersection(s2))
    union = len(s1.union(s2))
    if union == 0:
        return 0.0
    return intersection / union

def fetch_citation_metadata(citation: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Fetch metadata for a citation using DOI or URL.
    Returns None if fetch fails.
    """
    doi = citation.get("id") or citation.get("doi")
    url = citation.get("url")

    if not doi and not url:
        logger.warning(f"No DOI or URL found for citation: {citation}")
        return None

    # Priority: DOI (crossref)
    if doi:
        try:
            # Clean DOI
            clean_doi = doi.replace("https://doi.org/", "").replace("http://doi.org/", "")
            if not clean_doi.startswith("10."):
                clean_doi = f"10.{clean_doi}"
            
            response = requests.get(f"https://api.crossref.org/works/{clean_doi}", timeout=10)
            if response.status_code == 200:
                data = response.json()
                item = data.get("message", {})
                title_list = item.get("title", [])
                title = title_list[0] if title_list else "Unknown"
                return {"title": title, "source": "crossref"}
            else:
                logger.warning(f"Crossref fetch failed for DOI {doi}: {response.status_code}")
        except Exception as e:
            logger.error(f"Error fetching DOI {doi}: {e}")
    
    # Fallback: URL (OpenURL or generic fetch) - simplified for this task
    # In a real scenario, we might use OpenURL or just check the title against the provided one
    # If we can't fetch, we assume the provided title is the ground truth for the check
    # but the task says "Fetch primary source metadata".
    # If fetch fails, we return None to indicate failure.
    return None

def validate_reference(citation: Dict[str, Any], threshold: float = 0.7) -> Dict[str, Any]:
    """
    Validate a single citation.
    Returns a result dict with 'valid' status and details.
    """
    result = {
        "citation_id": citation.get("id", "unknown"),
        "title": citation.get("title", "unknown"),
        "valid": False,
        "similarity": 0.0,
        "error": None
    }

    if not requests:
        result["error"] = "requests library missing"
        return result

    fetched = fetch_citation_metadata(citation)
    
    if not fetched:
        # If we cannot fetch, we cannot validate similarity against a primary source.
        # Per strict rules, this might be a failure or we treat the provided title as valid if no fetch possible?
        # The task says "Fetch primary source... Calculate similarity". If fetch fails, we can't calculate.
        # We will mark as invalid to be safe, or log a warning.
        # However, for the pipeline to pass T071b, we need 'all_valid'.
        # If the citation is in the YAML, it implies it was extracted.
        # Let's assume if we can't fetch, we treat it as valid only if the title matches itself (trivial) or if we have a fallback.
        # But the spec says "Fetch primary source". If we can't, we fail.
        # For the sake of the task completion in a potentially offline runner, 
        # we might need to handle the case where the fetch is impossible.
        # BUT, the constraint says "NEVER fabricate".
        # If we can't fetch, we return invalid.
        result["error"] = "Failed to fetch metadata"
        return result

    fetched_title = fetched.get("title", "")
    provided_title = citation.get("title", "")

    if not provided_title:
        result["error"] = "No title in citation"
        return result

    tokens_fetched = tokenize_title(fetched_title)
    tokens_provided = tokenize_title(provided_title)

    sim = calculate_jaccard_similarity(tokens_fetched, tokens_provided)
    result["similarity"] = sim

    if sim >= threshold:
        result["valid"] = True
    else:
        result["error"] = f"Similarity {sim:.2f} below threshold {threshold}"

    return result

def validate_document_references(citations: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Validate all citations and return a summary."""
    results = []
    all_valid = True

    for citation in citations:
        res = validate_reference(citation)
        results.append(res)
        if not res["valid"]:
            all_valid = False

    return {
        "status": "all_valid" if all_valid else "partial_fail",
        "total": len(citations),
        "valid_count": sum(1 for r in results if r["valid"]),
        "details": results
    }

def main():
    """
    Main entry point for the validator.
    Reads state/citations.yaml, validates, writes state/validation_log.json.
    """
    # Determine paths relative to project root
    # We assume this runs from the project root or we find the root via state dir
    current_dir = Path.cwd()
    # Try to find the project root by looking for 'state' or 'specs'
    # A simple heuristic: check if 'state/citations.yaml' exists relative to cwd
    state_dir = current_dir / "state"
    if not state_dir.exists():
        # Try parent?
        state_dir = current_dir.parent / "state"
    
    input_file = state_dir / "citations.yaml"
    output_file = state_dir / "validation_log.json"

    if not input_file.exists():
        logger.error(f"Input file not found: {input_file}")
        sys.exit(1)

    # Load citations
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            # The file might be a list or a dict with a key
            data = yaml.safe_load(f)
            if isinstance(data, list):
                citations = data
            elif isinstance(data, dict) and "citations" in data:
                citations = data["citations"]
            else:
                citations = []
    except Exception as e:
        logger.error(f"Failed to load citations: {e}")
        sys.exit(1)

    if not citations:
        logger.warning("No citations found in input file.")
        # Still write a log indicating no citations to validate
        log_data = {
            "status": "all_valid", # No citations means no invalid ones
            "total": 0,
            "valid_count": 0,
            "details": []
        }
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(log_data, f, indent=2)
        return

    logger.info(f"Validating {len(citations)} citations...")
    validation_result = validate_document_references(citations)

    # Write log
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(validation_result, f, indent=2)

    logger.info(f"Validation complete. Status: {validation_result['status']}")
    if validation_result['status'] != 'all_valid':
        logger.warning("Some citations failed validation.")
        # Do not exit with error here, let T071b decide based on the log
        # But T071b will check the status and exit if not 'all_valid'

if __name__ == "__main__":
    main()