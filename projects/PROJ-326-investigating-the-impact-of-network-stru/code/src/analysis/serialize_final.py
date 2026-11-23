"""
Final serialization script that aggregates all results into final_results.json.
Implements T037d: Aggregates results from T037b (statistics) and T037c (figures),
and saves data/analysis/final_results.json with strict schema adherence.
"""
import json
import logging
import os
import sys
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
        logger.warning(f"Cannot count excluded runs: {simulation_results_path} not found")
        return 0
        
    if isinstance(data, list):
        records = data
    elif isinstance(data, dict) and "results" in data:
        records = data["results"]
    elif isinstance(data, dict) and "records" in data:
        records = data["records"]
    else:
        # Single record case
        records = [data]
        
    excluded = 0
    for r in records:
        if not isinstance(r, dict):
            continue
        status = r.get("status", "")
        if "[SIMULATION_DIVERGENCE]" in str(status) or "[DISCONNECTED_NETWORK_FAILURE]" in str(status):
            excluded += 1
    return excluded

def collect_figures_generated(figures_dir: str) -> List[str]:
    """Collect list of generated figure files (PNGs)."""
    fig_path = Path(figures_dir)
    if not fig_path.exists():
        logger.warning(f"Figures directory not found: {figures_dir}")
        return []
    png_files = [f.name for f in fig_path.glob("*.png")]
    logger.info(f"Found {len(png_files)} figures in {figures_dir}")
    return png_files

def aggregate_final_results(
    regression: Optional[Dict], 
    anova: Optional[Dict], 
    sensitivity: Optional[Dict], 
    figures: List[str], 
    excluded: int
) -> Dict[str, Any]:
    """
    Construct the final results dictionary adhering to strict schema.
    Schema: { "regression_results": {}, "anova_results": {}, "sensitivity_results": {}, "figures_generated": [], "excluded_runs_count": int }
    NOTE: No extra fields like 'timestamp' are included.
    """
    # Extract sensitivity results if available
    sens_results = []
    if sensitivity:
        if isinstance(sensitivity, list):
            sens_results = sensitivity
        elif isinstance(sensitivity, dict):
            sens_results = sensitivity.get("results", sensitivity.get("sensitivity_data", []))
    
    # Extract regression/anova from stats if they are nested
    reg_data = regression
    anova_data = anova
    
    return {
        "regression_results": reg_data if reg_data else {},
        "anova_results": anova_data if anova_data else {},
        "sensitivity_results": sens_results,
        "figures_generated": figures,
        "excluded_runs_count": excluded
    }

def main():
    """Main entry point for final serialization."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Serialize final analysis results (T037d)")
    parser.add_argument("--config", type=str, default="code/config.yaml", help="Path to config")
    parser.add_argument("--output", type=str, default="data", help="Output directory")
    args = parser.parse_args()
    
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    output_path = Path(args.output)
    analysis_dir = output_path / "analysis"
    analysis_dir.mkdir(parents=True, exist_ok=True)
    
    # Define paths based on task dependencies
    # T037b output: data/analysis/statistical_outputs.json
    stats_path = analysis_dir / "statistical_outputs.json"
    # T035c/T037b upstream: data/analysis/sensitivity_sweep.json (or sensitivity_correlation.json)
    sensitivity_path = analysis_dir / "sensitivity_sweep.json"
    # T029 output: data/analysis/simulation_results.json (for counting exclusions)
    simulation_results_path = analysis_dir / "simulation_results.json"
    # T037c output: figures in paper/ or data/analysis/figures
    # Based on T037c description: "saving them to paper/"
    figures_dir = Path("paper") 
    if not figures_dir.exists():
        # Fallback to common analysis figures dir if paper/ doesn't exist
        figures_dir = analysis_dir / "figures"
    
    logger.info(f"Loading statistical results from {stats_path}")
    stats_data = load_json_file(str(stats_path))
    
    logger.info(f"Loading sensitivity results from {sensitivity_path}")
    sensitivity_data = load_json_file(str(sensitivity_path))
    
    logger.info(f"Collecting figures from {figures_dir}")
    figures = collect_figures_generated(str(figures_dir))
    
    logger.info(f"Counting excluded runs from {simulation_results_path}")
    excluded = count_excluded_runs(str(simulation_results_path))
    
    # Validate upstream dependencies
    if not stats_data:
        logger.error("Critical: statistical_outputs.json (T037b) is missing or invalid. Cannot proceed.")
        sys.exit(1)
    
    # Extract components from stats_data
    regression_part = stats_data.get("regression_results") or stats_data.get("regression")
    anova_part = stats_data.get("anova_results") or stats_data.get("anova")
    
    final = aggregate_final_results(
        regression=regression_part,
        anova=anova_part,
        sensitivity=sensitivity_data,
        figures=figures,
        excluded=excluded
    )
    
    final_path = analysis_dir / "final_results.json"
    with open(final_path, 'w') as f:
        json.dump(final, f, indent=2)
        
    logger.info(f"Final results serialized to {final_path}")
    logger.info(f"Schema check: regression={bool(final['regression_results'])}, anova={bool(final['anova_results'])}, figures={len(final['figures_generated'])}, excluded={final['excluded_runs_count']}")

if __name__ == "__main__":
    main()
