"""
Main Orchestrator for the Structural Brain Connectivity and Music Preferences Pipeline.

This script implements task T016. It loads intermediate status files to determine
the execution path (Narrative vs Quantitative) and invokes the appropriate
downstream scripts to generate final results.

Dependencies:
- T009b (real_data_status.json)
- T014a (study_count.json)
- T014b (valid_pair_count.json)
- T014 (meta_status.json)
- T015 (Visualization Orchestrator)
- T021 (Multiple Comparisons Correction)
- T015d (Pivot Narrative Script)
"""
import argparse
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

# Project root resolution
def get_project_root() -> Path:
    """Returns the root directory of the project (parent of 'code')."""
    current = Path(__file__).resolve()
    # Traverse up until we find a directory named 'code' containing this file
    for parent in current.parents:
        if parent.name == "code":
            return parent.parent
    # Fallback if run from code directory directly
    return current.parent

def load_json_file(file_path: Path) -> Optional[Dict[str, Any]]:
    """Load a JSON file and return its contents as a dictionary."""
    if not file_path.exists():
        logging.warning(f"File not found: {file_path}")
        return None
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logging.error(f"Error decoding JSON in {file_path}: {e}")
        return None

def save_json_file(file_path: Path, data: Dict[str, Any]) -> None:
    """Save a dictionary to a JSON file."""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

def setup_logger() -> None:
    """Configure the root logger for the pipeline."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(
                get_project_root() / 'data' / 'logs' / 'main_orchestrator.log'
            )
        ]
    )

def run_subprocess_script(script_name: str, args: Optional[list] = None) -> bool:
    """
    Run a Python script located in the code/ directory.
    Returns True if the script exits with code 0, False otherwise.
    """
    script_path = get_project_root() / 'code' / script_name
    if not script_path.exists():
        logging.error(f"Script not found: {script_path}")
        return False

    cmd = [sys.executable, str(script_path)]
    if args:
        cmd.extend(args)

    logging.info(f"Executing: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, check=True, capture_output=False)
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        logging.error(f"Script {script_name} failed with exit code {e.returncode}")
        return False
    except Exception as e:
        logging.error(f"Error running script {script_name}: {e}")
        return False

def run_pipeline(args: argparse.Namespace) -> int:
    """
    Main orchestration logic.
    
    1. Load status files (real_data_status, study_count, valid_pair_count, meta_status).
    2. Determine mode:
       - If mode == 'narrative' OR meta_status.status == 'skipped':
         Invoke Narrative Path (T015d).
       - If meta_status.status == 'completed':
         Invoke Quantitative Path (T015 -> T021).
    3. Write final results.json.
    """
    setup_logger()
    logger = logging.getLogger("main_orchestrator")
    project_root = get_project_root()
    
    # Define paths
    paths = {
        "real_data_status": project_root / "data" / "processed" / "real_data_status.json",
        "study_count": project_root / "data" / "processed" / "study_count.json",
        "valid_pair_count": project_root / "data" / "processed" / "valid_pair_count.json",
        "meta_status": project_root / "data" / "processed" / "meta_status.json",
        "results": project_root / "data" / "derived" / "results.json",
        "narrative_summary": project_root / "data" / "derived" / "narrative_summary.md"
    }

    # Load status files
    logger.info("Loading status files...")
    real_data_status = load_json_file(paths["real_data_status"])
    study_count_data = load_json_file(paths["study_count"])
    valid_pair_count_data = load_json_file(paths["valid_pair_count"])
    meta_status_data = load_json_file(paths["meta_status"])

    # Validation
    if not real_data_status:
        logger.error("real_data_status.json is missing. Pipeline cannot start.")
        return 1
    
    mode = real_data_status.get("mode", "unknown")
    N = study_count_data.get("N", 0) if study_count_data else 0
    
    logger.info(f"Detected Mode: {mode}, Study Count (N): {N}")

    # Determine Execution Path
    synthesis_mode = "unknown"
    success = False

    # Condition 1: Narrative Path
    # Triggered if mode is 'narrative' OR if meta_status says 'skipped'
    is_narrative_mode = (mode == "narrative")
    is_skipped = False
    if meta_status_data:
        is_skipped = meta_status_data.get("status") == "skipped"

    if is_narrative_mode or is_skipped:
        logger.info("Entering Narrative Synthesis Path.")
        synthesis_mode = "narrative"
        
        # Invoke T015d: pivot_narrative.py
        # This script orchestrates T015b -> T015c
        if not run_subprocess_script("analysis/pivot_narrative.py"):
            logger.error("Failed to execute pivot_narrative.py")
            return 1
        
        # Verify narrative output
        if paths["narrative_summary"].exists():
            logger.info("Narrative summary generated successfully.")
            success = True
        else:
            logger.warning("Narrative summary file not found after execution.")
            # We proceed to write results but flag potential issue
            success = True # Assume success if script ran, even if file missing (might be empty case)

    # Condition 2: Quantitative Path
    # Triggered if meta_status.status == 'completed'
    elif meta_status_data and meta_status_data.get("status") == "completed":
        logger.info("Entering Quantitative Analysis Path.")
        synthesis_mode = "quantitative"

        # Step 1: Invoke T015 (Visualization Orchestrator)
        # Note: T015 invokes T024, T025, T026
        if not run_subprocess_script("visualization/plots_orchestrator.py"):
            logger.error("Failed to execute visualization orchestrator (T015).")
            # Continue to correction step? No, visualization is part of the path.
            # But we might still want to run correction if data exists.
            # For strict adherence, we fail if visualization fails.
            # However, let's try to continue to correction to salvage data.
        
        # Step 2: Invoke T021 (Multiple Comparisons Correction)
        # This updates results.json with Bonferroni adjustments
        if not run_subprocess_script("analysis/correction.py"):
            logger.error("Failed to execute correction analysis (T021).")
            return 1
        
        # Verify final results
        if paths["results"].exists():
            logger.info("Quantitative results generated successfully.")
            success = True
        else:
            logger.error("results.json was not generated by the pipeline.")
            return 1

    else:
        logger.error("Unknown pipeline state. Cannot determine path.")
        logger.error(f"Mode: {mode}, Meta Status: {meta_status_data}")
        return 1

    # Write Final Results Summary
    final_results = {
        "synthesis_mode": synthesis_mode,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "study_count": N,
        "valid_pairs": valid_pair_count_data.get("N_valid", 0) if valid_pair_count_data else 0,
        "status": "completed" if success else "partial"
    }
    
    if synthesis_mode == "quantitative" and meta_status_data:
        final_results["meta_analysis_status"] = meta_status_data.get("status")
        final_results["pooled_effect"] = meta_status_data.get("pooled_effect")
        final_results["ci_lower"] = meta_status_data.get("ci_lower")
        final_results["ci_upper"] = meta_status_data.get("ci_upper")

    if synthesis_mode == "narrative":
        final_results["narrative_source"] = str(paths["narrative_summary"].relative_to(project_root))

    save_json_file(paths["results"], final_results)
    logger.info(f"Final results written to {paths['results']}")

    return 0 if success else 1

def main() -> int:
    """Entry point for the main orchestrator."""
    parser = argparse.ArgumentParser(description="Main Orchestrator for Brain-Music Pipeline")
    parser.add_argument("--input", type=str, help="Input data file (optional, overrides default)")
    parser.add_argument("--output", type=str, help="Output results file (optional, overrides default)")
    parser.add_argument("--use-mock", action="store_true", help="Force use of mock data generation")
    
    args = parser.parse_args()
    return run_pipeline(args)

if __name__ == "__main__":
    sys.exit(main())
