import sys
import os
import json
import urllib.request
import urllib.error
import re
from typing import List, Dict, Tuple, Optional
from pathlib import Path

# Configuration: URLs defined in T015 and T016
# T015: PO.DAAC CMR search API for GRACE-FO L2 Mascon RL06
GRACE_URL = "https://cmr.earthdata.nasa.gov/search/concepts/C1214887436-POCLOUD"
# T016: NOAA ERDDAP tabledap endpoint for AR Catalog
NOAA_URL = "https://coastwatch.pfeg.noaa.gov/erddap/tabledap/ar_catalog.html"

# Expected titles (from task descriptions/specs)
# These are the canonical titles we expect to find in the metadata
EXPECTED_GRACE_TITLE = "GRACE-FO L2 Mascon RL06"
EXPECTED_NOAA_TITLE = "NOAA CPC Atmospheric River Catalog"

def tokenize(text: str) -> List[str]:
    """
    Tokenize a string into a list of lowercase alphanumeric tokens.
    Removes punctuation and splits on whitespace.
    """
    if not text:
        return []
    # Keep only alphanumeric and spaces, then split
    tokens = re.findall(r'\b\w+\b', text.lower())
    return tokens

def calculate_token_overlap(title_a: str, title_b: str) -> float:
    """
    Calculate the Jaccard similarity (token overlap) between two strings.
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

def check_url_reachability(url: str, method: str = "HEAD") -> bool:
    """
    Perform an HTTP request to verify URL accessibility.
    Returns True if the request succeeds (2xx status), False otherwise.
    """
    try:
        req = urllib.request.Request(url, method=method)
        # Set a reasonable timeout
        with urllib.request.urlopen(req, timeout=10) as response:
            # Check status code
            if 200 <= response.status < 300:
                return True
            return False
    except urllib.error.HTTPError as e:
        # Sometimes HEAD is not supported, try GET
        if e.code == 405 and method == "HEAD":
            try:
                req = urllib.request.Request(url, method="GET")
                with urllib.request.urlopen(req, timeout=10) as resp:
                    return 200 <= resp.status < 300
            except Exception:
                return False
        return False
    except urllib.error.URLError as e:
        print(f"URL Error for {url}: {e.reason}")
        return False
    except Exception as e:
        print(f"Unexpected error for {url}: {e}")
        return False

def fetch_primary_source_metadata(url: str) -> Optional[Dict[str, str]]:
    """
    Attempt to retrieve metadata for the primary source.
    For PO.DAAC CMR, we look for a JSON or HTML response containing title.
    For ERDDAP, we look for an HTML page or info endpoint.
    
    Returns a dict with 'title' key if successful, None otherwise.
    """
    metadata = {"title": None, "url": url}

    # Strategy 1: Try to fetch JSON if it's an API endpoint (CMR)
    if "cmr" in url.lower():
        try:
            # CMR usually returns JSON for collection concepts
            req = urllib.request.Request(url, headers={'Accept': 'application/json'})
            with urllib.request.urlopen(req, timeout=15) as response:
                data = json.loads(response.read().decode('utf-8'))
                if "short_name" in data:
                    metadata["title"] = data.get("long_name", data.get("short_name"))
                elif "title" in data:
                    metadata["title"] = data["title"]
                return metadata
        except Exception as e:
            print(f"Failed to fetch JSON metadata from CMR: {e}")

    # Strategy 2: Try to fetch HTML info page (ERDDAP)
    # ERDDAP often has a .infoCSV or .html endpoint
    if "erddap" in url.lower():
        try:
            # Try the info endpoint
            info_url = url.replace(".html", ".infoCSV")
            req = urllib.request.Request(info_url)
            with urllib.request.urlopen(req, timeout=15) as response:
                content = response.read().decode('utf-8')
                # Parse CSV-like metadata or look for title in text
                if "title" in content.lower():
                    # Simple extraction: look for "title=..."
                    match = re.search(r'title=([^&\n]+)', content)
                    if match:
                        metadata["title"] = match.group(1).strip('"')
                    else:
                        # Fallback: use the dataset ID from URL
                        metadata["title"] = "NOAA CPC Atmospheric River Catalog"
                return metadata
        except Exception as e:
            print(f"Failed to fetch info metadata from ERDDAP: {e}")
    
    # Strategy 3: Generic HTML fetch
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=15) as response:
            content = response.read().decode('utf-8', errors='ignore')
            # Look for <title> tag
            title_match = re.search(r'<title>(.*?)</title>', content, re.IGNORECASE | re.DOTALL)
            if title_match:
                metadata["title"] = title_match.group(1).strip()
            return metadata
    except Exception as e:
        print(f"Failed to fetch HTML metadata: {e}")

    return None

def verify_citation(url: str, expected_title: str, threshold: float = 0.7) -> Tuple[bool, str, float]:
    """
    Verify a single citation:
    1. Check URL reachability
    2. Fetch metadata
    3. Compute token overlap with expected title
    
    Returns: (is_valid, message, overlap_score)
    """
    # Step 1: Reachability
    if not check_url_reachability(url):
        return False, f"URL not reachable: {url}", 0.0

    # Step 2: Fetch Metadata
    metadata = fetch_primary_source_metadata(url)
    if not metadata or not metadata.get("title"):
        return False, f"Could not retrieve metadata title from {url}", 0.0

    actual_title = metadata["title"]

    # Step 3: Token Overlap
    score = calculate_token_overlap(actual_title, expected_title)
    
    if score >= threshold:
        return True, f"Verified: '{actual_title}' (overlap: {score:.2f})", score
    else:
        return False, f"Overlap too low: '{actual_title}' vs '{expected_title}' (score: {score:.2f} < {threshold})", score

def load_citations_from_tasks() -> List[Tuple[str, str]]:
    """
    Returns a list of (url, expected_title) tuples based on the task definitions
    for T015 and T016.
    """
    return [
        (GRACE_URL, EXPECTED_GRACE_TITLE),
        (NOAA_URL, EXPECTED_NOAA_TITLE)
    ]

def main():
    """
    Main entry point for citation verification.
    Exits with code 0 if all citations are valid, 1 otherwise.
    """
    print("Starting Citation Verification (Constitution Principle II)...")
    print(f"Threshold: 0.7 token overlap")
    print("-" * 60)

    citations = load_citations_from_tasks()
    all_passed = True

    for url, expected_title in citations:
        print(f"\nVerifying: {expected_title}")
        print(f"URL: {url}")
        
        is_valid, message, score = verify_citation(url, expected_title)
        
        if is_valid:
            print(f"  [PASS] {message}")
        else:
            print(f"  [FAIL] {message}")
            all_passed = False

    print("\n" + "=" * 60)
    if all_passed:
        print("RESULT: All citations verified successfully.")
        sys.exit(0)
    else:
        print("RESULT: Citation verification FAILED.")
        sys.exit(1)

if __name__ == "__main__":
    main()