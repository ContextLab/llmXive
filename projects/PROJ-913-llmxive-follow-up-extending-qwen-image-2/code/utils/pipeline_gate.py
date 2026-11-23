import sys
import json
from pathlib import Path
from config import PROJECT_ROOT
from utils.logger import get_logger

logger = get_logger("pipeline_gate")

def check_gate(validation_report_path: Path) -> bool:
    """
    Checks if the OOD validation gate is passed.
    Returns True if safe to proceed, False otherwise.
    """
    if not validation_report_path.exists():
        logger.error("Validation report not found.")
        return False
    
    with open(validation_report_path, "r") as f:
        report = json.load(f)
    
    if report.get("status") != "PASSED":
        logger.error("Gate check failed: Validation report indicates failure.")
        return False
    
    return True

def run_gate() -> None:
    """
    Runs the gate check. Exits with code 1 if failed.
    """
    report_path = PROJECT_ROOT / "data" / "prompts" / "validation_report.json"
    if not check_gate(report_path):
        logger.critical("[CRITICAL: DATA LEAKAGE DETECTED] Pipeline halted.")
        sys.exit(1)
    logger.info("Pipeline gate passed.")

def main():
    run_gate()

if __name__ == "__main__":
    main()
