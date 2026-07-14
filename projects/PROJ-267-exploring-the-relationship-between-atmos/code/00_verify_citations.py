import sys
import os
import json
import urllib.request
import urllib.error
import re
import time
from pathlib import Path

# Configuration for citation verification
# Path adjusted to project root structure: projects/PROJ-267/...
PROJECT_ROOT = Path(__file__).parent.parent
CITATIONS_FILE = PROJECT_ROOT / "specs" / "001-atmospheric-river-gravity" / "citations.json"
THRESHOLD_TOKEN_OVERLAP = 0.7
TIMEOUT_SECONDS = 10

def tokenize(text: str) -> set:
    """Convert text to a set of lowercase tokens (alphanumeric words)."""
    if not text:
        return set()
    # Normalize: lowercase, remove punctuation, split on whitespace
    tokens = re.findall(r'\b\w+\b', text.lower())
    return set(tokens)

def calculate_token_overlap(title_a: str, title_b: str) -> float:
    """Calculate Jaccard similarity (token overlap) between two titles."""
    tokens_a = tokenize(title_a)
    tokens_b = tokenize(title_b)
    if not tokens_a or not tokens_b:
        return 0.0
    intersection = tokens_a.intersection(tokens_b)
    union = tokens_a.union(tokens_b)
    if not union:
        return 0.0
    return len(intersection) / len(union)

def check_url_reachability(url: str) -> bool:
    """Check if a URL is reachable within TIMEOUT_SECONDS."""
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'llmXive-CitationVerifier/1.0'})
        with urllib.request.urlopen(req, timeout=TIMEOUT_SECONDS) as response:
            # Check for successful HTTP status (2xx)
            status = response.getcode()
            return 200 <= status < 300
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, Exception):
        return False

def fetch_primary_source_metadata(url: str) -> dict:
    """
    Attempt to fetch metadata (title) from the primary source URL.
    Supports:
      1. Direct JSON API (if content-type is application/json)
      2. HTML scraping (look for <title> tag)
      Returns a dict with 'title' key if successful, else empty dict.
    """
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'llmXive-CitationVerifier/1.0'})
        with urllib.request.urlopen(req, timeout=TIMEOUT_SECONDS) as response:
            content_type = response.headers.get('Content-Type', '').lower()
            html = response.read().decode('utf-8', errors='ignore')

            if 'application/json' in content_type:
                try:
                    data = json.loads(html)
                    # Try common keys for title
                    for key in ['title', 'name', 'headline', 'objectTitle']:
                        if key in data:
                            return {'title': str(data[key])}
                except json.JSONDecodeError:
                    pass
            elif 'text/html' in content_type or not content_type:
                # Look for <title> tag in HTML
                match = re.search(r'<title[^>]*>(.*?)</title>', html, re.IGNORECASE | re.DOTALL)
                if match:
                    title = match.group(1).strip()
                    # Clean up whitespace
                    title = re.sub(r'\s+', ' ', title)
                    return {'title': title}
    except Exception:
        pass
    return {}

def verify_citation(citation: dict) -> bool:
    """
    Verify a single citation:
    1. Check URL reachability.
    2. Fetch primary source metadata (title).
    3. Compare fetched title with citation title using token overlap >= THRESHOLD_TOKEN_OVERLAP.
    Returns True if valid, False otherwise.
    """
    url = citation.get('url')
    cited_title = citation.get('title', '')

    if not url:
        print(f"  [FAIL] Missing URL in citation: {cited_title[:50]}...")
        return False

    # 1. Check URL reachability
    if not check_url_reachability(url):
        print(f"  [FAIL] URL unreachable: {url}")
        return False

    # 2. Fetch primary source metadata
    metadata = fetch_primary_source_metadata(url)
    source_title = metadata.get('title', '')

    if not source_title:
        print(f"  [FAIL] Could not extract title from source: {url}")
        return False

    # 3. Calculate token overlap
    overlap = calculate_token_overlap(cited_title, source_title)
    print(f"  [INFO] Token overlap: {overlap:.2f} (Threshold: {THRESHOLD_TOKEN_OVERLAP})")
    print(f"  [INFO] Cited:   '{cited_title[:60]}...'")
    print(f"  [INFO] Source:  '{source_title[:60]}...'")

    if overlap < THRESHOLD_TOKEN_OVERLAP:
        print(f"  [FAIL] Token overlap {overlap:.2f} < {THRESHOLD_TOKEN_OVERLAP} for URL: {url}")
        return False

    print(f"  [PASS] Citation verified: {cited_title[:50]}...")
    return True

def main():
    """
    Main entry point for citation verification.
    Loads citations from specs/001-atmospheric-river-gravity/citations.json,
    verifies each, and exits with code 1 if any fail.
    """
    if not CITATIONS_FILE.exists():
        print(f"Error: Citations file not found at {CITATIONS_FILE}")
        print("Please ensure the citations.json file exists in the specs directory.")
        sys.exit(1)

    try:
        with open(CITATIONS_FILE, 'r', encoding='utf-8') as f:
            citations = json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in citations file: {e}")
        sys.exit(1)

    if not isinstance(citations, list):
        print("Error: Citations file must contain a JSON list of citation objects.")
        sys.exit(1)

    print(f"Verifying {len(citations)} citations from Constitution Principle II...")
    all_passed = True

    for i, citation in enumerate(citations):
        print(f"\n[{i+1}/{len(citations)}] Checking: {citation.get('title', 'Unknown')[:60]}...")
        if not verify_citation(citation):
            all_passed = False

    print("\n" + "="*60)
    if all_passed:
        print("RESULT: All citations verified successfully.")
        sys.exit(0)
    else:
        print("RESULT: One or more citations failed verification.")
        print("Constitution Principle II violation detected.")
        sys.exit(1)

if __name__ == '__main__':
    main()