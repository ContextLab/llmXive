"""
Visualization Orchestrator (Task T015).

Orchestrates the generation of visualization artifacts after a successful
quantitative meta-analysis.

Workflow:
1. Check `data/processed/meta_status.json` for status == "completed".
2. If completed, invoke T024 (Forest Plot), T025 (Funnel Plot), T026 (Correlation Plot).
3. Write `data/derived/visualization_status.json` with results.
"""
import json
import logging
import subprocess
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional

# Ensure we can import from the project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from utils.config import get_project_root, ensure_directory, get_output_path

logger = logging.getLogger(__name__)

META_STATUS_PATH = "data/processed/meta_status.json"
VISUALIZATION_STATUS_PATH = "data/derived/visualization_status.json"
RESULTS_PATH = "data/derived/results.json"

# Scripts to invoke
SCRIPTS = [
    ("code/visualization/plots_forest.py", "forest_plot.png"),
    ("code/visualization/plots_funnel.py", "funnel_plot.png"),
    ("code/visualization/plots_correlation.py", "correlation_summary.png"),
]

def load_json(path: str) -> Optional[Dict[str, Any]]:
    full_path = get_project_root() / path
    if not full_path.exists():
        return None
    with open(full_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json(path: str, data: Dict[str, Any]) -> None:
    full_path = get_project_root() / path
    ensure_directory(full_path)
    with open(full_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

def run_script(script_rel_path: str) -> bool:
    """Execute a visualization script and return True if it exits with 0."""
    script_path = get_project_root() / script_rel_path
    if not script_path.exists():
        logger.error(f"Script not found: {script_path}")
        return False

    try:
        # Run as a subprocess to avoid circular imports and state pollution
        result = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            timeout=300  # 5 minutes timeout per plot
        )
        if result.returncode != 0:
            logger.error(f"Script {script_rel_path} failed:\n{result.stderr}")
            return False
        return True
    except subprocess.TimeoutExpired:
        logger.error(f"Script {script_rel_path} timed out.")
        return False
    except Exception as e:
        logger.error(f"Error running {script_rel_path}: {e}")
        return False

def run_visualization_orchestrator() -> Dict[str, Any]:
    """
    Main logic for T015.
    Returns the status dictionary to be saved.
    """
    project_root = get_project_root()
    status = {
        "status": "skipped",
        "reason": "Meta-analysis not completed",
        "plots_generated": [],
        "plots_failed": [],
        "timestamp": None
    }

    # 1. Check Meta-Analysis Status
    meta_status = load_json(META_STATUS_PATH)
    if not meta_status:
        logger.warning(f"{META_STATUS_PATH} not found. Skipping visualization.")
        status["reason"] = f"File not found: {META_STATUS_PATH}"
        save_json(VISUALIZATION_STATUS_PATH, status)
        return status

    if meta_status.get("status") != "completed":
        logger.info(f"Meta-analysis status is '{meta_status.get('status')}'. Skipping visualization.")
        status["reason"] = f"Meta-analysis status is '{meta_status.get('status')}'"
        save_json(VISUALIZATION_STATUS_PATH, status)
        return status

    # 2. Run Plots
    logger.info("Meta-analysis completed. Starting visualization generation...")
    status["status"] = "completed"
    status["plots_generated"] = []
    status["plots_failed"] = []

    for script_path, output_file in SCRIPTS:
        logger.info(f"Generating {output_file}...")
        success = run_script(script_path)
        if success:
            # Verify output file exists
            output_path = project_root / output_file
            if output_path.exists():
                status["plots_generated"].append(output_file)
                logger.info(f"Successfully generated {output_file}")
            else:
                logger.warning(f"Script succeeded but output file missing: {output_file}")
                status["plots_failed"].append(output_file)
        else:
            status["plots_failed"].append(output_file)
            logger.error(f"Failed to generate {output_file}")

    # Determine overall status
    if status["plots_failed"]:
        status["status"] = "partial"
        status["reason"] = f"Failed to generate: {', '.join(status['plots_failed'])}"
    else:
        status["reason"] = "All visualizations generated successfully"

    status["timestamp"] = subprocess.run(
        ["date", "-Iseconds"],
        capture_output=True,
        text=True
    ).stdout.strip() if sys.platform != "win32" else "N/A"

    # 3. Save Status
    save_json(VISUALIZATION_STATUS_PATH, status)
    logger.info(f"Visualization status saved to {VISUALIZATION_STATUS_PATH}")

    return status

def main() -> int:
    """CLI entry point."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    try:
        run_visualization_orchestrator()
        return 0
    except Exception as e:
        logger.error(f"Orchestrator failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
