import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
import logging

from src.utils.config import get_results_path, get_project_root

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_json_safe(file_path: Path) -> Optional[Dict[str, Any]]:
    """Load a JSON file safely, returning None if it doesn't exist or is invalid."""
    if not file_path.exists():
        logger.warning(f"File not found: {file_path}")
        return None
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to decode JSON from {file_path}: {e}")
        return None

def aggregate_results(
    stats_data: Optional[Dict[str, Any]],
    sensitivity_data: Optional[Dict[str, Any]],
    linearity_data: Optional[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Aggregate results from stats, sensitivity, and linearity checks into a single report.
    """
    report = {
        "status": "completed",
        "summary": {
            "total_strategies_compared": 0,
            "best_strategy": None,
            "linearity_validated": False,
            "sensitivity_sweep_completed": False
        },
        "statistical_analysis": {},
        "sensitivity_analysis": {},
        "linearity_analysis": {}
    }

    if stats_data:
        report["statistical_analysis"] = stats_data
        # Determine best strategy based on success rate and BH correction
        comparisons = stats_data.get("comparisons", [])
        if comparisons:
            # Simple heuristic: look for highest success rate in the 'results'
            # assuming the stats module outputs a structure with success rates
            best_score = -1
            best_strat = None
            for comp in comparisons:
                strat_name = comp.get("strategy_a") or comp.get("strategy_b")
                # Fallback logic to find the winner if structure varies
                if "winner" in comp:
                    best_strat = comp["winner"]
                    best_score = comp.get("success_rate", 0)
                    break
                # If no explicit winner, assume higher mean success rate wins
                mean_rate = comp.get("mean_success_rate", 0)
                if mean_rate > best_score:
                    best_score = mean_rate
                    best_strat = strat_name
            
            report["summary"]["total_strategies_compared"] = len(comparisons)
            if best_strat:
                report["summary"]["best_strategy"] = best_strat

    if sensitivity_data:
        report["sensitivity_analysis"] = sensitivity_data
        report["summary"]["sensitivity_sweep_completed"] = True

    if linearity_data:
        report["linearity_analysis"] = linearity_data
        # Check if correlation is significant (e.g., > 0.5)
        pearson_r = linearity_data.get("pearson_r", 0)
        report["summary"]["linearity_validated"] = abs(pearson_r) > 0.5

    return report

def main():
    """
    Generate the final stats report by aggregating results from previous steps.
    Reads from:
      - data/results/statistics.json (from T029a/T029b)
      - data/results/sensitivity.yaml (from T031b)
      - data/results/linearity_check.json (from T030)
    Writes to:
      - data/results/stats_report.json
    """
    root = get_project_root()
    results_path = get_results_path()
    
    # Ensure output directory exists
    results_path.mkdir(parents=True, exist_ok=True)

    # Define input paths
    stats_file = results_path / "statistics.json"
    sensitivity_file = results_path / "sensitivity.yaml"
    linearity_file = results_path / "linearity_check.json"

    # Load data
    stats_data = load_json_safe(stats_file)
    
    # Load sensitivity (handle YAML if json loader fails, though we expect JSON/YAML handling)
    sensitivity_data = None
    if sensitivity_file.exists():
        try:
            import yaml
            with open(sensitivity_file, 'r') as f:
                sensitivity_data = yaml.safe_load(f)
        except ImportError:
            logger.error("PyYAML not installed, cannot load sensitivity.yaml")
        except Exception as e:
            logger.error(f"Failed to load sensitivity file: {e}")

    # Load linearity
    linearity_data = load_json_safe(linearity_file)

    # Aggregate
    report = aggregate_results(stats_data, sensitivity_data, linearity_data)

    # Write final report
    output_file = results_path / "stats_report.json"
    with open(output_file, 'w') as f:
        json.dump(report, f, indent=2)

    logger.info(f"Final report generated at {output_file}")
    return report

if __name__ == "__main__":
    main()