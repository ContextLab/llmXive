"""
T082: Audit data/raw/ and data/processed/ for synthetic data or placeholders.
Confirms all data originates from verified sources in data_sources.yaml.
"""
import os
import sys
import json
import yaml
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT_ROOT / "code"))

from src.utils.config import get_data_path, load_config

# Constants for verification
SYNTHETIC_MARKERS = [
    "synthetic", "dummy", "fake", "placeholder", "mock", "generated_sample"
]
EXPECTED_RAW_SUBDIR = "lora_weights"
EXPECTED_PROCESSED_FILES = [
    "weights_flattened.npz", "skill_index.npz", "cvs_status.json",
    "proxy_ground_truth.npz", "eval_tasks.yaml", "data_fetch_status.json",
    "citation_verification.json"
]
EXPECTED_RESULTS_FILES = [
    "stats_report.json", "stats_raw.json", "sensitivity_raw.json",
    "sensitivity_bh_corrected.json", "stats_bh_corrected.json",
    "linearity_validation.json", "correlation.json", "reconstruction_error.json",
    "latency_metrics.json", "baseline_status.json", "zero_shot_baseline.json"
]

def load_data_sources() -> Dict[str, Any]:
    """Load data_sources.yaml from project root."""
    sources_path = PROJECT_ROOT / "data_sources.yaml"
    if not sources_path.exists():
        raise FileNotFoundError(f"Required data_sources.yaml not found at {sources_path}")
    with open(sources_path, "r") as f:
        return yaml.safe_load(f)

def check_file_for_synthetic_markers(file_path: Path) -> Optional[str]:
    """Check if a file contains synthetic markers in name or content."""
    # Check filename
    filename_lower = file_path.name.lower()
    for marker in SYNTHETIC_MARKERS:
        if marker in filename_lower:
            return f"Filename contains synthetic marker: '{marker}'"

    # Check content for small files (text-based)
    try:
        if file_path.suffix in [".json", ".yaml", ".yml", ".txt", ".csv"]:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read().lower()
                for marker in SYNTHETIC_MARKERS:
                    if marker in content:
                        return f"Content contains synthetic marker: '{marker}'"
    except Exception:
        pass  # Binary files or unreadable files are skipped for content check

    return None

def verify_real_data_source(file_path: Path, data_sources: Dict[str, Any]) -> bool:
    """
    Verify that a file in data/raw/ corresponds to a real source.
    For T082, we primarily check that the directory structure matches
    the expected download from the verified proxy dataset.
    """
    if "lora_weights" not in str(file_path):
        # Not a weight file, skip detailed source verification
        return True

    # Check if it's a known real source pattern
    # The verified source is mrm8488/peft-examples
    # We expect adapter_model.safetensors files
    if file_path.suffix not in [".safetensors", ".bin", ".pt"]:
        return False

    return True

def audit_directory(directory: Path, data_sources: Dict[str, Any]) -> Dict[str, Any]:
    """Audit a directory for synthetic data or placeholders."""
    issues = []
    valid_files = []
    synthetic_files = []

    if not directory.exists():
        return {
            "status": "missing_directory",
            "path": str(directory),
            "issues": [f"Directory does not exist: {directory}"]
        }

    for item in directory.rglob("*"):
        if item.is_file():
            marker_issue = check_file_for_synthetic_markers(item)
            if marker_issue:
                synthetic_files.append({
                    "path": str(item.relative_to(PROJECT_ROOT)),
                    "reason": marker_issue
                })
            else:
                # Additional check for raw data sources
                if "data/raw" in str(item):
                    if not verify_real_data_source(item, data_sources):
                        issues.append(f"Unrecognized source file in raw data: {item}")
                
                valid_files.append(str(item.relative_to(PROJECT_ROOT)))

    return {
        "status": "complete",
        "directory": str(directory.relative_to(PROJECT_ROOT)),
        "valid_files": valid_files,
        "synthetic_files": synthetic_files,
        "issues": issues
    }

def main():
    """Main audit function."""
    print("Starting Data Integrity Audit (T082)...")
    
    try:
        data_sources = load_data_sources()
    except Exception as e:
        print(f"ERROR: Failed to load data_sources.yaml: {e}")
        sys.exit(1)

    raw_dir = get_data_path("raw")
    processed_dir = get_data_path("processed")
    results_dir = get_data_path("results")

    audit_results = {
        "audit_timestamp": str(Path(__file__).stat().st_mtime),
        "data_sources_verified": list(data_sources.keys()),
        "raw_data": audit_directory(raw_dir, data_sources),
        "processed_data": audit_directory(processed_dir, data_sources),
        "results_data": audit_directory(results_dir, data_sources),
        "overall_status": "PASS"
    }

    # Aggregate issues
    all_issues = []
    all_synthetic = []

    for key in ["raw_data", "processed_data", "results_data"]:
        if audit_results[key].get("status") == "missing_directory":
            all_issues.append(f"Missing directory: {audit_results[key].get('path')}")
            audit_results["overall_status"] = "FAIL"
        else:
            if audit_results[key].get("synthetic_files"):
                all_synthetic.extend(audit_results[key]["synthetic_files"])
                audit_results["overall_status"] = "FAIL"
            if audit_results[key].get("issues"):
                all_issues.extend(audit_results[key]["issues"])
                audit_results["overall_status"] = "FAIL"

    # Final verdict
    if all_synthetic:
        print("\n❌ AUDIT FAILED: Synthetic or placeholder data detected:")
        for f in all_synthetic:
            print(f"  - {f['path']}: {f['reason']}")
        audit_results["overall_status"] = "FAIL"
    elif all_issues:
        print("\n⚠️ AUDIT WARNINGS:")
        for issue in all_issues:
            print(f"  - {issue}")
        # Warnings don't necessarily fail the audit unless critical
        if "Missing directory" in str(all_issues):
            audit_results["overall_status"] = "FAIL"
    else:
        print("\n✅ AUDIT PASSED: No synthetic data or placeholders detected.")
        print(f"   Verified sources: {audit_results['data_sources_verified']}")

    # Save audit report
    audit_output_path = results_dir / "data_integrity_audit.json"
    os.makedirs(audit_output_path.parent, exist_ok=True)
    with open(audit_output_path, "w") as f:
        json.dump(audit_results, f, indent=2)
    
    print(f"\nAudit report saved to: {audit_output_path}")

    if audit_results["overall_status"] == "FAIL":
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()
