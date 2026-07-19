"""
Final serialization script that aggregates all results into final_results.json.
"""
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

def load_json_file(path: str) -> Optional[Dict[str, Any]]:
    """Load a JSON file, returning None if not found."""
    p = Path(path)
    if not p.exists():
        logger.warning(f"File not found: {path}")
        return None
    try:
        with open(p, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load {path}: {e}")
        return None

def count_excluded_runs(simulation_results_path: str) -> int:
    """Count runs excluded due to divergence or disconnection."""
    data = load_json_file(simulation_results_path)
    if not data:
        return 0
        
    if isinstance(data, list):
        records = data
    elif isinstance(data, dict) and "results" in data:
        records = data["results"]
    else:
        records = [data]
        
    excluded = 0
    for r in records:
        status = r.get("status", "")
        if "[SIMULATION_DIVERGENCE]" in status or "[DISCONNECTED_NETWORK_FAILURE]" in status:
            excluded += 1
    return excluded

def collect_figures_generated(figures_dir: str) -> List[str]:
    """Collect list of generated figure files."""
    fig_path = Path(figures_dir)
    if not fig_path.exists():
        return []
    return [f.name for f in fig_path.glob("*.png")]

def aggregate_final_results(regression: Optional[Dict], anova: Optional[Dict], sensitivity: Optional[Dict], figures: List[str], excluded: int) -> Dict[str, Any]:
    """Construct the final results dictionary."""
    return {
        "timestamp": datetime.now().isoformat(),
        "regression_results": regression or {"status": "skipped"},
        "anova_results": anova or {"status": "skipped"},
        "sensitivity_results": sensitivity.get("results", []) if sensitivity else [],
        "figures_generated": figures,
        "excluded_runs_count": excluded
    }

def main():
    """Main entry point for final serialization."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Serialize final analysis results")
    parser.add_argument("--config", type=str, default="code/config.yaml", help="Path to config")
    parser.add_argument("--output", type=str, default="data", help="Output directory")
    args = parser.parse_args()
    
    logging.basicConfig(level=logging.INFO)
    
    output_path = Path(args.output)
    analysis_dir = output_path / "analysis"
    
    # Load intermediate results
    stats_path = analysis_dir / "statistical_outputs.json"
    sensitivity_path = analysis_dir / "sensitivity_sweep.json"
    simulation_results_path = analysis_dir / "simulation_results.json"
    figures_dir = output_path.parent / "paper"  # or output_path / "figures"
    
    stats_data = load_json_file(str(stats_path))
    sensitivity_data = load_json_file(str(sensitivity_path))
    
    figures = collect_figures_generated(str(figures_dir))
    excluded = count_excluded_runs(str(simulation_results_path))
    
    final = aggregate_final_results(
        regression=stats_data.get("regression") if stats_data else None,
        anova=stats_data.get("anova") if stats_data else None,
        sensitivity=sensitivity_data,
        figures=figures,
        excluded=excluded
    )
    
    final_path = analysis_dir / "final_results.json"
    with open(final_path, 'w') as f:
        json.dump(final, f, indent=2)
        
    logger.info(f"Final results serialized to {final_path}")

if __name__ == "__main__":
    main()
