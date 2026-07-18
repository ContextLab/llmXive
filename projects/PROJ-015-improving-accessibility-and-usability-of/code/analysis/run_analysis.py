import sys
import argparse
import json
import os
from pathlib import Path
import pandas as pd
import numpy as np

# Local imports matching the API surface provided
from analysis.data_cleaner import DataCleaner, main as clean_main
from analysis.stat_utils import (
    run_anova_pipeline,
    run_holm_bonferroni,
    calculate_effect_size,
    generate_metrics_summary,
    main as stat_main
)
from analysis.power_analysis import PowerCalculator, main as power_main
from analysis.report_generator import ReportGenerator, main as report_main
from utils.logger import get_logger, get_project_root
from utils.seed import set_seed
from simulator.simulator import generate_simulated_data, main as sim_main

logger = get_logger(__name__)

def log_normality_test(results: dict, output_path: Path):
    """Log Shapiro-Wilk results to file."""
    with open(output_path, 'w') as f:
        f.write("Normality Test Results (Shapiro-Wilk)\n")
        f.write("=" * 40 + "\n")
        for metric, res in results.items():
            f.write(f"Metric: {metric}\n")
            f.write(f"  W: {res['W']:.4f}\n")
            f.write(f"  p-value: {res['p_value']:.4f}\n")
            f.write(f"  Normal: {'Yes' if res['is_normal'] else 'No'}\n\n")
    logger.info(f"Normality log written to {output_path}")

def log_test_selection_decision(decision: str, output_path: Path):
    """Log the decision on which test to use based on normality."""
    with open(output_path, 'w') as f:
        f.write("Test Selection Decision\n")
        f.write("=" * 40 + "\n")
        f.write(f"Decision: {decision}\n")
        f.write("Reasoning: ANOVA is robust to minor deviations; "
                "per Constitution Principle VII, ANOVA is always run.\n")
    logger.info(f"Test selection log written to {output_path}")

def log_exclusion_decision(count_excluded: int, count_remaining: int, output_path: Path):
    """Log exclusion decisions."""
    with open(output_path, 'w') as f:
        f.write("Exclusion Log\n")
        f.write("=" * 40 + "\n")
        f.write(f"Sessions excluded: {count_excluded}\n")
        f.write(f"Sessions remaining: {count_remaining}\n")
    logger.info(f"Exclusion log written to {output_path}")

