"""
prepare_ground_truth.py

Implements the Blinding Protocol:
1. Reads verification_report.json (contains verifier results).
2. Reads sample_tasks.json (task definitions).
3. Removes all verifier results and artifacts paths.
4. Generates blinded_ground_truth.json template for manual inspection.
5. Enforces schema: task_id, manual_verdict (pass/fail), manual_judgment_notes.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RESULTS_DIR = PROJECT_ROOT / "results"
DATA_DIR = PROJECT_ROOT / "data"

VERIFICATION_REPORT_PATH = RESULTS_DIR / "verification_report.json"
SAMPLE_TASKS_PATH = DATA_DIR / "sample_tasks.json"
OUTPUT_PATH = DATA_DIR / "blinded_ground_truth.json"


def load_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(data: Dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def create_blinded_entry(task_id: str) -> Dict[str, Any]:
    """Create a template entry for manual inspection."""
    return {
        "task_id": task_id,
        "manual_verdict": None,  # To be filled by inspector
        "manual_judgment_notes": None,
        "inspector_1": None,
        "inspector_2": None
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare blinded ground truth template.")
    parser.add_argument("--input-verification", type=str, default=str(VERIFICATION_REPORT_PATH), help="Path to verification_report.json")
    parser.add_argument("--input-tasks", type=str, default=str(SAMPLE_TASKS_PATH), help="Path to sample_tasks.json")
    parser.add_argument("--output", type=str, default=str(OUTPUT_PATH), help="Path to output blinded_ground_truth.json")
    args = parser.parse_args()

    try:
        # Load source data
        # We primarily need task IDs. We can get them from verification_report or sample_tasks.
        # Prefer sample_tasks if available to ensure we have the full list.
        if Path(args.input_tasks).exists():
            tasks_data = load_json(Path(args.input_tasks))
            task_ids = [t["task_id"] for t in tasks_data.get("tasks", [])]
        else:
            # Fallback to verification report
            ver_data = load_json(Path(args.input_verification))
            task_ids = [r["task_id"] for r in ver_data.get("results", [])]

        if not task_ids:
            print("Error: No task IDs found in input files.", file=sys.stderr)
            return 1

        # Construct blinded structure
        blinded_data = {
            "metadata": {
                "generated_at": "auto",
                "protocol": "Blinding Protocol v1.0",
                "description": "Manual inspection template. Verifier results removed."
            },
            "inspections": []
        }

        for tid in task_ids:
            blinded_data["inspections"].append(create_blinded_entry(tid))

        save_json(blinded_data, Path(args.output))
        print(f"Blinded ground truth template generated: {args.output}")
        return 0

    except Exception as e:
        print(f"Error generating blinded ground truth: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())