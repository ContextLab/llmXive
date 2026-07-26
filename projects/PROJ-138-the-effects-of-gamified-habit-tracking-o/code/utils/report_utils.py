"""
Utility functions for reporting and formatting.
"""
import os
import json
import logging
from code.utils.logging import pipeline_logger

logger = logging.getLogger("report_utils")

def report_cronbach_alpha():
    """
    Reads the calculated Cronbach's Alpha from data/processed/psychometrics.json
    and logs it for inclusion in the final report.
    
    This function is called by code/main.py after T012b (validation) runs.
    """
    psychometrics_path = "data/processed/psychometrics.json"
    
    if not os.path.exists(psychometrics_path):
        logger.warning(f"Psychometrics file not found at {psychometrics_path}. Skipping alpha report.")
        return

    try:
        with open(psychometrics_path, 'r') as f:
            data = json.load(f)
        
        alpha = data.get('cronbach_alpha')
        if alpha is not None:
            logger.info(f"Calculated Cronbach's Alpha: {alpha:.4f}")
        else:
            logger.warning("Cronbach's Alpha key missing in psychometrics.json.")
    except Exception as e:
        logger.error(f"Failed to read psychometrics.json: {e}")
        raise

def format_limitations():
    """
    Returns a standard string for the Data Limitations section.
    """
    return (
        "Sample size (N=500), synthetic nature of data, lack of external validation, "
        "and potential underpowering for interaction effects."
    )
