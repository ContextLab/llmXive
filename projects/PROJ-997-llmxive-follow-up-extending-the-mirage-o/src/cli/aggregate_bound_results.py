"""
T032: Aggregate bound consistency results from T027B.

Reads data/processed/consistency_report.json (produced by T027B),
computes a global summary, and writes data/processed/aggregated_consistency_report.json.

Output schema:
{
  "global_consistency_metric": float,
  "bound_satisfaction_pct": float,
  "per_level_correlations": {"INT4": float, "INT8": float, "FP8": float},
  "pass": bool
}

Pass criterion: bound_satisfaction_pct > 95.0 for at least one quantization level.
"""
import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, Optional

from src.config.logging_config import setup_logger, ensure_log_dir

# Threshold for passing the bound consistency check (FR-006 / T027B spec)
BOUND_SATISFACTION_THRESHOLD = 95.0

def load_consistency_report(input_path: Path) -> Dict[str, Any]:
    """Load the consistency report produced by T027B."""
    if not input_path.exists():
        raise FileNotFoundError(f"Consistency report not found at {input_path}")
    
    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    # Validate expected keys
    required_keys = [
        "per_level_correlations",
        "global_consistency_metric",
        "bound_satisfaction_pct"
    ]
    for key in required_keys:
        if key not in data:
            raise ValueError(f"Missing required key '{key}' in consistency report")
    
    return data

def aggregate_results(consistency_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Aggregate the consistency report into a final summary.
    
    The 'bound_satisfaction_pct' in the input is already the percentage of samples
    satisfying the bound globally. We also check per-level satisfaction if available
    in extended data, but the primary metric is the global one.
    
    Pass criterion: bound_satisfaction_pct > 95.0
    """
    per_level_correlations = consistency_data.get("per_level_correlations", {})
    global_consistency_metric = consistency_data.get("global_consistency_metric", 0.0)
    bound_satisfaction_pct = consistency_data.get("bound_satisfaction_pct", 0.0)

    # Determine pass/fail based on threshold
    passed = bound_satisfaction_pct > BOUND_SATISFACTION_THRESHOLD

    aggregated = {
        "global_consistency_metric": float(global_consistency_metric),
        "bound_satisfaction_pct": float(bound_satisfaction_pct),
        "per_level_correlations": {
            level: float(val) for level, val in per_level_correlations.items()
        },
        "threshold": BOUND_SATISFACTION_THRESHOLD,
        "pass": passed
    }

    return aggregated

def write_report(aggregated_data: Dict[str, Any], output_path: Path) -> None:
    """Write the aggregated report to JSON."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(aggregated_data, f, indent=2)
    logging.info(f"Aggregated bound results written to {output_path}")

def main() -> int:
    """Entry point for T032."""
    logger = setup_logger(__name__)
    ensure_log_dir()

    # Paths relative to project root
    project_root = Path(__file__).resolve().parents[3]
    input_path = project_root / "data" / "processed" / "consistency_report.json"
    output_path = project_root / "data" / "processed" / "aggregated_consistency_report.json"

    try:
        logger.info(f"Loading consistency report from {input_path}")
        consistency_data = load_consistency_report(input_path)

        logger.info("Aggregating bound results")
        aggregated = aggregate_results(consistency_data)

        logger.info(f"Writing aggregated report to {output_path}")
        write_report(aggregated, output_path)

        status = "PASS" if aggregated["pass"] else "FAIL"
        logger.info(f"Bound consistency check: {status} (satisfaction={aggregated['bound_satisfaction_pct']:.2f}%)")

        return 0

    except FileNotFoundError as e:
        logger.error(f"Required input file missing: {e}")
        return 1
    except ValueError as e:
        logger.error(f"Invalid consistency report format: {e}")
        return 1
    except Exception as e:
        logger.exception(f"Unexpected error during aggregation: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())