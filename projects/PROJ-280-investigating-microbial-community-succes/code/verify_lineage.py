import json
import hashlib
import sys
import os
from pathlib import Path
from typing import List, Dict, Any, Optional

def calculate_file_hash(file_path: str) -> Optional[str]:
    """Calculate SHA-256 hash of a file."""
    if not os.path.exists(file_path):
        return None
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except Exception:
        return None

def verify_lineage_entry(entry: Dict[str, Any], base_path: str) -> bool:
    """Verify a single lineage entry."""
    source_file = entry.get("source_file")
    expected_hash = entry.get("content_hash")
    metric_name = entry.get("metric_name")
    task_id = entry.get("task_id")

    if not source_file or not expected_hash:
        print(f"[ERROR] [T052] Missing source_file or content_hash for metric: {metric_name}")
        return False

    # Construct full path relative to project root
    full_path = os.path.join(base_path, source_file)
    
    if not os.path.exists(full_path):
        print(f"[ERROR] [T052] Source file missing for metric '{metric_name}' (Task: {task_id}): {full_path}")
        return False

    actual_hash = calculate_file_hash(full_path)
    
    if actual_hash is None:
        print(f"[ERROR] [T052] Could not read file for metric '{metric_name}': {full_path}")
        return False

    if actual_hash != expected_hash:
        print(f"[ERROR] [T052] Hash mismatch for metric '{metric_name}' (Task: {task_id}):")
        print(f"  Expected: {expected_hash}")
        print(f"  Actual:   {actual_hash}")
        print(f"  File:     {full_path}")
        return False

    print(f"[INFO] [T052] Verified: {metric_name} -> {source_file} ({task_id})")
    return True

def main():
    """Main entry point for lineage verification."""
    # Determine project root (parent of code/)
    base_dir = Path(__file__).parent.parent
    report_path = base_dir / "data" / "processed" / "final_analysis_report.json"

    # Check if final report exists
    if not report_path.exists():
        print(f"[CRITICAL] [T052] Final analysis report not found: {report_path}")
        print("This indicates T047 (Final Report Aggregation) has not run successfully.")
        sys.exit(1)

    # Load and parse the report
    try:
        with open(report_path, "r") as f:
            report_data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"[CRITICAL] [T052] Invalid JSON in final analysis report: {e}")
        sys.exit(1)

    lineage_entries = report_data.get("data_lineage", [])
    
    if not lineage_entries:
        print("[WARN] [T052] No data_lineage entries found in final analysis report.")
        print("[INFO] [T052] Verification complete (no lineage entries to check).")
        sys.exit(0)

    print(f"[INFO] [T052] Starting lineage verification for {len(lineage_entries)} entries...")
    
    all_valid = True
    for entry in lineage_entries:
        if not verify_lineage_entry(entry, str(base_dir)):
            all_valid = False

    if all_valid:
        print("[INFO] [T052] All lineage entries verified successfully.")
        sys.exit(0)
    else:
        print("[CRITICAL] [T052] Lineage verification FAILED. Some artifacts are missing or corrupted.")
        sys.exit(1)

if __name__ == "__main__":
    main()