"""
Data Collection Trigger Script

This script implements the 'trigger controlled data collection' pathway.
It acts as a guardrail to ensure that if real data is required but not
available (and synthetic fallback is disabled or insufficient), the pipeline
halts execution with clear instructions for manual IRB steps.

Per T012b requirements:
- Logs a warning if real data is required.
- Halts execution (raises SystemExit).
- Directs the user to manual IRB steps.
- Does NOT automate IRB logic.
"""

import sys
import os
from logging_config import get_logger, log_state_event

# Initialize logger
logger = get_logger(__name__)

def check_real_data_availability(data_dir: str = "data/raw") -> bool:
    """
    Check if real data files exist in the expected directory.

    Args:
        data_dir: Path to the raw data directory.

    Returns:
        True if real data is found, False otherwise.
    """
    if not os.path.exists(data_dir):
        return False

    # Check for any non-empty files in the directory
    files = [f for f in os.listdir(data_dir) if os.path.isfile(os.path.join(data_dir, f))]
    if not files:
        return False

    # Basic check for non-zero size files
    for f in files:
        if os.path.getsize(os.path.join(data_dir, f)) > 0:
            return True

    return False

def trigger_controlled_collection(require_real_data: bool = True) -> None:
    """
    Trigger the controlled data collection pathway.

    If real data is required and not available, this function logs a warning,
    prints instructions for manual IRB steps, and halts execution.

    Args:
        require_real_data: Boolean flag indicating if real data is mandatory.
                           If True and data is missing, execution halts.
    """
    data_path = os.path.join("data", "raw")
    has_data = check_real_data_availability(data_path)

    if require_real_data and not has_data:
        logger.warning("REAL DATA REQUIRED BUT NOT FOUND.")
        logger.warning("Execution halted to prevent synthetic data fabrication.")
        
        message = (
            "\n"
            "=" * 70 + "\n"
            "STOP: Controlled Data Collection Required\n"
            "=" * 70 + "\n\n"
            "The pipeline requires real interaction data (facial/vocal features) "
            "to proceed with the analysis.\n\n"
            "Since no real data was found in 'data/raw', you must manually "
            "initiate the data collection protocol.\n\n"
            "INSTRUCTIONS FOR MANUAL IRB STEPS:\n"
            "1. Review the approved IRB protocol in 'specs/001-emotional-synchrony-trust/consent_protocol.md'.\n"
            "2. Recruit participants and administer the survey interface (see code/data_collection.py).\n"
            "3. Ensure all consent forms are signed and stored securely.\n"
            "4. Run the collection protocol to generate raw data files.\n"
            "5. Place the resulting raw data files into the 'data/raw' directory.\n"
            "6. Once data is present, re-run this pipeline.\n\n"
            "DO NOT modify this script to bypass this check or generate fake data.\n"
            "=" * 70 + "\n"
        )
        
        print(message)
        log_state_event("DATA_COLLECTION_TRIGGERED", "Real data required but missing; manual collection initiated.")
        
        # Halt execution
        sys.exit(1)
    
    elif not require_real_data:
        logger.info("Real data requirement disabled. Synthetic data generation is permitted.")
        log_state_event("SYNTHETIC_FALLBACK_ALLOWED", "Pipeline configured to allow synthetic data.")

def main():
    """
    Main entry point for the data collection trigger.
    
    By default, this script enforces the requirement for real data.
    If the environment variable ALLOW_SYNTHETIC_DATA is set to 'true',
    it will skip the halt.
    """
    allow_synthetic = os.getenv("ALLOW_SYNTHETIC_DATA", "false").lower() == "true"
    
    logger.info("Starting Data Collection Trigger Check...")
    trigger_controlled_collection(require_real_data=not allow_synthetic)
    logger.info("Data collection check passed. Proceeding with pipeline.")

if __name__ == "__main__":
    main()