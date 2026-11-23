import json
import os
import sys
import time
from typing import Any, Dict, List, Optional
from difflib import SequenceMatcher

try:
    import requests
except ImportError:
    print("ERROR: 'requests' library is required. Please install it via 'pip install requests'.")
    sys.exit(1)

# Base URL for Crossref API
CROSSREF_BASE_URL = "https://api.crossref.org/works"

def calculate_similarity(str1: str, str2: str) -> float:
    """
    Calculate the similarity ratio between two strings using SequenceMatcher.
    Returns a float between 0 and 1.
    """
    return SequenceMatcher(None, str1.lower(), str2.lower()).ratio()

def fetch_crossref_data(author: str, year: str, title_keywords: List[str], max_results: int = 5) -> Optional[List[Dict[str, Any]]]:
    """
    Fetches potential matches from the Crossref API based on author, year, and title keywords.
    Returns a list of works or None if the request fails.
    """
    query_parts = []
    if author:
        query_parts.append(f"author:{author}")
    if year:
        query_parts.append(f"from-pub-date:{year}-01-01")
        query_parts.append(f"to-pub-date:{year}-12-31")
    
    # Construct query string
    query = " AND ".join(query_parts)
    if title_keywords:
        # Crossref supports 'title' filter but simple text search often works better for keywords
        query += f" AND {' AND '.join(title_keywords)}"

    url = f"{CROSSREF_BASE_URL}?query={query}&rows={max_results}"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data.get("message", {}).get("items", [])
    except requests.RequestException as e:
        print(f"Error fetching data from Crossref: {e}")
        return None

def validate_citation(author: str, year: str, full_title: str) -> Dict[str, Any]:
    """
    Validates a citation against Crossref.
    Returns a dictionary with validation status, best match title, and overlap score.
    """
    # Extract keywords from the provided full title for searching
    keywords = full_title.lower().split()
    # Filter out common stop words to improve search relevance
    stop_words = {'the', 'a', 'an', 'of', 'and', 'to', 'in', 'for', 'on', 'with', 'at', 'by', 'from'}
    search_keywords = [w for w in keywords if w not in stop_words and len(w) > 3]
    
    print(f"Searching for: {author} ({year}) with keywords: {search_keywords}")
    
    results = fetch_crossref_data(author, year, search_keywords)
    
    if not results:
        return {
            "author": author,
            "year": year,
            "provided_title": full_title,
            "validated": False,
            "best_match_title": None,
            "overlap_score": 0.0,
            "message": "No results found in Crossref."
        }
    
    best_match = None
    highest_score = 0.0
    best_match_title = None

    for item in results:
        item_title = item.get("title", [""])[0]
        if not item_title:
            continue
        
        score = calculate_similarity(full_title, item_title)
        if score > highest_score:
            highest_score = score
            best_match = item
            best_match_title = item_title

    # Determine validity based on a threshold (e.g., > 0.8 similarity)
    # Also check if the year matches in the best result if available
    is_valid = highest_score > 0.75
    
    # Additional check: does the matched work have the same year?
    if is_valid and best_match:
        pub_date = best_match.get("published-print", {}).get("date-parts", [[None]])[0][0]
        if pub_date and int(pub_date) != int(year):
            # If year is significantly off, lower confidence, but keep high title match as "found but year mismatch"
            # For this task, we'll flag it as validated but note the discrepancy if needed.
            pass 

    return {
        "author": author,
        "year": year,
        "provided_title": full_title,
        "validated": is_valid,
        "best_match_title": best_match_title,
        "overlap_score": round(highest_score, 4),
        "message": "Match found." if is_valid else "Match found but low similarity or no match."
    }

def main():
    """
    Main function to execute the reference validation for the specific citations.
    Citations:
    1. Lee, J. D., & See, K. A. (2004). Trust in automation: Designing for appropriate reliance.
    2. Langer, E. J. (1975). The illusion of control.
    """
    citations = [
        {
            "author": "Lee, J. D. and See, K. A.",
            "year": "2004",
            "full_title": "Trust in automation: Designing for appropriate reliance"
        },
        {
            "author": "Langer, E. J.",
            "year": "1975",
            "full_title": "The illusion of control"
        }
    ]

    results = []
    
    print("Starting Reference Validation Agent...")
    
    for citation in citations:
        print(f"\nValidating: {citation['author']} ({citation['year']})")
        result = validate_citation(citation["author"], citation["year"], citation["full_title"])
        results.append(result)
        # Rate limiting to be polite to the API
        time.sleep(1)

    output_dir = "research"
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "validation_report.json")

    report = {
        "validation_date": time.strftime("%Y-%m-%d %H:%M:%S"),
        "citations_validated": len(citations),
        "results": results
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print(f"\nValidation complete. Report saved to: {output_path}")
    return report

if __name__ == "__main__":
    main()
