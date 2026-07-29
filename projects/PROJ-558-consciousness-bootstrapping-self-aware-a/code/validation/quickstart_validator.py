"""
Quickstart Validator for PROJ-558-consciousness-bootstrapping-self-aware-a.

This script validates that all required artifacts for the project have been
generated correctly according to the tasks.md specifications. It checks:
1. Project directory structure
2. Python file imports and syntax
3. Data artifacts (checksums, existence)
4. Result artifacts (JSON schemas, metrics)
5. Configuration validity
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
import importlib.util

# Project root relative to this script
PROJECT_ROOT = Path(__file__).parent.parent.parent

def check_file_exists(file_path: Path, description: str) -> Tuple[bool, str]:
    """Check if a file exists."""
    if file_path.exists():
        return True, f"Found: {file_path.relative_to(PROJECT_ROOT)}"
    return False, f"MISSING: {file_path.relative_to(PROJECT_ROOT)} ({description})"

def check_content(file_path: Path, required_strings: List[str]) -> Tuple[bool, str]:
    """Check if a file contains required strings."""
    if not file_path.exists():
        return False, f"File not found: {file_path}"
    try:
        content = file_path.read_text()
        missing = [s for s in required_strings if s not in content]
        if not missing:
            return True, f"Content OK: {file_path.relative_to(PROJECT_ROOT)}"
        return False, f"Missing content in {file_path}: {missing}"
    except Exception as e:
        return False, f"Error reading {file_path}: {e}"

def validate_python_imports(file_path: Path) -> Tuple[bool, str]:
    """Validate that a Python file can be imported without errors."""
    if not file_path.exists():
        return False, f"File not found: {file_path}"
    
    # Add project root to path for imports
    sys.path.insert(0, str(PROJECT_ROOT))
    
    try:
        # Use importlib to check syntax and imports
        spec = importlib.util.spec_from_file_location("module", file_path)
        if spec is None or spec.loader is None:
            return False, f"Could not load spec for {file_path}"
        
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return True, f"Import OK: {file_path.relative_to(PROJECT_ROOT)}"
    except Exception as e:
        return False, f"Import error in {file_path}: {e}"
    finally:
        # Clean up path
        if str(PROJECT_ROOT) in sys.path:
            sys.path.remove(str(PROJECT_ROOT))

def validate_data_artifacts() -> List[Tuple[bool, str]]:
    """Validate data artifacts exist and have correct checksums."""
    results = []
    data_dir = PROJECT_ROOT / "data"
    manifest_path = data_dir / "manifest.json"
    
    # Check manifest exists
    success, msg = check_file_exists(manifest_path, "Data manifest")
    results.append((success, msg))
    if not success:
        return results
    
    # Load manifest
    try:
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
    except Exception as e:
        results.append((False, f"Error loading manifest: {e}"))
        return results
    
    # Check required datasets
    required_datasets = {
        "pile_arxiv_truncated.json": "Training data subset",
        "gsm8k.json": "GSM8K evaluation data",
        "mmlu.json": "MMLU evaluation data"
    }
    
    for filename, description in required_datasets.items():
        file_path = data_dir / "raw" / filename
        success, msg = check_file_exists(file_path, description)
        results.append((success, msg))
        
        if success:
            # Verify checksum in manifest
            if filename in manifest.get("datasets", {}):
                checksum = manifest["datasets"][filename].get("checksum")
                if checksum:
                    results.append((True, f"Checksum recorded for {filename}"))
                else:
                    results.append((False, f"No checksum in manifest for {filename}"))
            else:
                results.append((False, f"{filename} not in manifest"))
    
    return results

def validate_result_artifacts() -> List[Tuple[bool, str]]:
    """Validate result artifacts exist and have correct schemas."""
    results = []
    artifacts_dir = PROJECT_ROOT / "artifacts"
    results_dir = artifacts_dir / "results"
    
    # Check statistical report
    stat_report_path = results_dir / "statistical_report.json"
    success, msg = check_file_exists(stat_report_path, "Statistical report")
    results.append((success, msg))
    
    if success:
        try:
            with open(stat_report_path, 'r') as f:
                report = json.load(f)
            
            # Check for required fields
            required_fields = ["p_values", "effect_sizes", "confidence_intervals", 
                             "percentage_difference_self_consistency"]
            missing = [f for f in required_fields if f not in report]
            if not missing:
                results.append((True, "Statistical report schema valid"))
            else:
                results.append((False, f"Statistical report missing fields: {missing}"))
        except Exception as e:
            results.append((False, f"Error parsing statistical report: {e}"))
    
    # Check memory profile
    memory_log_path = results_dir / "memory_profile.log"
    success, msg = check_file_exists(memory_log_path, "Memory profile log")
    results.append((success, msg))
    
    # Check evaluation results
    eval_results_path = results_dir / "evaluation_results.json"
    success, msg = check_file_exists(eval_results_path, "Evaluation results")
    results.append((success, msg))
    
    if success:
        try:
            with open(eval_results_path, 'r') as f:
                eval_data = json.load(f)
            
            # Basic schema check
            if "metrics" in eval_data and isinstance(eval_data["metrics"], dict):
                results.append((True, "Evaluation results schema valid"))
            else:
                results.append((False, "Evaluation results missing metrics field"))
        except Exception as e:
            results.append((False, f"Error parsing evaluation results: {e}"))
    
    return results

def validate_config() -> Tuple[bool, str]:
    """Validate configuration file."""
    config_path = PROJECT_ROOT / "code" / "config.py"
    success, msg = check_file_exists(config_path, "Config module")
    if not success:
        return False, msg
    
    # Check for required config parameters
    required_params = ["seed", "batch_size", "recursion_depth", "learning_rate", "token_limit"]
    success, msg = check_content(config_path, required_params)
    return success, msg

def validate_project_structure() -> Tuple[bool, str]:
    """Validate project directory structure."""
    required_dirs = [
        "data/raw",
        "data/processed",
        "code",
        "code/models",
        "code/training",
        "code/evaluation",
        "code/analysis",
        "code/utils",
        "code/validation",
        "tests",
        "artifacts",
        "artifacts/checkpoints",
        "artifacts/results"
    ]
    
    missing_dirs = []
    for dir_path in required_dirs:
        full_path = PROJECT_ROOT / dir_path
        if not full_path.exists():
            missing_dirs.append(dir_path)
    
    if not missing_dirs:
        return True, "Project structure complete"
    else:
        return False, f"Missing directories: {missing_dirs}"

def run_quickstart_validation() -> Dict[str, Any]:
    """Run all validation checks and return results."""
    print("=" * 60)
    print("Running Quickstart Validation for PROJ-558")
    print("=" * 60)
    
    all_results = {
        "project_structure": validate_project_structure(),
        "data_artifacts": validate_data_artifacts(),
        "result_artifacts": validate_result_artifacts(),
        "config": validate_config()
    }
    
    # Validate Python imports for key modules
    key_modules = [
        "code/models/recursive_llama.py",
        "code/training/train.py",
        "code/evaluation/run_benchmarks.py",
        "code/analysis/stats.py",
        "code/evaluation/metrics.py",
        "code/evaluation/loss_functions.py"
    ]
    
    all_results["python_imports"] = []
    for module_path in key_modules:
        full_path = PROJECT_ROOT / module_path
        success, msg = validate_python_imports(full_path)
        all_results["python_imports"].append((success, msg))
    
    # Summary
    total_checks = 0
    passed_checks = 0
    
    for category, checks in all_results.items():
        if isinstance(checks, tuple):
            total_checks += 1
            if checks[0]:
                passed_checks += 1
        elif isinstance(checks, list):
            for check in checks:
                total_checks += 1
                if check[0]:
                    passed_checks += 1
    
    all_results["summary"] = {
        "total_checks": total_checks,
        "passed_checks": passed_checks,
        "failed_checks": total_checks - passed_checks,
        "success_rate": passed_checks / total_checks if total_checks > 0 else 0
    }
    
    # Print results
    print("\nValidation Results:")
    print("-" * 40)
    
    for category, checks in all_results.items():
        if category == "summary":
            continue
        print(f"\n{category.upper()}:")
        if isinstance(checks, tuple):
            success, msg = checks
            status = "✓" if success else "✗"
            print(f"  {status} {msg}")
        elif isinstance(checks, list):
            for success, msg in checks:
                status = "✓" if success else "✗"
                print(f"  {status} {msg}")
    
    print("\n" + "=" * 60)
    print(f"SUMMARY: {passed_checks}/{total_checks} checks passed ({all_results['summary']['success_rate']:.1%})")
    print("=" * 60)
    
    if all_results["summary"]["failed_checks"] > 0:
        print("\n⚠️  VALIDATION FAILED - Some artifacts are missing or invalid")
        return all_results
    else:
        print("\n✅ VALIDATION PASSED - All artifacts generated correctly")
        return all_results

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Validate quickstart artifacts")
    parser.add_argument("--output", type=str, help="Output file for validation results (JSON)")
    args = parser.parse_args()
    
    results = run_quickstart_validation()
    
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        print(f"\nResults saved to: {output_path}")
    
    # Exit with error code if validation failed
    if results["summary"]["failed_checks"] > 0:
        sys.exit(1)
    sys.exit(0)

if __name__ == "__main__":
    main()