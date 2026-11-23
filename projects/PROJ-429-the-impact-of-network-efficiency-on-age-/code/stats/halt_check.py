"""
Halt Check Module for T027b.

Implements the logic to check power analysis results and determine if
downstream cognitive visualization tasks should be skipped due to underpowering.
"""
import json
import logging
import sys
from pathlib import Path

from config import ensure_dirs, get_config_summary

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_power_analysis(power_file_path: Path) -> dict:
    """
    Load the power analysis JSON file.

    Args:
        power_file_path: Path to the power_analysis.json file.

    Returns:
        Dictionary containing power analysis results.

    Raises:
        FileNotFoundError: If the power analysis file does not exist.
        json.JSONDecodeError: If the file is not valid JSON.
    """
    if not power_file_path.exists():
        raise FileNotFoundError(f"Power analysis file not found: {power_file_path}")

    with open(power_file_path, 'r') as f:
        return json.load(f)

def check_halt_conditions(power_results: dict, sample_size: int = None) -> bool:
    """
    Check if the study is underpowered for cognitive analysis.

    Logic:
    - If power_for_r03 < 0.80 AND sample_size < 85:
      -> Underpowered due to insufficient sample size.
      -> Return True (halt cognitive tasks).
    - If power_for_r03 >= 0.80:
      -> Study is sufficiently powered.
      -> Return False (continue cognitive tasks).
    - If sample_size >= 85 but power is low:
      -> Underpowered due to effect size or other factors.
      -> Return True (halt cognitive tasks).

    Args:
        power_results: Dictionary from load_power_analysis().
        sample_size: Optional override for sample size (if not in results).

    Returns:
        True if cognitive tasks should be skipped, False otherwise.
    """
    power_for_r03 = power_results.get('power_for_r03', 0.0)
    is_sufficient = power_results.get('is_sufficient', False)
    n = sample_size if sample_size is not None else power_results.get('n', 0)

    logger.info(f"Checking halt conditions: power={power_for_r03:.4f}, is_sufficient={is_sufficient}, n={n}")

    # If the analysis says it's sufficient, we continue
    if is_sufficient:
        logger.info("Power analysis indicates sufficient power. Continuing cognitive tasks.")
        return False

    # If power is low, check if it's due to sample size
    if n < 85:
        logger.warning(f"Study underpowered for cognitive analysis (n={n} < 85). Skipping cognitive visualization tasks.")
        return True
    else:
        # Even with enough samples, if power is low, we should halt cognitive tasks
        logger.warning(f"Study underpowered for cognitive analysis (power={power_for_r03:.4f} < 0.80). Skipping cognitive visualization tasks.")
        return True

def write_status_file(status_path: Path, skip_cognitive: bool, reason: str):
    """
    Write a status file indicating whether to skip cognitive tasks.

    Args:
        status_path: Path to the status file.
        skip_cognitive: Boolean indicating if cognitive tasks should be skipped.
        reason: Reason for the decision.
    """
    ensure_dirs(status_path.parent)
    status_data = {
        "skip_cognitive_tasks": skip_cognitive,
        "reason": reason,
        "timestamp": get_config_summary().get('timestamp', 'unknown')
    }

    with open(status_path, 'w') as f:
        json.dump(status_data, f, indent=2)

    logger.info(f"Status file written to {status_path}: {status_data}")

def main():
    """
    Main entry point for the halt check script.

    Reads power_analysis.json, checks conditions, and writes a status file.
    Exits with code 0 regardless of outcome (pipeline continues, but skips cognitive viz).
    """
    config = get_config_summary()
    results_dir = Path(config.get('results_dir', 'data/results'))
    power_file = results_dir / 'power_analysis.json'
    status_file = results_dir / 'halt_status.json'

    try:
        power_results = load_power_analysis(power_file)
    except FileNotFoundError:
        logger.error(f"Power analysis file not found: {power_file}")
        logger.warning("Assuming underpowered due to missing data. Skipping cognitive tasks.")
        write_status_file(status_file, True, "Power analysis file missing")
        sys.exit(0)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in power analysis file: {e}")
        logger.warning("Assuming underpowered due to invalid data. Skipping cognitive tasks.")
        write_status_file(status_file, True, "Power analysis file invalid JSON")
        sys.exit(0)

    skip_cognitive = check_halt_conditions(power_results)

    reason = "Insufficient power for cognitive analysis" if skip_cognitive else "Study sufficiently powered"
    write_status_file(status_file, skip_cognitive, reason)

    if skip_cognitive:
        logger.warning("HALT CHECK: Cognitive visualization tasks (T031, T034, T035) will be skipped.")
        logger.warning("Continuing to Phase 5 (Viz) for EEG-only analysis.")
    else:
        logger.info("HALT CHECK: Cognitive visualization tasks can proceed.")

    sys.exit(0)

if __name__ == '__main__':
    main()
