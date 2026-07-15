"""
Citation Verification Script (T005)

Reads the '## References' block from spec.md, extracts DOIs,
queries the primary source (Crossref API), and writes a verification report.
"""
import re
import json
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
import urllib.request
import urllib.error
import ssl

# Configuration
PROJECT_ROOT = Path(__file__).resolve().parents[2]
SPEC_PATH = PROJECT_ROOT / "specs" / "001-llmxive-extend-enterprisecrclawbench" / "spec.md"
OUTPUT_DIR = PROJECT_ROOT / "data" / "results"
OUTPUT_FILE = OUTPUT_DIR / "citation_report.json"

def load_spec_content() -> str:
    """Load the content of spec.md."""
    if not SPEC_PATH.exists():
        raise FileNotFoundError(f"Spec file not found at {SPEC_PATH}")
    return SPEC_PATH.read_text(encoding="utf-8")

def extract_references_block(content: str) -> Optional[str]:
    """
    Extract the content between '## References' and the next '##' or end of file.
    """
    # Pattern to match the References header and capture content until next header or EOF
    pattern = r'##\s+References\s*\n(.*?)(?=##\s|\Z)'
    match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return None

def extract_dois(text: str) -> List[str]:
    """
    Extract DOI strings from the text using regex.
    Matches standard DOI format: 10.xxxx/xxxxx
    """
    # DOI regex pattern
    doi_pattern = r'10\.\d{4,9}/[-._;()/:A-Z0-9]+'
    matches = re.findall(doi_pattern, text, re.IGNORECASE)
    return list(set(matches))  # Remove duplicates

def verify_doi_via_crossref(doi: str) -> Dict[str, Any]:
    """
    Query the Crossref API to verify a DOI.
    Returns a dict with 'source', 'status', 'error_message'.
    """
    url = f"https://api.crossref.org/works/{doi}"
    
    # Create an SSL context that does not verify certificates (for robustness in restricted envs)
    # In a strict production env, this should be True, but for this research script we allow it.
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE

    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "llmXive-research/1.0 (researcher@example.com)"}
        )
        with urllib.request.urlopen(req, timeout=10, context=context) as response:
            if response.status == 200:
                data = json.loads(response.read().decode("utf-8"))
                # Check if 'message' exists in the response
                if "message" in data:
                    return {
                        "source": doi,
                        "status": "pass",
                        "error_message": None
                    }
                else:
                    return {
                        "source": doi,
                        "status": "fail",
                        "error_message": "DOI found but no message content returned"
                    }
            else:
                return {
                    "source": doi,
                    "status": "fail",
                    "error_message": f"HTTP {response.status}"
                }
    except urllib.error.HTTPError as e:
        return {
            "source": doi,
            "status": "fail",
            "error_message": f"HTTP Error: {e.code} {e.reason}"
        }
    except urllib.error.URLError as e:
        return {
            "source": doi,
            "status": "fail",
            "error_message": f"URL Error: {e.reason}"
        }
    except Exception as e:
        return {
            "source": doi,
            "status": "fail",
            "error_message": f"Unexpected error: {str(e)}"
        }

def main():
    """Main entry point for the citation verification script."""
    print(f"Loading spec from: {SPEC_PATH}")
    try:
        content = load_spec_content()
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        sys.exit(1)

    references_text = extract_references_block(content)
    if not references_text:
        print("No '## References' block found in spec.md.")
        # Write an empty report or a failure report
        report = {
            "status": "fail",
            "reason": "No references block found",
            "sources": []
        }
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
        print(f"Report written to {OUTPUT_FILE}")
        return

    dois = extract_dois(references_text)
    if not dois:
        print("No DOIs found in the References block.")
        report = {
            "status": "fail",
            "reason": "No DOIs found",
            "sources": []
        }
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
        print(f"Report written to {OUTPUT_FILE}")
        return

    print(f"Found {len(dois)} DOI(s) to verify.")
    results = []
    
    for doi in dois:
        print(f"Verifying: {doi}...")
        result = verify_doi_via_crossref(doi)
        results.append(result)
        if result["status"] == "pass":
            print(f"  -> PASS")
        else:
            print(f"  -> FAIL: {result['error_message']}")

    # Determine overall status
    all_pass = all(r["status"] == "pass" for r in results)
    report = {
        "status": "pass" if all_pass else "fail",
        "sources": results
    }

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print(f"Verification complete. Report saved to {OUTPUT_FILE}")
    if not all_pass:
        print("WARNING: Some citations failed verification.")
        sys.exit(1)

if __name__ == "__main__":
    main()