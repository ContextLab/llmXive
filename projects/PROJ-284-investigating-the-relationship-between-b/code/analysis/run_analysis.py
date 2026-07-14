import shutil
from pathlib import Path
from code.logging_config import get_logger
from code.analysis.correlations import main as correlations_main

logger = get_logger(__name__)

def main() -> None:
    """
    Orchestrates the analysis pipeline.
    This script ensures the analysis step runs and produces the required CSVs.
    """
    logger.log("run_analysis", operation="start", status="running")
    
    try:
        # Run the correlations and metrics generation
        correlations_main()
        
        logger.log("run_analysis", operation="complete", status="success")
    except Exception as e:
        logger.log("run_analysis", operation="failed", error=str(e))
        raise

if __name__ == "__main__":
    main()
