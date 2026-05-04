"""
T078: Verify paired t-tests with Bonferroni correction completed across all datasets.

This script verifies that statistical test results exist for all three UCI datasets
(Electricity, Traffic, Synthetic Control Chart) and that Bonferroni-corrected
p-values are present in the results.

Per US2 acceptance scenario 2: "The system computes paired t-tests with
Bonferroni correction across datasets to validate statistical significance."
"""
import os
import sys
import json
import yaml
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Tuple

# Project root
PROJECT_ROOT = Path(__file__).parent.parent.parent
RESULTS_DIR = PROJECT_ROOT / "data" / "processed" / "results"

# Expected datasets per SC-001
EXPECTED_DATASETS = ["electricity", "traffic", "synthetic_control_chart"]

# Expected models per US2
EXPECTED_MODELS = ["dp_gmm", "arima", "moving_average", "lstm_ae"]

def load_json_file(filepath: Path) -> Dict[str, Any]:
    """Load JSON file and return contents."""
    with open(filepath, 'r') as f:
        return json.load(f)

def load_yaml_file(filepath: Path) -> Dict[str, Any]:
    """Load YAML file and return contents."""
    with open(filepath, 'r') as f:
        return yaml.safe_load(f)

def check_statistical_test_results(dataset_name: str) -> Tuple[bool, Dict[str, Any]]:
    """
    Check if statistical test results exist for a dataset.
    
    Returns:
        Tuple of (found, details) where details contains verification info
    """
    details = {
        "dataset": dataset_name,
        "results_file": None,
        "bonferroni_correction": False,
        "paired_ttest": False,
        "model_comparisons": [],
        "p_values": [],
        "significance_level": None
    }
    
    # Look for statistical test results
    possible_paths = [
        RESULTS_DIR / f"{dataset_name}_statistical_tests.json",
        RESULTS_DIR / f"{dataset_name}_ttest_results.json",
        RESULTS_DIR / "statistical_tests" / f"{dataset_name}_results.json",
        RESULTS_DIR / "comparison" / f"{dataset_name}_comparison.json",
    ]
    
    for path in possible_paths:
        if path.exists():
            details["results_file"] = str(path.relative_to(PROJECT_ROOT))
            try:
                results = load_json_file(path)
                
                # Check for Bonferroni correction
                if "bonferroni" in str(results).lower() or "bonferroni" in results:
                    details["bonferroni_correction"] = True
                    if isinstance(results.get("bonferroni"), dict):
                        details["significance_level"] = results["bonferroni"].get("alpha")
                
                # Check for paired t-test
                if "paired_ttest" in str(results).lower() or "paired_ttest" in results:
                    details["paired_ttest"] = True
                
                # Extract model comparisons
                comparisons = results.get("comparisons", [])
                if not comparisons:
                    comparisons = results.get("model_comparisons", [])
                if not comparisons:
                    comparisons = results.get("results", [])
                
                details["model_comparisons"] = [c.get("model_pair", str(c)) for c in comparisons[:5]]
                
                # Extract p-values
                p_values = results.get("p_values", [])
                if not p_values:
                    p_values = results.get("adjusted_p_values", [])
                details["p_values"] = p_values[:5]
                
                return True, details
                
            except Exception as e:
                details["error"] = str(e)
                return False, details
    
    return False, details

def check_summary_report() -> Tuple[bool, Dict[str, Any]]:
    """Check if summary report exists with statistical test results."""
    details = {
        "summary_file": None,
        "has_statistical_tests": False,
        "datasets_covered": [],
        "bonferroni_applied": False
    }
    
    # Look for summary report
    possible_paths = [
        RESULTS_DIR / "summary.md",
        RESULTS_DIR / "summary.json",
        RESULTS_DIR / "evaluation_summary.json",
    ]
    
    for path in possible_paths:
        if path.exists():
            details["summary_file"] = str(path.relative_to(PROJECT_ROOT))
            
            if path.suffix == '.md':
                with open(path, 'r') as f:
                    content = f.read().lower()
                    details["has_statistical_tests"] = "statistical test" in content or "t-test" in content
                    details["bonferroni_applied"] = "bonferroni" in content
                    
                    for ds in EXPECTED_DATASETS:
                        if ds in content.lower():
                            details["datasets_covered"].append(ds)
            else:
                try:
                    results = load_json_file(path)
                    details["has_statistical_tests"] = "statistical_test" in str(results).lower() or "ttest" in str(results).lower()
                    details["bonferroni_applied"] = "bonferroni" in str(results).lower()
                except:
                    pass
            
            return True, details
    
    return False, details

