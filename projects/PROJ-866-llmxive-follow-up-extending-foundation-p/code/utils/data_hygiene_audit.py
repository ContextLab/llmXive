"""
Data Hygiene Audit Module (T049)

Verifies that:
1. data/raw/ contains only generated files (no hand-edited or downloaded files).
2. data/processed/ and data/results/ are derived solely from data/raw/.
"""
import json
import os
import sys
import hashlib
from pathlib import Path
from typing import Dict, List, Set, Tuple, Any
import glob

# Constants for project structure
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
DATA_RESULTS_DIR = PROJECT_ROOT / "data" / "results"
OUTPUT_LOG_PATH = DATA_RESULTS_DIR / "data_hygiene_audit.log"

# Expected file patterns for generated data
GENERATED_WORKFLOW_PATTERNS = [
    "workflows.json",
    "workflow_*.json",
    "workflow_*.yaml"
]

GENERATED_LOG_PATTERNS = [
    "log_*.json",
    "*_context_logs.json",
    "edge_cases*.log"
]

GENERATED_RESULT_PATTERNS = [
    "tradeoff_curve.csv",
    "threshold_ci.json",
    "reproducibility_report.json",
    "data_consistency_report.json",
    "edge_case_summary.json",
    "glmm_diagnostics.json",
    "corrected_pvalues.json",
    "pairwise_comparison_results.json",
    "binned_data.json",
    "data_hygiene_audit.log" # This script writes itself
]


def compute_file_hash(file_path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    if not file_path.exists():
        return ""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except Exception:
        return ""


def get_generated_workflow_ids(raw_dir: Path) -> Set[str]:
    """
    Extract workflow IDs from raw data files.
    Assumes workflows.json or similar contains a list of workflow objects with 'id'.
    """
    workflow_ids = set()
    if not raw_dir.exists():
        return workflow_ids

    # Look for main workflows file
    workflows_file = raw_dir / "workflows.json"
    if workflows_file.exists():
        try:
            with open(workflows_file, "r") as f:
                data = json.load(f)
                if isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict) and "id" in item:
                            workflow_ids.add(str(item["id"]))
                elif isinstance(data, dict) and "workflows" in data:
                    for item in data["workflows"]:
                        if isinstance(item, dict) and "id" in item:
                            workflow_ids.add(str(item["id"]))
        except (json.JSONDecodeError, IOError):
            pass

    # Also check individual workflow files if they exist
    for wf_file in raw_dir.glob("workflow_*.json"):
        try:
            with open(wf_file, "r") as f:
                data = json.load(f)
                if isinstance(data, dict) and "id" in data:
                    workflow_ids.add(str(data["id"]))
        except (json.JSONDecodeError, IOError):
            pass

    return workflow_ids


def get_processed_workflow_ids(processed_dir: Path) -> Set[str]:
    """
    Extract workflow IDs from processed log files.
    Looks for log_*.json files or aggregated logs.
    """
    workflow_ids = set()
    if not processed_dir.exists():
        return workflow_ids

    # Check individual logs: log_{id}_{depth}.json
    for log_file in processed_dir.glob("log_*.json"):
        try:
            # Extract ID from filename: log_{id}_{depth}.json
            stem = log_file.stem # e.g., "log_wf_123_5"
            parts = stem.split("_")
            if len(parts) >= 3 and parts[0] == "log":
                # Reconstruct ID: everything between 'log' and last number
                # Format: log_{id}_{depth}
                # We assume the ID is the middle part(s).
                # A safer approach: load the file and check 'workflow_id'
                with open(log_file, "r") as f:
                    data = json.load(f)
                    if isinstance(data, dict) and "workflow_id" in data:
                        workflow_ids.add(str(data["workflow_id"]))
        except (json.JSONDecodeError, IOError):
            pass

    # Check aggregated logs
    aggregated_logs = [
        processed_dir / "full_context_logs.json",
        processed_dir / "compressed_context_logs.json"
    ]
    for agg_log in aggregated_logs:
        if agg_log.exists():
            try:
                with open(agg_log, "r") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        for item in data:
                            if isinstance(item, dict) and "workflow_id" in item:
                                workflow_ids.add(str(item["workflow_id"]))
                    elif isinstance(data, dict) and "logs" in data:
                        for item in data["logs"]:
                            if isinstance(item, dict) and "workflow_id" in item:
                                workflow_ids.add(str(item["workflow_id"]))
            except (json.JSONDecodeError, IOError):
                pass

    return workflow_ids


def get_results_workflow_ids(results_dir: Path) -> Set[str]:
    """
    Extract workflow IDs from results files (if applicable).
    Many result files are aggregated statistics, so this might be empty or partial.
    We primarily check consistency with processed data.
    """
    # For T049, we mainly verify that results exist and are derived from processed.
    # We don't necessarily need to extract IDs from aggregated CSVs/JSONs unless they contain them.
    return set()


