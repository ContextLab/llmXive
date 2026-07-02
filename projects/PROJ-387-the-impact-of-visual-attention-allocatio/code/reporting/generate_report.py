"""
Generate the final research report compiling LMM coefficients, corrected p-values,
and associational disclaimers.

This script aggregates results from the analysis phase (LMM models and Bonferroni
corrections) and produces a Markdown report file.
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from utils.logger import get_logger
from utils.config import get_output_path, get_project_root
from analysis.lmm_model import load_processed_data, run_lmm_analysis
from analysis.correction import load_lmm_results, apply_bonferroni_correction, save_results as save_correction_results
from utils.directories import ensure_directory

logger = get_logger(__name__)

# Constants
ASSOCIATIONAL_DISCLAIMER = (
    "DISCLAIMER: This report presents associational findings derived from "
    "statistical modeling. No causal inferences should be drawn from these results. "
    "Correlation does not imply causation."
)

def load_lmm_summary_csv(csv_path: Path) -> List[Dict[str, Any]]:
    """
    Load LMM summary results from a CSV file.
    
    Args:
        csv_path: Path to the LMM summary CSV file.
        
    Returns:
        List of dictionaries containing model results.
    """
    import pandas as pd
    
    if not csv_path.exists():
        raise FileNotFoundError(f"LMM summary file not found: {csv_path}")
        
    df = pd.read_csv(csv_path)
    results = []
    for _, row in df.iterrows():
        results.append({
            "metric": row.get("metric"),
            "valence": row.get("valence"),
            "coef": row.get("coef"),
            "p_raw": row.get("p_raw"),
            "std_err": row.get("std_err", None),
            "z_value": row.get("z_value", None)
        })
    return results

def load_correction_results_json(json_path: Path) -> List[Dict[str, Any]]:
    """
    Load Bonferroni correction results from a JSON file.
    
    Args:
        json_path: Path to the correction results JSON file.
        
    Returns:
        List of dictionaries containing corrected p-values.
    """
    if not json_path.exists():
        raise FileNotFoundError(f"Correction results file not found: {json_path}")
        
    with open(json_path, 'r') as f:
        data = json.load(f)
        
    if isinstance(data, list):
        return data
    elif isinstance(data, dict) and "results" in data:
        return data["results"]
    else:
        return [data]

def generate_report_content(
    lmm_results: List[Dict[str, Any]],
    correction_results: List[Dict[str, Any]],
    sensitivity_results: Optional[Dict[str, Any]] = None
) -> str:
    """
    Generate the Markdown content for the final report.
    
    Args:
        lmm_results: List of LMM model results.
        correction_results: List of corrected p-value results.
        sensitivity_results: Optional sensitivity analysis results.
        
    Returns:
        Formatted Markdown string.
    """
    lines = []
    lines.append("# Final Research Report: Visual Attention and Recall")
    lines.append("")
    lines.append("## Overview")
    lines.append("")
    lines.append("This report summarizes the statistical analysis of the relationship between ")
    lines.append("visual attention allocation metrics and recall accuracy for emotionally valenced stories.")
    lines.append("")
    lines.append(f"**Analysis Type**: Associational (Linear Mixed-Effects Modeling)")
    lines.append("")
    lines.append("## Methodology")
    lines.append("")
    lines.append("- **Model**: Linear Mixed-Effects Models (LMM) using statsmodels")
    lines.append("- **Correction**: Bonferroni correction for multiple comparisons")
    lines.append("- **Metrics Analyzed**: Fixation duration, saccade amplitude, gaze distribution")
    lines.append("- **Valence Categories**: Positive, Negative, Neutral")
    lines.append("")
    lines.append("## Disclaimer")
    lines.append("")
    lines.append(f"> {ASSOCIATIONAL_DISCLAIMER}")
    lines.append("")
    lines.append("## LMM Results Summary")
    lines.append("")
    lines.append("The following table presents the coefficients and p-values from the Linear Mixed-Effects Models.")
    lines.append("")
    lines.append("| Metric | Valence | Coefficient | Raw P-Value | Corrected P-Value | Significant (α=0.05) |")
    lines.append("|--------|---------|-------------|-------------|-------------------|----------------------|")
    
    # Create a lookup for corrected p-values
    correction_lookup = {}
    for item in correction_results:
        key = (item.get("metric"), item.get("valence"))
        correction_lookup[key] = item.get("p_corrected", item.get("p_value"))
        
    for result in lmm_results:
        metric = result.get("metric", "N/A")
        valence = result.get("valence", "N/A")
        coef = result.get("coef", "N/A")
        p_raw = result.get("p_raw", "N/A")
        
        key = (metric, valence)
        p_corrected = correction_lookup.get(key, "N/A")
        
        significant = "Yes" if (isinstance(p_corrected, (int, float)) and p_corrected < 0.05) else "No"
        
        lines.append(f"| {metric} | {valence} | {coef:.4f} | {p_raw:.4f} | {p_corrected} | {significant} |")
        
    lines.append("")
    lines.append("## Sensitivity Analysis")
    lines.append("")
    
    if sensitivity_results:
        lines.append("The following thresholds were evaluated for stability of findings:")
        lines.append("")
        lines.append("| Threshold | Significant Findings Count |")
        lines.append("|-----------|---------------------------|")
        for thresh, count in sensitivity_results.items():
            lines.append(f"| {thresh} | {count} |")
    else:
        lines.append("Sensitivity analysis was not performed or results were unavailable.")
        
    lines.append("")
    lines.append("## Conclusions")
    lines.append("")
    lines.append("This analysis identified associational patterns between visual attention metrics ")
    lines.append("and recall accuracy across different emotional valence categories. ")
    lines.append("Results should be interpreted with caution due to the associational nature of the study.")
    lines.append("")
    lines.append("---")
    lines.append(f"*Report generated by llmXive pipeline on {Path(__file__).stem}*")
    
    return "\n".join(lines)

def main():
    """Main entry point for report generation."""
    parser = argparse.ArgumentParser(description="Generate final research report")
    parser.add_argument(
        "--lmm-results",
        type=str,
        default=None,
        help="Path to LMM results CSV (default: auto-detect)"
    )
    parser.add_argument(
        "--correction-results",
        type=str,
        default=None,
        help="Path to correction results JSON (default: auto-detect)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output report path (default: output/results/final_report.md)"
    )
    parser.add_argument(
        "--sensitivity-results",
        type=str,
        default=None,
        help="Path to sensitivity analysis JSON (optional)"
    )
    
    args = parser.parse_args()
    
    project_root = get_project_root()
    
    # Determine paths
    if args.lmm_results:
        lmm_path = Path(args.lmm_results)
    else:
        lmm_path = project_root / "output" / "results" / "lmm_summary.csv"
        
    if args.correction_results:
        correction_path = Path(args.correction_results)
    else:
        correction_path = project_root / "output" / "results" / "correction_results.json"
        
    if args.output:
        output_path = Path(args.output)
    else:
        output_path = project_root / "output" / "results" / "final_report.md"
        
    if args.sensitivity_results:
        sensitivity_path = Path(args.sensitivity_results)
    else:
        sensitivity_path = project_root / "output" / "results" / "sensitivity_analysis.json"
        
    logger.info(f"Loading LMM results from: {lmm_path}")
    logger.info(f"Loading correction results from: {correction_path}")
    logger.info(f"Output report will be saved to: {output_path}")
    
    try:
        # Load results
        lmm_results = load_lmm_summary_csv(lmm_path)
        correction_results = load_correction_results_json(correction_path)
        
        sensitivity_results = None
        if sensitivity_path.exists():
            with open(sensitivity_path, 'r') as f:
                sensitivity_results = json.load(f)
                
        logger.info(f"Loaded {len(lmm_results)} LMM results and {len(correction_results)} correction results")
        
        # Generate report content
        report_content = generate_report_content(
            lmm_results,
            correction_results,
            sensitivity_results
        )
        
        # Ensure output directory exists
        ensure_directory(output_path.parent)
        
        # Write report
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report_content)
            
        logger.info(f"Report successfully generated: {output_path}")
        print(f"Report generated: {output_path}")
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"Required input file not found: {e}")
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        logger.error(f"Error generating report: {e}", exc_info=True)
        print(f"Error: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())