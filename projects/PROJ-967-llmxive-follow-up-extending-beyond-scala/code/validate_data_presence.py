import argparse
import json
import logging
import os
import sys
from pathlib import Path

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)

def check_config_json(config_path: Path, logger: logging.Logger) -> bool:
    """Check if config.json exists and is readable."""
    if not config_path.exists():
        logger.warning(f"Config file not found: {config_path}")
        return False
    try:
        with open(config_path, 'r') as f:
            json.load(f)
        return True
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in config: {e}")
        return False

def check_research_md(research_path: Path, logger: logging.Logger) -> bool:
    """Check if research.md exists."""
    if not research_path.exists():
        logger.warning(f"Research file not found: {research_path}")
        return False
    return True

def check_validation_log(validation_log_path: Path, logger: logging.Logger) -> bool:
    """Check if validation log exists and indicates success."""
    if not validation_log_path.exists():
        logger.warning(f"Validation log not found: {validation_log_path}")
        return False
    try:
        with open(validation_log_path, 'r') as f:
            data = json.load(f)
            if data.get('status') != 'success':
                logger.warning(f"Validation log indicates failure: {data.get('message')}")
                return False
        return True
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in validation log: {e}")
        return False

def check_lineage_report(lineage_path: Path, logger: logging.Logger) -> bool:
    """Check if lineage report exists."""
    if not lineage_path.exists():
        logger.warning(f"Lineage report not found: {lineage_path}")
        return False
    try:
        with open(lineage_path, 'r') as f:
            json.load(f)
        return True
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in lineage report: {e}")
        return False

def enforce_fail_loud(logger: logging.Logger):
    """
    Enforce the 'Fail Loud' policy.
    Checks if real data verification passed. If not, raises RuntimeError.
    """
    # Define paths relative to project root
    project_root = Path(__file__).resolve().parent.parent
    config_path = project_root / 'data' / 'processed' / 'config.json'
    research_path = project_root / 'specs' / '001-llmxive-follow-up-extending-beyond-scala' / 'research.md'
    validation_log_path = project_root / 'data' / 'raw' / 'validation_log.json'
    lineage_path = project_root / 'data' / 'processed' / 'lineage_report.json'

    # Check for synthetic flag in config
    is_synthetic = False
    if config_path.exists():
        try:
            with open(config_path, 'r') as f:
                config_data = json.load(f)
                is_synthetic = config_data.get('IS_SYNTHETIC_RUN', False)
        except json.JSONDecodeError:
            pass

    # If synthetic flag is set, we must fail loud as per FR-006
    if is_synthetic:
        error_msg = "No real data found. Synthetic fallback is prohibited by FR-006/Constitution Principle VII."
        logger.error(error_msg)
        raise RuntimeError(error_msg)

    # Check validation log status
    if not check_validation_log(validation_log_path, logger):
        error_msg = "No real data found. Synthetic fallback is prohibited by FR-006/Constitution Principle VII."
        logger.error(error_msg)
        raise RuntimeError(error_msg)

    logger.info("Real data verification passed. Proceeding.")

def parse_args():
    parser = argparse.ArgumentParser(description='Validate data presence and enforce fail-loud policy.')
    parser.add_argument('--project-root', type=str, default=None, help='Path to project root')
    return parser.parse_args()

def main():
    logger = setup_logging()
    args = parse_args()

    try:
        enforce_fail_loud(logger)
        logger.info("Validation successful. No synthetic fallback detected.")
    except RuntimeError as e:
        logger.error(f"Pipeline halted: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()