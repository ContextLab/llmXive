import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from utils.logger import get_logger, log_error_context
from utils.validator import validate_generated_plots
from extraction.parser import parse_input
from analysis.meta_analysis import run_meta_analysis
from analysis.narrative import generate_narrative_summary
from analysis.bias import run_bias_assessment
from visualization.plots import run_visualization_analysis

logger = get_logger(__name__)

def run_pipeline(input_path: str, output_dir: str, plot_dir: str, max_plot_size_mb: int = 5):
    """
    Execute the full research pipeline.
    
    Args:
        input_path: Path to the raw input data (CSV or JSON).
        output_dir: Directory to write analysis results.
        plot_dir: Directory to write generated plots.
        max_plot_size_mb: Maximum allowed size for plot files in MB.
    """
    logger.info(f"Starting pipeline with input: {input_path}")
    
    # Ensure output directories exist
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    Path(plot_dir).mkdir(parents=True, exist_ok=True)
    
    # 1. Extraction
    studies = parse_input(input_path)
    if not studies:
        logger.warning("No studies found in input. Generating empty narrative.")
        narrative_result = generate_narrative_summary(studies, 0, "No studies found in input.")
        output_path = Path(output_dir) / "meta_analysis_result.json"
        with open(output_path, "w") as f:
            json.dump(narrative_result, f, indent=2)
        return 0
    
    # 2. Meta-Analysis
    meta_result = run_meta_analysis(studies)
    study_count = meta_result.get("study_count", 0)
    
    # 3. Bias & Heterogeneity (if N >= 10)
    bias_result = {}
    if study_count >= 10:
        logger.info("Running bias and heterogeneity analysis (N >= 10)")
        bias_result = run_bias_assessment(studies, meta_result)
        meta_result.update(bias_result)
    else:
        logger.info(f"Skipping bias analysis (N={study_count} < 10)")
        meta_result["bias_assessment"] = {
            "egger_test": "Skipped: Insufficient studies (N < 10) for Egger's regression",
            "heterogeneity": "Skipped: Insufficient studies (N < 10) for I² calculation"
        }
    
    # 4. Narrative Fallback (if N < 10)
    if study_count < 10:
        logger.info("Triggering narrative fallback (N < 10)")
        narrative_summary = generate_narrative_summary(studies, study_count, meta_result)
        meta_result["narrative_summary"] = narrative_summary
    
    # 5. Visualization
    logger.info("Generating visualizations")
    plot_files = run_visualization_analysis(meta_result, plot_dir)
    
    # 6. File Size Validation (T031)
    logger.info("Validating generated plot file sizes")
    max_size_bytes = max_plot_size_mb * 1024 * 1024
    all_valid, validation_results = validate_generated_plots(plot_dir, max_size_bytes)
    
    meta_result["validation"] = {
        "plot_size_check": "passed" if all_valid else "failed",
        "max_size_mb": max_plot_size_mb,
        "details": validation_results
    }
    
    if not all_valid:
        logger.error("Plot size validation failed. Pipeline completed with warnings.")
        # We do not exit with error code here to allow inspection, but we log the failure
    
    # 7. Save Final Results
    output_path = Path(output_dir) / "meta_analysis_result.json"
    with open(output_path, "w") as f:
        json.dump(meta_result, f, indent=2)
    
    logger.info(f"Pipeline completed. Results saved to {output_path}")
    return 0 if all_valid else 1

def main():
    """CLI entry point for the main pipeline."""
    parser = argparse.ArgumentParser(description="Run the brain connectivity meta-analysis pipeline")
    parser.add_argument("--input", required=True, help="Path to input data file (CSV/JSON)")
    parser.add_argument("--output-dir", default="data/derived", help="Directory for output files")
    parser.add_argument("--plot-dir", default="figures", help="Directory for generated plots")
    parser.add_argument("--max-plot-size", type=int, default=5, help="Max plot size in MB")
    
    args = parser.parse_args()
    
    try:
        return run_pipeline(args.input, args.output_dir, args.plot_dir, args.max_plot_size)
    except Exception as e:
        log_error_context(logger, e, {"input": args.input})
        return 1

if __name__ == "__main__":
    sys.exit(main())