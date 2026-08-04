import sys
import os
import json
import urllib.request
import urllib.error
import re
from typing import List, Dict, Any, Optional, Tuple

# Constants for citation verification
TOKEN_OVERLAP_THRESHOLD = 0.7
CITATION_FILES = [
    "specs/001-atmospheric-river-gravity/spec.md",
    "plan.md"
]

def tokenize(text: str) -> List[str]:
    """
    Convert a string into a list of lowercase alphanumeric tokens.
    Removes punctuation and splits on whitespace.
    """
    if not text:
        return []
    # Convert to lowercase and replace non-alphanumeric with space
    cleaned = re.sub(r'[^a-z0-9\s]', ' ', text.lower())
    # Split on whitespace and filter empty strings
    tokens = [t for t in cleaned.split() if t]
    return tokens

def calculate_token_overlap(title_a: str, title_b: str) -> float:
    """
    Calculate the Jaccard similarity (token overlap) between two titles.
    Returns a value between 0.0 and 1.0.
    """
    tokens_a = set(tokenize(title_a))
    tokens_b = set(tokenize(title_b))
    
    if not tokens_a or not tokens_b:
        return 0.0
    
    intersection = tokens_a.intersection(tokens_b)
    union = tokens_a.union(tokens_b)
    
    return len(intersection) / len(union) if union else 0.0

def check_url_reachability(url: str) -> bool:
    """
    Perform an HTTP HEAD request to verify URL accessibility.
    Returns True if the URL is reachable (status 200 or 301/302 redirect), False otherwise.
    """
    try:
        req = urllib.request.Request(url, method='HEAD')
        # Set a reasonable timeout
        with urllib.request.urlopen(req, timeout=10) as response:
            status = response.getcode()
            return status == 200 or 300 <= status < 400
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, Exception):
        return False

def fetch_primary_source_metadata(url: str) -> Optional[Dict[str, Any]]:
    """
    Attempt to retrieve metadata from the primary source URL.
    Tries to parse JSON metadata if available, otherwise attempts to extract title from HTML.
    Returns a dict with 'title' and 'url' if successful, None otherwise.
    """
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=15) as response:
            content_type = response.headers.get('Content-Type', '')
            content = response.read().decode('utf-8', errors='ignore')
            
            # Try to parse JSON metadata (e.g., from APIs)
            if 'application/json' in content_type:
                try:
                    data = json.loads(content)
                    # Look for common title keys
                    for key in ['title', 'name', 'name_title', 'document_title']:
                        if key in data:
                            return {'title': str(data[key]), 'url': url}
                    # Fallback: return first string value found
                    for val in data.values():
                        if isinstance(val, str) and len(val) > 10:
                            return {'title': val, 'url': url}
                except json.JSONDecodeError:
                    pass
            
            # Try to extract title from HTML
            if 'text/html' in content_type:
                title_match = re.search(r'<title[^>]*>(.*?)</title>', content, re.IGNORECASE | re.DOTALL)
                if title_match:
                    title = title_match.group(1).strip()
                    # Clean up HTML entities and extra whitespace
                    title = re.sub(r'<[^>]+>', '', title)
                    title = re.sub(r'\s+', ' ', title).strip()
                    if title:
                        return {'title': title, 'url': url}
            
            return None
    except Exception:
        return None

def verify_citation(citation: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Verify a single citation entry.
    Returns (success: bool, message: str).
    """
    url = citation.get('url')
    expected_title = citation.get('title', citation.get('name', ''))
    
    if not url:
        return False, "Missing URL in citation"
    
    if not expected_title:
        return False, f"Missing title in citation for URL: {url}"
    
    # Step 1: Check URL reachability
    if not check_url_reachability(url):
        return False, f"URL not reachable: {url}"
    
    # Step 2: Fetch primary source metadata
    metadata = fetch_primary_source_metadata(url)
    if not metadata or not metadata.get('title'):
        return False, f"Could not retrieve title from primary source: {url}"
    
    actual_title = metadata['title']
    
    # Step 3: Compute token overlap
    overlap = calculate_token_overlap(expected_title, actual_title)
    
    if overlap < TOKEN_OVERLAP_THRESHOLD:
        return False, (
            f"Title token overlap ({overlap:.2f}) below threshold ({TOKEN_OVERLAP_THRESHOLD}) "
            f"for URL: {url}\n"
            f"  Expected: {expected_title}\n"
            f"  Actual:   {actual_title}"
        )
    
    return True, f"Verified: {url} (overlap: {overlap:.2f})"

def load_citations() -> List[Dict[str, Any]]:
    """
    Extract citation metadata from spec.md and plan.md.
    Looks for patterns like 'Title: ... URL: ...' or JSON blocks.
    Returns a list of citation dicts with 'title' and 'url' keys.
    """
    citations = []
    
    for file_path in CITATION_FILES:
        if not os.path.exists(file_path):
            continue
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Pattern 1: Look for JSON-like blocks with title and url
        json_pattern = r'\{[^{}]*"title"[^{}]*"url"[^{}]*\}|\{[^{}]*"url"[^{}]*"title"[^{}]*\}'
        json_matches = re.findall(json_pattern, content, re.DOTALL)
        
        for match in json_matches:
            try:
                data = json.loads(match)
                if 'url' in data and 'title' in data:
                    citations.append({'title': data['title'], 'url': data['url']})
            except json.JSONDecodeError:
                continue
        
        # Pattern 2: Look for "Title: ... URL: ..." lines
        line_pattern = r'Title:\s*([^\n]+)\s*URL:\s*([^\s\n]+)'
        for match in re.finditer(line_pattern, content):
            title = match.group(1).strip().strip('"\'')
            url = match.group(2).strip().strip('"\'')
            if title and url:
                citations.append({'title': title, 'url': url})
        
        # Pattern 3: Look for markdown links with titles: [Title](URL)
        # Only if it looks like a citation (contains "DOI", "URL", "Accessed", or specific journal names)
        if 'doi' in content.lower() or 'journal' in content.lower():
            link_pattern = r'\[([^\]]+)\]\((https?://[^\)]+)\)'
            for match in re.finditer(link_pattern, content):
                title = match.group(1).strip()
                url = match.group(2).strip()
                # Filter for likely citations
                if len(title) > 10 and (len(url) > 20):
                    citations.append({'title': title, 'url': url})
    
    # Remove duplicates based on URL
    seen_urls = set()
    unique_citations = []
    for c in citations:
        if c['url'] not in seen_urls:
            seen_urls.add(c['url'])
            unique_citations.append(c)
    
    return unique_citations

def main() -> int:
    """
    Main entry point for citation verification.
    Returns 0 if all citations pass, 1 if any fail.
    """
    print("Starting citation verification...")
    
    citations = load_citations()
    
    if not citations:
        print("WARNING: No citations found in spec.md or plan.md.")
        print("Please ensure citations are formatted as JSON blocks or 'Title: ... URL: ...' lines.")
        # Do not fail if no citations found, just warn
        return 0
    
    print(f"Found {len(citations)} citation(s) to verify.\n")
    
    failed = False
    for i, citation in enumerate(citations, 1):
        print(f"[{i}/{len(citations)}] Checking: {citation.get('url', 'N/A')}")
        success, message = verify_citation(citation)
        
        if success:
            print(f"  ✓ PASS: {message}\n")
        else:
            print(f"  ✗ FAIL: {message}\n")
            failed = True
    
    if failed:
        print("Citation verification FAILED. Please review the errors above.")
        return 1
    else:
        print("All citations verified successfully.")
        return 0

if __name__ == "__main__":
    sys.exit(main())