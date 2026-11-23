"""
Validation script for alignment duration benchmarking.
Parses pipeline.log and asserts alignment duration <= 2 hours.
"""
import re
import sys
from loguru import logger
from code.utils.logger import setup_logger

setup_logger("pipeline.log", level="INFO")

MAX_DURATION_HOURS = 2
MAX_DURATION_SECONDS = MAX_DURATION_HOURS * 3600

def parse_alignment_duration(log_file: str) -> float:
    """
    Parse the duration of the last alignment from pipeline.log.

    Args:
        log_file: Path to pipeline.log.

    Returns:
        Duration in seconds.
    """
    with open(log_file, 'r') as f:
        content = f.read()

    # Regex to find "Duration: X.XXs"
    pattern = r"Duration:\s*([\d.]+)s"
    matches = re.findall(pattern, content)

    if not matches:
        raise ValueError("No alignment duration found in pipeline.log")

    # Return the last found duration
    return float(matches[-1])

def validate():
    """
    Validate alignment duration against threshold.
    """
    log_file = "pipeline.log"
    if not os.path.exists(log_file):
        logger.error(f"Log file {log_file} not found.")
        sys.exit(1)

    duration = parse_alignment_duration(log_file)
    logger.info(f"Alignment duration: {duration:.2f}s")

    if duration > MAX_DURATION_SECONDS:
        logger.error(f"Alignment duration {duration:.2f}s exceeds limit {MAX_DURATION_SECONDS}s.")
        sys.exit(1)
    else:
        logger.info("Alignment duration validation PASSED.")
        sys.exit(0)

if __name__ == "__main__":
    validate()