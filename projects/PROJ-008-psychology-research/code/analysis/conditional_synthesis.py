"""
Conditional synthesis routing module.
Implements logic to suppress subgroup/meta-regression if N < 10
and switch to descriptive synthesis.
"""
import logging
import os
from typing import List, Dict, Any, Optional
from pathlib import Path

import pandas as pd

from code.utils.logging import get_logger
from code.analysis.descriptive_synthesis import perform_descriptive_synthesis, format_synthesis_report

logger = get_logger(__name__)

def check_sample_size_and_route(
    input_csv: str,
    output_docs: str,
    min_sample_size: int = 10
) -> Dict[str, Any]:
    """
    Check sample size of input data and route to appropriate analysis.
    
    Args:
        input_csv: Path to the cleaned studies CSV file.
        output_docs: Path to the output documentation directory.
        min_sample_size: Minimum number of studies required for meta-analysis.
        
    Returns:
        Dictionary containing analysis results and routing decision.
    """
    logger.info(f"Checking sample size for {input_csv} with threshold {min_sample_size}")
    
    if not os.path.exists(input_csv):
        raise FileNotFoundError(f"Input CSV file not found: {input_csv}")
    
    df = pd.read_csv(input_csv)
    n_studies = len(df)
    
    logger.info(f"Found {n_studies} studies in input data")
    
    result = {
        "n_studies": n_studies,
        "min_sample_size": min_sample_size,
        "route": None,
        "analysis_results": None
    }
    
    if n_studies < min_sample_size:
        logger.info(f"Sample size ({n_studies}) is below threshold ({min_sample_size}). "
                    f"Routing to descriptive synthesis.")
        result["route"] = "descriptive_synthesis"
        
        # Perform descriptive synthesis
        synthesis_result = perform_descriptive_synthesis(df)
        formatted_report = format_synthesis_report(synthesis_result)
        
        # Ensure output directory exists
        output_path = Path(output_docs)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Write report to file
        report_file = output_path / "native_synthesis.md"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(formatted_report)
        
        logger.info(f"Descriptive synthesis report written to {report_file}")
        
        result["analysis_results"] = {
            "type": "descriptive_synthesis",
            "report_file": str(report_file),
            "summary": synthesis_result
        }
    else:
        logger.info(f"Sample size ({n_studies}) meets threshold ({min_sample_size}). "
                    f"Routing to meta-analysis (not implemented in this task).")
        result["route"] = "meta_analysis"
        result["analysis_results"] = {
            "type": "meta_analysis",
            "note": "Meta-analysis path not implemented in this task. "
                    "Please run code/analysis/meta_analysis.py for full results."
        }
    
    return result

def main():
    """Main entry point for conditional synthesis routing."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Route analysis based on sample size")
    parser.add_argument(
        "--input",
        type=str,
        required=True,
        help="Path to the cleaned studies CSV file"
    )
    parser.add_argument(
        "--output-docs",
        type=str,
        default="docs",
        help="Path to the output documentation directory"
    )
    parser.add_argument(
        "--min-sample",
        type=int,
        default=10,
        help="Minimum number of studies for meta-analysis"
    )
    
    args = parser.parse_args()
    
    try:
        result = check_sample_size_and_route(
            args.input,
            args.output_docs,
            args.min_sample
        )
        
        print(f"Routing decision: {result['route']}")
        print(f"Studies found: {result['n_studies']}")
        
        if result['route'] == 'descriptive_synthesis':
            print(f"Report generated: {result['analysis_results']['report_file']}")
        
        return 0
    except Exception as e:
        logger.error(f"Error in conditional synthesis routing: {e}")
        raise

if __name__ == "__main__":
    main()
