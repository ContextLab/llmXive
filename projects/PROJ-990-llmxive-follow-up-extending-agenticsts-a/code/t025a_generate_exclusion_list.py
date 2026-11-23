"""
Task T025a: Generate Exclusion List.

If is_paired is false (from T024), log a warning and produce
data/processed/exclusion_report.json containing is_paired, valid_trajectory_ids,
excluded_trajectory_ids, and divergence_rate.

Depends on: T024 (data/processed/paired_status.json)
"""
import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, List

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_paired_status(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Paired status file not found: {path}")
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def generate_exclusion_report(paired_status: Dict[str, Any]) -> Dict[str, Any]:
    is_paired = paired_status.get("is_paired", False)
    valid_ids = paired_status.get("valid_trajectory_ids", [])
    excluded_ids = paired_status.get("excluded_trajectory_ids", [])
    
    total_ids = len(valid_ids) + len(excluded_ids)
    divergence_rate = len(excluded_ids) / total_ids if total_ids > 0 else 0.0

    report = {
        "is_paired": is_paired,
        "valid_trajectory_ids": valid_ids,
        "excluded_trajectory_ids": excluded_ids,
        "divergence_rate": divergence_rate,
        "total_trajectories_checked": total_ids,
        "warning": "Divergence detected between dynamic and static simulation logs." if not is_paired else "No divergence detected."
    }

    if not is_paired:
        logger.warning(f"Divergence rate: {divergence_rate:.4f}. {len(excluded_ids)} trajectories excluded.")
    else:
        logger.info("No divergence detected. All trajectories are valid.")

    return report

def main():
    project_root = Path(__file__).resolve().parent.parent
    input_path = project_root / "data" / "processed" / "paired_status.json"
    output_path = project_root / "data" / "processed" / "exclusion_report.json"

    try:
        paired_status = load_paired_status(input_path)
        report = generate_exclusion_report(paired_status)
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Exclusion report written to: {output_path}")
        return 0
    except FileNotFoundError as e:
        logger.error(f"T025a FAILED: {e}")
        return 1
    except Exception as e:
        logger.error(f"T025a FAILED: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
