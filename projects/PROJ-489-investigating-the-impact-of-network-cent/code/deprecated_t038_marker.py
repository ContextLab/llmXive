"""
Deprecated Task T038 Marker Module.

This file serves as a placeholder to track the status of Task T038.
The functionality originally assigned to T038 (FDR correction) has been
fully implemented and superseded by Task T037 in code/analysis.py.

Implementation Details:
- T037 implements the Benjamini-Hochberg FDR correction via apply_benjamini_hochberg.
- T037 generates the analysis_results.json with corrected p-values.

This module exists solely to indicate that T038 is deprecated and should not be
executed or modified.
"""

import logging

logger = logging.getLogger(__name__)

def check_deprecated_status():
    """
    Returns a status message confirming T038 is deprecated.
    
    Returns:
        str: A message indicating the task is superseded.
    """
    logger.info("Task T038 is deprecated. Functionality moved to T037 (code/analysis.py).")
    return "T038 is deprecated; FDR logic is in T037."

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print(check_deprecated_status())