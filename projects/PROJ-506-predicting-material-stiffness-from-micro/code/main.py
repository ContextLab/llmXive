import sys
import argparse
import logging
from pathlib import Path
import json
from datetime import datetime
from code.utils.verify_spec import verify_spec
from code.utils.verify_constitution import verify_constitution
from code.utils.verify_spec_anova import verify_anova_mention

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def parse_args():
    parser = argparse.ArgumentParser(description="Main pipeline orchestrator.")
    parser.add_argument("--verify-spec", action="store_true", help="Run spec verification (T004v).")
    parser.add_argument("--verify-constitution", action="store_true", help="Run constitution verification (T002v).")
    parser.add_argument("--verify-anova", action="store_true", help="Run ANOVA mention verification (T005v).")
    return parser.parse_args()

def run_verification():
    """Run all governance verification tasks."""
    logger.info("Starting governance verification...")
    
    t002v_pass = verify_constitution()
    t004v_pass = verify_spec()
    t005v_pass = verify_anova_mention()
    
    if t002v_pass and t004v_pass and t005v_pass:
        logger.info("All governance verifications passed.")
        return True
    else:
        logger.error("One or more governance verifications failed.")
        return False

def run_generation_pipeline():
    """Placeholder for the generation pipeline execution."""
    logger.info("Running generation pipeline...")
    # This would be implemented in subsequent tasks
    return True

def main():
    args = parse_args()
    
    if args.verify_spec:
        success = verify_spec()
        sys.exit(0 if success else 1)
    elif args.verify_constitution:
        success = verify_constitution()
        sys.exit(0 if success else 1)
    elif args.verify_anova:
        success = verify_anova_mention()
        sys.exit(0 if success else 1)
    elif args.verify_spec or args.verify_constitution or args.verify_anova:
        # Run all if no specific flag but verification is implied
        success = run_verification()
        sys.exit(0 if success else 1)
    else:
        # Default behavior
        logger.info("Running default pipeline...")
        # Run verifications first
        if not run_verification():
            logger.error("Governance verification failed. Aborting.")
            sys.exit(1)
        
        # Run generation
        if not run_generation_pipeline():
            logger.error("Generation pipeline failed.")
            sys.exit(1)
        
        logger.info("Pipeline completed successfully.")

if __name__ == "__main__":
    main()