def run_analysis_pipeline(input_path: Path, output_dir: Path, simulate: bool = False, seed: int = 42):
    """
    Main orchestration logic for the analysis pipeline.
    
    Args:
        input_path: Path to cleaned_sessions.csv
        output_dir: Directory to write outputs
        simulate: If True, generate simulated data if input is missing.
                  MUST be explicitly allowed by CI environment.
        seed: Random seed for reproducibility.
    """
    set_seed(seed)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Check for input data
    if not input_path.exists():
        if simulate:
            # Check CI environment variable to prevent accidental production use
            ci_simulate = os.environ.get('CI_SIMULATE', 'false').lower()
            if ci_simulate != 'true':
                logger.error("Simulate flag is set, but CI_SIMULATE is not 'true'. "
                             "Refusing to generate synthetic data for production claims.")
                logger.error("To enable simulation for local CI validation, set CI_SIMULATE=true")
                sys.exit(1)
            
            logger.info("Input data missing. Generating simulated data for local validation...")
            # Generate simulated data directly to the raw directory, then clean it
            raw_dir = output_dir.parent.parent / "raw"
            raw_dir.mkdir(parents=True, exist_ok=True)
            sim_output = raw_dir / "simulated_sessions.json"
            generate_simulated_data(n=50, seed=seed, output_path=str(sim_output))
            
            # Re-run cleaning to produce the input CSV
            logger.info("Running cleaning pipeline on simulated data...")
            # We assume the cleaner looks for raw JSONs in data/raw
            clean_main() 
            
            if not input_path.exists():
                logger.error("Failed to generate cleaned input data from simulation.")
                sys.exit(1)
        else:
            logger.error(f"Input file {input_path} not found. "
                         "Run data collection or use --simulate for local validation.")
            sys.exit(1)

    # 2. Load and Validate Data
    logger.info(f"Loading cleaned data from {input_path}")
    try:
        df = pd.read_csv(input_path)
    except Exception as e:
        logger.error(f"Failed to load CSV: {e}")
        sys.exit(1)

    # Validate exact columns
    required_cols = [
        'participant_id', 'interface_type', 'completion_time_seconds',
        'error_count', 'sus_score', 'explanation_engagement_time_seconds'
    ]
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        logger.error(f"Missing required columns: {missing_cols}")
        sys.exit(1)

    # Type and range checks
    try:
        df['completion_time_seconds'] = pd.to_numeric(df['completion_time_seconds'], errors='raise')
        df['error_count'] = pd.to_numeric(df['error_count'], errors='raise').astype(int)
        df['sus_score'] = pd.to_numeric(df['sus_score'], errors='raise').astype(int)
        df['explanation_engagement_time_seconds'] = pd.to_numeric(
            df['explanation_engagement_time_seconds'], errors='raise'
        )
        
        # Range checks
        if (df['completion_time_seconds'] < 0).any():
            raise ValueError("Completion time cannot be negative")
        if (df['error_count'] < 0).any():
            raise ValueError("Error count cannot be negative")
        if (df['sus_score'] < 0).any() or (df['sus_score'] > 100).any():
            raise ValueError("SUS score must be between 0 and 100")
        
        logger.info("Data validation passed.")
    except Exception as e:
        logger.error(f"Data validation failed: {e}")
        sys.exit(1)

    # 3. Normality Test (Shapiro-Wilk)
    logger.info("Running Shapiro-Wilk normality tests...")
    normality_results = {}
    metrics_to_test = ['completion_time_seconds', 'error_count', 'sus_score']
    
    for metric in metrics_to_test:
        # Group by interface to check difference scores or residuals
        # For simplicity in this pipeline, we check the distribution of the metric
        # In a strict repeated measures design, we'd test the difference between conditions
        if metric in df.columns:
            # Assuming we test the combined distribution or per group for robustness
            # Here we test the per-group distributions as a proxy
            for iface in df['interface_type'].unique():
                subset = df[df['interface_type'] == iface][metric]
                if len(subset) > 3:
                    stat, p_val = stats.shapiro(subset)
                    normality_results[f"{metric}_{iface}"] = {
                        'W': stat,
                        'p_value': p_val,
                        'is_normal': p_val > 0.05
                    }
    
    normality_log = output_dir / "normality_log.txt"
    log_normality_test(normality_results, normality_log)

    # 4. Log Test Selection (Always ANOVA per Principle VII)
    decision_log = output_dir / "primary_test_verification.txt"
    log_test_selection_decision("Repeated Measures ANOVA", decision_log)

    # 5. Run ANOVA Pipeline
    logger.info("Running Repeated Measures ANOVA...")
    # We pass the dataframe and specify the within-subject factor (interface_type)
    # and the metrics to test
    anova_results = run_anova_pipeline(
        df, 
        within_factor='interface_type',
        metrics=metrics_to_test,
        output_path=output_dir / "metrics_summary.csv"
    )

    # 6. Holm-Bonferroni Correction
    logger.info("Applying Holm-Bonferroni correction...")
    # The run_anova_pipeline might return raw p-values; we correct them
    # Assuming the output CSV has p_value and we need adjusted_p_value
    if os.path.exists(output_dir / "metrics_summary.csv"):
        summary_df = pd.read_csv(output_dir / "metrics_summary.csv")
        if 'p_value' in summary_df.columns:
            # Apply Holm-Bonferroni to the p-values in the summary
            # We need to group by metric or test all together?
            # Task says "for the multiple ANOVA comparisons" -> likely across metrics
            p_vals = summary_df['p_value'].values
            adjusted = run_holm_bonferroni(p_vals)
            summary_df['adjusted_p_value'] = adjusted
            summary_df.to_csv(output_dir / "metrics_summary.csv", index=False)
            logger.info("Holm-Bonferroni correction applied and saved.")

    # 7. Descriptive Stats (including excluded from ANOVA)
    logger.info("Computing descriptive statistics...")
    # T023b: explanation_engagement_time excluded from ANOVA but included here
    desc_stats = df.groupby('interface_type')[['completion_time_seconds', 'error_count', 
                                               'sus_score', 'explanation_engagement_time_seconds']].agg(['mean', 'std'])
    desc_stats.to_csv(output_dir / "descriptive_stats.csv")
    
    # Log exclusion of engagement time from ANOVA
    exclusion_log = output_dir / "exclusion_log.txt"
    with open(exclusion_log, 'w') as f:
        f.write("Exclusion Log\n")
        f.write("=" * 40 + "\n")
        f.write("Metric: explanation_engagement_time_seconds\n")
        f.write("Status: Excluded from ANOVA (T023b-exclude-enforce)\n")
        f.write("Reason: Not a primary performance metric for ANOVA; used for descriptive reporting only.\n")
    logger.info("Exclusion log written.")

    # 8. Power Analysis
    logger.info("Running Power Analysis...")
    power_main(input_csv=output_dir / "metrics_summary.csv", output_json=output_dir / "power_flags.json")

    # 9. Generate Report
    logger.info("Generating final report...")
    report_main(input_csv=output_dir / "metrics_summary.csv", 
                output_path=output_dir / "report_summary.txt")

    logger.info("Analysis pipeline completed successfully.")
    return True

def main():
    parser = argparse.ArgumentParser(description="Run the full statistical analysis pipeline.")
    parser.add_argument('--input', type=str, required=False, 
                        default='data/processed/cleaned_sessions.csv',
                        help='Path to the cleaned sessions CSV.')
    parser.add_argument('--output', type=str, required=False,
                        default='data/processed',
                        help='Output directory for analysis results.')
    parser.add_argument('--simulate', action='store_true',
                        help='Generate simulated data if input is missing. '
                             'MUST be used with CI_SIMULATE=true in production pipelines.')
    parser.add_argument('--seed', type=int, default=42,
                        help='Random seed for reproducibility.')
    
    args = parser.parse_args()
    
    input_path = Path(args.input)
    output_dir = Path(args.output)
    
    success = run_analysis_pipeline(
        input_path=input_path,
        output_dir=output_dir,
        simulate=args.simulate,
        seed=args.seed
    )
    
    if not success:
        sys.exit(1)
    sys.exit(0)

if __name__ == "__main__":
    main()