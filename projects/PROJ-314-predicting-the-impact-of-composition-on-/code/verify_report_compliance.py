"""
Verify Final Report Compliance (Task T085).

This script generates the final report (if not present) and verifies:
1. It contains the required disclaimer.
2. It does NOT contain the word "cause" (case-insensitive) in the 'conclusion' field.

Execution: python code/verify_report_compliance.py
"""
import os
import sys
import json
import re
import logging
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from report import generate_final_report, main as report_main
from ingestion import main as ingestion_main
from modeling import main as modeling_main
from generate_shap_plots import main as shap_main

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

REPORT_PATH = project_root / "data" / "reports" / "final_report.md"
METRICS_PATH = project_root / "data" / "results" / "model_metrics.json"
SUFFICIENCY_PATH = project_root / "data" / "results" / "descriptor_sufficiency.json"
STABILITY_PATH = project_root / "data" / "results" / "stability_metrics.json"

def ensure_pipeline_run():
    """
    Ensure the pipeline has been run to generate necessary artifacts.
    If artifacts are missing, attempt to run the pipeline components.
    """
    logger.info("Checking for required pipeline artifacts...")
    
    # Check if report exists
    if not REPORT_PATH.exists():
        logger.warning(f"Report {REPORT_PATH} not found. Attempting to generate it.")
        try:
            # Run the report generation directly
            report_main()
            if not REPORT_PATH.exists():
                logger.error("Report generation failed: file still missing.")
                return False
        except Exception as e:
            logger.error(f"Failed to generate report: {e}")
            return False
    
    # Check dependencies for the report
    required_deps = [METRICS_PATH, SUFFICIENCY_PATH, STABILITY_PATH]
    missing_deps = [p for p in required_deps if not p.exists()]
    
    if missing_deps:
        logger.warning(f"Missing dependency files: {missing_deps}")
        logger.info("Attempting to run the full pipeline to generate dependencies...")
        try:
            # Run ingestion
            logger.info("Running ingestion...")
            ingestion_main()
            
            # Run modeling
            logger.info("Running modeling...")
            modeling_main()
            
            # Run SHAP plots
            logger.info("Running SHAP analysis...")
            shap_main()
            
            # Run report again
            logger.info("Regenerating report...")
            report_main()
            
        except Exception as e:
            logger.error(f"Pipeline execution failed: {e}")
            return False

    return True

def verify_compliance():
    """
    Verify the final report compliance.
    Returns True if compliant, False otherwise.
    """
    if not REPORT_PATH.exists():
        logger.error(f"Report file {REPORT_PATH} does not exist.")
        return False

    logger.info(f"Reading report from {REPORT_PATH}")
    with open(REPORT_PATH, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Check for required disclaimer
    disclaimer_keywords = [
        "statistical associations only",
        "do not imply causal relationships",
        "causal"
    ]
    
    disclaimer_found = False
    for keyword in disclaimer_keywords:
        if keyword.lower() in content.lower():
            disclaimer_found = True
            logger.info(f"Disclaimer found containing: '{keyword}'")
            break
    
    if not disclaimer_found:
        logger.error("FAIL: Required disclaimer not found in report.")
        return False

    # 2. Check for "cause" in conclusion section
    # We look for a section header like "## Conclusion" or "### Conclusion"
    # and then check the content until the next header or end of file.
    conclusion_pattern = r'(?:^|\n)\s*#{1,6}\s+Conclusion\s*\n(.*?)(?=\n\s*#{1,6}\s|\Z)'
    match = re.search(conclusion_pattern, content, re.IGNORECASE | re.DOTALL)
    
    if match:
        conclusion_text = match.group(1)
        logger.info("Found conclusion section.")
        
        # Check for "cause" (case-insensitive)
        if re.search(r'\bcause\b', conclusion_text, re.IGNORECASE):
            logger.error("FAIL: The word 'cause' was found in the conclusion section.")
            logger.error(f"Conclusion content: {conclusion_text[:200]}...")
            return False
        else:
            logger.info("PASS: No 'cause' found in conclusion section.")
    else:
        logger.warning("No explicit 'Conclusion' section header found. Checking entire report for 'cause' near end.")
        # Fallback: check last 1000 chars for "cause"
        tail = content[-1000:]
        if re.search(r'\bcause\b', tail, re.IGNORECASE):
             logger.error("FAIL: The word 'cause' was found in the tail of the report.")
             return False

    logger.info("PASS: Report is compliant.")
    return True

def main():
    logger.info("Starting T085: Verify Final Report Compliance")
    
    if not ensure_pipeline_run():
        logger.error("Pipeline execution failed. Cannot verify compliance.")
        sys.exit(1)
    
    if verify_compliance():
        logger.info("T085 Verification Successful.")
        sys.exit(0)
    else:
        logger.error("T085 Verification Failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()
