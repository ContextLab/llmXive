import os
import sys
import logging
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from utils.reference_validator import validate_research_md, ConstitutionError
from utils.logging_config import get_logger

def main():
    logger = get_logger(__name__)
    logger.info("Starting Reference Validation for T008b")

    # Define paths relative to project root
    candidate_sources_path = project_root / "data" / "config" / "candidate_sources.txt"
    verified_research_path = project_root / "specs" / "001-predict-solder-hardness" / "research_verified.md"
    sources_yaml_path = project_root / "data" / "config" / "sources.yaml"

    # Ensure directories exist
    verified_research_path.parent.mkdir(parents=True, exist_ok=True)
    sources_yaml_path.parent.mkdir(parents=True, exist_ok=True)

    if not candidate_sources_path.exists():
        logger.error(f"Candidate sources file not found: {candidate_sources_path}")
        logger.error("T008a must be completed before T008b can run.")
        # Fail loudly as per constraints
        sys.exit(1)

    try:
        # Run validation
        # The validator reads candidate_sources.txt, checks URLs, and writes verified content
        is_validated, verified_content = validate_research_md(
            candidate_source_path=candidate_sources_path,
            output_path=verified_research_path
        )

        if is_validated:
            logger.info("Verification successful. Verified sources written to research_verified.md")
            # Update sources.yaml to mark as verified if it exists or create it
            # We assume a helper in utils or a simple update here.
            # Since we can't invent APIs, we'll just log the success and let T009c handle the YAML update
            # based on the verified file.
            return 0
        else:
            logger.warning("Verification failed or timed out. Proceeding with provisional status.")
            # Write a marker in the verified file indicating provisional status
            with open(verified_research_path, 'w') as f:
                f.write("# PROVISIONAL SOURCES - Verification Failed/Timeout\n")
                f.write("# Fallback to candidate_sources.txt for T009c\n")
                f.write(verified_content if verified_content else "")
            return 1

    except ConstitutionError as e:
        logger.error(f"Constitution Error during validation: {e}")
        # Proceed to provisional
        with open(verified_research_path, 'w') as f:
            f.write("# PROVISIONAL SOURCES - Constitution Error\n")
            f.write(f"# Error: {e}\n")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error during validation: {e}")
        # Fail loudly
        raise

if __name__ == "__main__":
    main()
