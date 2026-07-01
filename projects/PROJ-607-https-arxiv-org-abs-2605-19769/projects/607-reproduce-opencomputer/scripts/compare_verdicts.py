"""
compare_verdicts.py

Merges verification_report.json with blinded_ground_truth.json.
Calculates matches/mismatches.
Handles Dual-Inspection protocol (inspector_1 vs inspector_2).
Generates qualitative alignment_observation.
Outputs summary to data/summary.json and detailed results to data/verification_results.csv.
"""

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RESULTS_DIR = PROJECT_ROOT / "results"
DATA_DIR = PROJECT_ROOT / "data"

VERIFICATION_REPORT_PATH = RESULTS_DIR / "verification_report.json"
BLINDED_GROUND_TRUTH_PATH = DATA_DIR / "blinded_ground_truth.json"
SUMMARY_JSON_PATH = DATA_DIR / "summary.json"
RESULTS_CSV_PATH = DATA_DIR / "verification_results.csv"


def load_json(path: Path) -> Optional[Dict[str, Any]]:
    if not path.exists():
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def resolve_manual_verdict(inspection: Dict[str, Any]) -> str:
    """
    Resolve final manual verdict from inspector_1 and inspector_2.
    Logic:
    - If both agree, use that verdict.
    - If disagree, flag as 'discrepancy' (or use majority if 3rd exists, but here we just flag).
    - If missing, use 'unknown'.
    """
    i1 = inspection.get("inspector_1", {}).get("manual_verdict")
    i2 = inspection.get("inspector_2", {}).get("manual_verdict")

    if i1 and i2:
        if i1 == i2:
            return i1
        else:
            return "discrepancy"
    elif i1:
        return i1
    elif i2:
        return i2
    else:
        return "unknown"


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare verifier verdicts with manual ground truth.")
    parser.add_argument("--input-verification", type=str, default=str(VERIFICATION_REPORT_PATH))
    parser.add_argument("--input-ground-truth", type=str, default=str(BLINDED_GROUND_TRUTH_PATH))
    parser.add_argument("--output-summary", type=str, default=str(SUMMARY_JSON_PATH))
    parser.add_argument("--output-csv", type=str, default=str(RESULTS_CSV_PATH))
    args = parser.parse_args()

    ver_data = load_json(Path(args.input_verification))
    gt_data = load_json(Path(args.input_ground_truth))

    if not ver_data or not gt_data:
        print("Error: Missing input files.", file=sys.stderr)
        return 1

    # Index ground truth by task_id
    gt_map = {}
    for item in gt_data.get("inspections", []):
        gt_map[item["task_id"]] = item

    results = ver_data.get("results", [])
    matches = 0
    mismatches = 0
    discrepancies = 0
    total = len(results)
    csv_rows = []

    for res in results:
        tid = res["task_id"]
        verifier_verdict = res.get("verdict", "unknown")
        gt_item = gt_map.get(tid, {})

        manual_verdict = resolve_manual_verdict(gt_item)
        
        # Determine match status
        if manual_verdict == verifier_verdict:
            status = "match"
            matches += 1
        elif manual_verdict == "discrepancy":
            status = "discrepancy"
            discrepancies += 1
        else:
            status = "mismatch"
            mismatches += 1

        csv_rows.append({
            "task_id": tid,
            "verifier_verdict": verifier_verdict,
            "manual_verdict": manual_verdict,
            "status": status,
            "discrepancy_reason": gt_item.get("manual_judgment_notes", "") if status == "discrepancy" else ""
        })

    # Calculate metrics
    alignment_rate = (matches / total * 100) if total > 0 else 0.0
    
    # Update summary.json
    summary = load_json(Path(args.output_summary)) or {}
    summary["verifier_alignment_rate"] = alignment_rate
    summary["total_tasks"] = total
    summary["matches"] = matches
    summary["mismatches"] = mismatches
    summary["discrepancies"] = discrepancies
    
    with open(Path(args.output_summary), "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    # Write CSV
    with open(Path(args.output_csv), "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["task_id", "verifier_verdict", "manual_verdict", "status", "discrepancy_reason"])
        writer.writeheader()
        writer.writerows(csv_rows)

    # Generate observation string
    obs = f"Alignment: {matches}/{total} matches ({alignment_rate:.1f}%). "
    if mismatches > 0:
        obs += f"Mismatches: {mismatches}. "
    if discrepancies > 0:
        obs += f"Inspection Discrepancies: {discrepancies}. "
    
    print(f"Comparison complete. Alignment Rate: {alignment_rate:.1f}%")
    print(f"Observation: {obs}")
    return 0


if __name__ == "__main__":
    sys.exit(main())