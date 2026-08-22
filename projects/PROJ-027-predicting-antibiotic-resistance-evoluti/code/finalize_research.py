"""
T040: Finalize research state by computing hashes and marking research complete.

This script runs the hash_artifacts utility to:
1. Compute SHA256 hashes for all files in data/ and code/
2. Update the state/ directory with the new hashes
3. Mark the research as complete in the state file
"""
import os
import sys
import logging
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root / "code"))

from utils.logging import init_pipeline_logging, get_logger
from utils.hash_artifacts import main as hash_main

def main():
    """Execute the finalization of research state."""
    # Initialize logging
    log_path = project_root / "logs" / "finalize_research.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    logger = init_pipeline_logging("finalize_research", str(log_path))
    
    logger.info("Starting T040: Finalize research state")
    
    try:
        # Change to project root to ensure relative paths work correctly
        os.chdir(project_root)
        
        # Run the hash_artifacts main function
        # This will compute hashes, update state/, and mark research complete
        logger.info("Executing hash_artifacts...")
        hash_main()
        
        logger.info("T040 completed successfully. Research state finalized.")
        return 0
        
    except Exception as e:
        logger.error(f"Failed to finalize research state: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())