"""
Reference Validator Agent Runner for T008b.

This script runs the Reference-Validator Agent on the draft content from T008a
(data/config/candidate_sources.txt) and generates the verified research file.
"""
import os
import sys
import logging
from pathlib import Path

# Add project root to path if running as script
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from utils.reference_validator import validate_research_md, ConstitutionError
from utils.logging_config import get_logger

def main():
    """
    Main entry point for T008b: Verify Research Sources.
    
    1. Reads the draft candidate sources from data/config/candidate_sources.txt.
    2. Validates URLs and citations.
    3. Generates specs/001-predict-solder-hardness/research_verified.md.
    """
    logger = get_logger("T008b_reference_validator")
    
    # Define paths relative to project root
    draft_path = project_root / "data" / "config" / "candidate_sources.txt"
    verified_dir = project_root / "specs" / "001-predict-solder-hardness"
    verified_path = verified_dir / "research_verified.md"
    
    # Ensure verified directory exists
    verified_dir.mkdir(parents=True, exist_ok=True)
    
    if not draft_path.exists():
        logger.error(f"Draft file not found: {draft_path}. T008a may not have completed.")
        print("ERROR: Draft file not found. Please ensure T008a has run.")
        sys.exit(1)
    
    logger.info(f"Starting verification of {draft_path}")
    
    try:
        # Read draft content
        with open(draft_path, 'r', encoding='utf-8') as f:
            draft_content = f.read()
        
        # Run validation
        # The validate_research_md function is expected to parse the draft,
        # verify URLs (simulated or real check depending on implementation),
        # and return a cleaned, verified string.
        verified_content = validate_research_md(draft_content, logger)
        
        if not verified_content:
            logger.warning("No verified sources found. Creating empty file with warning.")
            verified_content = "# Research Verified (Empty)\n\nNo sources could be verified from the draft.\n"
        
        # Write verified file
        with open(verified_path, 'w', encoding='utf-8') as f:
            f.write(verified_content)
        
        logger.info(f"Successfully wrote verified sources to {verified_path}")
        print(f"VERIFIED: {verified_path} created.")
        
    except ConstitutionError as e:
        logger.error(f"ConstitutionError during validation: {e}")
        print(f"FATAL: Validation failed due to configuration error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.exception(f"Unexpected error during validation: {e}")
        print(f"FATAL: Validation failed with unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