def verify_all_datasets() -> Dict[str, Any]:
    """Verify statistical test results for all expected datasets."""
    verification = {
        "timestamp": datetime.now().isoformat(),
        "project_root": str(PROJECT_ROOT),
        "results_directory": str(RESULTS_DIR),
        "expected_datasets": EXPECTED_DATASETS,
        "expected_models": EXPECTED_MODELS,
        "dataset_results": {},
        "summary_verification": {},
        "overall_status": "PASS",
        "issues": [],
        "recommendations": []
    }
    
    # Check each dataset
    all_datasets_pass = True
    for dataset in EXPECTED_DATASETS:
        found, details = check_statistical_test_results(dataset)
        verification["dataset_results"][dataset] = details
        
        if not found:
            all_datasets_pass = False
            verification["issues"].append(f"Statistical test results not found for {dataset}")
            verification["recommendations"].append(
                f"Run evaluation pipeline for {dataset} to generate t-test results"
            )
        elif not details.get("bonferroni_correction"):
            verification["issues"].append(
                f"Bonferroni correction not found in {dataset} results"
            )
            verification["recommendations"].append(
                f"Ensure paired_ttest_with_bonferroni() was called for {dataset}"
            )
        elif not details.get("paired_ttest"):
            verification["issues"].append(
                f"Paired t-test not found in {dataset} results"
            )
            verification["recommendations"].append(
                f"Ensure paired_ttest_with_bonferroni() was called for {dataset}"
            )
    
    # Check summary report
    summary_found, summary_details = check_summary_report()
    verification["summary_verification"] = summary_details
    
    if not summary_found:
        verification["issues"].append("Summary report not found in results directory")
        verification["recommendations"].append("Create summary report documenting statistical test results")
    
    # Overall status
    if all_datasets_pass and summary_found:
        verification["overall_status"] = "PASS"
    else:
        verification["overall_status"] = "FAIL"
    
    return verification

def print_verification_report(verification: Dict[str, Any]):
    """Print formatted verification report."""
    print("=" * 70)
    print("T078: Paired t-test with Bonferroni Correction Verification Report")
    print("=" * 70)
    print(f"\nTimestamp: {verification['timestamp']}")
    print(f"Project Root: {verification['project_root']}")
    print(f"Results Directory: {verification['results_directory']}")
    print(f"\nExpected Datasets: {', '.join(verification['expected_datasets'])}")
    print(f"Expected Models: {', '.join(verification['expected_models'])}")
    print(f"\nOverall Status: {verification['overall_status']}")
    
    print("\n" + "-" * 70)
    print("Dataset Verification Results:")
    print("-" * 70)
    
    for dataset, details in verification["dataset_results"].items():
        print(f"\n[{dataset.upper()}]")
        print(f"  Results File: {details.get('results_file', 'NOT FOUND')}")
        print(f"  Bonferroni Correction: {details.get('bonferroni_correction', False)}")
        print(f"  Paired T-Test: {details.get('paired_ttest', False)}")
        if details.get("model_comparisons"):
            print(f"  Model Comparisons: {', '.join(details['model_comparisons'])}")
        if details.get("p_values"):
            print(f"  P-Values: {details['p_values']}")
        if details.get("significance_level"):
            print(f"  Significance Level (alpha): {details['significance_level']}")
        if details.get("error"):
            print(f"  Error: {details['error']}")
    
    print("\n" + "-" * 70)
    print("Summary Report Verification:")
    print("-" * 70)
    summary = verification["summary_verification"]
    print(f"  Summary File: {summary.get('summary_file', 'NOT FOUND')}")
    print(f"  Has Statistical Tests: {summary.get('has_statistical_tests', False)}")
    print(f"  Bonferroni Applied: {summary.get('bonferroni_applied', False)}")
    print(f"  Datasets Covered: {', '.join(summary.get('datasets_covered', []))}")
    
    if verification["issues"]:
        print("\n" + "-" * 70)
        print("Issues Found:")
        print("-" * 70)
        for i, issue in enumerate(verification["issues"], 1):
            print(f"  {i}. {issue}")
    
    if verification["recommendations"]:
        print("\n" + "-" * 70)
        print("Recommendations:")
        print("-" * 70)
        for i, rec in enumerate(verification["recommendations"], 1):
            print(f"  {i}. {rec}")
    
    print("\n" + "=" * 70)
    
    return verification["overall_status"] == "PASS"

def save_verification_report(verification: Dict[str, Any]):
    """Save verification report to results directory."""
    report_path = RESULTS_DIR / "ttest_bonferroni_verification.json"
    with open(report_path, 'w') as f:
        json.dump(verification, f, indent=2)
    print(f"\nVerification report saved to: {report_path.relative_to(PROJECT_ROOT)}")

def main():
    """Main entry point for verification."""
    print(f"\nChecking for statistical test results in: {RESULTS_DIR}\n")
    
    if not RESULTS_DIR.exists():
        print(f"ERROR: Results directory does not exist: {RESULTS_DIR}")
        print("Run the evaluation pipeline first to generate results.")
        sys.exit(1)
    
    # Run verification
    verification = verify_all_datasets()
    
    # Print report
    passed = print_verification_report(verification)
    
    # Save report
    save_verification_report(verification)
    
    # Exit with appropriate code
    sys.exit(0 if passed else 1)

if __name__ == "__main__":
    main()
