"""
Verification script for FR-011: Limitation disclosures in all reports and visualizations.

This script verifies that all generated reports (JSON) and visualizations (notebooks/plots)
contain the mandatory limitation headers and footers as required by FR-011.

Usage:
    python code/verification/verify_limitations.py
"""

import os
import sys
import json
import nbformat
import re
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from viz.templates import get_limitation_header, get_limitation_footer, validate_limitation_injection


def check_json_file(filepath: Path) -> Tuple[bool, List[str]]:
    """
    Check if a JSON file contains limitation disclosures.
    
    For JSON reports, we check for:
    1. A 'limitations' or 'disclaimer' key at the root level
    2. Or a 'metadata.limitations' structure
    
    Returns:
        Tuple of (is_valid, list of issues)
    """
    issues = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Check for limitation fields
        has_limitations = False
        
        # Check root level
        if 'limitations' in data or 'disclaimer' in data:
            has_limitations = True
        
        # Check metadata
        if 'metadata' in data and isinstance(data['metadata'], dict):
            if 'limitations' in data['metadata']:
                has_limitations = True
        
        # Check for specific expected keys based on file type
        if 'trend_results.json' in str(filepath):
            if not has_limitations:
                issues.append("Missing 'limitations' or 'metadata.limitations' field")
            else:
                # Validate content is not empty
                lim_content = data.get('limitations') or data.get('metadata', {}).get('limitations')
                if not lim_content or (isinstance(lim_content, str) and len(lim_content.strip()) == 0):
                    issues.append("Limitations field is empty or null")
        
        elif 'decomposition_results.json' in str(filepath):
            if not has_limitations:
                issues.append("Missing 'limitations' or 'metadata.limitations' field")
            else:
                lim_content = data.get('limitations') or data.get('metadata', {}).get('limitations')
                if not lim_content or (isinstance(lim_content, str) and len(lim_content.strip()) == 0):
                    issues.append("Limitations field is empty or null")
        
        elif 'cluster_results.json' in str(filepath):
            if not has_limitations:
                issues.append("Missing 'limitations' or 'metadata.limitations' field")
            else:
                lim_content = data.get('limitations') or data.get('metadata', {}).get('limitations')
                if not lim_content or (isinstance(lim_content, str) and len(lim_content.strip()) == 0):
                    issues.append("Limitations field is empty or null")
        
        return len(issues) == 0, issues
        
    except json.JSONDecodeError as e:
        return False, [f"Invalid JSON: {str(e)}"]
    except Exception as e:
        return False, [f"Error reading file: {str(e)}"]


def check_notebook(filepath: Path) -> Tuple[bool, List[str]]:
    """
    Check if a Jupyter notebook contains limitation headers and footers.
    
    We verify that:
    1. The first cell contains the limitation header
    2. The last cell contains the limitation footer
    
    Returns:
        Tuple of (is_valid, list of issues)
    """
    issues = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            nb = nbformat.read(f, as_version=4)
        
        if len(nb.cells) == 0:
            return False, ["Notebook has no cells"]
        
        # Check header in first cell
        first_cell = nb.cells[0]
        first_content = first_cell.source.lower() if first_cell.source else ""
        
        expected_header = get_limitation_header().lower()
        if expected_header not in first_content:
            issues.append("Missing limitation header in first cell")
        
        # Check footer in last cell
        last_cell = nb.cells[-1]
        last_content = last_cell.source.lower() if last_cell.source else ""
        
        expected_footer = get_limitation_footer().lower()
        if expected_footer not in last_content:
            issues.append("Missing limitation footer in last cell")
        
        # Additional check: validate using the template validator
        is_valid, validation_issues = validate_limitation_injection(str(filepath))
        if not is_valid:
            issues.extend(validation_issues)
        
        return len(issues) == 0, issues
        
    except Exception as e:
        return False, [f"Error reading notebook: {str(e)}"]


