"""
Pivot Narrative Script (Task T015d).

Orchestrates the narrative synthesis path when quantitative analysis is skipped
or insufficient data is detected.

Steps:
1. Invoke T015b (Narrative Synthesis Engine)
2. Invoke T015c (Generate Narrative Summary)

Output: data/derived/narrative_summary.md
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
            logging.FileHandler(get_project_root() / 'data' / 'logs' / 'pivot_narrative.log')
        ]
    )
    logger = logging.getLogger("pivot_narrative")
    logger.info("Starting Narrative Pivot (T015d)")

    # Step 1: T015b - Narrative Synthesis Engine
    # This generates narrative_content.md
    if not run_script("analysis/narrative_engine.py"):
        logger.error("Failed to run narrative engine (T015b)")
        return 1

    # Step 2: T015c - Generate Narrative Summary
    # This generates narrative_summary.md from narrative_content.md
    if not run_script("analysis/narrative.py"):
        logger.error("Failed to run narrative generator (T015c)")
        return 1

    # Verify output
    output_path = get_project_root() / "data" / "derived" / "narrative_summary.md"
    if output_path.exists():
        logger.info(f"Narrative summary generated: {output_path}")
        return 0
    else:
        logger.error("Narrative summary file not found.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
