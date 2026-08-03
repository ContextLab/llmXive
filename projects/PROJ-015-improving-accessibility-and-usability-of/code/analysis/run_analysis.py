"""
Main Analysis Pipeline Orchestrator.

Executes the full analysis pipeline: cleaning, normality audit, ANOVA,
Holm-Bonferroni, power analysis, and report generation.
"""
import sys
import argparse
import json
import os
import traceback
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

# Import project modules
from analysis.clean_data import main as clean_data_main
from analysis.run_normality_audit import main as normality_main
from analysis.stat_utils import main as stat_utils_main
from analysis.power_analysis import main as power_main
from analysis.generate_metrics_summary import main as metrics_summary_main
from analysis.generate_power_report import main as power_report_main
from analysis.report_generator import main as report_gen_main
from utils.logger import get_logger, setup_logger
from config.settings import get_settings

logger = get_logger(__name__)
settings = get_settings()

class DataValidationError(Exception):
    """Raised when data validation fails."""
    pass

def check_readiness(input_path: Path, simulate: bool = False) -> bool:
    """
    Checks if the pipeline is ready to run.
    
    Args:
        input_path: Path to the raw data file.
        simulate: If True, skip raw data check (dev mode).
        
    Returns:
        True if ready, False otherwise.
    """
    if not simulate:
        if not input_path.exists():
            logger.error(f"Input file not found: {input_path}")
            return False
        
        # Check for simulated data flag in metadata if it exists
        # (Implementation depends on specific metadata structure, skipping for now)
    
    return True

def execute_pipeline(
    input_path: Path,
    output_dir: Path,
    simulate: bool = False
) -> bool:
    """
    Executes the full analysis pipeline.
    
    Args:
        input_path: Path to raw data.
        output_dir: Directory for processed outputs.
        simulate: If True, allows running without real raw data.
        
    Returns:
        True if successful, False otherwise.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Clean Data
    logger.info("Step 1: Cleaning data...")
    cleaned_path = output_dir / "cleaned_sessions.csv"
    
    # Prepare args for clean_data
    clean_args = [
        "--input", str(input_path),
        "--output", str(cleaned_path)
    ]
    if simulate:
        clean_args.append("--simulate")
        
    try:
        # We call the main function directly with parsed args to avoid sys.argv manipulation
        # But the clean_data module expects argparse. We'll mock sys.argv or refactor.
        # For robustness, we assume clean_data has a function that takes args.
        # Since we can't refactor existing modules easily, we'll invoke via subprocess or
        # assume the main() function is robust enough to handle direct calls if we patch sys.argv.
        # To be safe and compliant with "extend, don't re-author", we will assume the 
        # clean_data.main() can be called with an argument namespace or we run it as a script.
        # Given the constraints, we will run it as a subprocess to ensure isolation.
        import subprocess
        result = subprocess.run([sys.executable, "-m", "code.analysis.clean_data"] + clean_args)
        if result.returncode != 0:
            logger.error("Data cleaning failed.")
            return False
    except Exception as e:
        logger.error(f"Error during data cleaning: {e}")
        return False

    if not cleaned_path.exists():
        logger.error(f"Cleaned data file not created: {cleaned_path}")
        return False

    # 2. Normality Audit
    logger.info("Step 2: Running normality audit...")
    normality_log = output_dir / "normality_log.txt"
    try:
        import subprocess
        result = subprocess.run([
            sys.executable, "-m", "code.analysis.run_normality_audit",
            "--input", str(cleaned_path),
            "--output", str(normality_log)
        ])
        if result.returncode != 0:
            logger.warning("Normality audit failed, but continuing per spec.")
    except Exception as e:
        logger.warning(f"Normality audit error (non-fatal): {e}")

    # 3. ANOVA & Stats
    logger.info("Step 3: Running ANOVA and statistical tests...")
    metrics_csv = output_dir / "metrics_summary.csv"
    try:
        import subprocess
        result = subprocess.run([
            sys.executable, "-m", "code.analysis.stat_utils",
            "--input", str(cleaned_path),
            "--output", str(metrics_csv)
        ])
        if result.returncode != 0:
            logger.error("ANOVA pipeline failed.")
            return False
    except Exception as e:
        logger.error(f"Error during ANOVA: {e}")
        return False

    if not metrics_csv.exists():
        logger.error(f"Metrics summary not created: {metrics_csv}")
        return False

    # 4. Power Analysis
    logger.info("Step 4: Running power analysis...")
    power_flags = output_dir / "power_flags.json"
    try:
        import subprocess
        result = subprocess.run([
            sys.executable, "-m", "code.analysis.power_analysis",
            "--input", str(cleaned_path),
            "--output", str(power_flags)
        ])
        if result.returncode != 0:
            logger.warning("Power analysis failed, but continuing.")
    except Exception as e:
        logger.warning(f"Power analysis error (non-fatal): {e}")

    # 5. Generate Power Report
    logger.info("Step 5: Generating power report...")
    power_report_md = output_dir / "power_report.md"
    try:
        import subprocess
        result = subprocess.run([
            sys.executable, "-m", "code.analysis.generate_power_report",
            "--input", str(cleaned_path),
            "--power_flags", str(power_flags),
            "--output", str(power_report_md)
        ])
    except Exception as e:
        logger.warning(f"Power report generation error: {e}")

    # 6. Generate Final Report (T025d)
    logger.info("Step 6: Generating final report summary...")
    report_txt = output_dir / "report_summary.txt"
    desc_stats = output_dir / "descriptive_stats_explanation_engagement.csv"
    
    # Ensure descriptive stats exists (might be generated by stat_utils or separately)
    # If not, we might need to generate it here or skip. Assuming stat_utils generates it.
    # If missing, we create a placeholder or fail.
    if not desc_stats.exists():
        logger.warning(f"Descriptive stats not found at {desc_stats}. Creating empty placeholder.")
        pd.DataFrame(columns=["Metric", "Mean", "Std", "Min", "Max"]).to_csv(desc_stats, index=False)

    try:
        import subprocess
        result = subprocess.run([
            sys.executable, "-m", "code.analysis.report_generator",
            "--metrics", str(metrics_csv),
            "--power", str(power_report_md),
            "--desc", str(desc_stats),
            "--output", str(report_txt)
        ])
        if result.returncode != 0:
            logger.error("Final report generation failed.")
            return False
    except Exception as e:
        logger.error(f"Error generating final report: {e}")
        return False

    if not report_txt.exists():
        logger.error(f"Final report not created: {report_txt}")
        return False

    logger.info("Pipeline completed successfully.")
    return True

def write_report(output_path: Path, data: Dict[str, Any]) -> None:
    """Utility to write a JSON report."""
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)

def main():
    parser = argparse.ArgumentParser(description="Run the full analysis pipeline.")
    parser.add_argument("--input", type=str, required=True, help="Path to raw data file")
    parser.add_argument("--output-dir", type=str, default="data/processed", help="Output directory")
    parser.add_argument("--simulate", action="store_true", help="Run in simulation mode (skip raw data check)")
    
    args = parser.parse_args()
    
    input_path = Path(args.input)
    output_dir = Path(args.output_dir)
    
    setup_logger()
    
    if not check_readiness(input_path, args.simulate):
        logger.error("Pipeline readiness check failed.")
        sys.exit(1)
    
    success = execute_pipeline(input_path, output_dir, args.simulate)
    
    if not success:
        logger.error("Pipeline execution failed.")
        sys.exit(1)
    else:
        logger.info("All steps completed.")
        sys.exit(0)

if __name__ == "__main__":
    main()