def check_python_script(filepath: Path) -> Tuple[bool, List[str]]:
    """
    Check if a Python script that generates visualizations includes limitation injection.
    
    We verify that:
    1. The script imports from viz.templates
    2. The script calls limitation injection functions
    
    Returns:
        Tuple of (is_valid, list of issues)
    """
    issues = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for required imports
        has_templates_import = 'from viz.templates import' in content or 'from viz import templates' in content
        
        # Check for limitation injection calls
        has_injection_call = (
            'get_limitation_header' in content or
            'get_limitation_footer' in content or
            'inject_limitation_to_notebook' in content or
            'create_plot_with_limitation' in content or
            'validate_limitation_injection' in content
        )
        
        if not has_templates_import:
            issues.append("Missing import from viz.templates")
        
        if not has_injection_call:
            issues.append("Missing call to limitation injection function")
        
        return len(issues) == 0, issues
        
    except Exception as e:
        return False, [f"Error reading script: {str(e)}"]


def verify_all_artifacts() -> Dict[str, Any]:
    """
    Verify all generated artifacts for limitation disclosures.
    
    Returns:
        Dictionary with verification results
    """
    results = {
        "total_files": 0,
        "passed": 0,
        "failed": 0,
        "details": []
    }
    
    data_dir = PROJECT_ROOT / "data" / "processed"
    notebooks_dir = PROJECT_ROOT / "notebooks"
    code_dir = PROJECT_ROOT / "code"
    
    # Check JSON reports
    if data_dir.exists():
        for json_file in data_dir.glob("*.json"):
            results["total_files"] += 1
            is_valid, issues = check_json_file(json_file)
            
            if is_valid:
                results["passed"] += 1
                results["details"].append({
                    "file": str(json_file.relative_to(PROJECT_ROOT)),
                    "status": "PASS",
                    "issues": []
                })
            else:
                results["failed"] += 1
                results["details"].append({
                    "file": str(json_file.relative_to(PROJECT_ROOT)),
                    "status": "FAIL",
                    "issues": issues
                })
    
    # Check notebooks
    if notebooks_dir.exists():
        for nb_file in notebooks_dir.glob("*.ipynb"):
            results["total_files"] += 1
            is_valid, issues = check_notebook(nb_file)
            
            if is_valid:
                results["passed"] += 1
                results["details"].append({
                    "file": str(nb_file.relative_to(PROJECT_ROOT)),
                    "status": "PASS",
                    "issues": []
                })
            else:
                results["failed"] += 1
                results["details"].append({
                    "file": str(nb_file.relative_to(PROJECT_ROOT)),
                    "status": "FAIL",
                    "issues": issues
                })
    
    # Check visualization scripts
    if code_dir.exists():
        for py_file in code_dir.rglob("viz*.py"):
            if "plots.py" in str(py_file) or "templates.py" in str(py_file):
                results["total_files"] += 1
                is_valid, issues = check_python_script(py_file)
                
                if is_valid:
                    results["passed"] += 1
                    results["details"].append({
                        "file": str(py_file.relative_to(PROJECT_ROOT)),
                        "status": "PASS",
                        "issues": []
                    })
                else:
                    results["failed"] += 1
                    results["details"].append({
                        "file": str(py_file.relative_to(PROJECT_ROOT)),
                        "status": "FAIL",
                        "issues": issues
                    })
    
    return results


def main():
    """Main entry point for verification."""
    print("=" * 80)
    print("FR-011 Limitation Disclosure Verification")
    print("=" * 80)
    print()
    
    results = verify_all_artifacts()
    
    print(f"Total artifacts checked: {results['total_files']}")
    print(f"Passed: {results['passed']}")
    print(f"Failed: {results['failed']}")
    print()
    
    if results['failed'] > 0:
        print("Failed artifacts:")
        print("-" * 40)
        for detail in results['details']:
            if detail['status'] == 'FAIL':
                print(f"  - {detail['file']}")
                for issue in detail['issues']:
                    print(f"      * {issue}")
                print()
        
        print()
        print("VERIFICATION FAILED: Some artifacts are missing limitation disclosures.")
        print("Please ensure all reports and visualizations include the mandatory")
        print("limitation headers and footers as per FR-011.")
        return 1
    else:
        print("VERIFICATION PASSED: All artifacts contain required limitation disclosures.")
        return 0


if __name__ == "__main__":
    sys.exit(main())
