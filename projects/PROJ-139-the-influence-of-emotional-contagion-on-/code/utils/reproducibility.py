"""
Reproducibility verification module.

This module re-runs the pipeline (or loads existing outputs) and verifies
that the computed checksums match the previously recorded artifact hashes
stored in the state directory.
"""
import os
import json
import hashlib
import logging
import subprocess
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

# Import from existing project modules
from utils.artifact_checksums import compute_file_hash, find_artifacts, record_checksums
from config.settings import get_config, DatasetPaths

logger = logging.getLogger(__name__)

# Constants
PROJECT_ID = "PROJ-139-the-influence-of-emotional-contagion-on-"
STATE_DIR = "state/projects"
CHECKSUM_FILE_PATTERN = "checksums.yaml"


def get_previous_checksums_path() -> Path:
    """Return the path to the previously recorded checksums file."""
    config = get_config()
    state_base = Path(config.state_dir)
    project_state_dir = state_base / PROJECT_ID
    return project_state_dir / CHECKSUM_FILE_PATTERN


def load_previous_checksums() -> Optional[Dict[str, Any]]:
    """
    Load the previously recorded checksums from the state file.
    Returns None if the file does not exist.
    """
    path = get_previous_checksums_path()
    if not path.exists():
        logger.warning(f"Previous checksums file not found: {path}")
        return None

    import yaml
    with open(path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    return data


def compute_current_checksums() -> Dict[str, str]:
    """
    Compute the current checksums for all tracked artifacts.
    Returns a dictionary mapping relative paths to their SHA256 hashes.
    """
    config = get_config()
    # Define the directories to scan for artifacts
    artifact_dirs = [
        config.data_processed_dir,
        config.data_raw_dir,
        config.state_dir,
        "figures",
        "docs"
    ]

    # Filter to existing directories
    existing_dirs = [d for d in artifact_dirs if Path(d).exists()]

    all_artifacts = []
    for d in existing_dirs:
        all_artifacts.extend(find_artifacts(Path(d)))

    checksums = {}
    for artifact_path in all_artifacts:
        # Store relative path from project root
        rel_path = str(artifact_path.relative_to(Path.cwd()))
        file_hash = compute_file_hash(artifact_path)
        checksums[rel_path] = file_hash

    return checksums


def compare_checksums(
    previous: Dict[str, Any],
    current: Dict[str, str]
) -> Tuple[bool, List[Dict[str, Any]]]:
    """
    Compare previous and current checksums.
    Returns (is_match, list_of_differences).
    """
    differences = []
    is_match = True

    # Check for missing files in current
    prev_hashes = previous.get("artifact_hashes", {})
    for path, prev_hash in prev_hashes.items():
        if path not in current:
            differences.append({
                "path": path,
                "status": "missing",
                "previous_hash": prev_hash,
                "current_hash": None
            })
            is_match = False
        elif current[path] != prev_hash:
            differences.append({
                "path": path,
                "status": "mismatch",
                "previous_hash": prev_hash,
                "current_hash": current[path]
            })
            is_match = False

    # Check for new files in current that weren't in previous
    for path in current:
        if path not in prev_hashes:
            differences.append({
                "path": path,
                "status": "new",
                "previous_hash": None,
                "current_hash": current[path]
            })
            # New files might be acceptable depending on policy, but for strict
            # reproducibility we flag them.
            is_match = False

    return is_match, differences


def save_reproducibility_report(
    is_match: bool,
    differences: List[Dict[str, Any]],
    previous_checksums: Dict[str, Any],
    current_checksums: Dict[str, str],
    output_path: Optional[Path] = None
) -> Path:
    """
    Save a detailed reproducibility report to a JSON file.
    """
    if output_path is None:
        config = get_config()
        state_base = Path(config.state_dir)
        project_state_dir = state_base / PROJECT_ID
        output_path = project_state_dir / "reproducibility_report.json"

    output_path.parent.mkdir(parents=True, exist_ok=True)

    report = {
        "timestamp": "generated_at_runtime",  # Will be replaced by actual time in real usage
        "project_id": PROJECT_ID,
        "reproducibility_verified": is_match,
        "previous_checksums_count": len(previous_checksums.get("artifact_hashes", {})),
        "current_checksums_count": len(current_checksums),
        "differences": differences,
        "summary": {
            "total_previous": len(previous_checksums.get("artifact_hashes", {})),
            "total_current": len(current_checksums),
            "missing_count": sum(1 for d in differences if d["status"] == "missing"),
            "mismatch_count": sum(1 for d in differences if d["status"] == "mismatch"),
            "new_count": sum(1 for d in differences if d["status"] == "new")
        }
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)

    logger.info(f"Reproducibility report saved to: {output_path}")
    return output_path


def run_pipeline_if_needed() -> bool:
    """
    Check if the pipeline has been run. If not, attempt to run it.
    Returns True if the pipeline ran successfully or if outputs already exist.
    Returns False if the pipeline run failed.
    """
    config = get_config()
    # Check if the main processed data exists
    processed_file = Path(config.data_processed_dir) / "metrics_results.csv"
    
    if processed_file.exists():
        logger.info("Pipeline outputs already exist. Skipping re-run.")
        return True

    logger.info("Pipeline outputs not found. Attempting to run the full pipeline...")
    
    # Attempt to run the pipeline
    # This assumes the main entry point is code/main.py or similar
    # We'll try to run the individual stages if a main entry point isn't found
    pipeline_scripts = [
        "code/main.py",
        "code/run_pipeline.py",
        "code/pipeline.py"
    ]
    
    script_path = None
    for script in pipeline_scripts:
        if Path(script).exists():
            script_path = script
            break
    
    if script_path is None:
        logger.error("No pipeline entry point found. Cannot re-run pipeline.")
        return False

    try:
        result = subprocess.run(
            [sys.executable, script_path],
            check=True,
            capture_output=True,
            text=True
        )
        logger.info("Pipeline executed successfully.")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Pipeline execution failed: {e}")
        logger.error(f"stdout: {e.stdout}")
        logger.error(f"stderr: {e.stderr}")
        return False


def verify_reproducibility() -> bool:
    """
    Main function to verify reproducibility.
    1. Ensure pipeline has been run (run if necessary).
    2. Load previous checksums.
    3. Compute current checksums.
    4. Compare and generate report.
    5. Return True if reproducible, False otherwise.
    """
    logger.info("Starting reproducibility verification...")

    # Step 1: Ensure pipeline outputs exist
    if not run_pipeline_if_needed():
        logger.error("Pipeline execution failed or could not be run. Cannot verify reproducibility.")
        return False

    # Step 2: Load previous checksums
    previous = load_previous_checksums()
    if previous is None:
        logger.error("No previous checksums found. Cannot verify reproducibility.")
        return False

    # Step 3: Compute current checksums
    current = compute_current_checksums()
    if not current:
        logger.error("No current artifacts found to checksum.")
        return False

    # Step 4: Compare checksums
    is_match, differences = compare_checksums(previous, current)

    # Step 5: Save report
    save_reproducibility_report(is_match, differences, previous, current)

    if is_match:
        logger.info("SUCCESS: Reproducibility verified. All checksums match.")
    else:
        logger.warning("FAILURE: Reproducibility check failed. Differences found.")
        for diff in differences:
            logger.warning(f"  - {diff['path']}: {diff['status']}")

    return is_match


def main():
    """Entry point for the reproducibility verification script."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    success = verify_reproducibility()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
