"""
Visualization Orchestrator (Task T015).

This script invokes the specific plot generators (Forest, Funnel, Correlation)
after a successful quantitative meta-analysis.

Dependencies:
- T024 (Forest Plot)
- T025 (Funnel Plot)
- T026 (Correlation Plot)
- T042 (Memory Safe Utilities)
"""
import logging
import sys
import subprocess
from pathlib import Path

def get_project_root() -> Path:
    current = Path(__file__).resolve()
    for parent in current.parents:
        if parent.name == "code":
            return parent.parent
    return current.parent

def run_script(script_rel_path: str) -> bool:
    script_path = get_project_root() / script_rel_path
    if not script_path.exists():
        logging.error(f"Script not found: {script_path}")
        return False
    
    cmd = [sys.executable, str(script_path)]
    logging.info(f"Running: {' '.join(cmd)}")
    try:
        subprocess.run(cmd, check=True, capture_output=False)
        return True
    except subprocess.CalledProcessError as e:
        logging.error(f"Script {script_rel_path} failed: {e}")
        return False

def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(get_project_root() / 'data' / 'logs' / 'visualization_orchestrator.log')
        ]
    )
    logger = logging.getLogger("viz_orchestrator")
    logger.info("Starting Visualization Orchestrator (T015)")

    # Define the sequence of plots
    plots = [
        "visualization/plots_forest.py",
        "visualization/plots_funnel.py",
        "visualization/plots_correlation.py"
    ]

    success_count = 0
    for plot_script in plots:
        if run_script(plot_script):
            success_count += 1
        else:
            logger.warning(f"Failed to generate plot from {plot_script}")

    # Write status
    status = {
        "status": "completed" if success_count == len(plots) else "partial",
        "plots_generated": success_count,
        "total_plots": len(plots)
    }
    
    results_path = get_project_root() / "data" / "derived" / "visualization_status.json"
    results_path.parent.mkdir(parents=True, exist_ok=True)
    import json
    with open(results_path, 'w') as f:
        json.dump(status, f, indent=2)
    
    logger.info(f"Visualization status written to {results_path}")
    return 0 if success_count == len(plots) else 1

if __name__ == "__main__":
    sys.exit(main())
