"""
Main analysis pipeline orchestration script.
Implements the statistical engine wrapper as per Task T025c.
"""
import sys
import argparse
import json
import os
import traceback
import logging
from pathlib import Path
from datetime import datetime

# Import statistical functions from stat_utils (T022, T023a, T024)
# Note: shapiro_wilk is logged via log_normality_test in stat_utils
# anova_rm is run via run_anova_pipeline in stat_utils
# holm_bonferroni is run via run_holm_bonferroni in stat_utils
# descriptive_stats is run via run_descriptive_stats (separate module)
from analysis.stat_utils import (
    log_normality_test,
    run_anova_pipeline,
    run_holm_bonferroni,
    calculate_effect_size,
    verify_primary_anova_pvalue,
    generate_metrics_summary
)
from analysis.run_descriptive_stats import main as run_descriptive_stats_main
from analysis.data_cleaner import DataCleaner
from analysis.run_analysis import load_and_validate_data, validate_columns
from utils.logger import get_logger

# Ensure we can import from the project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

logger = get_logger("run_analysis")

def execute_pipeline(input_path: str, output_dir: str) -> bool:
    """
    Implements the statistical engine wrapper for Task T025c.
    
    Logic:
    1. Load and validate data (T025b).
    2. Run Shapiro-Wilk normality test (T022).
    3. Run Repeated Measures ANOVA (T023a).
    4. Run Holm-Bonferroni correction (T024).
    5. Compute descriptive statistics (T023b).
    6. Log any import or runtime errors to error_log.txt.
    
    Args:
        input_path: Path to cleaned_sessions.csv
        output_dir: Directory to write outputs (metrics_summary.csv, etc.)
        
    Returns:
        bool: True if pipeline completed successfully, False otherwise.
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    error_log_path = output_path / "error_log.txt"
    error_log = []
    
    try:
        logger.info(f"Starting analysis pipeline on {input_path}")
        
        # 1. Load and Validate Data (T025b)
        logger.info("Step 1: Loading and validating data...")
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"Input file not found: {input_path}")
        
        df = load_and_validate_data(input_path)
        if df is None:
            raise ValueError("Data validation failed. Check logs.")
        
        # 2. Shapiro-Wilk Normality Test (T022)
        # This logs to data/processed/normality_log.txt
        logger.info("Step 2: Running Shapiro-Wilk normality test...")
        log_normality_test(df, output_dir)
        
        # 3. Repeated Measures ANOVA (T023a)
        # This computes F-stat, p-value, effect size
        logger.info("Step 3: Running Repeated Measures ANOVA...")
        anova_results = run_anova_pipeline(df, output_dir)
        
        # 4. Holm-Bonferroni Correction (T024)
        logger.info("Step 4: Applying Holm-Bonferroni correction...")
        corrected_results = run_holm_bonferroni(anova_results, output_dir)
        
        # 5. Descriptive Statistics (T023b)
        # This writes descriptive_stats.csv
        logger.info("Step 5: Computing descriptive statistics...")
        # We call the main function of the descriptive stats module
        # It expects args, so we simulate them
        desc_args = argparse.Namespace(
            input=input_path,
            output=str(output_path / "descriptive_stats.csv"),
            log=str(output_path / "exclusion_log.txt")
        )
        run_descriptive_stats_main(desc_args)
        
        # 6. Generate Final Summary (T025d preparation)
        logger.info("Step 6: Generating metrics summary...")
        generate_metrics_summary(df, output_dir)
        
        logger.info("Pipeline completed successfully.")
        return True
        
    except Exception as e:
        error_msg = f"Pipeline failed at {datetime.now()}: {str(e)}\n{traceback.format_exc()}"
        error_log.append(error_msg)
        logger.error(error_msg)
        
        # Write error log immediately
        try:
            with open(error_log_path, 'w') as f:
                f.write("\n".join(error_log))
        except Exception as write_err:
            logger.error(f"Failed to write error log: {write_err}")
        
        return False

def write_report(output_dir: str) -> bool:
    """
    Writes the final report and verifies outputs.
    """
    output_path = Path(output_dir)
    summary_file = output_path / "metrics_summary.csv"
    report_file = output_path / "report_summary.txt"
    
    if not summary_file.exists():
        logger.error("metrics_summary.csv not found. Cannot write report.")
        return False
        
    try:
        import pandas as pd
        df = pd.read_csv(summary_file)
        
        required_cols = ['metric_name', 'interface_type', 'F_statistic', 'p_value', 'adjusted_p_value', 'effect_size']
        if not all(col in df.columns for col in required_cols):
            logger.error(f"metrics_summary.csv missing required columns. Found: {df.columns.tolist()}")
            return False
            
        with open(report_file, 'w') as f:
            f.write("Statistical Analysis Report\n")
            f.write("=" * 40 + "\n")
            f.write(f"Generated: {datetime.now()}\n")
            f.write("\n")
            f.write("Methodology Notes:\n")
            f.write("- Repeated Measures ANOVA used for all metrics.\n")
            f.write("- Holm-Bonferroni correction applied for multiple comparisons.\n")
            f.write("- Per Spec FR-002 (Amended by T035a) and Constitution Principle VII.\n")
            f.write("- Shapiro-Wilk logged for audit; Levene's test omitted (inappropriate for paired design).\n")
            f.write("\n")
            f.write("Results Summary:\n")
            f.write(df.to_string(index=False))
            
        logger.info(f"Report written to {report_file}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to write report: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Run the full statistical analysis pipeline.")
    parser.add_argument("--input", type=str, required=True, help="Path to cleaned_sessions.csv")
    parser.add_argument("--output", type=str, required=True, help="Output directory for results")
    parser.add_argument("--simulate", action="store_true", help="Run in simulation mode (for CI only)")
    
    args = parser.parse_args()
    
    # Check simulation flag enforcement (T033)
    if args.simulate:
        ci_env = os.getenv('CI_SIMULATE', 'false')
        if ci_env.lower() != 'true':
            logger.error("Production mode: simulation disabled. Set CI_SIMULATE=true for CI runs.")
            sys.exit(1)
    
    success = execute_pipeline(args.input, args.output)
    
    if success:
        report_success = write_report(args.output)
        if not report_success:
            sys.exit(1)
        logger.info("Analysis pipeline completed successfully.")
        sys.exit(0)
    else:
        logger.error("Analysis pipeline failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()