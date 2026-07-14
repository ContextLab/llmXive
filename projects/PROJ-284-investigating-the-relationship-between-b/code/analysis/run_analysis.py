"""
Run Analysis Script.
Orchestrates the full analysis pipeline: PCA, merging, and correlation preparation.
"""
import shutil
from pathlib import Path
from code.logging_config import get_logger
from code.analysis.correlations import main as correlations_main

logger = get_logger(__name__)

def main():
    """
    Run the full analysis pipeline.
    """
    try:
        logger.log("run_analysis", step="start")
        
        # Execute the correlation analysis (which includes PCA and merging)
        correlations_main()
        
        logger.log("run_analysis", step="complete", status="success")
        
    except Exception as e:
        logger.log("run_analysis", step="error", error=str(e))
        raise

if __name__ == "__main__":
    main()
