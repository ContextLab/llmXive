import argparse
import json
import os
import sys
import time
from typing import Any, Dict, List, Optional
from pathlib import Path
import urllib.request
import urllib.error
import urllib.parse

def fetch_crossref_data(title: str) -> Optional[Dict[str, Any]]:
    """
    Fetches data from the Crossref API for a given title.
    Returns the first work found or None if not found/error.
    """
    base_url = "https://api.crossref.org/works"
    # Encode the title for URL
    query_params = urllib.parse.urlencode({'query.title': title})
    url = f"{base_url}?{query_params}&rows=1&select=title,DOI"

    headers = {
        "User-Agent": "llmXive-research-agent (contact@example.com)",
        "Accept": "application/json"
    }

    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            items = data.get("message", {}).get("items", [])
            if items:
                return items[0]
            return None
    except (urllib.error.URLError, json.JSONDecodeError, Exception) as e:
        # Log error but return None to allow graceful handling
        print(f"Warning: Failed to fetch Crossref data for '{title}': {e}", file=sys.stderr)
        return None

def calculate_similarity(set1: set, set2: set) -> float:
    """
    Calculates Jaccard similarity between two sets of tokens.
    Jaccard = |A ∩ B| / |A ∪ B|
    """
    if not set1 and not set2:
        return 1.0
    if not set1 or not set2:
        return 0.0
    
    intersection = len(set1.intersection(set2))
    union = len(set1.union(set2))
    
    if union == 0:
        return 0.0
    return intersection / union

def tokenize(text: str) -> set:
    """
    Simple tokenization: lower case, remove punctuation, split by whitespace.
    """
    if not text:
        return set()
    # Remove punctuation and lower case
    cleaned = "".join(c.lower() if c.isalnum() or c.isspace() else " " for c in text)
    return set(cleaned.split())

def validate_citation(citation_str: str) -> Dict[str, Any]:
    """
    Validates a single citation string against Crossref.
    Expected format: "Author & Author (Year)" or similar.
    We extract the likely title if it's a full reference, or use the string as title query if it looks like a title.
    
    For this task, the input is "Lee & See (2004)" and "Langer (1975)".
    We will attempt to query these as titles directly as they are famous papers,
    or we can try to parse. Given the ambiguity, we will query the string itself 
    as the title query, which Crossref handles reasonably well for famous works.
    """
    # Attempt to fetch data
    result = fetch_crossref_data(citation_str)
    
    status = "invalid"
    doi = None
    overlap_score = 0.0
    
    if result:
        doi = result.get("DOI")
        api_title = result.get("title", [""])[0] if result.get("title") else ""
        
        # Tokenize input and API result
        input_tokens = tokenize(citation_str)
        api_tokens = tokenize(api_title)
        
        overlap_score = calculate_similarity(input_tokens, api_tokens)
        
        if overlap_score >= 0.7:
            status = "valid"
        else:
            # If low overlap, it might be a partial match or the query was too generic.
            # For the purpose of this validation, we stick to the 0.7 threshold.
            status = "invalid"
    else:
        # API failed or no result found
        status = "Verification Pending"
        
    return {
        "title": citation_str,
        "doi": doi,
        "overlap_score": round(overlap_score, 4),
        "status": status
    }

def main():
    parser = argparse.ArgumentParser(description="Validate citations against Crossref.")
    parser.add_argument(
        "--citations", 
        type=str, 
        required=True, 
        help='Comma-separated list of citation strings, e.g. "Lee & See (2004), Langer (1975)"'
    )
    parser.add_argument(
        "--output", 
        type=str, 
        default="research/validation_report.json",
        help="Path to output JSON file."
    )
    args = parser.parse_args()

    # Ensure output directory exists
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Parse input citations
    citations = [c.strip() for c in args.citations.split(",")]
    
    validation_results = []
    
    for citation in citations:
        if not citation:
            continue
        print(f"Validating: {citation}")
        result = validate_citation(citation)
        validation_results.append(result)
        # Be polite to the API
        time.sleep(0.5)

    # Write output
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(validation_results, f, indent=2)
        
    print(f"Validation complete. Results written to {args.output}")
    
    # Print summary
    valid_count = sum(1 for r in validation_results if r["status"] == "valid")
    print(f"Summary: {valid_count}/{len(validation_results)} citations validated successfully.")

if __name__ == "__main__":
    main()
