import os
import sys
import argparse
from pathlib import Path
import subprocess
import json

def validate_quickstart_file():
    """Check if docs/quickstart.md exists and is non-empty."""
    path = Path("docs/quickstart.md")
    if not path.exists():
        print("ERROR: docs/quickstart.md does not exist.")
        return False
    if path.stat().st_size == 0:
        print("ERROR: docs/quickstart.md is empty.")
        return False
    print("OK: docs/quickstart.md exists and is non-empty.")
    return True

def validate_project_structure():
    """Check if required directories exist."""
    required_dirs = [
        "code", "data", "data/raw", "data/summaries", "data/interaction_logs",
        "data/analysis_results", "data/consent", "docs", "tests"
    ]
    missing = []
    for d in required_dirs:
        if not Path(d).exists():
            missing.append(d)
    if missing:
        print(f"ERROR: Missing directories: {missing}")
        return False
    print("OK: Project structure validated.")
    return True

def validate_python_syntax():
    """Check if all .py files in code/ have valid syntax."""
    py_files = list(Path("code").rglob("*.py"))
    errors = []
    for f in py_files:
        try:
            with open(f, "r", encoding="utf-8") as file:
                compile(file.read(), f, "exec")
        except SyntaxError as e:
            errors.append(f"{f}: {e}")
    if errors:
        print("ERROR: Syntax errors found:")
        for e in errors:
            print(f"  {e}")
        return False
    print("OK: All Python files have valid syntax.")
    return True

def validate_dependencies():
    """Check if requirements.txt exists and is non-empty."""
    path = Path("requirements.txt")
    if not path.exists():
        print("ERROR: requirements.txt does not exist.")
        return False
    if path.stat().st_size == 0:
        print("ERROR: requirements.txt is empty.")
        return False
    print("OK: requirements.txt exists and is non-empty.")
    return True

def validate_data_files():
    """Check if critical data files exist (optional, for CI)."""
    # Check for generated data files if they are expected
    critical_files = [
        "data/raw/defects4j/ground_truth.csv",
        "data/summaries/llm_summaries.csv",
        "data/interaction_logs/anonymized_logs.csv"
    ]
    missing = []
    for f in critical_files:
        if not Path(f).exists():
            missing.append(f)
    if missing:
        print(f"WARNING: Critical data files not found (expected if not generated yet): {missing}")
        # Do not fail validation if files are missing, as they might not be generated yet
        return True 
    print("OK: Critical data files exist.")
    return True

def run_quickstart_validation():
    """Run all validation checks."""
    results = [
        validate_quickstart_file(),
        validate_project_structure(),
        validate_python_syntax(),
        validate_dependencies(),
        validate_data_files()
    ]
    if all(results):
        print("\n=== VALIDATION SUCCESSFUL ===")
        return 0
    else:
        print("\n=== VALIDATION FAILED ===")
        return 1

def main():
    parser = argparse.ArgumentParser(description="Validate the project setup and quickstart guide.")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")
    args = parser.parse_args()
    
    sys.exit(run_quickstart_validation())

if __name__ == "__main__":
    main()
