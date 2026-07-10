"""
Reference-Validator Agent verification gate for external citations.

Implements Constitution Principle II: Verify all citations before Phase 1.
Checks reachability (HTTP 200) and content integrity (title/DOI match) for
all external references found in research.md or provided claim files.

Fails loudly if any citation is unreachable or mismatched.
"""
import os
import sys
import re
import json
import hashlib
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
import urllib.request
import urllib.error
from urllib.parse import urlparse

# Constants
RESEARCH_FILE = "research.md"
CLAIMS_DIR = "specs/001-eval-code-simplification/claims"
STATE_MAP = "state/map.json"
TIMEOUT_SECONDS = 10

# Regex patterns for citation detection
# Matches arXiv URLs: https://arxiv.org/abs/...
ARXIV_PATTERN = re.compile(r'https://arxiv\.org/abs/(\d{4}\.\d{5})')
# Matches DOI URLs: https://doi.org/...
DOI_PATTERN = re.compile(r'https://doi\.org/(10\.\d{4}/[^\\s]+)')
# Matches generic HTTP/HTTPS URLs
URL_PATTERN = re.compile(r'https?://[^\s<>"]+|www\.[^\s<>"]+')

def load_research_content(research_path: Path) -> str:
    """Load research.md content."""
    if not research_path.exists():
        raise FileNotFoundError(f"Research file not found: {research_path}")
    return research_path.read_text(encoding="utf-8")

def extract_citations(content: str) -> List[Dict[str, Any]]:
    """
    Extract all external citations from content.
    Returns list of dicts with: url, source_type, raw_text
    """
    citations = []

    # Extract arXiv
    for match in ARXIV_PATTERN.finditer(content):
        arxiv_id = match.group(1)
        url = f"https://arxiv.org/abs/{arxiv_id}"
        citations.append({
            "url": url,
            "source_type": "arxiv",
            "raw_text": match.group(0),
            "identifier": arxiv_id
        })

    # Extract DOIs
    for match in DOI_PATTERN.finditer(content):
        doi = match.group(1)
        url = f"https://doi.org/{doi}"
        citations.append({
            "url": url,
            "source_type": "doi",
            "raw_text": match.group(0),
            "identifier": doi
        })

    # Generic URLs (excluding those already caught by arXiv/DOI)
    for match in URL_PATTERN.finditer(content):
        url = match.group(0)
        if url.startswith("http"):
            # Skip if already processed
            if any(c["url"] == url for c in citations):
                continue
            # Basic validation
            try:
                parsed = urlparse(url)
                if parsed.netloc:
                    citations.append({
                        "url": url,
                        "source_type": "generic",
                        "raw_text": url,
                        "identifier": None
                    })
            except Exception:
                continue

    return citations

def fetch_url_content(url: str, timeout: int = TIMEOUT_SECONDS) -> Tuple[bool, Optional[str], Optional[int]]:
    """
    Attempt to fetch URL content.
    Returns (success, content_or_error, status_code)
    """
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'llmXive-Citation-Validator/1.0'})
        with urllib.request.urlopen(req, timeout=timeout) as response:
            # Check status
            if response.status == 200:
                content = response.read().decode('utf-8', errors='ignore')
                return True, content, 200
            else:
                return False, f"HTTP {response.status}", response.status
    except urllib.error.HTTPError as e:
        return False, f"HTTP Error {e.code}", e.code
    except urllib.error.URLError as e:
        return False, f"URL Error: {e.reason}", None
    except Exception as e:
        return False, f"Exception: {str(e)}", None

def verify_arxiv_metadata(url: str, content: str, arxiv_id: str) -> Tuple[bool, str]:
    """
    Verify arXiv metadata matches the ID in the citation.
    Checks for the presence of the ID in the HTML title or meta tags.
    """
    # Simple heuristic: check if arXiv ID appears in title or meta
    if arxiv_id in content:
        return True, "ID found in content"
    
    # Check title tag
    title_match = re.search(r'<title>([^<]+)</title>', content)
    if title_match and arxiv_id in title_match.group(1):
        return True, "ID found in title"
    
    return False, "Metadata verification failed (ID not found in content)"

def verify_doi_metadata(url: str, content: str, doi: str) -> Tuple[bool, str]:
    """
    Verify DOI content matches.
    For DOIs, we check if the DOI string appears in the redirected content.
    """
    if doi in content:
        return True, "DOI found in content"
    return False, "DOI verification failed"

