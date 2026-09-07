#!/usr/bin/env python3
"""
Task T060: Verify Spec Completeness

This script scans 'spec.md' and 'plan.md' for:
1. Any '_TODO:' markers (indicating incomplete work).
2. The presence of a 'Research Hypothesis' section with falsifiable statements.
3. Quantifiable success criteria (e.g., "≥ 95% linkage").

Exit Codes:
0: All checks pass.
1: One or more checks failed (TODOs found, missing hypothesis, missing criteria).
"""
import os
import sys
import re
from pathlib import Path

# Constants
TODO_PATTERN = re.compile(r'_TODO:', re.IGNORECASE)
HYPOTHESIS_PATTERN = re.compile(r'Research\s+Hypothesis', re.IGNORECASE)
# Look for quantifiable criteria: numbers with units, percentages, or specific thresholds
CRITERIA_PATTERN = re.compile(r'(≥\s*\d+%|≥\s*\d+|≤\s*\d+%|≤\s*\d+|target.*\d+|threshold.*\d+)', re.IGNORECASE)

def get_project_root() -> Path:
    """Determine the project root relative to this script."""
    # Script is at scripts/validate_spec_completeness.py
    # Project root is two levels up
    return Path(__file__).resolve().parent.parent

def check_file_for_todos(file_path: Path) -> list[str]:
    """Check a file for _TODO: markers."""
    if not file_path.exists():
        return [f"File not found: {file_path}"]
    
    issues = []
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    for i, line in enumerate(lines, 1):
        if TODO_PATTERN.search(line):
            issues.append(f"Line {i}: Found _TODO: marker -> '{line.strip()}'")
    
    return issues

def check_hypothesis_section(file_path: Path) -> list[str]:
    """Check for the presence of a Research Hypothesis section."""
    if not file_path.exists():
        return [f"File not found: {file_path}"]
    
    issues = []
    content = file_path.read_text(encoding='utf-8')
    
    if not HYPOTHESIS_PATTERN.search(content):
        issues.append(f"Missing 'Research Hypothesis' section in {file_path.name}")
    else:
        # Optional: Check if the section has content (falsifiable statements)
        # Simple heuristic: look for directional words or specific claims after the header
        hypothesis_match = HYPOTHESIS_PATTERN.search(content)
        if hypothesis_match:
            start_idx = hypothesis_match.end()
            # Grab next ~500 chars to see if there's actual text
            context = content[start_idx:start_idx+500]
            if len(context.strip()) < 50:
                issues.append(f"'Research Hypothesis' section in {file_path.name} appears empty or too short.")
    
    return issues

def check_success_criteria(file_path: Path) -> list[str]:
    """Check for quantifiable success criteria."""
    if not file_path.exists():
        return [f"File not found: {file_path}"]
    
    issues = []
    content = file_path.read_text(encoding='utf-8')
    
    # We expect criteria in spec.md or plan.md. 
    # If the pattern is found, we assume it's valid.
    if not CRITERIA_PATTERN.search(content):
        issues.append(f"No quantifiable success criteria (e.g., percentages, thresholds) found in {file_path.name}")
    
    return issues

def main():
    project_root = get_project_root()
    spec_path = project_root / "specs" / "001-climate-smart-eval" / "spec.md"
    plan_path = project_root / "specs" / "001-climate-smart-eval" / "plan.md"
    
    # Fallback if specs are in root (legacy structure)
    if not spec_path.exists():
        spec_path = project_root / "spec.md"
    if not plan_path.exists():
        plan_path = project_root / "plan.md"

    all_issues = []

    print(f"Checking spec completeness in: {project_root}")
    print(f"Scanning: {spec_path.name}, {plan_path.name}")
    print("-" * 40)

    # 1. Check for TODOs
    print("1. Checking for _TODO: markers...")
    for p in [spec_path, plan_path]:
        if p.exists():
            issues = check_file_for_todos(p)
            if issues:
                all_issues.extend(issues)
        else:
            print(f"   Warning: {p} not found, skipping TODO check.")

    # 2. Check for Hypothesis
    print("2. Checking for 'Research Hypothesis' section...")
    for p in [spec_path, plan_path]:
        if p.exists():
            issues = check_hypothesis_section(p)
            if issues:
                all_issues.extend(issues)

    # 3. Check for Success Criteria
    print("3. Checking for quantifiable success criteria...")
    for p in [spec_path, plan_path]:
        if p.exists():
            issues = check_success_criteria(p)
            if issues:
                all_issues.extend(issues)

    # Report
    print("-" * 40)
    if all_issues:
        print("❌ SPEC COMPLETENESS FAILED")
        for issue in all_issues:
            print(f"   - {issue}")
        sys.exit(1)
    else:
        print("✅ SPEC COMPLETENESS PASSED")
        print("   - No _TODO: markers found.")
        print("   - Research Hypothesis section present.")
        print("   - Quantifiable success criteria found.")
        sys.exit(0)

if __name__ == "__main__":
    main()