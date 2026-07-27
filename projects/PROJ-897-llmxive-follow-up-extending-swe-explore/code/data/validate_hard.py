"""
Validate the hard subset and generate a validation report.
Implements automated validation gate with manual review.
"""
import json
import sys
import ast
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import get_path, get_config_summary, VALIDATION_SAMPLE_SIZE, COVERAGE_COLUMN_NAME, DATA_CURATED, HARD_INSTANCE_PERCENTILE

def load_hard_subset(input_file: Path) -> List[Dict[str, Any]]:
    """Load the hard subset from JSONL."""
    records = []
    with open(input_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return records

def load_synthetic_issues(input_file: Path) -> List[Dict[str, Any]]:
    """Load synthetic issues from JSONL."""
    records = []
    with open(input_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return records

def validate_issue(record: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Validate a single issue record.
    
    Returns:
        Tuple of (is_valid, notes)
    """
    # Check required fields
    required_fields = ['instance_id', 'source_code', COVERAGE_COLUMN_NAME]
    missing = [f for f in required_fields if f not in record]
    if missing:
        return False, f"Missing fields: {missing}"
    
    # Check coverage score is valid
    coverage = record.get(COVERAGE_COLUMN_NAME)
    if coverage is None or not isinstance(coverage, (int, float)):
        return False, f"Invalid coverage score: {coverage}"
    
    # Check code is valid Python
    code = record.get('source_code', '')
    try:
        ast.parse(code)
    except SyntaxError as e:
        return False, f"Syntax error in code: {e}"
    
    # Check if it's actually "hard" (low coverage)
    # Note: This is a sanity check, not a strict validation
    if coverage > 0.5:
        return False, f"Coverage score {coverage} seems high for a 'hard' instance"
    
    return True, "OK"

def generate_report(
    hard_subset: List[Dict[str, Any]],
    sample_size: Optional[int] = None
) -> Tuple[str, Dict[str, Any]]:
    """
    Generate a validation report for the hard subset.
    
    Args:
        hard_subset: List of hard subset records.
        sample_size: Number of records to sample for manual review. Defaults to config.VALIDATION_SAMPLE_SIZE.
        
    Returns:
        Tuple of (markdown_report, status_json)
    """
    if sample_size is None:
        sample_size = VALIDATION_SAMPLE_SIZE
    
    import random
    random.seed(42)  # For reproducibility
    
    # Sample records
    sample = random.sample(hard_subset, min(sample_size, len(hard_subset)))
    
    # Validate each
    valid_count = 0
    invalid_count = 0
    sample_results = []
    
    for record in sample:
        is_valid, notes = validate_issue(record)
        if is_valid:
            valid_count += 1
        else:
            invalid_count += 1
        
        sample_results.append({
            "instance_id": record.get('instance_id'),
            "coverage_score": record.get(COVERAGE_COLUMN_NAME),
            "complexity_score": record.get('metadata', {}).get('complexity_score', 'N/A'),
            "notes": notes
        })
    
    # Generate Markdown report
    md_lines = [
        "# Validation Report: Hard Subset",
        "",
        "## Summary",
        f"- Total records in hard subset: {len(hard_subset)}",
        f"- Sample size for validation: {len(sample)}",
        f"- Valid records: {valid_count}",
        f"- Invalid records: {invalid_count}",
        "",
        "## Plan Override Justification",
        "",
        "This validation report documents the decision to use **initial_coverage** scores",
        "for hard instance selection, as per **Spec FR-001**, overriding the Plan's previous",
        "mandate for Cyclomatic Complexity. This ensures alignment with the benchmark's",
        "definition of 'hard' (low retrieval success).",
        "",
        "## Sample Validation Results",
        "",
        "| IssueID | CoverageScore | ComplexityScore | Notes |",
        "|---------|---------------|-----------------|-------|"
    ]
    
    for result in sample_results:
        md_lines.append(
            f"| {result['instance_id']} | {result['coverage_score']} | "
            f"{result['complexity_score']} | {result['notes']} |"
        )
    
    md_lines.extend([
        "",
        "## Conclusion",
        "",
        f"The hard subset validation {'PASSED' if invalid_count == 0 else 'HAS WARNINGS'}.",
        f"Manual review of the sampled records is recommended before proceeding to Phase 4."
    ])
    
    markdown_report = "\n".join(md_lines)
    
    # Generate status JSON
    status = {
        "status": "PASSED" if invalid_count == 0 else "WARNING",
        "message": f"Validated {len(sample)} records. {valid_count} valid, {invalid_count} invalid.",
        "sample_size": len(sample),
        "valid_count": valid_count,
        "invalid_count": invalid_count,
        "total_records": len(hard_subset)
    }
    
    return markdown_report, status

def main():
    """Entry point for the validation script."""
    print("Starting hard subset validation...")
    
    input_file = DATA_CURATED / "hard_subset.jsonl"
    if not input_file.exists():
        print(f"ERROR: Hard subset not found at {input_file}.")
        print("Ensure T012 (filter_hard.py) has been executed.")
        sys.exit(1)
    
    try:
        hard_subset = load_hard_subset(input_file)
        print(f"Loaded {len(hard_subset)} hard subset records.")
        
        report, status = generate_report(hard_subset)
        
        # Write report
        report_file = DATA_CURATED / "validation_report.md"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"Validation report saved to: {report_file}")
        
        # Write status
        status_file = DATA_CURATED / "validation_status.json"
        with open(status_file, 'w', encoding='utf-8') as f:
            json.dump(status, f, indent=2)
        print(f"Validation status saved to: {status_file}")
        
        print(f"Validation complete. Status: {status['status']}")
        
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
