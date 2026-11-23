import json
import os
import sys
import logging
from pathlib import Path

# Import the validator main function from the API surface
from utils.validator import main as validate_main

def main():
    """
    T071b: Execute the Reference-Validator Agent.
    
    This script runs the validator defined in T071a against the research.md
    and plan.md files. It asserts that the validation log indicates 'all_valid'
    and creates the required lock file to unblock Phase 1.
    """
    # Ensure we are in the project root context for relative paths
    project_root = Path(__file__).resolve().parent.parent
    os.chdir(project_root)

    # Define paths based on task description
    research_md_path = project_root / "specs" / "001-evaluating-the-impact-of-llm-generated-c" / "research.md"
    plan_md_path = project_root / "plan.md"
    state_dir = project_root / "state"
    validation_log_path = state_dir / "validation_log.json"
    lock_path = state_dir / "research_validated.lock"

    # Ensure state directory exists
    state_dir.mkdir(parents=True, exist_ok=True)

    # Check if input files exist
    if not research_md_path.exists():
        logging.error(f"Research file not found: {research_md_path}")
        sys.exit(1)
    
    if not plan_md_path.exists():
        logging.error(f"Plan file not found: {plan_md_path}")
        sys.exit(1)

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)

    logger.info(f"Starting Reference-Validator Agent execution (T071b).")
    logger.info(f"Input: {research_md_path}, {plan_md_path}")
    logger.info(f"Output: {validation_log_path}")

    try:
        # Execute the validator logic
        # The validator is expected to read state/citations.yaml (created by T070a)
        # and validate references, writing results to state/validation_log.json
        validate_main()

        # Verify the output file exists
        if not validation_log_path.exists():
            logger.error("Validation failed: state/validation_log.json was not created.")
            sys.exit(1)

        # Load and verify the content
        with open(validation_log_path, 'r', encoding='utf-8') as f:
            log_data = json.load(f)

        status = log_data.get("status", "unknown")
        
        if status != "all_valid":
            logger.error(f"Validation failed: Status is '{status}', expected 'all_valid'.")
            logger.error(f"Log content: {json.dumps(log_data, indent=2)}")
            # Do not create lock file, abort pipeline
            sys.exit(1)

        logger.info("Validation successful: Status is 'all_valid'.")

        # Create the lock file to signal success
        with open(lock_path, 'w', encoding='utf-8') as f:
            f.write(f"Research validated successfully.\nTimestamp: {Path(validation_log_path).stat().st_mtime}\n")
        
        logger.info(f"Lock file created: {lock_path}")
        logger.info("T071b completed successfully. Pipeline can proceed to Phase 1.")
        sys.exit(0)

    except Exception as e:
        logger.error(f"Unexpected error during validation: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
