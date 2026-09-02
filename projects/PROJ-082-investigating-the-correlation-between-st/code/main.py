"""
Main Orchestrator for the llmXive pipeline (T016).
Orchestrates the pipeline based on the gatekeeper decision.
"""
import argparse
import json
import logging
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

# Import utilities from the project's API surface
# Note: We use absolute imports relative to the project root 'code'
# assuming the script is run from the project root or code directory.
# To ensure compatibility with the provided API surface, we import from specific modules.
try:
    from utils.config import get_project_root, ensure_directory
except ImportError:
    # Fallback if run directly without package context
    from pathlib import Path
    def get_project_root():
        return Path(__file__).resolve().parent.parent
    def ensure_directory(path):
        Path(path).mkdir(parents=True, exist_ok=True)

def setup_logger(log_path: str) -> logging.Logger:
    """
    Sets up the logger. Ensures the log directory exists before creating the file handler.
    This fixes the FileNotFoundError observed in execution logs.
    """
    logger = logging.getLogger("main_orchestrator")
    logger.setLevel(logging.INFO)

    # Clear existing handlers to avoid duplicates in repeated runs
    if logger.handlers:
        logger.handlers.clear()

    # Ensure directory exists
    log_dir = Path(log_path).parent
    ensure_directory(log_dir)

    # File handler
    fh = logging.FileHandler(log_path)
    fh.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    return logger

def load_json_file(path: Path) -> Optional[Dict[str, Any]]:
    """Load a JSON file, returning None if it doesn't exist or is invalid."""
    if not path.exists():
        return None
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        logging.warning(f"Failed to load {path}: {e}")
        return None

def save_json_file(path: Path, data: Dict[str, Any]) -> None:
    """Save data to a JSON file."""
    ensure_directory(path.parent)
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)

def run_script(script_name: str, args: Optional[list] = None) -> bool:
    """
    Runs a Python script as a subprocess.
    Returns True if successful (exit code 0), False otherwise.
    """
    cmd = [sys.executable, script_name]
    if args:
        cmd.extend(args)
    
    logging.info(f"Running: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        if result.stdout:
            logging.info(result.stdout)
        if result.stderr:
            logging.warning(result.stderr)
        return True
    except subprocess.CalledProcessError as e:
        logging.error(f"Script {script_name} failed with exit code {e.returncode}")
        if e.stderr:
            logging.error(e.stderr)
        return False

def run_pipeline(args: argparse.Namespace) -> int:
    """
    Main pipeline orchestration logic.
    1. Load gate result.
    2. If narrative_required: Run narrative pipeline.
    3. If quantitative_ok: Run quantitative pipeline.
    4. Write final results.json.
    """
    project_root = get_project_root()
    data_dir = project_root / "data"
    derived_dir = data_dir / "derived"
    processed_dir = data_dir / "processed"
    logs_dir = data_dir / "logs"

    # Ensure directories exist
    ensure_directory(derived_dir)
    ensure_directory(processed_dir)
    ensure_directory(logs_dir)

    # Setup logger with the fixed path
    log_path = logs_dir / "main_orchestrator.log"
    logger = setup_logger(str(log_path))
    logger.info("Pipeline started.")

    # Paths to status files
    gate_path = derived_dir / "gate_result.json"
    study_count_path = processed_dir / "study_count.json"
    valid_pair_path = processed_dir / "valid_pair_count.json"
    meta_status_path = derived_dir / "meta_status.json"
    final_results_path = derived_dir / "results.json"

    # Load Gate Result
    gate_data = load_json_file(gate_path)
    if not gate_data:
        logger.error(f"Gate result file not found: {gate_path}. Cannot proceed.")
        return 1

    status = gate_data.get("status", "unknown")
    logger.info(f"Gate status: {status}")

    results_payload = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "synthesis_mode": "unknown",
        "gate_status": status
    }

    if status == "narrative_required":
        logger.info("Insufficient data for quantitative analysis. Running Narrative Pipeline.")
        results_payload["synthesis_mode"] = "narrative"
        
        # Run Narrative Pivot
        # T015d: pivot_narrative.py
        if not run_script("code/analysis/pivot_narrative.py"):
            logger.error("Narrative pivot failed.")
            results_payload["error"] = "Narrative pivot failed"
        else:
            logger.info("Narrative pipeline completed successfully.")
            # The pivot script should have generated narrative_summary.md
            # We assume success if the script ran.

    elif status == "quantitative_ok":
        logger.info("Sufficient data for quantitative analysis. Running Quantitative Pipeline.")
        results_payload["synthesis_mode"] = "quantitative"

        # 1. Meta-Analysis (T014)
        logger.info("Step 1: Running Meta-Analysis...")
        # Note: T014 checks gate_result internally, but we already know it's ok.
        # We run the script to ensure meta_results.json is generated/updated.
        if not run_script("code/analysis/meta_analysis.py"):
            logger.error("Meta-analysis failed.")
            results_payload["error"] = "Meta-analysis failed"
            # Even if meta fails, we might want to proceed or stop. 
            # Given the strictness, we stop quantitative flow but save status.
            save_json_file(final_results_path, results_payload)
            return 1

        # 2. Bias & Heterogeneity (T017, T018)
        logger.info("Step 2: Running Bias Assessment (Egger's)...")
        if not run_script("code/analysis/bias.py"):
            logger.warning("Bias assessment failed (non-fatal).")
            # Non-fatal, continue

        logger.info("Step 3: Running Heterogeneity Analysis...")
        if not run_script("code/analysis/heterogeneity.py"):
            logger.warning("Heterogeneity analysis failed (non-fatal).")

        # 4. Hartung-Knapp Adjustment (T041) - Optional but good practice
        logger.info("Step 4: Running Hartung-Knapp Adjustment...")
        if not run_script("code/analysis/hartung_knapp.py"):
            logger.warning("Hartung-Knapp adjustment failed (non-fatal).")

        # 5. Multiple Comparisons Correction (T021)
        logger.info("Step 5: Running Bonferroni Correction...")
        if not run_script("code/analysis/correction.py"):
            logger.warning("Bonferroni correction failed (non-fatal).")

        # 6. Independence Checker (T044)
        logger.info("Step 6: Running Independence Check...")
        if not run_script("code/analysis/independence_checker.py"):
            logger.warning("Independence check failed (non-fatal).")

        # 7. Visualization (T015)
        logger.info("Step 7: Running Visualization Orchestrator...")
        if not run_script("code/visualization/orchestrator.py"):
            logger.warning("Visualization failed (non-fatal).")

        # 8. Report Generation (T032)
        logger.info("Step 8: Generating Paper Draft...")
        if not run_script("code/report/generate_paper.py"):
            logger.warning("Report generation failed (non-fatal).")
        
        logger.info("Quantitative pipeline completed.")

    else:
        logger.error(f"Unknown gate status: {status}")
        results_payload["error"] = f"Unknown gate status: {status}"

    # Save Final Results
    save_json_file(final_results_path, results_payload)
    logger.info(f"Final results saved to {final_results_path}")
    
    return 0

def main():
    parser = argparse.ArgumentParser(description="Main Pipeline Orchestrator")
    parser.add_argument("--input", type=str, help="Input data path (optional, mostly for legacy compatibility)")
    parser.add_argument("--output", type=str, help="Output path for results (optional)")
    args = parser.parse_args()

    # If --output is provided, we could potentially override the default results path,
    # but for now we stick to the standard derived/results.json as per spec.
    # The --input is ignored as the pipeline reads from standard locations.
    
    return run_pipeline(args)

if __name__ == "__main__":
    sys.exit(main())