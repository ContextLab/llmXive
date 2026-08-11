import sys
import argparse
import json
import os
import traceback
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

# Import local modules
from analysis.data_loader import load_real_data
from analysis.data_cleaner import DataCleaner
from analysis.stat_utils import run_anova_pipeline, run_holm_bonferroni, generate_metrics_summary
from analysis.power_analysis import PowerCalculator
from analysis.report_generator import generate_report_summary
from analysis.visualizer import plot_completion_time, plot_error_count, plot_sus_score
from analysis.report_consistency_check import verify_consistency, compute_file_checksum

logger = logging.getLogger(__name__)

class DataValidationError(Exception):
    """Raised when data validation fails."""
    pass

def precondition_check(cleaned_path: Path) -> None:
    """
    Check if cleaned_sessions.csv exists before proceeding.
    Raises DataValidationError if missing.
    """
    if not cleaned_path.exists():
        raise DataValidationError(
            f"Precondition failed: {cleaned_path} is missing. "
            "Run cleaning pipeline first."
        )

def check_readiness(input_dir: Path, simulate: bool = False) -> bool:
    """
    Check if the project is ready to run analysis.
    Returns True if ready, False otherwise (logs errors).
    """
    errors = []
    
    raw_dir = input_dir / "raw"
    if not raw_dir.exists() or not list(raw_dir.glob("*")):
        if not simulate:
            errors.append(f"Raw data directory is empty or missing: {raw_dir}")
    
    if not simulate:
        # Check for real data presence logic if needed
        pass
        
    if errors:
        for err in errors:
            logger.error(err)
        return False
    return True

def execute_pipeline(
    input_dir: Path,
    output_dir: Path,
    simulate: bool = False
) -> Dict[str, Any]:
    """
    Execute the full analysis pipeline.
    """
    results = {}
    
    # 1. Load Data
    raw_files = list((input_dir / "raw").glob("*"))
    if not raw_files and not simulate:
        raise DataValidationError("No raw data files found in data/raw/")
    
    # In a real scenario, we would load from raw files.
    # For this implementation, we assume cleaned data exists or is generated.
    cleaned_path = output_dir / "cleaned_sessions.csv"
    
    if not cleaned_path.exists():
        # If cleaned data is missing, we might need to run the cleaner first.
        # However, for this task, we assume the pipeline is run in order.
        # If the file is missing, we raise an error.
        raise DataValidationError(f"Cleaned data missing: {cleaned_path}")
    
    # 2. Statistical Analysis
    logger.info("Running ANOVA pipeline...")
    try:
        anova_results = run_anova_pipeline(cleaned_path)
        results["anova"] = anova_results
    except Exception as e:
        logger.error(f"ANOVA failed: {e}")
        # Continue if possible, or fail depending on severity
        # For now, we assume it's critical
        raise
    
    # 3. Holm-Bonferroni
    logger.info("Applying Holm-Bonferroni correction...")
    corrected_results = run_holm_bonferroni(anova_results)
    results["corrected"] = corrected_results
    
    # 4. Generate Metrics Summary
    logger.info("Generating metrics summary...")
    metrics_path = output_dir / "metrics_summary.csv"
    generate_metrics_summary(corrected_results, metrics_path)
    results["metrics_path"] = str(metrics_path)
    
    # 5. Power Analysis
    logger.info("Running power analysis...")
    power_calc = PowerCalculator()
    power_results = power_calc.compute(cleaned_path)
    power_flags_path = output_dir / "power_flags.json"
    with open(power_flags_path, 'w') as f:
        json.dump(power_results, f, indent=2)
    results["power"] = power_results
    
    # 6. Visualizations
    logger.info("Generating visualizations...")
    plot_completion_time(cleaned_path, output_dir / "figures" / "completion_time.png")
    plot_error_count(cleaned_path, output_dir / "figures" / "error_count.png")
    plot_sus_score(cleaned_path, output_dir / "figures" / "sus_score.png")
    
    # 7. Generate Report
    logger.info("Generating report summary...")
    report_path = output_dir / "report_summary.txt"
    generate_report_summary(
        metrics_path=metrics_path,
        power_results=power_results,
        output_path=report_path
    )
    
    # 8. Report Consistency Check (T113)
    logger.info("Running report consistency check...")
    descriptive_path = output_dir / "descriptive_stats_explanation_engagement.csv"
    # Ensure descriptive stats file exists (it should be created by generate_metrics_summary or similar)
    # If it doesn't exist, we create a placeholder or error out.
    # For this task, we assume it exists if metrics_summary exists.
    if not descriptive_path.exists():
        # Create a minimal one if missing to satisfy the check, or fail.
        # Let's fail loudly if expected files are missing.
        raise DataValidationError(f"Descriptive stats file missing: {descriptive_path}")
    
    is_consistent, message = verify_consistency(
        report_path, metrics_path, descriptive_path
    )
    
    if not is_consistent:
        raise DataValidationError(f"Report consistency check failed: {message}")
    
    logger.info("Pipeline completed successfully.")
    return results

def write_report(results: Dict[str, Any], output_path: Path) -> None:
    """Write final results to a report file."""
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)

def main():
    parser = argparse.ArgumentParser(description="Run the full analysis pipeline.")
    parser.add_argument("--input", type=str, default="data", help="Input directory")
    parser.add_argument("--output", type=str, default="data/processed", help="Output directory")
    parser.add_argument("--simulate", action="store_true", help="Run in simulation mode")
    
    args = parser.parse_args()
    
    input_dir = Path(args.input)
    output_dir = Path(args.output)
    
    # Ensure output directories exist
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "figures").mkdir(parents=True, exist_ok=True)
    
    try:
        if not check_readiness(input_dir, args.simulate):
            sys.exit(1)
        
        results = execute_pipeline(input_dir, output_dir, args.simulate)
        print("Analysis completed successfully.")
        sys.exit(0)
        
    except DataValidationError as e:
        logger.error(f"Data validation error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()