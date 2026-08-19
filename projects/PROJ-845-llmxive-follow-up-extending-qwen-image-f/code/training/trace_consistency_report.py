import os
import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

# Import existing utilities
from utils.logger import get_logger
from config import get_config

logger = get_logger("trace_consistency_report")
config = get_config()

def load_distillation_runs(
    processed_dir: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Load all DistillationRun JSON files from the processed directory.
    Returns a list of dicts, each representing a run.
    """
    if processed_dir is None:
        processed_dir = config.processed_dir

    processed_path = Path(processed_dir)
    if not processed_path.exists():
        logger.warning(f"Processed directory {processed_dir} does not exist.")
        return []

    run_files = list(processed_path.glob("*_run.json"))
    runs = []
    for rf in run_files:
        try:
            with open(rf, "r", encoding="utf-8") as f:
                data = json.load(f)
                runs.append(data)
                logger.info(f"Loaded run: {rf.name}")
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Failed to load {rf.name}: {e}")
    return runs

def aggregate_statistics(
    runs: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Aggregate statistics from a list of distillation runs.
    Computes total samples, filtered counts per entropy subset, and pass/fail status.
    """
    total_samples = 0
    filtered_counts = {"high": 0, "low": 0, "target": 0}
    total_filtered = 0
    failed_runs = []
    passed_runs = []

    for run in runs:
        entropy_subset = run.get("entropy_subset", "unknown")
        status = run.get("status", "unknown")
        samples_in_run = run.get("total_samples", 0)
        filtered_in_run = run.get("filtered_samples", 0)

        total_samples += samples_in_run
        total_filtered += filtered_in_run

        if entropy_subset in filtered_counts:
            filtered_counts[entropy_subset] += filtered_in_run
        else:
            logger.warning(f"Unknown entropy subset in run: {entropy_subset}")

        if status == "failed_non_converge":
            failed_runs.append(run.get("run_id", "unknown"))
        else:
            passed_runs.append(run.get("run_id", "unknown"))

    overall_pass = len(failed_runs) == 0
    pass_rate = len(passed_runs) / len(runs) if runs else 0.0

    return {
        "total_samples": total_samples,
        "total_filtered": total_filtered,
        "filtered_by_subset": filtered_counts,
        "run_summary": {
            "total_runs": len(runs),
            "passed_runs": passed_runs,
            "failed_runs": failed_runs,
            "pass_rate": pass_rate,
        },
        "fr_009_compliance": overall_pass,
    }

def generate_report(
    stats: Dict[str, Any],
    output_path: str,
) -> None:
    """
    Generate the trace consistency report JSON file.
    """
    report = {
        "generated_at": datetime.utcnow().isoformat(),
        "config": {
            "seed": config.seed,
            "max_ram_gb": config.max_ram_gb,
            "max_runtime_hours": config.max_runtime_hours,
        },
        "statistics": stats,
        "fr_009_status": (
            "PASS" if stats["fr_009_compliance"] else "FAIL"
        ),
    }

    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    logger.info(f"Report written to {output_file}")

def main() -> None:
    """
    Main entry point for generating the trace consistency report.
    """
    logger.info("Starting trace consistency report generation.")

    # Load distillation runs
    runs = load_distillation_runs()
    if not runs:
        logger.error("No distillation runs found. Cannot generate report.")
        sys.exit(1)

    logger.info(f"Found {len(runs)} distillation runs.")

    # Aggregate statistics
    stats = aggregate_statistics(runs)

    # Generate report
    output_path = os.path.join(config.processed_dir, "trace_consistency_report.json")
    generate_report(stats, output_path)

    logger.info("Trace consistency report generation complete.")
    sys.exit(0)

if __name__ == "__main__":
    main()
