"""
Integration test for FR-002 Verification: Extracted fields exist for > 95% of valid pages.

This test verifies that the extraction logic successfully populates the required fields
for at least 95% of the valid pages processed in the pipeline.

It loads the extracted summaries from the standard output location and calculates
the ratio of records where all mandatory fields are present and non-null.
"""
import json
import sys
from pathlib import Path
from typing import List, Dict, Any

# Constants for FR-002
REQUIRED_FIELDS = [
    "url",
    "domain",
    "sample_size_control",
    "sample_size_treatment",
    "conversion_rate_control",
    "conversion_rate_treatment",
    "p_value",
    "effect_size",
    "outcome_type",
    "test_type"
]
THRESHOLD = 0.95

def load_extracted_summaries(path: Path) -> List[Dict[str, Any]]:
    """Load extracted summaries from JSON file."""
    if not path.exists():
        raise FileNotFoundError(f"Extracted summaries file not found: {path}")
    
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def count_valid_records(summaries: List[Dict[str, Any]]) -> int:
    """Count records where all required fields are present and non-null."""
    valid_count = 0
    for record in summaries:
        if not isinstance(record, dict):
            continue
        
        all_fields_present = True
        for field in REQUIRED_FIELDS:
            value = record.get(field)
            if value is None or value == "":
                all_fields_present = False
                break
        
        if all_fields_present:
            valid_count += 1
    
    return valid_count

def calculate_extraction_coverage(summaries: List[Dict[str, Any]]) -> float:
    """Calculate the percentage of records with all required fields."""
    if not summaries:
        return 0.0
    
    valid_count = count_valid_records(summaries)
    return valid_count / len(summaries)

def main() -> int:
    """
    Main entry point for the test.
    
    Returns:
        0 if FR-002 verification passes (coverage >= 95%),
        1 if verification fails.
    """
    # Determine the path to extracted summaries
    # Based on project structure, this should be in output/extracted_summaries.json
    # or data/processed/extracted_summaries.json depending on the pipeline stage
    project_root = Path(__file__).parent.parent.parent
    output_dir = project_root / "output"
    data_dir = project_root / "data" / "processed"
    
    # Check common locations
    summaries_path = None
    possible_paths = [
        output_dir / "extracted_summaries.json",
        output_dir / "summaries" / "extracted_summaries.json",
        data_dir / "extracted_summaries.json",
        data_dir / "summaries.json"
    ]
    
    for path in possible_paths:
        if path.exists():
            summaries_path = path
            break
    
    if not summaries_path:
        print("ERROR: Could not find extracted summaries file in expected locations.")
        print("Expected paths:")
        for path in possible_paths:
            print(f"  - {path}")
        return 1
    
    try:
        print(f"Loading extracted summaries from: {summaries_path}")
        summaries = load_extracted_summaries(summaries_path)
        
        if not summaries:
            print("ERROR: Extracted summaries file is empty.")
            return 1
        
        coverage = calculate_extraction_coverage(summaries)
        total_records = len(summaries)
        valid_records = count_valid_records(summaries)
        
        print(f"Total records: {total_records}")
        print(f"Valid records (all required fields present): {valid_records}")
        print(f"Extraction coverage: {coverage:.2%}")
        print(f"Required threshold (FR-002): {THRESHOLD:.2%}")
        
        if coverage >= THRESHOLD:
            print(f"SUCCESS: FR-002 verification passed. Coverage {coverage:.2%} >= {THRESHOLD:.2%}")
            return 0
        else:
            print(f"FAILURE: FR-002 verification failed. Coverage {coverage:.2%} < {THRESHOLD:.2%}")
            return 1
            
    except Exception as e:
        print(f"ERROR during verification: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())