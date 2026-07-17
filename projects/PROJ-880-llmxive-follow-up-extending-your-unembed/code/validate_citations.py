"""
validate_citations.py

Parses markdown files to extract citation URLs and verifies them against a
local manifest (data/citations_manifest.json). Implements Constitution Principle II.

Usage:
    python code/validate_citations.py [--manifest PATH] [--output PATH]

The script reads all .md files in the `specs/` directory (or a specified root),
extracts URLs found in standard markdown citation syntax `[^n]: <url>`,
and checks them against the provided manifest.
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple

# Default paths relative to project root
DEFAULT_SPECS_DIR = "specs"
DEFAULT_MANIFEST_PATH = "data/citations_manifest.json"
DEFAULT_OUTPUT_PATH = "data/citation_validation_report.json"

# Regex to match markdown citation definitions:
# Matches: [^1]: https://example.com
# Captures the URL group
CITATION_REGEX = re.compile(r'\[\^\d+\]:\s*(https?://[^\s\]]+)')

def load_manifest(manifest_path: str) -> Dict[str, any]:
    """
    Loads the citations manifest from a JSON file.
    Expected format:
    {
        "verified_urls": ["https://...", "..."],
        "last_verified": "YYYY-MM-DD"
    }
    """
    if not os.path.exists(manifest_path):
        raise FileNotFoundError(f"Citation manifest not found at: {manifest_path}")
    
    with open(manifest_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if "verified_urls" not in data:
        raise ValueError("Manifest must contain a 'verified_urls' key.")
    
    return set(data["verified_urls"])

def extract_urls_from_markdown(root_dir: str) -> Dict[str, List[str]]:
    """
    Recursively scans .md files in root_dir and extracts citation URLs.
    Returns a dict mapping file path to list of extracted URLs.
    """
    extracted: Dict[str, List[str]] = {}
    root_path = Path(root_dir)

    if not root_path.exists():
        raise FileNotFoundError(f"Specs directory not found: {root_dir}")

    md_files = list(root_path.rglob("*.md"))
    
    if not md_files:
        print(f"Warning: No markdown files found in {root_dir}")
        return extracted

    for md_file in md_files:
        try:
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            urls = CITATION_REGEX.findall(content)
            if urls:
                extracted[str(md_file)] = urls
        except Exception as e:
            print(f"Error reading {md_file}: {e}", file=sys.stderr)
            continue

    return extracted

def verify_citations(
    extracted: Dict[str, List[str]], 
    verified_set: Set[str]
) -> Dict[str, any]:
    """
    Compares extracted URLs against the verified set.
    Returns a report structure.
    """
    all_extracted_urls = set()
    missing_urls: Dict[str, List[str]] = {}
    valid_urls: Dict[str, List[str]] = {}

    for file_path, urls in extracted.items():
        file_missing = []
        file_valid = []
        for url in urls:
            all_extracted_urls.add(url)
            if url in verified_set:
                file_valid.append(url)
            else:
                file_missing.append(url)
        
        if file_missing:
            missing_urls[file_path] = file_missing
        if file_valid:
            valid_urls[file_path] = file_valid

    total_missing = sum(len(v) for v in missing_urls.values())
    total_valid = sum(len(v) for v in valid_urls.values())
    total_extracted = len(all_extracted_urls)

    report = {
        "total_unique_citations": total_extracted,
        "verified_count": total_valid,
        "unverified_count": total_missing,
        "verification_rate": total_valid / total_extracted if total_extracted > 0 else 0.0,
        "status": "PASS" if total_missing == 0 else "FAIL",
        "details": {
            "missing_citations": missing_urls,
            "verified_citations": valid_urls
        }
    }

    return report

def main():
    parser = argparse.ArgumentParser(
        description="Validate markdown citations against a local manifest."
    )
    parser.add_argument(
        "--manifest", 
        default=DEFAULT_MANIFEST_PATH, 
        help=f"Path to the citations manifest JSON (default: {DEFAULT_MANIFEST_PATH})"
    )
    parser.add_argument(
        "--specs-dir", 
        default=DEFAULT_SPECS_DIR, 
        help=f"Root directory for markdown specs (default: {DEFAULT_SPECS_DIR})"
    )
    parser.add_argument(
        "--output", 
        default=DEFAULT_OUTPUT_PATH, 
        help=f"Path to output the validation report JSON (default: {DEFAULT_OUTPUT_PATH})"
    )

    args = parser.parse_args()

    try:
        print(f"Loading manifest from: {args.manifest}")
        verified_set = load_manifest(args.manifest)
        print(f"Loaded {len(verified_set)} verified URLs.")

        print(f"Scanning specs directory: {args.specs_dir}")
        extracted = extract_urls_from_markdown(args.specs_dir)
        
        if not extracted:
            print("No citations found in markdown files.")
            report = {
                "total_unique_citations": 0,
                "verified_count": 0,
                "unverified_count": 0,
                "verification_rate": 0.0,
                "status": "PASS",
                "details": {
                    "missing_citations": {},
                    "verified_citations": {}
                }
            }
        else:
            print(f"Found citations in {len(extracted)} files.")
            report = verify_citations(extracted, verified_set)

        # Ensure output directory exists
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)

        print(f"Validation report written to: {args.output}")
        print(f"Status: {report['status']}")
        print(f"Verified: {report['verified_count']}, Unverified: {report['unverified_count']}")

        if report['status'] == 'FAIL':
            sys.exit(1)

    except FileNotFoundError as e:
        print(f"Critical Error: {e}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Manifest JSON Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
