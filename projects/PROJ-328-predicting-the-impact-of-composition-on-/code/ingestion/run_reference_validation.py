"""
Script to run the reference validation process.

This script reads the draft research sources from T008a and validates them,
producing the verified research_verified.md file required by downstream tasks.
"""
import os
import sys
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from utils.reference_validator import validate_research_md, ConstitutionError
from utils.logging_config import get_logger

logger = get_logger(__name__)

def main():
    """Main function to run reference validation."""
    # Define paths
    # T008a outputs to data/config/candidate_sources.txt
    # But the task description says it generates research.md
    # Let's check both possibilities
    draft_sources_paths = [
        'data/config/candidate_sources.txt',
        'specs/001-predict-solder-hardness/research.md',
        'data/config/research.md'
    ]

    output_path = 'specs/001-predict-solder-hardness/research_verified.md'

    draft_path = None
    for path in draft_sources_paths:
        full_path = project_root / path
        if full_path.exists():
            draft_path = str(full_path)
            logger.info(f"Found draft sources at: {draft_path}")
            break

    if not draft_path:
        logger.error("No draft research sources file found. T008a may not have completed successfully.")
        logger.error("Expected files: data/config/candidate_sources.txt, specs/001-predict-solder-hardness/research.md")
        return 1

    output_file = project_root / output_path

    try:
        logger.info(f"Starting reference validation...")
        logger.info(f"Input: {draft_path}")
        logger.info(f"Output: {output_file}")

        success = validate_research_md(draft_path, str(output_file))

        if success:
            logger.info("Reference validation completed successfully.")
            logger.info(f"Verified sources written to: {output_file}")
            return 0
        else:
            logger.error("Reference validation failed.")
            return 1

    except ConstitutionError as e:
        logger.error(f"Constitution error during validation: {str(e)}")
        logger.error("Verification failed. The pipeline must halt.")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error during validation: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
