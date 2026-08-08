import os
import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

from utils.logger import get_logger

logger = get_logger(__name__)

def load_distillation_runs(
    processed_dir: Optional[Path] = None,
    entropy_subsets: List[str] = None,
) -> Dict[str, Dict[str, Any]]:
    """
    Load all distillation run JSON files from the processed directory.
    
    Args:
        processed_dir: Path to data/processed directory. Defaults to 'data/processed'.
        entropy_subsets: List of entropy subset names to look for (e.g., ['high', 'low', 'target']).
    
    Returns:
        Dictionary mapping subset name to run data.
    """
    if entropy_subsets is None:
        entropy_subsets = ["high", "low", "target"]
    
    if processed_dir is None:
        processed_dir = Path("data/processed")
    
    runs = {}
    
    if not processed_dir.exists():
        logger.warning(f"Processed directory {processed_dir} does not exist.")
        return runs
    
    for subset in entropy_subsets:
        # Look for files matching pattern: distillation_run_{subset}.json
        pattern = f"distillation_run_{subset}.json"
        files = list(processed_dir.glob(pattern))
        
        if not files:
            logger.warning(f"No distillation run found for subset '{subset}' matching pattern '{pattern}'")
            continue
        
        # Take the most recent file if multiple exist
        latest_file = max(files, key=lambda f: f.stat().st_mtime)
        
        try:
            with open(latest_file, "r", encoding="utf-8") as f:
                run_data = json.load(f)
                runs[subset] = run_data
                logger.info(f"Loaded distillation run for '{subset}' from {latest_file}")
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Failed to load {latest_file}: {e}")
            continue
    
    return runs

def aggregate_statistics(
    runs: Dict[str, Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Aggregate statistics from multiple distillation runs.
    
    Args:
        runs: Dictionary of run data per entropy subset.
    
    Returns:
        Aggregated statistics dictionary.
    """
    total_samples = 0
    filtered_samples = 0
    subset_stats = {}
    all_passed = True
    
    for subset_name, run_data in runs.items():
        subset_total = run_data.get("total_samples", 0)
        subset_filtered = run_data.get("filtered_samples", 0)
        status = run_data.get("status", "unknown")
        
        subset_stats[subset_name] = {
            "total_samples": subset_total,
            "filtered_samples": subset_filtered,
            "status": status,
            "pass_rate": (subset_total - subset_filtered) / subset_total if subset_total > 0 else 0.0,
        }
        
        total_samples += subset_total
        filtered_samples += subset_filtered
        
        # FR-009: Check if run status indicates failure
        if status in ["failed_non_converge", "failed", "error"]:
            all_passed = False
            logger.warning(f"Run for subset '{subset_name}' did not pass: status={status}")
    
    overall_pass_rate = (total_samples - filtered_samples) / total_samples if total_samples > 0 else 0.0
    
    return {
        "total_samples": total_samples,
        "total_filtered": filtered_samples,
        "overall_pass_rate": overall_pass_rate,
        "all_runs_passed": all_passed,
        "subset_details": subset_stats,
    }

def generate_report(
    stats: Dict[str, Any],
    output_path: Path,
) -> None:
    """
    Generate the trace consistency report JSON file.
    
    Args:
        stats: Aggregated statistics from aggregate_statistics().
        output_path: Path where the report JSON will be written.
    """
    report = {
        "report_type": "trace_consistency_report",
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "summary": {
            "total_samples": stats["total_samples"],
            "total_filtered": stats["total_filtered"],
            "overall_pass_rate": stats["overall_pass_rate"],
            "fr_009_status": "PASS" if stats["all_runs_passed"] else "FAIL",
            "conclusion": (
                "All distillation runs passed trace consistency checks."
                if stats["all_runs_passed"]
                else "One or more distillation runs failed trace consistency checks."
            ),
        },
        "subset_statistics": stats["subset_details"],
    }
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Trace consistency report written to {output_path}")

def main():
    """
    Main entry point for generating the trace consistency report.
    
    This script loads all distillation runs from data/processed/,
    aggregates their statistics, and writes a validation report
    to data/processed/trace_consistency_report.json.
    """
    logger.info("Starting trace consistency report generation...")
    
    processed_dir = Path("data/processed")
    output_path = processed_dir / "trace_consistency_report.json"
    
    # Define the entropy subsets we expect
    entropy_subsets = ["high", "low", "target"]
    
    # Load distillation runs
    runs = load_distillation_runs(processed_dir, entropy_subsets)
    
    if not runs:
        logger.error("No distillation runs found. Cannot generate report.")
        # Still generate a report indicating failure
        stats = {
            "total_samples": 0,
            "total_filtered": 0,
            "overall_pass_rate": 0.0,
            "all_runs_passed": False,
            "subset_details": {},
        }
        generate_report(stats, output_path)
        sys.exit(1)
    
    # Aggregate statistics
    stats = aggregate_statistics(runs)
    
    # Generate report
    generate_report(stats, output_path)
    
    # Exit with appropriate code based on FR-009 status
    if stats["all_runs_passed"]:
        logger.info("Trace consistency report generation completed successfully.")
        sys.exit(0)
    else:
        logger.warning("Trace consistency report generated, but FR-009 check failed.")
        sys.exit(0)  # Report generated, but status is FAIL (logged)

if __name__ == "__main__":
    main()