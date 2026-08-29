import argparse
import json
import os
import sys
from typing import List, Dict, Any, Optional

# Import crossrefapi for DOI resolution
try:
    from crossrefapi.rest import CrossrefRestAPI
except ImportError:
    print("Error: crossrefapi is not installed. Please run: pip install crossrefapi")
    sys.exit(1)

# Import project utilities
from utils import load_json, save_json, ensure_directory

# Constants
MIN_TITLE_OVERLAP = 0.7
VERIFICATION_REPORT_PATH = "state/verification_report.json"
SOURCES_FILE_DEFAULT = "sources_list.md"

def parse_sources_file(file_path: str) -> List[Dict[str, str]]:
    """
    Parses the sources_list.md file to extract citations.
    Expects a markdown file with a YAML-like or simple list structure.
    Format assumed:
    - doi: 10.xxxx/xxxx
      title: "Title of the paper"
    """
    citations = []
    current_doi = None
    current_title = None

    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue

            if line.startswith('- doi:'):
                # Save previous if exists
                if current_doi and current_title:
                    citations.append({"doi": current_doi, "title": current_title})
                current_doi = line.split(':', 1)[1].strip()
                current_title = None
            elif line.startswith('title:'):
                current_title = line.split(':', 1)[1].strip().strip('"').strip("'")
            elif line.startswith('  doi:') or line.startswith('    doi:'):
                # Handle indented DOI if format varies
                if current_doi and current_title:
                    citations.append({"doi": current_doi, "title": current_title})
                current_doi = line.split(':', 1)[1].strip()
                current_title = None
            elif line.startswith('  title:') or line.startswith('    title:'):
                current_title = line.split(':', 1)[1].strip().strip('"').strip("'")

    # Append the last one
    if current_doi and current_title:
        citations.append({"doi": current_doi, "title": current_title})
    
    return citations

def validate_doi(doi: str, expected_title: str) -> Dict[str, Any]:
    """
    Validates a DOI using Crossref API.
    Returns a dict with 'valid', 'title', 'metadata_title', 'overlap_score'.
    """
    api = CrossrefRestAPI()
    try:
        # Fetch metadata for the DOI
        metadata = api.works(ids=doi)
        
        if not metadata or 'message' not in metadata:
            return {
                "valid": False,
                "reason": "DOI not found or invalid metadata response",
                "doi": doi
            }

        message = metadata.get('message', {})
        title_list = message.get('title', [])
        metadata_title = title_list[0] if title_list else "Unknown Title"
        
        # Calculate Title Overlap (Jaccard-like or simple word overlap)
        # Simple implementation: Jaccard index on words
        def jaccard_similarity(s1, s2):
            set1 = set(s1.lower().split())
            set2 = set(s2.lower().split())
            intersection = set1.intersection(set2)
            union = set1.union(set2)
            if not union:
                return 0.0
            return len(intersection) / len(union)

        overlap_score = jaccard_similarity(expected_title, metadata_title)

        is_valid = overlap_score >= MIN_TITLE_OVERLAP

        return {
            "valid": is_valid,
            "doi": doi,
            "expected_title": expected_title,
            "metadata_title": metadata_title,
            "overlap_score": overlap_score,
            "reason": "Valid" if is_valid else f"Title overlap {overlap_score:.2f} < {MIN_TITLE_OVERLAP}"
        }

    except Exception as e:
        return {
            "valid": False,
            "doi": doi,
            "reason": f"API Error: {str(e)}"
        }

def main():
    parser = argparse.ArgumentParser(description="Verify citations from sources_list.md against Crossref")
    parser.add_argument("--sources-file", type=str, default=SOURCES_FILE_DEFAULT,
                        help="Path to the sources list file (default: sources_list.md)")
    args = parser.parse_args()

    if not os.path.exists(args.sources_file):
        print(f"Error: Sources file not found: {args.sources_file}")
        sys.exit(1)

    print(f"Loading citations from {args.sources_file}...")
    citations = parse_sources_file(args.sources_file)

    if not citations:
        print("Error: No citations found in the sources file.")
        sys.exit(1)

    print(f"Found {len(citations)} citations. Validating...")
    
    results = []
    all_valid = True

    for i, citation in enumerate(citations):
        doi = citation.get('doi')
        title = citation.get('title')
        
        if not doi or not title:
            print(f"Warning: Skipping citation {i+1} due to missing DOI or title.")
            continue

        print(f"Validating {i+1}/{len(citations)}: {doi}...")
        validation_result = validate_doi(doi, title)
        results.append(validation_result)

        if not validation_result['valid']:
            all_valid = False
            print(f"  -> FAILED: {validation_result['reason']}")
        else:
            print(f"  -> OK: Overlap {validation_result['overlap_score']:.2f}")

    # Prepare report
    report = {
        "status": "verification_complete",
        "total_citations": len(citations),
        "valid_citations": sum(1 for r in results if r['valid']),
        "all_valid": all_valid,
        "meta_analysis": []
    }

    if all_valid:
        # Construct the meta_analysis section as required by T000d
        for r in results:
            report["meta_analysis"].append({
                "source_id": r['doi'],
                "title": r['metadata_title'],
                "verified": True
            })
    else:
        report["meta_analysis"] = results # Include full details on failure

    # Ensure state directory exists
    ensure_directory(os.path.dirname(VERIFICATION_REPORT_PATH))

    # Write report
    save_json(report, VERIFICATION_REPORT_PATH)
    
    print(f"\nVerification report written to {VERIFICATION_REPORT_PATH}")

    if not all_valid:
        print("\nERROR: One or more citations failed validation. Halting.")
        sys.exit(1)
    
    print("\nAll citations validated successfully.")
    sys.exit(0)

if __name__ == "__main__":
    main()
