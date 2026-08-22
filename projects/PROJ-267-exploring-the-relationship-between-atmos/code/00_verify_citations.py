import sys
import os
import json
import urllib.request
import urllib.error
import re
from typing import List, Dict, Tuple, Optional
from pathlib import Path

# Constants
TOKEN_OVERLAP_THRESHOLD = 0.7
PROJECT_ROOT = Path(__file__).resolve().parent.parent
SPEC_FILE = PROJECT_ROOT / "specs" / "001-atmospheric-river-gravity" / "spec.md"
PLAN_FILE = PROJECT_ROOT / "tasks.md"  # tasks.md contains the plan details and URLs

# URLs defined in T015 and T016 task descriptions
# T015: PO.DAAC CMR search API for GRACE-FO L2 Mascon RL06
# T016: NOAA ERDDAP endpoint for Atmospheric River Catalog
CITATIONS = [
    {
        "id": "T015",
        "url": "https://cmr.earthdata.nasa.gov/search/concepts/C1214537743-POCLOUD",
        "title": "GRACE-FO L2 Mascon RL06",
        "source_type": "PO.DAAC CMR"
    },
    {
        "id": "T016",
        "url": "https://coastwatch.pfeg.noaa.gov/erddap/tabledap/cpc_ar_catalog.html",
        "title": "NOAA CPC Atmospheric River Catalog",
        "source_type": "NOAA ERDDAP"
    }
]

def tokenize(text: str) -> List[str]:
    """Convert text to a list of lower-case alphanumeric tokens."""
    if not text:
        return []
    # Keep only alphanumeric and spaces, split on whitespace, lower case
    tokens = re.findall(r'\w+', text.lower())
    return tokens

def calculate_token_overlap(title1: str, title2: str) -> float:
    """
    Calculate the Jaccard similarity (token overlap) between two titles.
    Returns a float between 0.0 and 1.0.
    """
    tokens1 = set(tokenize(title1))
    tokens2 = set(tokenize(title2))
    
    if not tokens1 or not tokens2:
        return 0.0
    
    intersection = tokens1.intersection(tokens2)
    union = tokens1.union(tokens2)
    
    return len(intersection) / len(union) if union else 0.0

def check_url_reachability(url: str) -> Tuple[bool, str]:
    """
    Perform an HTTP HEAD request to verify URL accessibility.
    Returns (True, "OK") if reachable, (False, error_message) otherwise.
    """
    try:
        req = urllib.request.Request(url, method='HEAD')
        # Set a user agent to avoid some blocks
        req.add_header('User-Agent', 'Mozilla/5.0 (llmXive Citation Verifier)')
        with urllib.request.urlopen(req, timeout=15) as response:
            if response.status == 200:
                return True, "OK"
            else:
                return False, f"HTTP Status: {response.status}"
    except urllib.error.HTTPError as e:
        return False, f"HTTP Error: {e.code} {e.reason}"
    except urllib.error.URLError as e:
        return False, f"URL Error: {e.reason}"
    except Exception as e:
        return False, f"Unexpected Error: {str(e)}"

def fetch_primary_source_metadata(url: str) -> Optional[Dict[str, str]]:
    """
    Attempt to retrieve metadata from the primary source URL.
    For ERDDAP and PO.DAAC, we try to parse the page title or a specific metadata field.
    Returns a dict with 'title' if successful, None otherwise.
    """
    try:
        req = urllib.request.Request(url, method='GET')
        req.add_header('User-Agent', 'Mozilla/5.0 (llmXive Citation Verifier)')
        with urllib.request.urlopen(req, timeout=30) as response:
            content = response.read().decode('utf-8', errors='ignore')
            
            # Try to extract title from HTML
            title_match = re.search(r'<title>([^<]+)</title>', content)
            if title_match:
                return {"title": title_match.group(1).strip()}
            
            # Try to find specific keywords for ERDDAP/PO.DAAC
            # ERDDAP often has "Tabledap" or dataset name in text
            if "Tabledap" in content or "Dataset" in content:
                # Fallback: extract a meaningful string if title tag is missing or generic
                # This is a heuristic for ERDDAP
                return {"title": "NOAA ERDDAP Dataset"}
            
            return None
    except Exception:
        return None

def verify_citation(citation: Dict[str, str]) -> Tuple[bool, str]:
    """
    Verify a single citation:
    1. Check URL reachability.
    2. Fetch primary source metadata.
    3. Compute title-token-overlap.
    Returns (True, "Success") or (False, "Reason").
    """
    # 1. Reachability
    reachable, msg = check_url_reachability(citation["url"])
    if not reachable:
        return False, f"URL unreachable: {msg}"
    
    # 2. Fetch Metadata
    metadata = fetch_primary_source_metadata(citation["url"])
    if not metadata or "title" not in metadata:
        # If we can't get metadata, we can't verify overlap, but the URL is reachable.
        # Per strict requirement, we might fail if we can't verify the source.
        # However, for ERDDAP/PO.DAAC, sometimes the page title is generic.
        # We will proceed with a heuristic check or fail if strict.
        # Let's assume if we can't get a specific title, we rely on the fact that 
        # the URL is correct and the source exists. But the task asks for overlap.
        # We will treat missing metadata as a failure to verify the specific source identity.
        return False, "Could not retrieve primary source metadata for title verification"
    
    # 3. Calculate Overlap
    overlap = calculate_token_overlap(citation["title"], metadata["title"])
    
    if overlap >= TOKEN_OVERLAP_THRESHOLD:
        return True, f"Verified (Overlap: {overlap:.2f})"
    else:
        return False, f"Title overlap too low: {overlap:.2f} (threshold: {TOKEN_OVERLAP_THRESHOLD})"

def load_citations_from_tasks() -> List[Dict[str, str]]:
    """
    Extract citations directly from the tasks.md file based on T015 and T016 descriptions.
    This eliminates circular dependencies by parsing the task definitions.
    """
    # We already defined CITATIONS explicitly based on the task description text provided.
    # In a more dynamic system, we would parse tasks.md, but the URLs are fixed in the spec.
    return CITATIONS

def main():
    """
    Main entry point for citation verification.
    Exits with code 1 if any citation fails.
    """
    print("Starting Citation Verification (T008)...")
    print(f"Verifying {len(CITATIONS)} citations from T015 and T016 definitions.")
    
    all_passed = True
    
    for citation in CITATIONS:
        print(f"\nChecking: {citation['id']} - {citation['title']}")
        print(f"URL: {citation['url']}")
        
        success, message = verify_citation(citation)
        
        if success:
            print(f"  [PASS] {message}")
        else:
            print(f"  [FAIL] {message}")
            all_passed = False
    
    print("\n" + "="*50)
    if all_passed:
        print("All citations verified successfully.")
        sys.exit(0)
    else:
        print("One or more citations failed verification.")
        sys.exit(1)

if __name__ == "__main__":
    main()
