"""
Verify F1-scores, ROC/PR curves, memory profiles, and runtime measurements exist
in data/processed/results/ directory per SC-001 through SC-005.

This script checks for the presence of all required evaluation artifacts
and validates they are non-trivial (not empty files).

Exit codes:
  0: All required artifacts exist and are valid
  1: Missing or invalid artifacts found
"""
import os
import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Any, Optional

# Project root relative to this script
PROJECT_ROOT = Path(__file__).parent.parent.parent

# Results directory path
RESULTS_DIR = PROJECT_ROOT / "data" / "processed" / "results"

# Required artifact patterns per SC-001 through SC-005
REQUIRED_ARTIFACTS = {
    # F1-scores and metrics (SC-001)
    "f1_scores": [
        "dp_gmm_f1_scores.json",
        "arima_f1_scores.json",
        "moving_average_f1_scores.json",
        "lstm_ae_f1_scores.json",
        "metrics_summary.json",
    ],
    # ROC/PR curves (SC-002)
    "roc_pr_curves": [
        "dp_gmm_roc_curve.png",
        "dp_gmm_pr_curve.png",
        "arima_roc_curve.png",
        "arima_pr_curve.png",
        "moving_average_roc_curve.png",
        "moving_average_pr_curve.png",
        "lstm_ae_roc_curve.png",
        "lstm_ae_pr_curve.png",
    ],
    # Memory profiles (SC-003)
    "memory_profiles": [
        "dp_gmm_memory_profile.json",
        "dp_gmm_memory_1000_obs.json",
    ],
    # Runtime measurements (SC-004)
    "runtime_measurements": [
        "dp_gmm_runtime.json",
        "arima_runtime.json",
        "moving_average_runtime.json",
        "lstm_ae_runtime.json",
        "pipeline_runtime_summary.json",
    ],
    # Statistical tests (SC-005)
    "statistical_tests": [
        "paired_ttest_results.json",
        "bonferroni_correction_results.json",
        "model_comparison_summary.json",
    ],
}

# Minimum file sizes to consider as "non-trivial" (in bytes)
MIN_FILE_SIZES = {
    ".json": 50,  # JSON files should have actual content
    ".png": 1000,  # PNG files should be actual images
    ".csv": 100,  # CSV files should have data rows
    ".txt": 50,  # Text files should have content
}


def get_file_extension(path: Path) -> str:
    """Get file extension with dot prefix."""
    return path.suffix.lower() if path.suffix else ".unknown"


def check_file_validity(file_path: Path) -> Tuple[bool, str]:
    """
    Check if a file exists and has non-trivial size.

    Returns:
      Tuple of (is_valid, error_message)
    """
    if not file_path.exists():
        return False, f"File does not exist: {file_path}"

    file_size = file_path.stat().st_size
    ext = get_file_extension(file_path)
    min_size = MIN_FILE_SIZES.get(ext, 100)

    if file_size < min_size:
        return False, f"File too small ({file_size} bytes < {min_size} min): {file_path}"

    # For JSON files, try to parse them
    if ext == ".json":
        try:
            with open(file_path, "r") as f:
                data = json.load(f)
                if not data:
                    return False, f"JSON file is empty: {file_path}"
        except json.JSONDecodeError as e:
            return False, f"Invalid JSON in {file_path}: {e}"

    return True, "OK"


def scan_results_directory() -> Dict[str, List[Dict[str, Any]]]:
    """
    Scan results directory and report status of all required artifacts.

    Returns:
      Dict mapping artifact category to list of file statuses
    """
    results = {category: [] for category in REQUIRED_ARTIFACTS}

    if not RESULTS_DIR.exists():
        print(f"ERROR: Results directory does not exist: {RESULTS_DIR}")
        return results

    print(f"\nScanning results directory: {RESULTS_DIR}")
    print("=" * 60)

    for category, artifact_names in REQUIRED_ARTIFACTS.items():
        print(f"\n[{category.upper()}]")
        for artifact_name in artifact_names:
            file_path = RESULTS_DIR / artifact_name
            is_valid, message = check_file_validity(file_path)
            status = "✓" if is_valid else "✗"
            results[category].append({
                "name": artifact_name,
                "path": str(file_path),
                "exists": is_valid,
                "message": message,
            })
            print(f"  {status} {artifact_name}: {message}")

    return results


def generate_summary_report(results: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
    """
    Generate summary report from scan results.

    Returns:
      Summary dict with totals and missing artifacts
    """
    summary = {
        "total_categories": len(REQUIRED_ARTIFACTS),
        "total_artifacts": sum(len(v) for v in REQUIRED_ARTIFACTS.values()),
        "artifacts_found": 0,
        "artifacts_missing": 0,
        "missing_artifacts": [],
        "timestamp": datetime.now().isoformat(),
    }

    for category, artifact_list in results.items():
        for artifact in artifact_list:
            if artifact["exists"]:
                summary["artifacts_found"] += 1
            else:
                summary["artifacts_missing"] += 1
                summary["missing_artifacts"].append({
                    "category": category,
                    "name": artifact["name"],
                    "message": artifact["message"],
                })

    return summary


def print_summary_report(summary: Dict[str, Any]) -> None:
    """Print formatted summary report."""
    print("\n" + "=" * 60)
    print("SUMMARY REPORT")
    print("=" * 60)
    print(f"Timestamp: {summary['timestamp']}")
    print(f"Total artifact categories: {summary['total_categories']}")
    print(f"Total artifacts checked: {summary['total_artifacts']}")
    print(f"Artifacts found: {summary['artifacts_found']}")
    print(f"Artifacts missing: {summary['artifacts_missing']}")

    if summary["artifacts_missing"] > 0:
        print(f"\nMissing artifacts ({summary['artifacts_missing']}):")
        for missing in summary["missing_artifacts"]:
            print(f"  - [{missing['category']}] {missing['name']}: {missing['message']}")
        print("\n⚠️  VERIFICATION FAILED - Missing artifacts detected")
    else:
        print("\n✅ VERIFICATION PASSED - All required artifacts present")


def save_report(summary: Dict[str, Any], results: Dict[str, List[Dict[str, Any]]]) -> None:
    """Save detailed report to results directory."""
    report = {
        "summary": summary,
        "detailed_results": results,
    }

    report_path = RESULTS_DIR / "verification_report.json"
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)

    print(f"\nDetailed report saved to: {report_path}")


def main() -> int:
    """
    Main entry point for artifact verification.

    Returns:
      Exit code (0 for success, 1 for failure)
    """
    print("=" * 60)
    print("RESULTS ARTIFACT VERIFICATION")
    print("Verifying F1-scores, ROC/PR curves, memory profiles,")
    print("and runtime measurements per SC-001 through SC-005")
    print("=" * 60)

    # Scan results directory
    results = scan_results_directory()

    # Generate summary
    summary = generate_summary_report(results)

    # Print summary
    print_summary_report(summary)

    # Save detailed report
    save_report(summary, results)

    # Return appropriate exit code
    if summary["artifacts_missing"] > 0:
        print("\n⚠️  Some artifacts are missing. Run evaluation pipeline to generate them.")
        return 1
    else:
        print("\n✅ All required artifacts verified successfully.")
        return 0


if __name__ == "__main__":
    sys.exit(main())
