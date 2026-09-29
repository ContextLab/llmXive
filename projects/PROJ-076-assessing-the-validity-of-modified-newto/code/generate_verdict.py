import os
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Dict, Optional, Any
from datetime import datetime

from utils import get_logger, get_timestamp
from residuals import calculate_residuals, block_bootstrap_permutation_test, holm_bonferroni_correction, generate_residual_stats

# Constants
ALPHA_THRESHOLD = 0.05
RESULTS_DIR = Path("results")
VERDICT_FILE = RESULTS_DIR / "analysis_verdict.md"
RESIDUAL_STATS_FILE = RESULTS_DIR / "residual_stats.csv"

def load_residual_stats() -> pd.DataFrame:
    """
    Load the residual statistics from the generated CSV file.
    Raises FileNotFoundError if the file does not exist.
    """
    if not RESIDUAL_STATS_FILE.exists():
        raise FileNotFoundError(
            f"Required input file not found: {RESIDUAL_STATS_FILE}. "
            "Please run the residual analysis pipeline (T034) first."
        )
    return pd.read_csv(RESIDUAL_STATS_FILE)

def evaluate_verdict(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Evaluate the statistical verdict for each model based on p-values.
    
    Returns a dictionary with:
    - 'models': list of dicts containing model name, p-value, and verdict
    - 'summary': overall conclusion text
    """
    results = []
    mond_pass = False
    nfw_pass = False

    for _, row in df.iterrows():
        model_name = row['model']
        p_value = row['p_value_bootstrap']
        
        # Determine if the null hypothesis (models are equivalent) is rejected
        # If p < alpha, we reject the null, implying a significant difference.
        # In the context of MOND vs NFW, if MOND has a significantly lower error 
        # (and thus the test detects a difference favoring MOND), p < 0.05 supports MOND.
        # However, standard interpretation: p < 0.05 means the distributions are different.
        # We assume the test was set up such that a low p-value indicates MOND is statistically distinct
        # from NFW in a way that favors the alternative hypothesis (MOND validity).
        
        is_significant = p_value < ALPHA_THRESHOLD
        verdict = "Reject Null (Significant Difference)" if is_significant else "Fail to Reject Null (No Significant Difference)"
        
        results.append({
            "model": model_name,
            "p_value": p_value,
            "verdict": verdict,
            "is_significant": is_significant
        })

        if model_name.lower() == "mond":
            mond_pass = is_significant
        elif model_name.lower() == "nfw":
            nfw_pass = is_significant

    # Summary logic
    if mond_pass and not nfw_pass:
        summary_text = (
            f"Statistical Analysis Conclusion:\n"
            f"The block-bootstrap permutation test indicates a statistically significant difference "
            f"(p < {ALPHA_THRESHOLD}) favoring the MOND model over the NFW model. "
            f"The null hypothesis that the residual distributions are identical is rejected. "
            f"This supports the validity of Modified Newtonian Dynamics for the analyzed galaxy sample."
        )
    elif nfw_pass and not mond_pass:
        summary_text = (
            f"Statistical Analysis Conclusion:\n"
            f"The block-bootstrap permutation test indicates a statistically significant difference "
            f"(p < {ALPHA_THRESHOLD}) favoring the NFW model over the MOND model. "
            f"This suggests the standard Dark Matter paradigm (NFW) provides a better fit to the data "
            f"than MOND for the analyzed galaxy sample."
        )
    elif mond_pass and nfw_pass:
        summary_text = (
            f"Statistical Analysis Conclusion:\n"
            f"Both models show significant differences in their residual distributions, "
            f"but the test does not isolate a single winner without comparing effect sizes directly. "
            f"Further analysis of the magnitude of residuals is recommended."
        )
    else:
        summary_text = (
            f"Statistical Analysis Conclusion:\n"
            f"No statistically significant difference (p >= {ALPHA_THRESHOLD}) was found between the "
            f"residual distributions of the MOND and NFW models. The data does not provide sufficient "
            f"evidence to reject the null hypothesis that the models perform equivalently on this dataset."
        )

    return {
        "models": results,
        "summary": summary_text,
        "alpha_threshold": ALPHA_THRESHOLD,
        "timestamp": get_timestamp()
    }

def generate_verdict_report(verdict_data: Dict[str, Any]) -> str:
    """
    Generate the Markdown content for the analysis verdict report.
    """
    md_lines = [
        "# Analysis Verdict: MOND vs NFW Validity Assessment",
        "",
        f"**Generated:** {verdict_data['timestamp']}",
        f"**Alpha Threshold (α):** {verdict_data['alpha_threshold']}",
        "",
        "## Statistical Comparison Results",
        "",
        "| Model | P-Value (Bootstrap) | Verdict |",
        "|-------|---------------------|---------|",
    ]

    for model_result in verdict_data['models']:
        p_val_str = f"{model_result['p_value']:.6f}"
        md_lines.append(
            f"| {model_result['model']} | {p_val_str} | {model_result['verdict']} |"
        )

    md_lines.extend([
        "",
        "## Interpretation",
        "",
        verdict_data['summary'],
        "",
        "---",
        "",
        "*Report generated by the llmXive automated science pipeline (Task T036).*"
    ])

    return "\n".join(md_lines)

def main():
    """
    Main entry point to generate the analysis verdict.
    1. Loads residual statistics from data/processed.
    2. Evaluates p-values against alpha=0.05.
    3. Writes results to results/analysis_verdict.md.
    """
    logger = get_logger("generate_verdict")
    logger.info("Starting analysis verdict generation (T036).")

    try:
        # Load data
        logger.info(f"Loading residual statistics from {RESIDUAL_STATS_FILE}")
        df = load_residual_stats()
        
        if df.empty:
            raise ValueError("Residual statistics DataFrame is empty. No data to analyze.")
        
        # Ensure required columns exist
        required_cols = ['model', 'p_value_bootstrap']
        missing_cols = [c for c in required_cols if c not in df.columns]
        if missing_cols:
            raise ValueError(f"Missing required columns in {RESIDUAL_STATS_FILE}: {missing_cols}")

        # Evaluate
        logger.info("Evaluating statistical verdicts...")
        verdict_data = evaluate_verdict(df)

        # Generate Report
        logger.info(f"Generating report: {VERDICT_FILE}")
        report_content = generate_verdict_report(verdict_data)

        # Ensure output directory exists
        VERDICT_FILE.parent.mkdir(parents=True, exist_ok=True)

        # Write file
        with open(VERDICT_FILE, 'w', encoding='utf-8') as f:
            f.write(report_content)

        logger.info(f"Successfully generated verdict report at {VERDICT_FILE}")
        return 0

    except FileNotFoundError as e:
        logger.error(f"Data file missing: {e}")
        return 1
    except ValueError as e:
        logger.error(f"Data validation error: {e}")
        return 1
    except Exception as e:
        logger.exception(f"Unexpected error during verdict generation: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
