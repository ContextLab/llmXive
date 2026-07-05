"""
Integration test for T036: FR-002 Verification.
Verifies that extracted fields exist for > 95% of valid pages.

This test loads the extracted summaries from data/processed/extracted_summaries.json
(produced by T020) and calculates the field presence rate.

A page is considered "valid" if it was successfully parsed (no extraction errors).
Required fields per ABTestSummary model:
  - url
  - domain
  - outcome_type
  - sample_size_control
  - sample_size_treatment
  - metric_control (or baseline_conversion_rate)
  - metric_treatment (or treatment_conversion_rate)
  - p_value
"""
import json
import sys
from pathlib import Path
from typing import List, Dict, Any

# Add project root to path for imports if running as script
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

REQUIRED_FIELDS = [
    "url",
    "domain",
    "outcome_type",
    "sample_size_control",
    "sample_size_treatment",
    "metric_control",
    "metric_treatment",
    "p_value"
]

def load_extracted_summaries(path: Path) -> List[Dict[str, Any]]:
    """Load extracted summaries from JSON file."""
    if not path.exists():
        raise FileNotFoundError(f"Extracted summaries file not found: {path}")
    
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Handle both list and dict with 'summaries' key
    if isinstance(data, dict) and 'summaries' in data:
        return data['summaries']
    elif isinstance(data, list):
        return data
    else:
        raise ValueError(f"Unexpected data format in {path}")

def calculate_field_coverage(summaries: List[Dict[str, Any]]) -> tuple:
    """
    Calculate the percentage of valid pages where all required fields are present.
    
    Returns:
        tuple: (coverage_percentage, total_valid_pages, pages_with_all_fields)
    """
    if not summaries:
        return 0.0, 0, 0
    
    total_valid = 0
    complete_records = 0
    
    for summary in summaries:
        # A valid page is one that has at least a URL and domain (basic structure)
        if not summary.get("url") or not summary.get("domain"):
            continue
        
        total_valid += 1
        
        # Check if all required fields are present and not None
        all_fields_present = True
        for field in REQUIRED_FIELDS:
            value = summary.get(field)
            if value is None or (isinstance(value, str) and value.strip() == ""):
                all_fields_present = False
                break
        
        if all_fields_present:
            complete_records += 1
    
    if total_valid == 0:
        return 0.0, 0, 0
    
    coverage = (complete_records / total_valid) * 100
    return coverage, total_valid, complete_records

def main():
    """Main test entry point."""
    # Path to extracted summaries (produced by T020)
    extracted_path = project_root / "data" / "processed" / "extracted_summaries.json"
    
    print("T036: FR-002 Verification - Extracted Fields Coverage")
    print("=" * 60)
    
    try:
        summaries = load_extracted_summaries(extracted_path)
        print(f"Loaded {len(summaries)} summaries from {extracted_path}")
        
        coverage, total_valid, complete_records = calculate_field_coverage(summaries)
        
        print(f"Total valid pages: {total_valid}")
        print(f"Pages with all required fields: {complete_records}")
        print(f"Field coverage: {coverage:.2f}%")
        
        # Threshold from FR-002: > 95%
        threshold = 95.0
        
        if coverage > threshold:
            print(f"✓ PASS: Coverage ({coverage:.2f}%) exceeds threshold ({threshold}%)")
            return 0
        else:
            print(f"✗ FAIL: Coverage ({coverage:.2f}%) does not exceed threshold ({threshold}%)")
            print(f"  Required: > {threshold}%")
            print(f"  Actual: {coverage:.2f}%")
            print(f"  Gap: {threshold - coverage:.2f} percentage points")
            return 1
            
    except FileNotFoundError as e:
        print(f"✗ FAIL: {e}")
        print("  Ensure T020 (extractor) has been run successfully.")
        return 1
    except Exception as e:
        print(f"✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
