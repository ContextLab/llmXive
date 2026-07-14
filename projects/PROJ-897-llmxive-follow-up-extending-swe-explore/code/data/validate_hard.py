"""
T015: Validate Hard Subset and Generate Inspection Report

Reads the curated hard subset and synthetic issues, samples a subset based on
VALIDATION_SAMPLE_SIZE from config, and generates a markdown report for manual
inspection.
"""
import json
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

# Import from project modules
from config import get_config_summary
from data.curate import load_derived_ground_truth, filter_hard_instances, generate_synthetic_issues
from utils.schemas import load_schema


def load_hard_subset() -> List[Dict[str, Any]]:
    """Load the curated hard subset from data/curated/hard_subset.jsonl"""
    config = get_config_summary()
    path = Path(config["data_curated"]) / "hard_subset.jsonl"
    if not path.exists():
        raise FileNotFoundError(f"Hard subset not found at {path}. Run T014a first.")
    
    issues = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                issues.append(json.loads(line))
    return issues


def load_synthetic_issues() -> List[Dict[str, Any]]:
    """Load synthetic issues from data/curated/synthetic_issues.jsonl"""
    config = get_config_summary()
    path = Path(config["data_curated"]) / "synthetic_issues.jsonl"
    if not path.exists():
        # Synthetic issues are optional if pool was small, but we try to load
        return []
    
    issues = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                issues.append(json.loads(line))
    return issues


def validate_issue(issue: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate a single issue for the report.
    Checks schema compliance and basic structural validity.
    """
    result = {
        "issue_id": issue.get("instance_id", "UNKNOWN"),
        "coverage_score": issue.get("initial_coverage", "N/A"),
        "mutation_type": issue.get("mutation_type", "Original"),
        "validity_status": "VALID",
        "notes": ""
    }

    # Check required fields
    required_fields = ["instance_id", "problem_statement", "repo", "commit"]
    missing = [f for f in required_fields if f not in issue]
    if missing:
        result["validity_status"] = "INVALID"
        result["notes"] = f"Missing fields: {', '.join(missing)}"
        return result

    # Check code validity if present (for synthetic issues)
    if "code" in issue:
        code = issue["code"]
        if not isinstance(code, str):
            result["validity_status"] = "INVALID"
            result["notes"] = "Code field is not a string"
            return result
        
        # Try to parse as Python to ensure syntactic validity
        try:
            import ast
            ast.parse(code)
        except SyntaxError as e:
            result["validity_status"] = "INVALID"
            result["notes"] = f"Syntax error: {str(e)}"
            return result

    # Check ground truth lines presence for synthetic issues
    if issue.get("mutation_type") == "synthetic" and "ground_truth_lines" not in issue:
        result["validity_status"] = "WARNING"
        result["notes"] = "Synthetic issue missing ground_truth_lines metadata"

    return result


def generate_report(sampled_issues: List[Dict[str, Any]], output_path: Path) -> None:
    """Generate the markdown validation report."""
    lines = [
        "# Hard Subset Validation Report",
        "",
        "This report provides a manual inspection guide for the curated hard subset.",
        f"Sample size: {len(sampled_issues)} issues.",
        "",
        "## Validation Results",
        "",
        "| Issue ID | Coverage Score | Mutation Type | Validity Status | Notes |",
        "|----------|----------------|---------------|-----------------|-------|"
    ]

    for issue in sampled_issues:
        validation = validate_issue(issue)
        lines.append(
            f"| {validation['issue_id']} | {validation['coverage_score']} | "
            f"{validation['mutation_type']} | {validation['validity_status']} | "
            f"{validation['notes']} |"
        )

    lines.extend([
        "",
        "## Instructions for Manual Inspection",
        "",
        "1. **Coverage Score**: Verify that issues marked as 'hard' have low initial coverage scores.",
        "2. **Mutation Type**: For synthetic issues, verify that mutations (variable rename, comment removal, "
        "control flow reordering) preserve the original logic and ground truth.",
        "3. **Validity Status**: Ensure all issues are syntactically valid and contain required metadata.",
        "4. **Ground Truth**: For synthetic issues, confirm that `ground_truth_lines` correctly identify "
        "the solution lines in the original code.",
        "",
        "## Summary",
        "",
        f"Total sampled: {len(sampled_issues)}",
        f"Valid: {sum(1 for i in sampled_issues if validate_issue(i)['validity_status'] == 'VALID')}",
        f"Warnings: {sum(1 for i in sampled_issues if validate_issue(i)['validity_status'] == 'WARNING')}",
        f"Invalid: {sum(1 for i in sampled_issues if validate_issue(i)['validity_status'] == 'INVALID')}",
    ])

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def main() -> int:
    """Main entry point for T015."""
    config = get_config_summary()
    
    # Read configuration
    sample_size = config.get("VALIDATION_SAMPLE_SIZE", 20)
    
    # Load datasets
    print("Loading hard subset...")
    hard_issues = load_hard_subset()
    
    print("Loading synthetic issues...")
    synthetic_issues = load_synthetic_issues()
    
    # Combine all issues for sampling
    all_issues = hard_issues + synthetic_issues
    
    if not all_issues:
        print("ERROR: No issues found to validate. Run T014a and T014b first.")
        return 1
    
    # Sample subset (deterministic for reproducibility)
    import random
    random.seed(config.get("random_seed", 42))
    sampled = random.sample(all_issues, min(sample_size, len(all_issues)))
    
    # Generate report
    output_path = Path(config["data_curated"]) / "validation_report.md"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"Generating validation report for {len(sampled)} issues...")
    generate_report(sampled, output_path)
    
    print(f"Report saved to {output_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())