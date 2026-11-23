"""
Script to execute Task T021c: Implement 'high-quality human documentation' rubric.
This script imports from code/validation.py and runs the evaluation.
"""
import os
import sys
import logging

# Ensure we can import from code/
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from validation import main as run_rubric

def main():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger("run_doc_quality_rubric")
    logger.info("Starting T021c: Documentation Quality Rubric Execution")
    
    try:
        run_rubric()
        logger.info("T021c completed successfully. Output: data/raw/doc_quality_scores.json")
    except Exception as e:
        logger.error(f"T021c failed: {e}")
        raise

if __name__ == "__main__":
    main()
