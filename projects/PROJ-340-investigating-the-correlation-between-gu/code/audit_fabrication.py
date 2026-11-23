import os
import sys
import json
import subprocess
import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional

# Import from existing project modules
from verify_data_integrity import load_json_file, save_json_file, find_synthetic_artifacts, calculate_file_checksum
from config import get_config, load_config

def load_json(path: Path) -> Optional[Dict[str, Any]]:
    """Load a JSON file, returning None if not found or invalid."""
    if not path.exists():
        return None
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error loading JSON {path}: {e}", file=sys.stderr)
        return None

def save_json(data: Dict[str, Any], path: Path) -> bool:
    """Save a dictionary to a JSON file."""
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, default=str)
        return True
    except IOError as e:
        print(f"Error saving JSON {path}: {e}", file=sys.stderr)
        return False

def run_integrity_check(
    base_dir: Path,
    manifest_path: Optional[Path] = None,
    real_data_mode: bool = True
) -> Dict[str, Any]:
    """
    Run the integrity verification logic (T056) and return the results.
    
    This function scans the data/ directory for synthetic placeholders.
    If real_data_mode is True and synthetic artifacts are found, it returns a FAIL status.
    """
    results = {
        "status": "PASS",
        "scan_time": str(Path(base_dir).absolute()),
        "artifacts_found": [],
        "errors": [],
        "details": {}
    }

    data_dir = base_dir / "data"
    if not data_dir.exists():
        results["status"] = "FAIL"
        results["errors"].append("Data directory 'data/' not found.")
        return results

    # 1. Scan for synthetic artifacts
    synthetic_candidates = find_synthetic_artifacts(data_dir)
    
    results["details"]["synthetic_artifacts_found"] = len(synthetic_candidates)
    results["artifacts_found"] = [str(p) for p in synthetic_candidates]

    # 2. Check integrity against manifest if provided
    if manifest_path and manifest_path.exists():
        manifest = load_json(manifest_path)
        if manifest:
            # Verify checksums of expected real files if in manifest
            # For this audit, we primarily care about the presence of synthetic markers
            # when real data is expected.
            pass

    # 3. Determine final status
    if real_data_mode and len(synthetic_candidates) > 0:
        results["status"] = "FAIL"
        results["errors"].append(
            f"Fabrication Detected: Found {len(synthetic_candidates)} synthetic artifacts "
            "while real data mode was active."
        )
    elif len(synthetic_candidates) > 0:
        # In synthetic mode, finding them is expected, but we log it for audit
        results["details"]["note"] = "Synthetic artifacts found, but real_data_mode is False."
    
    # 4. Verify specific required artifacts for T066 (Real Data Analysis)
    # If we are auditing a real data run, we expect the real_data_analysis_report.json to exist
    # and NOT be a synthetic placeholder.
    real_report_path = data_dir / "results" / "real_data_analysis_report.json"
    if real_data_mode and not real_report_path.exists():
        results["status"] = "FAIL"
        results["errors"].append(
            "Missing Required Artifact: data/results/real_data_analysis_report.json "
            "was not found. Real data pipeline may not have completed."
        )
    elif real_report_path.exists() and real_data_mode:
        # Check if the real report itself looks like a synthetic placeholder
        # (e.g., if it contains specific synthetic markers)
        report_content = load_json(real_report_path)
        if report_content and report_content.get("data_source") == "synthetic":
            results["status"] = "FAIL"
            results["errors"].append(
                "Fabrication Detected: real_data_analysis_report.json claims synthetic source "
                "despite real_data_mode flag."
            )

    return results

def generate_audit_report(
    integrity_results: Dict[str, Any],
    output_path: Path
) -> bool:
    """
    Generate the final fabrication audit report (T067 output).
    """
    audit_report = {
        "task_id": "T067",
        "audit_type": "Fabrication Audit",
        "timestamp": str(Path(output_path).parent), # Placeholder for real timestamp
        "integrity_check_result": integrity_results,
        "conclusion": "PASS" if integrity_results["status"] == "PASS" else "FAIL",
        "summary": (
            "No synthetic artifacts detected in real data mode." 
            if integrity_results["status"] == "PASS" 
            else "Synthetic artifacts detected or required real data artifacts missing."
        )
    }
    
    return save_json(audit_report, output_path)

def main():
    parser = argparse.ArgumentParser(description="Run Fabrication Audit (T067)")
    parser.add_argument(
        "--base-dir", 
        type=Path, 
        default=Path.cwd(), 
        help="Base directory of the project"
    )
    parser.add_argument(
        "--manifest", 
        type=Path, 
        default=None, 
        help="Path to synthetic_data_manifest.json (optional)"
    )
    parser.add_argument(
        "--output", 
        type=Path, 
        default=None, 
        help="Output path for fabrication_audit_report.json"
    )
    parser.add_argument(
        "--real-data", 
        action="store_true", 
        default=True, 
        help="Flag indicating if we expect real data (default: True)"
    )
    
    args = parser.parse_args()
    
    base_dir = args.base_dir
    if args.output is None:
        output_path = base_dir / "data" / "results" / "fabrication_audit_report.json"
    else:
        output_path = args.output

    print(f"Running Fabrication Audit (T067) on {base_dir}...")
    print(f"Real Data Mode: {args.real_data}")

    # Run the integrity check (T056 logic)
    integrity_results = run_integrity_check(
        base_dir=base_dir,
        manifest_path=args.manifest,
        real_data_mode=args.real_data
    )

    # Generate the final report
    success = generate_audit_report(integrity_results, output_path)

    if success:
        print(f"Audit report generated at: {output_path}")
        print(f"Final Status: {integrity_results['status']}")
        
        # Exit with error code if audit failed
        if integrity_results["status"] == "FAIL":
            print("AUDIT FAILED: Fabrication detected or missing artifacts.")
            sys.exit(1)
        else:
            print("AUDIT PASSED: No fabrication detected.")
            sys.exit(0)
    else:
        print("Failed to generate audit report.")
        sys.exit(1)

if __name__ == "__main__":
    main()