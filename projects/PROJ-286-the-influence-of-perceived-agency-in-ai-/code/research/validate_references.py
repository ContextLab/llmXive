"""
Reference Validator Agent for llmXive Project PROJ-286.

This module validates academic citations (Lee & See, 2004 and Langer, 1975)
against real bibliographic sources (Crossref API) to confirm existence,
retrieve titles, and calculate title overlap scores against expected strings.
"""
import json
import os
import sys
import time
from typing import Any, Dict, List, Optional
from difflib import SequenceMatcher

# Try to use requests, fallback to urllib if not available
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False
    from urllib.request import urlopen
    from urllib.error import URLError, HTTPError
    import json as json_lib

# Expected citations to validate
EXPECTED_CITATIONS = [
    {
        "key": "lee_see_2004",
        "authors": ["Lee", "J. D.", "See", "K. A."],
        "year": 2004,
        "expected_title_keywords": ["trust", "automation", "human"],
        "full_title_hint": "Trust in Automation: Designing for Appropriate Reliance"
    },
    {
        "key": "langer_1975",
        "authors": ["Langer", "E. J."],
        "year": 1975,
        "expected_title_keywords": ["illusion", "control", "human"],
        "full_title_hint": "The Illusion of Control"
    }
]

CROSSREF_BASE_URL = "https://api.crossref.org/works"

def calculate_similarity(str1: str, str2: str) -> float:
    """Calculate similarity ratio between two strings using SequenceMatcher."""
    return SequenceMatcher(None, str1.lower(), str2.lower()).ratio()

def fetch_crossref_data(query: str) -> Optional[Dict[str, Any]]:
    """Fetch bibliographic data from Crossref API."""
    params = {
        "query": query,
        "rows": 5,
        "sort": "score",
        "order": "desc"
    }

    if HAS_REQUESTS:
        try:
            response = requests.get(CROSSREF_BASE_URL, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error fetching from Crossref: {e}", file=sys.stderr)
            return None
    else:
        try:
            url = CROSSREF_BASE_URL + "?" + "&".join(f"{k}={v}" for k, v in params.items())
            with urlopen(url, timeout=10) as resp:
                data = json_lib.load(resp)
            return data
        except Exception as e:
            print(f"Error fetching from Crossref (urllib): {e}", file=sys.stderr)
            return None

def validate_citation(citation: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate a single citation against Crossref.
    Returns a validation report for that citation.
    """
    query = f"{citation['authors'][0]} {citation['year']}"
    data = fetch_crossref_data(query)

    result = {
        "key": citation["key"],
        "status": "failed",
        "message": "No API access or network error",
        "found": False,
        "title": None,
        "title_overlap_score": 0.0,
        "matched_citation": None
    }

    if not data or "message" not in data or "items" not in data["message"]:
        return result

    items = data["message"]["items"]
    best_match = None
    best_score = 0.0

    for item in items:
        # Check year match (approximate)
        item_year = item.get("published-print", {}).get("date-parts", [[None]])[0][0]
        if item_year and item_year != citation["year"]:
            continue

        title = item.get("title", [""])[0]
        if not title:
            continue

        # Check keyword overlap in title
        title_lower = title.lower()
        keyword_matches = sum(1 for kw in citation["expected_title_keywords"] if kw in title_lower)
        
        if keyword_matches > 0:
            score = calculate_similarity(title, citation["full_title_hint"])
            if score > best_score:
                best_score = score
                best_match = item

    if best_match:
        result["status"] = "validated"
        result["found"] = True
        result["title"] = best_match.get("title", [""])[0]
        result["title_overlap_score"] = round(best_score, 4)
        result["matched_citation"] = {
            "doi": best_match.get("DOI"),
            "publisher": best_match.get("publisher"),
            "author": best_match.get("author", [])
        }
    else:
        result["status"] = "unverified"
        result["message"] = "No matching title found with expected keywords"

    return result

def main():
    """Main entry point to validate references and write report."""
    print("Starting Reference Validation Agent...")
    
    # Ensure output directory exists
    output_dir = "research"
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "validation_report.json")

    validation_results = []
    all_validated = True

    for citation in EXPECTED_CITATIONS:
        print(f"Validating: {citation['key']}...")
        result = validate_citation(citation)
        validation_results.append(result)
        if result["status"] != "validated":
            all_validated = False
        # Be polite to the API
        time.sleep(1)

    report = {
        "project": "PROJ-286-the-influence-of-perceived-agency-in-ai-",
        "task_id": "T000",
        "validation_timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "overall_status": "completed" if all_validated else "partial",
        "citations_validated": len(validation_results),
        "results": validation_results
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print(f"Validation report written to: {output_path}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
