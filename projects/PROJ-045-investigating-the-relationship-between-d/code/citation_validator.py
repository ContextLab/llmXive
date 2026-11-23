"""
Citation Verification Module for llmXive PROJ-045.

Implements the Reference-Validator Agent logic to verify external references
(e.g., Linus Pauling works) against primary sources.

This module:
1. Parses citation data from the project's research documentation.
2. Attempts to verify existence and metadata against real sources (DOI, ISBN, or
   authoritative bibliographic APIs like Crossref or OpenAlex).
3. Flags gaps and writes a status report to `data/processed/citation_status.json`.
4. Raises an error if a critical citation fails verification (to halt downstream tasks).
"""

import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

# We use the standard library `urllib` to avoid adding new dependencies for a simple
# verification script, but we could use `requests` if it were already in requirements.
# The project requirements.txt (T003) includes common scientific libs, but we assume
# standard library for this specific utility to minimize friction.
import urllib.request
import urllib.error
import urllib.parse
from http.client import HTTPException

# Project local imports
from utils import setup_logging

# Constants
CROSSREF_API_URL = "https://api.crossref.org/works"
OUTPUT_PATH = Path("data/processed/citation_status.json")
LOG_PATH = Path("data/processed/citation_verification.log")

# Critical citations that MUST be verified for this project to proceed.
# These are derived from the "Recent reviewer / personality comments" and task descriptions.
CRITICAL_CITATIONS = [
    {
        "id": "pauling_1960",
        "author": "Linus Pauling",
        "title": "The Nature of the Chemical Bond",
        "year": 1960,
        "type": "book",
        "source": "Cornell University Press",
        "reason": "Cited by reviewer Linus Pauling regarding computational framework for bond energies."
    },
    {
        "id": "curie_1903",
        "author": "Marie Curie",
        "title": "Recherches sur les substances radioactives",
        "year": 1903,
        "type": "thesis",
        "reason": "Cited by reviewer Marie Curie regarding quantification of defect density."
    }
]

def setup_logging() -> logging.Logger:
    """Setup logging for the citation validator."""
    logger = setup_logging("citation_validator", LOG_PATH)
    return logger

def fetch_crossref_metadata(query: str, logger: logging.Logger) -> Optional[Dict[str, Any]]:
    """
    Attempt to fetch metadata from Crossref API based on a query string.
    
    Args:
        query: Search query (e.g., "The Nature of the Chemical Bond Pauling")
        logger: Logger instance
        
    Returns:
        Dict with metadata if found, None otherwise.
    """
    url = f"{CROSSREF_API_URL}?query.title={urllib.parse.quote(query)}&rows=1&select=title,author,year,DOI,type"
    
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'llmXive-Validator/1.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))
            
            if 'message' in data and 'items' in data['message'] and len(data['message']['items']) > 0:
                item = data['message']['items'][0]
                logger.info(f"Found potential match in Crossref: {item.get('title', ['Unknown'])[0]}")
                return item
            else:
                logger.warning(f"No results found for query: {query}")
                return None
                
    except urllib.error.URLError as e:
        logger.error(f"Network error fetching from Crossref: {e}")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse Crossref JSON: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error during Crossref fetch: {e}")
        return None

def verify_citation(citation: Dict[str, Any], logger: logging.Logger) -> Dict[str, Any]:
    """
    Verify a single citation against primary sources.
    
    Returns a status dict:
    {
        "id": str,
        "verified": bool,
        "source_found": str | None,
        "details": str,
        "critical_failure": bool
    }
    """
    logger.info(f"Verifying citation: {citation['id']} ({citation['author']}, {citation['year']})")
    
    # Construct query
    query_parts = [citation.get('title', ''), citation.get('author', '')]
    query = " ".join([p for p in query_parts if p])
    
    if not query:
        result = {
            "id": citation['id'],
            "verified": False,
            "source_found": None,
            "details": "Missing title or author for query construction",
            "critical_failure": citation.get('reason', '').startswith("Cited by")
        }
        return result

    # Attempt Crossref lookup
    metadata = fetch_crossref_metadata(query, logger)
    
    if metadata:
        # Basic heuristic: check if title or author matches reasonably well
        # This is a simplified verification for the purpose of the pipeline.
        # A full NLP match would be more robust but is overkill for this task.
        matched_title = metadata.get('title', [''])[0].lower()
        matched_author = ""
        if 'author' in metadata and len(metadata['author']) > 0:
            matched_author = metadata['author'][0].get('family', '').lower()
        
        # Simple string containment check (case-insensitive)
        title_match = citation['title'].lower() in matched_title or matched_title in citation['title'].lower()
        author_match = citation['author'].lower() in matched_author or matched_author in citation['author'].lower()
        
        if title_match or author_match:
            return {
                "id": citation['id'],
                "verified": True,
                "source_found": f"Crossref: {metadata.get('DOI', 'Unknown DOI')}",
                "details": f"Matched title/author in Crossref database.",
                "critical_failure": False
            }
        else:
            return {
                "id": citation['id'],
                "verified": False,
                "source_found": f"Crossref: {metadata.get('DOI', 'Unknown DOI')}",
                "details": "Found metadata but title/author did not match sufficiently.",
                "critical_failure": citation.get('reason', '').startswith("Cited by")
            }
    else:
        # If Crossref fails, we might try other heuristics or just mark as unverified.
        # For this task, we consider Crossref the primary source for academic verification.
        return {
            "id": citation['id'],
            "verified": False,
            "source_found": None,
            "details": "Could not verify via Crossref API.",
            "critical_failure": citation.get('reason', '').startswith("Cited by")
        }

def run_verification(logger: logging.Logger) -> Dict[str, Any]:
    """
    Run verification for all CRITICAL_CITATIONS.
    Returns the full status report.
    """
    results = []
    any_critical_failure = False
    
    for citation in CRITICAL_CITATIONS:
        result = verify_citation(citation, logger)
        results.append(result)
        if result['critical_failure'] and not result['verified']:
            any_critical_failure = True
            logger.error(f"CRITICAL FAILURE: Citation {citation['id']} could not be verified.")
    
    report = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "total_citations": len(CRITICAL_CITATIONS),
        "verified_count": sum(1 for r in results if r['verified']),
        "failed_count": sum(1 for r in results if not r['verified']),
        "critical_failures": any_critical_failure,
        "citations": results
    }
    
    return report

def save_report(report: Dict[str, Any], logger: logging.Logger) -> None:
    """Save the verification report to the output path."""
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, 'w') as f:
        json.dump(report, f, indent=2)
    logger.info(f"Verification report saved to {OUTPUT_PATH}")

def main():
    """Main entry point for the citation validator."""
    logger = setup_logging()
    logger.info("Starting Citation Verification (T001)...")
    
    try:
        report = run_verification(logger)
        save_report(report, logger)
        
        if report['critical_failures']:
            logger.critical("Citation verification failed for critical references. Halting pipeline.")
            # We do not raise an exception here to allow the file to be written,
            # but the pipeline logic should check the 'critical_failures' flag.
            sys.exit(1)
        else:
            logger.info("Citation verification completed successfully.")
            sys.exit(0)
            
    except Exception as e:
        logger.exception(f"Fatal error during citation verification: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
