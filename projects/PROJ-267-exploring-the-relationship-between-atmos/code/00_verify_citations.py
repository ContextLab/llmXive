"""
Citation Verification Script for PROJ-267
Validates URL reachability and citation metadata (title-token-overlap)
against primary sources before Phase 0 begins.
"""
import sys
import os
import json
import urllib.request
import urllib.error
import re
from pathlib import Path
from typing import List, Dict, Any, Tuple

# Constants
PROJECT_ROOT = Path(__file__).resolve().parent.parent
CITATIONS_FILE = PROJECT_ROOT / "docs" / "citations.json"
MIN_OVERLAP_THRESHOLD = 0.7
REQUEST_TIMEOUT = 30

def tokenize(text: str) -> List[str]:
    """
    Tokenize text into a set of normalized tokens.
    Converts to lowercase, removes punctuation, and splits by whitespace.
    """
    if not text:
        return []
    # Lowercase and remove non-alphanumeric characters (keeping spaces)
    normalized = re.sub(r'[^a-z0-9\s]', '', text.lower())
    # Split and filter empty strings
    tokens = set(normalized.split())
    return list(tokens)

def calculate_token_overlap(title_a: str, title_b: str) -> float:
    """
    Calculate the Jaccard similarity (token overlap) between two titles.
    Returns a float between 0.0 and 1.0.
    """
    tokens_a = set(tokenize(title_a))
    tokens_b = set(tokenize(title_b))

    if not tokens_a or not tokens_b:
        return 0.0

    intersection = tokens_a.intersection(tokens_b)
    union = tokens_a.union(tokens_b)

    if not union:
        return 0.0

    return len(intersection) / len(union)

def check_url_reachability(url: str) -> Tuple[bool, str]:
    """
    Checks if a URL is reachable via HTTP GET.
    Returns (True, message) if reachable, (False, error_message) otherwise.
    """
    if not url or not url.startswith(('http://', 'https://')):
        return False, f"Invalid URL format: {url}"

    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as response:
            if response.status == 200:
                return True, "URL reachable"
            else:
                return False, f"HTTP {response.status}"
    except urllib.error.HTTPError as e:
        return False, f"HTTP Error: {e.code}"
    except urllib.error.URLError as e:
        return False, f"URL Error: {e.reason}"
    except Exception as e:
        return False, f"Unexpected Error: {str(e)}"

def fetch_primary_source_metadata(url: str) -> Dict[str, Any]:
    """
    Attempts to fetch metadata (specifically title) from a URL.
    Supports standard HTML parsing for <title> tags.
    """
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as response:
            html_content = response.read().decode('utf-8', errors='ignore')
            
            # Simple regex to find <title>...</title>
            title_match = re.search(r'<title>(.*?)</title>', html_content, re.IGNORECASE | re.DOTALL)
            if title_match:
                title = title_match.group(1).strip()
                # Clean up extra whitespace
                title = re.sub(r'\s+', ' ', title)
                return {"title": title, "source": "html_parse"}
            
            return {"title": None, "source": "no_title_tag"}
    except Exception as e:
        return {"title": None, "source": "fetch_failed", "error": str(e)}

def verify_citation(citation: Dict[str, Any]) -> Dict[str, Any]:
    """
    Verifies a single citation entry.
    Checks:
    1. URL reachability
    2. Title token overlap >= 0.7 between provided title and fetched title
    
    Returns a result dictionary with status and details.
    """
    url = citation.get("url")
    provided_title = citation.get("title", "")
    citation_id = citation.get("id", "unknown")

    result = {
        "id": citation_id,
        "url": url,
        "provided_title": provided_title,
        "status": "FAIL",
        "details": []
    }

    # 1. Check URL Reachability
    reachable, msg = check_url_reachability(url)
    if not reachable:
        result["details"].append(f"URL unreachable: {msg}")
        return result
    
    result["details"].append(f"URL reachable: {msg}")

    # 2. Fetch Primary Source Metadata
    metadata = fetch_primary_source_metadata(url)
    fetched_title = metadata.get("title")

    if not fetched_title:
        result["details"].append("Could not fetch title from primary source.")
        return result

    result["fetched_title"] = fetched_title

    # 3. Calculate Token Overlap
    overlap = calculate_token_overlap(provided_title, fetched_title)
    result["overlap_score"] = overlap

    if overlap >= MIN_OVERLAP_THRESHOLD:
        result["status"] = "PASS"
        result["details"].append(f"Title overlap ({overlap:.2f}) >= {MIN_OVERLAP_THRESHOLD}")
    else:
        result["details"].append(f"Title overlap ({overlap:.2f}) < {MIN_OVERLAP_THRESHOLD}")

    return result

def load_citations(filepath: Path) -> List[Dict[str, Any]]:
    """
    Loads citations from a JSON file.
    """
    if not filepath.exists():
        raise FileNotFoundError(f"Citations file not found: {filepath}")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    # Handle both list format and dict with 'citations' key
    if isinstance(data, list):
        return data
    elif isinstance(data, dict) and 'citations' in data:
        return data['citations']
    else:
        raise ValueError("Invalid citations file format. Expected a list or a dict with 'citations' key.")

def main():
    """
    Main entry point for citation verification.
    Exits with code 1 if any citation fails verification.
    """
    print("Starting Citation Verification...")
    print(f"Loading citations from: {CITATIONS_FILE}")

    if not CITATIONS_FILE.exists():
        print(f"ERROR: Citations file not found at {CITATIONS_FILE}")
        print("Please create docs/citations.json with your reference list.")
        sys.exit(1)

    try:
        citations = load_citations(CITATIONS_FILE)
    except Exception as e:
        print(f"ERROR: Failed to load citations: {e}")
        sys.exit(1)

    print(f"Found {len(citations)} citations to verify.\n")

    all_passed = True
    results = []

    for citation in citations:
        if not citation.get("url"):
            print(f"Skipping citation {citation.get('id', 'unknown')}: No URL provided.")
            continue

        print(f"Verifying: {citation.get('id', 'unknown')} - {citation.get('title', 'No Title')[:50]}...")
        result = verify_citation(citation)
        results.append(result)

        status_icon = "✓" if result["status"] == "PASS" else "✗"
        print(f"  Status: {status_icon} {result['status']}")
        for detail in result["details"]:
            print(f"    - {detail}")
        print()

        if result["status"] != "PASS":
            all_passed = False

    print("-" * 50)
    if all_passed:
        print("All citations verified successfully.")
        sys.exit(0)
    else:
        print("VERIFICATION FAILED: One or more citations did not pass checks.")
        print("Please review the errors above and correct docs/citations.json.")
        sys.exit(1)

if __name__ == "__main__":
    main()
