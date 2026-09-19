"""
Feasibility Gate Enforcer for Plant Disease Susceptibility Pipeline.

This script enforces the feasibility gate by reading the status generated
by T001a. If the status is 'FAIL', it logs the failure and exits with code 1.
If the status is 'PASS', it exits with code 0, allowing subsequent tasks to run.
"""
import sys
import yaml
from pathlib import Path

# Add project root to path for imports if running as script
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from src.utils.logger import get_logger, setup_logging_for_task

logger = get_logger(__name__)

GATE_STATUS_PATH = Path("data/processed/feasibility_gate_status.yaml")

def main() -> int:
    """
    Reads the feasibility gate status and exits accordingly.

    Returns:
        int: 0 if PASS, 1 if FAIL or error.
    """
    setup_logging_for_task("feasibility_gate_enforcer")

    if not GATE_STATUS_PATH.exists():
        logger.error(f"Feasibility gate status file not found at: {GATE_STATUS_PATH}")
        logger.error("Pipeline cannot proceed without a valid gate status file.")
        print("Feasibility Gate Failed: Status file missing.", file=sys.stderr)
        return 1

    try:
        with open(GATE_STATUS_PATH, 'r', encoding='utf-8') as f:
            status_data = yaml.safe_load(f)

        if status_data is None:
            logger.error("Feasibility gate status file is empty or invalid YAML.")
            print("Feasibility Gate Failed: Invalid status file content.", file=sys.stderr)
            return 1

        status_value = status_data.get("status")

        if status_value is None:
            logger.error("Feasibility gate status file missing 'status' key.")
            print("Feasibility Gate Failed: Missing 'status' key.", file=sys.stderr)
            return 1

        if status_value == "PASS":
            logger.info("Feasibility Gate PASSED. Proceeding with pipeline.")
            print("Feasibility Gate: PASS")
            return 0

        elif status_value == "FAIL":
            logger.error("Feasibility Gate FAILED. Halting pipeline.")
            print("Feasibility Gate Failed: Halting pipeline.", file=sys.stderr)
            return 1

        else:
            logger.error(f"Feasibility Gate Failed: Unknown status value '{status_value}'.")
            print(f"Feasibility Gate Failed: Unknown status value '{status_value}'.", file=sys.stderr)
            return 1

    except yaml.YAMLError as e:
        logger.error(f"Error parsing YAML file: {e}")
        print("Feasibility Gate Failed: YAML parsing error.", file=sys.stderr)
        return 1
    except Exception as e:
        logger.error(f"Unexpected error during feasibility gate check: {e}")
        print(f"Feasibility Gate Failed: Unexpected error: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
