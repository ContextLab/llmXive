"""
Main entry point for the llmXive pipeline.

Orchestrates the execution of:
1. Oracle Generation (US1)
2. Rule Extraction (US2)
3. Divergence Analysis (US3)
"""
import logging
import sys
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

def main():
    logger.info("Starting llmXive pipeline...")
    
    # Check project structure
    root = Path(__file__).parent.parent
    required_dirs = [
        "data/raw", "data/processed",
        "specs/001-llmxive-followup/contracts",
        "code/utils", "code/oracle", "code/rules", "code/analysis"
    ]
    
    for d in required_dirs:
        dir_path = root / d
        if not dir_path.exists():
            logger.error(f"Missing required directory: {dir_path}")
            raise FileNotFoundError(f"Directory not found: {dir_path}")
    
    logger.info("Project structure validated.")
    logger.info("Pipeline execution sequence:")
    logger.info("  1. Generate Ground Truth Oracle (US1)")
    logger.info("  2. Extract Rules from Traces (US2)")
    logger.info("  3. Quantify Divergence (US3)")
    
    # Orchestration logic:
    # Since US1, US2, and US3 modules are not yet fully implemented,
    # we verify the existence of the expected output paths and check
    # for code drift in the current implementation using checksums.
    
    # 1. Verify Code Drift (Self-check)
    logger.info("Performing code drift check on current implementation...")
    try:
        # We check the current file's checksum against a hypothetical baseline
        # In a real scenario, this would compare against a stored manifest.
        # Here we just demonstrate the integration with checksums.py.
        current_file = Path(__file__).resolve()
        checksum = compute_file_sha256(current_file)
        logger.info(f"Current main.py checksum: {checksum}")
    except Exception as e:
        logger.warning(f"Checksum verification skipped or failed: {e}")

    # 2. Placeholder for Phase Execution
    # In the next tasks, specific orchestration logic will be added here
    # to call oracle.parser, rules.extractor, etc.
    
    logger.info("Pipeline initialization complete. Ready for user story implementation.")
    return 0

if __name__ == "__main__":
    sys.exit(main())