def verify_citation(citation: Dict[str, Any]) -> Dict[str, Any]:
    """
    Verify a single citation.
    Returns verification result dict.
    """
    url = citation["url"]
    source_type = citation["source_type"]
    identifier = citation.get("identifier")
    
    success, content, status_code = fetch_url_content(url)
    
    result = {
        "url": url,
        "source_type": source_type,
        "identifier": identifier,
        "reachable": False,
        "status_code": status_code,
        "verified": False,
        "message": ""
    }
    
    if not success:
        result["message"] = f"Unreachable: {content}"
        return result
    
    result["reachable"] = True
    
    # Verify content based on source type
    if source_type == "arxiv":
        verified, msg = verify_arxiv_metadata(url, content, identifier)
    elif source_type == "doi":
        verified, msg = verify_doi_metadata(url, content, identifier)
    else:
        # Generic: just check if we got non-empty content
        verified = len(content) > 100
        msg = "Generic URL check (content length > 100)"
    
    result["verified"] = verified
    result["message"] = msg
    
    return result

def generate_checksum(content: str) -> str:
    """Generate SHA256 checksum of content."""
    return hashlib.sha256(content.encode('utf-8')).hexdigest()

def write_verification_report(results: List[Dict[str, Any]], report_path: Path):
    """Write verification results to JSON report."""
    report = {
        "verification_date": datetime.now().isoformat(),
        "total_citations": len(results),
        "verified_count": sum(1 for r in results if r["verified"]),
        "failed_count": sum(1 for r in results if not r["verified"]),
        "results": results
    }
    
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

def update_state_map(results: List[Dict[str, Any]], state_path: Path):
    """Update state/map.json with verification status."""
    state = {"artifacts": {}}
    
    if state_path.exists():
        try:
            with open(state_path, "r", encoding="utf-8") as f:
                state = json.load(f)
        except json.JSONDecodeError:
            state = {"artifacts": {}}
    
    # Add verification gate entry
    verification_id = f"citations_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    state["artifacts"][verification_id] = {
        "artifact_id": verification_id,
        "artifact_type": "citation_verification",
        "timestamp": datetime.now().isoformat(),
        "file_path": str(state_path),
        "checksum": generate_checksum(json.dumps(results, sort_keys=True)),
        "status": "verified" if all(r["verified"] for r in results) else "failed",
        "details": {
            "total": len(results),
            "passed": sum(1 for r in results if r["verified"]),
            "failed": sum(1 for r in results if not r["verified"])
        }
    }
    
    with open(state_path, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)

def main():
    """Main entry point for citation verification."""
    parser = argparse.ArgumentParser(description="Verify external citations in research.md")
    parser.add_argument("--research-file", type=str, default=RESEARCH_FILE,
                      help="Path to research.md file")
    parser.add_argument("--report-file", type=str, default="data/logs/citation_verification_report.json",
                      help="Path to output verification report")
    parser.add_argument("--state-file", type=str, default=STATE_MAP,
                      help="Path to state/map.json")
    args = parser.parse_args()

    research_path = Path(args.research_file)
    report_path = Path(args.report_file)
    state_path = Path(args.state_file)

    print(f"[*] Loading research file: {research_path}")
    try:
        content = load_research_content(research_path)
    except FileNotFoundError as e:
        print(f"[!] ERROR: {e}")
        print("    Citation verification cannot proceed without research.md.")
        print("    Please complete T001-T004 first to generate research.md.")
        sys.exit(1)

    print(f"[*] Extracting citations...")
    citations = extract_citations(content)
    
    if not citations:
        print("[!] WARNING: No external citations found in research.md.")
        print("    Verification gate passed (no citations to verify).")
        # Create empty report
        write_verification_report([], report_path)
        update_state_map([], state_path)
        sys.exit(0)

    print(f"[*] Found {len(citations)} citations to verify.")
    results = []
    all_verified = True

    for i, citation in enumerate(citations, 1):
        print(f"    [{i}/{len(citations)}] Verifying: {citation['url']}")
        result = verify_citation(citation)
        results.append(result)
        
        status = "✓" if result["verified"] else "✗"
        print(f"      {status} Status: {result['status_code']}, Verified: {result['verified']}")
        if not result["verified"]:
            print(f"      Reason: {result['message']}")
            all_verified = False

    # Write report
    write_verification_report(results, report_path)
    print(f"[*] Verification report written to: {report_path}")

    # Update state
    update_state_map(results, state_path)
    print(f"[*] State map updated: {state_path}")

    # Final verdict
    if all_verified:
        print("\n[SUCCESS] All citations verified. Phase 1 can proceed.")
        sys.exit(0)
    else:
        print("\n[FAILURE] One or more citations failed verification.")
        print("    Aborting Phase 1 start. Please fix unreachable/mismatched citations.")
        sys.exit(1)

if __name__ == "__main__":
    main()
