"""
Conditional synthesis logic for meta-analysis.
Implements FR-014: Suppress subgroup/meta-regression if N < 10 and switch to descriptive synthesis.
"""
import logging
import os
from typing import List, Dict, Any, Optional
from pathlib import Path

import pandas as pd

from code.utils.logging import get_logger
from code.utils.config import get_docs_path, get_data_path
from code.analysis.descriptive_synthesis import perform_descriptive_synthesis, format_synthesis_report

logger = get_logger(__name__)

MIN_SUBGROUP_SIZE = 10

def check_sample_size_and_route(
    cleaned_studies_path: Optional[str] = None,
    output_doc_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Checks the number of studies in the cleaned dataset.
    If N < 10, performs descriptive synthesis and writes the report.
    If N >= 10, returns a flag indicating meta-analysis should proceed (subgroup/regression).
    
    Args:
        cleaned_studies_path: Path to the cleaned studies CSV. Defaults to data/processed/cleaned_studies.csv.
        output_doc_path: Path for the output markdown report. Defaults to docs/native_synthesis.md.
        
    Returns:
        A dictionary with:
            - 'proceed_meta_analysis': bool (True if N >= 10)
            - 'n_studies': int
            - 'synthesis_report_path': str (if descriptive synthesis was performed)
    """
    if cleaned_studies_path is None:
        cleaned_studies_path = str(get_data_path() / "processed" / "cleaned_studies.csv")
    if output_doc_path is None:
        output_doc_path = str(get_docs_path() / "native_synthesis.md")

    logger.info(f"Checking sample size for conditional synthesis logic. Source: {cleaned_studies_path}")

    if not os.path.exists(cleaned_studies_path):
        raise FileNotFoundError(f"Cleaned studies file not found at {cleaned_studies_path}. "
                                "Ensure T021 (verify_output) and the data pipeline have run successfully.")

    try:
        df = pd.read_csv(cleaned_studies_path)
    except Exception as e:
        logger.error(f"Failed to read cleaned studies CSV: {e}")
        raise

    n_studies = len(df)
    logger.info(f"Found {n_studies} studies in cleaned dataset.")

    result = {
        "n_studies": n_studies,
        "proceed_meta_analysis": n_studies >= MIN_SUBGROUP_SIZE
    }

    if n_studies < MIN_SUBGROUP_SIZE:
        logger.warning(f"Sample size ({n_studies}) is below threshold ({MIN_SUBGROUP_SIZE}). "
                       f"Switching to descriptive synthesis (FR-014).")
        
        # Perform descriptive synthesis
        synthesis_result = perform_descriptive_synthesis(df)
        
        # Format the report
        report_content = format_synthesis_report(synthesis_result, n_studies)
        
        # Ensure output directory exists
        output_path = Path(output_doc_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write the report
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        logger.info(f"Descriptive synthesis report written to {output_doc_path}")
        result["synthesis_report_path"] = str(output_path)
    else:
        logger.info(f"Sample size ({n_studies}) meets threshold ({MIN_SUBGROUP_SIZE}). "
                    f"Meta-analysis and subgroup regression should proceed.")
        
    return result

def main():
    """
    Entry point for the conditional synthesis script.
    """
    try:
        result = check_sample_size_and_route()
        print(f"Conditional Synthesis Check Complete.")
        print(f"  Studies Found: {result['n_studies']}")
        print(f"  Proceed to Meta-Analysis: {result['proceed_meta_analysis']}")
        if not result['proceed_meta_analysis']:
            print(f"  Descriptive Synthesis Generated: {result.get('synthesis_report_path', 'N/A')}")
        return 0
    except Exception as e:
        logger.error(f"Error in conditional synthesis check: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
