"""
Citation Validation Module for llmXive Project.

This module implements Constitution Principle II by validating citation metadata
against primary sources (CrossRef API) to ensure scientific integrity before
proceeding with research implementation.

Validated citations: Lee & See (2004), Langer (1975)
"""

import argparse
import json
import os
import sys
import time
from typing import Any, Dict, List, Optional

import requests


def tokenize(text: str) -> List[str]:
    """
    Tokenize a string into words, handling punctuation and case.
    
    Args:
        text: Input string to tokenize
        
    Returns:
        List of lowercase words
    """
    if not text:
        return []
    # Simple tokenization: split on whitespace and punctuation
    import re
    words = re.findall(r'\b\w+\b', text.lower())
    return words


def calculate_similarity(text1: str, text2: str) -> float:
    """
    Calculate similarity between two texts using token overlap.
    
    Args:
        text1: First text
        text2: Second text
        
    Returns:
        Similarity score between 0 and 1
    """
    tokens1 = set(tokenize(text1))
    tokens2 = set(tokenize(text2))
    
    if not tokens1 or not tokens2:
        return 0.0
    
    intersection = tokens1 & tokens2
    union = tokens1 | tokens2
    
    return len(intersection) / len(union) if union else 0.0


def fetch_crossref_data(doi: str) -> Optional[Dict[str, Any]]:
    """
    Fetch metadata for a DOI from the CrossRef API.
    
    Args:
        doi: Digital Object Identifier
        
    Returns:
        Metadata dictionary or None if not found
    """
    url = f"https://api.crossref.org/works/{doi}"
    headers = {
        "User-Agent": "llmXive-research-agent (research-validation)"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if "message" in data:
            return data["message"]
        return None
    except requests.RequestException as e:
        print(f"Error fetching DOI {doi}: {e}", file=sys.stderr)
        return None
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON for DOI {doi}: {e}", file=sys.stderr)
        return None


def validate_citation(citation_str: str) -> Dict[str, Any]:
    """
    Validate a citation string against primary sources.
    
    Args:
        citation_str: Citation string (e.g., "Lee & See (2004)")
        
    Returns:
        Validation result dictionary
    """
    result = {
        "title": "",
        "doi": "",
        "overlap_score": 0.0,
        "content_verified": False,
        "status": "unknown",
        "source_url": ""
    }
    
    # Parse citation to extract author and year
    # Expected format: "Author & Author (Year)" or "Author (Year)"
    import re
    match = re.match(r'([A-Za-z\s&]+)\s*\((\d{4})\)', citation_str)
    if not match:
        result["status"] = "invalid_format"
        return result
    
    authors = match.group(1).strip()
    year = match.group(2)
    
    # Map known citations to DOIs
    # Lee & See (2004) - "Trust in Automation: Designing for Appropriate Reliance"
    known_dois = {
        "Lee & See (2004)": "10.1518/0018864042363777",
        "Langer (1975)": "10.1037/h0076653"  # Langer, E. J. (1975). The illusion of control
    }
    
    doi = known_dois.get(citation_str)
    if not doi:
        result["status"] = "unknown_citation"
        return result
    
    # Fetch from CrossRef
    metadata = fetch_crossref_data(doi)
    if not metadata:
        result["status"] = "fetch_failed"
        return result
    
    # Extract title and authors from metadata
    title = metadata.get("title", [""])[0]
    crossref_authors = metadata.get("author", [])
    crossref_year = str(metadata.get("published-print", {}).get("date-parts", [[[]]])[0][0]) if metadata.get("published-print", {}).get("date-parts", [[[]]])[0] else ""
    
    # Verify title overlap
    overlap = calculate_similarity(citation_str, title)
    
    # Verify authors
    author_names = [a.get("given", "") + " " + a.get("family", "") for a in crossref_authors]
    authors_str = " ".join(author_names)
    
    # Check if expected authors are in the metadata
    expected_authors = authors.replace("&", "").split()
    found_authors = all(any(exp.lower() in author.lower() for author in author_names) for exp in expected_authors)
    
    # Verify year
    year_match = year == crossref_year
    
    # Construct source URL
    source_url = f"https://doi.org/{doi}"
    
    result["title"] = title
    result["doi"] = doi
    result["overlap_score"] = round(overlap, 3)
    result["content_verified"] = found_authors and year_match and overlap > 0.3
    result["status"] = "valid" if result["content_verified"] else "partial_match"
    result["source_url"] = source_url
    
    return result


def main():
    """
    Main entry point for citation validation script.
    
    Usage:
        python validate_citations.py --citations "Lee & See (2004), Langer (1975)" --output research/validation_report.json
    """
    parser = argparse.ArgumentParser(description="Validate citation metadata against primary sources")
    parser.add_argument("--citations", type=str, required=True,
                      help="Comma-separated list of citation strings")
    parser.add_argument("--output", type=str, required=True,
                      help="Output JSON file path for validation report")
    
    args = parser.parse_args()
    
    # Parse citations
    citations = [c.strip() for c in args.citations.split(",")]
    
    # Validate each citation
    validation_results = []
    all_valid = True
    
    for citation in citations:
        print(f"Validating: {citation}")
        result = validate_citation(citation)
        validation_results.append(result)
        
        if result["status"] != "valid":
            print(f"  WARNING: {citation} - Status: {result['status']}")
            all_valid = False
        else:
            print(f"  ✓ Validated: {result['title']}")
        
        # Rate limit for API calls
        time.sleep(0.5)
    
    # Write output
    output_dir = os.path.dirname(args.output)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    report = {
        "citations": citations,
        "validation_results": validation_results,
        "all_valid": all_valid,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    
    print(f"\nValidation report written to: {args.output}")
    
    # Exit with error if any citation is invalid
    if not all_valid:
        print("\n⚠️  VALIDATION FAILED: One or more citations could not be fully validated.")
        print("Per Constitution Principle II, the pipeline must halt.")
        sys.exit(1)
    else:
        print("\n✓ All citations validated successfully.")
        sys.exit(0)


if __name__ == "__main__":
    main()