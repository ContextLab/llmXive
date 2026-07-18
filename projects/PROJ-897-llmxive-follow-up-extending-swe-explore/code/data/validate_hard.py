"""
Validation logic for hard instances and synthetic issues.
Generates validation_report.md (T015).

Reads VALIDATION_SAMPLE_SIZE from config.py.
Outputs a Markdown table with columns: [IssueID, CoverageScore, MutationType, ValidityStatus, Notes].
"""
import json
import sys
import ast
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

from config import get_path, get_config_summary


def load_hard_subset() -> List[Dict[str, Any]]:
    """Load the hard subset from data/curated/hard_subset.jsonl."""
    path = get_path("curated", "hard_subset.jsonl")
    if not path.exists():
        raise FileNotFoundError(f"Hard subset not found at {path}. "
                                "Ensure T014a has been executed.")
    
    issues = []
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                issues.append(json.loads(line))
    return issues


def load_synthetic_issues() -> List[Dict[str, Any]]:
    """Load synthetic issues from data/curated/synthetic_issues.jsonl."""
    path = get_path("curated", "synthetic_issues.jsonl")
    if not path.exists():
        # If synthetic issues haven't been generated yet, return empty list
        # but log a warning in the report
        return []
    
    issues = []
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                issues.append(json.loads(line))
    return issues


def validate_issue(issue: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Validate a single issue.
    
    Checks:
    1. Required fields (issue_id, code)
    2. AST parse validity of code
    3. Presence of ground_truth_lines (optional but noted)
    
    Returns:
        Tuple of (is_valid, status_message).
    """
    # Check required fields
    if not issue.get("issue_id"):
        return False, "Missing issue_id"
    
    if not issue.get("code"):
        return False, "Missing code"
    
    # Check AST validity
    try:
        ast.parse(issue["code"])
        ast_valid = True
    except SyntaxError as e:
        ast_valid = False
        return False, f"AST Error: {e}"
    
    # Check ground truth lines (optional but noted)
    if not issue.get("ground_truth_lines"):
        # Not strictly invalid, but noted
        return True, "Valid (no ground truth defined)"
    
    return True, "Valid"


def generate_report(
    hard_issues: List[Dict[str, Any]],
    synthetic_issues: List[Dict[str, Any]],
    sample_size: int = 20
) -> str:
    """
    Generate a markdown validation report for manual inspection.
    
    Args:
        hard_issues: List of hard issues from T014a.
        synthetic_issues: List of synthetic issues from T014b.
        sample_size: Number of issues to sample for manual inspection (from config).
    
    Returns:
        Markdown string report with a table of sampled issues.
    """
    lines = []
    lines.append("# Validation Report: Hard & Synthetic Issues")
    lines.append("")
    lines.append(f"**Generated**: {get_config_summary().get('timestamp', 'N/A')}")
    lines.append(f"**Sample Size**: {sample_size}")
    lines.append("")
    
    # Summary
    lines.append("## Summary")
    lines.append(f"- Total Hard Issues: {len(hard_issues)}")
    lines.append(f"- Total Synthetic Issues: {len(synthetic_issues)}")
    lines.append(f"- Sampled for Inspection: {min(sample_size, len(hard_issues) + len(synthetic_issues))}")
    lines.append("")
    
    # Table header
    lines.append("## Validation Table")
    lines.append("")
    lines.append("| IssueID | CoverageScore | MutationType | ValidityStatus | Notes |")
    lines.append("|---------|---------------|--------------|----------------|-------|")
    
    # Sample hard issues
    sample_hard = hard_issues[:sample_size]
    for issue in sample_hard:
        issue_id = issue.get("issue_id", "unknown")
        coverage = issue.get("initial_coverage", 0.0)
        mutation = "None"  # Hard instances are not mutated
        is_valid, status = validate_issue(issue)
        validity = "Valid" if is_valid else "Invalid"
        notes = status
        
        lines.append(f"| {issue_id} | {coverage:.4f} | {mutation} | {validity} | {notes} |")
    
    # Sample synthetic issues
    sample_synth = synthetic_issues[:sample_size]
    for issue in sample_synth:
        issue_id = issue.get("issue_id", "unknown")
        # Synthetic issues might not have coverage score directly, use 0.0 or derived
        coverage = issue.get("initial_coverage", 0.0)
        mutation = issue.get("mutation_type", "unknown")
        is_valid, status = validate_issue(issue)
        validity = "Valid" if is_valid else "Invalid"
        notes = status
        
        lines.append(f"| {issue_id} | {coverage:.4f} | {mutation} | {validity} | {notes} |")
    
    lines.append("")
    
    # Footer instructions
    lines.append("---")
    lines.append("### Manual Inspection Guide")
    lines.append("1. Verify that `ValidityStatus` is 'Valid' for all sampled items.")
    lines.append("2. Check that `MutationType` correctly reflects the transformation applied (for synthetic issues).")
    lines.append("3. Ensure `CoverageScore` aligns with the selection criteria (bottom percentile).")
    lines.append("4. If any item is 'Invalid', review the `Notes` column for specific errors.")
    lines.append("")
    lines.append("*End of Report*")
    
    return "\n".join(lines)


def main():
    """Main entry point for validation report generation."""
    print("Generating Validation Report...")
    
    # Read configuration
    config = get_config_summary()
    sample_size = config.get("VALIDATION_SAMPLE_SIZE", 20)
    
    if not isinstance(sample_size, int) or sample_size <= 0:
        print(f"Warning: Invalid VALIDATION_SAMPLE_SIZE ({sample_size}), defaulting to 20.", file=sys.stderr)
        sample_size = 20
    
    try:
        # Load data
        print("Loading hard subset...")
        hard_issues = load_hard_subset()
        
        print("Loading synthetic issues...")
        synthetic_issues = load_synthetic_issues()
        
        # Generate report
        print(f"Generating report with sample size {sample_size}...")
        report = generate_report(hard_issues, synthetic_issues, sample_size)
        
        # Write output
        output_path = get_path("curated", "validation_report.md")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"Validation report successfully saved to {output_path}")
        return 0
        
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        print("Ensure T014a (curate.py) has been run to generate hard_subset.jsonl.", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Validation failed with unexpected error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())