def check_for_non_generated_files(raw_dir: Path) -> List[Dict[str, Any]]:
    """
    Check for files in data/raw/ that do not match expected generated patterns.
    Returns a list of suspicious files.
    """
    issues = []
    if not raw_dir.exists():
        return issues

    expected_patterns = GENERATED_WORKFLOW_PATTERNS + ["*.keep", ".gitkeep"]

    for file_path in raw_dir.iterdir():
        if file_path.is_dir():
            continue
        
        is_expected = False
        file_name = file_path.name
        
        # Check against expected patterns
        for pattern in expected_patterns:
            if file_path.match(pattern):
                is_expected = True
                break
        
        # Check if it's a hidden file or system file (often ignored)
        if file_name.startswith(".") or file_name.startswith("_"):
            if file_name != ".gitkeep":
                # Hidden files might be suspicious unless they are .gitkeep
                # But usually .gitkeep is the only one we care about
                pass 
        
        if not is_expected:
            issues.append({
                "file": str(file_path.relative_to(PROJECT_ROOT)),
                "type": "unexpected_file",
                "reason": "File does not match expected generated workflow patterns"
            })

    return issues


def check_derivation_consistency(
    raw_ids: Set[str],
    processed_ids: Set[str],
    results_dir: Path
) -> List[Dict[str, Any]]:
    """
    Verify that processed data corresponds to raw data.
    Every workflow in processed should have a source in raw.
    """
    issues = []

    # Check if processed IDs are a subset of raw IDs
    # Note: processed_ids might be a subset if some workflows failed validation
    missing_in_raw = processed_ids - raw_ids
    
    if missing_in_raw:
        for wf_id in list(missing_in_raw)[:10]: # Limit report size
            issues.append({
                "workflow_id": wf_id,
                "type": "missing_source",
                "reason": f"Workflow ID '{wf_id}' found in processed logs but not in raw data"
            })
        
        if len(missing_in_raw) > 10:
            issues.append({
                "type": "summary",
                "reason": f"and {len(missing_in_raw) - 10} more workflows missing in raw"
            })

    # Check if results directory has expected files (basic existence check)
    if results_dir.exists():
        # We expect certain files to exist if analysis ran
        expected_results = [
            "tradeoff_curve.csv",
            "threshold_ci.json"
        ]
        for res_file in expected_results:
            if not (results_dir / res_file).exists():
                # This is a warning, not necessarily a derivation error, but relevant for hygiene
                issues.append({
                    "file": str(results_dir / res_file),
                    "type": "missing_expected_result",
                    "reason": f"Expected result file '{res_file}' not found"
                })
    else:
        issues.append({
            "type": "missing_directory",
            "reason": "data/results/ directory does not exist"
        })

    return issues


def main():
    """
    Main function to run the data hygiene audit.
    Writes results to data/results/data_hygiene_audit.log
    """
    # Ensure output directory exists
    OUTPUT_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

    details = []
    status = "PASS"

    # 1. Check for non-generated files in raw
    details.append("=== Checking data/raw/ for non-generated files ===")
    raw_issues = check_for_non_generated_files(DATA_RAW_DIR)
    if raw_issues:
        status = "FAIL"
        for issue in raw_issues:
            details.append(f"  [ISSUE] {issue['file']}: {issue['reason']}")
    else:
        details.append("  [OK] All files in data/raw/ match expected patterns.")

    # 2. Check derivation consistency
    details.append("\n=== Checking derivation consistency ===")
    raw_ids = get_generated_workflow_ids(DATA_RAW_DIR)
    processed_ids = get_processed_workflow_ids(DATA_PROCESSED_DIR)
    
    details.append(f"  Raw workflow IDs found: {len(raw_ids)}")
    details.append(f"  Processed workflow IDs found: {len(processed_ids)}")

    consistency_issues = check_derivation_consistency(raw_ids, processed_ids, DATA_RESULTS_DIR)
    if consistency_issues:
        status = "FAIL"
        for issue in consistency_issues:
            details.append(f"  [ISSUE] {issue['reason']}")
    else:
        details.append("  [OK] Processed data is consistent with raw data.")

    # 3. Summary
    details.append(f"\n=== Summary ===")
    details.append(f"Status: {status}")
    
    # Write log
    log_content = "\n".join(details)
    with open(OUTPUT_LOG_PATH, "w") as f:
        f.write(log_content)

    # Also write a JSON summary for programmatic access
    summary = {
        "status": status,
        "details": details
    }
    # Overwrite or append to a JSON file if needed, but task asks for .log
    # We can embed the JSON summary at the end of the log or separate.
    # Let's write a separate JSON summary for clarity if needed, but the task specifies .log.
    # We'll just ensure the log contains the summary.
    
    print(f"Data Hygiene Audit complete. Status: {status}")
    print(f"Log written to: {OUTPUT_LOG_PATH}")
    
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
