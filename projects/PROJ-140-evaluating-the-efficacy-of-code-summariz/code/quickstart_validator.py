"""
Quickstart Validation Script for T043.

This script validates the project's quickstart.md file and ensures
all prerequisites for running the project are met.

Usage:
    python code/quickstart_validator.py
"""
import os
import sys
import argparse
from pathlib import Path
import subprocess
import json

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from utils.logging_utils import get_logger

def validate_quickstart_file(quickstart_path: Path) -> dict:
    """Validate the quickstart.md file exists and has content."""
    logger = get_logger("quickstart_validator")
    results = {
        "file_exists": False,
        "has_content": False,
        "has_install_section": False,
        "has_execution_section": False,
        "issues": []
    }
    
    if not quickstart_path.exists():
        results["issues"].append("quickstart.md does not exist")
        return results
    
    results["file_exists"] = True
    
    try:
        with open(quickstart_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if not content.strip():
            results["issues"].append("quickstart.md is empty")
            return results
        
        results["has_content"] = True
        
        content_lower = content.lower()
        if "install" not in content_lower and "dependenc" not in content_lower:
            results["issues"].append("Missing installation/dependency instructions")
        else:
            results["has_install_section"] = True
        
        if "run" not in content_lower and "execute" not in content_lower and "python" not in content_lower:
            results["issues"].append("Missing execution instructions")
        else:
            results["has_execution_section"] = True
            
    except Exception as e:
        results["issues"].append(f"Error reading quickstart.md: {str(e)}")
    
    return results

def validate_project_structure(project_root: Path) -> dict:
    """Validate the project directory structure."""
    logger = get_logger("quickstart_validator")
    results = {
        "directories_exist": True,
        "files_exist": True,
        "issues": []
    }
    
    required_dirs = [
        "code",
        "code/data_prep",
        "code/analysis",
        "code/utils",
        "code/tests",
        "data",
        "data/defects4j",
        "data/summaries",
        "data/interaction_logs",
        "data/analysis_results",
        "data/consent",
        "tests"
    ]
    
    for dir_path in required_dirs:
        full_path = project_root / dir_path
        if not full_path.exists() or not full_path.is_dir():
            results["directories_exist"] = False
            results["issues"].append(f"Missing directory: {dir_path}")
    
    required_files = [
        "requirements.txt",
        ".gitignore",
        "quickstart.md",
        "code/data_prep/download_defects4j.py",
        "code/data_prep/generate_summaries.py",
        "code/analysis/run_statistics.py",
        "code/utils/interaction_logger.py",
        "code/utils/anonymize_logs.py",
        "contracts/api_participant.md",
        ".github/workflows/test_reproducibility.yml"
    ]
    
    for file_path in required_files:
        full_path = project_root / file_path
        if not full_path.exists() or not full_path.is_file():
            results["files_exist"] = False
            results["issues"].append(f"Missing file: {file_path}")
    
    return results

def validate_python_syntax(project_root: Path) -> dict:
    """Validate Python syntax of core modules."""
    logger = get_logger("quickstart_validator")
    results = {
        "all_valid": True,
        "issues": []
    }
    
    core_modules = [
        "code/data_prep/download_defects4j.py",
        "code/data_prep/generate_summaries.py",
        "code/analysis/run_statistics.py",
        "code/utils/interaction_logger.py",
        "code/utils/anonymize_logs.py",
        "code/utils/latency_calibrator.py",
        "code/utils/assignment_generator.py"
    ]
    
    for module_path in core_modules:
        full_path = project_root / module_path
        if full_path.exists():
            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    compile(f.read(), str(full_path), 'exec')
            except SyntaxError as e:
                results["all_valid"] = False
                results["issues"].append(f"Syntax error in {module_path}: {str(e)}")
    
    return results

def validate_dependencies(project_root: Path) -> dict:
    """Validate dependencies are specified."""
    logger = get_logger("quickstart_validator")
    results = {
        "requirements_exists": False,
        "has_dependencies": False,
        "issues": []
    }
    
    req_path = project_root / "requirements.txt"
    if not req_path.exists():
        results["issues"].append("requirements.txt not found")
        return results
    
    results["requirements_exists"] = True
    
    try:
        with open(req_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if not content.strip():
            results["issues"].append("requirements.txt is empty")
            return results
        
        results["has_dependencies"] = True
    except Exception as e:
        results["issues"].append(f"Error reading requirements.txt: {str(e)}")
    
    return results

def validate_data_files(project_root: Path) -> dict:
    """Validate expected data files exist."""
    logger = get_logger("quickstart_validator")
    results = {
        "data_files_exist": True,
        "issues": []
    }
    
    # Expected output files from completed tasks
    expected_files = [
        "data/summaries/llm_sim_summaries.csv",
        "data/summaries/rule_summaries.csv",
        "data/interaction_logs/raw_logs.csv",
        "data/interaction_logs/anonymized_logs.csv",
        "data/analysis_results/results.csv",
        "data/analysis_results/sensitivity_analysis.csv",
        "data/analysis_results/outlier_flags.json",
        "data/reproducibility_package_v1.0.tar.gz"
    ]
    
    for file_path in expected_files:
        full_path = project_root / file_path
        if not full_path.exists():
            results["data_files_exist"] = False
            results["issues"].append(f"Missing expected data file: {file_path}")
    
    return results

def run_quickstart_validation(project_root: Path = None) -> dict:
    """Run all validation checks and return results."""
    if project_root is None:
        project_root = PROJECT_ROOT
    
    logger = get_logger("quickstart_validator")
    logger.info("Starting quickstart validation...")
    
    overall_results = {
        "validation_timestamp": str(Path(project_root).stat().st_mtime),
        "project_root": str(project_root),
        "quickstart": {},
        "structure": {},
        "syntax": {},
        "dependencies": {},
        "data_files": {},
        "overall_status": "PASS",
        "issues": []
    }
    
    # Run validations
    overall_results["quickstart"] = validate_quickstart_file(project_root / "quickstart.md")
    overall_results["structure"] = validate_project_structure(project_root)
    overall_results["syntax"] = validate_python_syntax(project_root)
    overall_results["dependencies"] = validate_dependencies(project_root)
    overall_results["data_files"] = validate_data_files(project_root)
    
    # Aggregate issues
    for key in ["quickstart", "structure", "syntax", "dependencies", "data_files"]:
        if "issues" in overall_results[key]:
            overall_results["issues"].extend(overall_results[key]["issues"])
    
    # Determine overall status
    critical_failures = [
        not overall_results["quickstart"]["file_exists"],
        not overall_results["structure"]["directories_exist"],
        not overall_results["structure"]["files_exist"],
        not overall_results["syntax"]["all_valid"],
        not overall_results["dependencies"]["requirements_exists"]
    ]
    
    if any(critical_failures):
        overall_results["overall_status"] = "FAIL"
    elif overall_results["issues"]:
        overall_results["overall_status"] = "WARN"
    else:
        overall_results["overall_status"] = "PASS"
    
    logger.info(f"Validation complete. Status: {overall_results['overall_status']}")
    
    return overall_results

def main():
    """Main entry point for quickstart validation."""
    parser = argparse.ArgumentParser(
        description="Validate project quickstart.md and prerequisites"
    )
    parser.add_argument(
        "--project-root",
        type=str,
        default=None,
        help="Path to project root (default: auto-detect)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output file for validation results (JSON)"
    )
    
    args = parser.parse_args()
    
    project_root = Path(args.project_root) if args.project_root else PROJECT_ROOT
    
    results = run_quickstart_validation(project_root)
    
    # Print summary
    print("\n" + "="*60)
    print("QUICKSTART VALIDATION RESULTS")
    print("="*60)
    print(f"Project Root: {results['project_root']}")
    print(f"Overall Status: {results['overall_status']}")
    print(f"Issues Found: {len(results['issues'])}")
    
    if results["issues"]:
        print("\nIssues:")
        for i, issue in enumerate(results["issues"], 1):
            print(f"  {i}. {issue}")
    else:
        print("\nNo issues found. Project is ready for quickstart execution.")
    
    print("="*60 + "\n")
    
    # Save results if requested
    if args.output:
        output_path = Path(args.output)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2)
        print(f"Validation results saved to: {output_path}")
    
    # Exit with appropriate code
    if results["overall_status"] == "FAIL":
        sys.exit(1)
    elif results["overall_status"] == "WARN":
        sys.exit(0)  # Warning but not fatal
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()
