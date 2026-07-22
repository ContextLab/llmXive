"""
Main orchestration script for the statistical analysis pipeline.
Executes data cleaning, normality checks, ANOVA, and report generation.

Supports a --simulate flag for CI/local validation ONLY.
In production (CI_SIMULATE=false or no flag), it fails loudly if data is missing.
"""
import sys
import argparse
import json
import os
import traceback
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils.logger import get_logger
from analysis.data_cleaner import DataCleaner
from analysis.stat_utils import run_anova_pipeline, run_holm_bonferroni, log_normality_test, generate_metrics_summary
from analysis.power_analysis import PowerCalculator
from analysis.report_generator import ReportGenerator
from simulator.simulator import DeterministicDataSimulator

logger = get_logger(__name__)

def validate_columns(df):
    """
    Validate that the cleaned dataframe has the required columns.
    """
    required = ['participant_id', 'interface_type', 'completion_time_seconds', 
                'error_count', 'sus_score', 'explanation_engagement_time_seconds']
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Missing columns: {missing}")
    return True

def execute_pipeline(input_path: str, output_dir: str, simulate: bool = False):
    """
    Execute the full analysis pipeline.
    
    Args:
        input_path: Path to input data (raw or cleaned).
        output_dir: Output directory for results.
        simulate: If True, generate deterministic synthetic data if input is missing/empty.
                 ONLY for CI/local validation.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    cleaned_csv = output_dir / "cleaned_sessions.csv"
    metrics_csv = output_dir / "metrics_summary.csv"
    normality_log = output_dir / "normality_log.txt"
    power_flags = output_dir / "power_flags.json"
    report_txt = output_dir / "report_summary.txt"
    methodology_txt = output_dir / "methodology_notes.txt"
    
    logger.info(f"Starting analysis pipeline. Input: {input_path}")
    logger.info(f"Simulate mode: {simulate}")

    # Check CI environment variable for production enforcement
    ci_simulate_env = os.getenv('CI_SIMULATE', 'false').lower()
    if simulate and ci_simulate_env == 'false':
        logger.error("Production mode: simulation disabled. Set CI_SIMULATE=true in CI to allow simulation.")
        sys.exit(1)

    # 0. Handle Data Loading / Simulation
    # If input_path doesn't exist or is empty, and simulate is True, generate data.
    # If simulate is False and data is missing, fail loudly.
    
    import pandas as pd
    df = None
    
    if not Path(input_path).exists():
        if simulate:
            logger.warning(f"Input file {input_path} not found. Generating deterministic simulated data.")
            # Generate simulated data to the expected location or a temp location
            # The simulator writes to a specific output path. We'll generate to a temp file and read it.
            temp_raw_path = output_dir / "simulated_raw.json"
            try:
                simulator = DeterministicDataSimulator()
                # Generate a small dataset for validation (e.g., 20 participants)
                simulator.run(n_participants=20, output_path=str(temp_raw_path))
                
                # Now we need to run the cleaning pipeline on this simulated raw data
                # T021c logic: load_raw_sessions -> filter_incomplete -> impute_sus
                from analysis.clean_data import load_raw_sessions, filter_incomplete, impute_sus
                
                # Load raw sessions
                raw_sessions = load_raw_sessions(str(temp_raw_path))
                
                # Filter incomplete
                complete_sessions = filter_incomplete(raw_sessions)
                
                # Impute SUS
                imputed_sessions = impute_sus(complete_sessions)
                
                # Write cleaned CSV
                cleaned_df = pd.DataFrame(imputed_sessions)
                cleaned_df.to_csv(cleaned_csv, index=False)
                logger.info(f"Simulated data cleaned and saved to {cleaned_csv}")
                
                # Use the cleaned CSV as input for the rest of the pipeline
                input_path = str(cleaned_csv)
            except Exception as e:
                logger.error(f"Failed to generate or process simulated data: {e}")
                traceback.print_exc()
                sys.exit(1)
        else:
            logger.error(f"Input file {input_path} not found.")
            logger.error("Production mode: simulation disabled. Please provide real data.")
            sys.exit(1)
    else:
        # File exists, load it
        try:
            df = pd.read_csv(input_path)
            validate_columns(df)
            logger.info(f"Loaded data: {len(df)} rows.")
        except FileNotFoundError:
            logger.error(f"Data file not found: {input_path}")
            sys.exit(1)
        except Exception as e:
            logger.error(f"Failed to load data: {e}")
            sys.exit(1)

    # If we loaded from input_path directly (not simulated), df is already set.
    # If we simulated, we need to load the cleaned CSV we just wrote.
    if df is None:
        try:
            df = pd.read_csv(input_path)
            validate_columns(df)
            logger.info(f"Loaded data: {len(df)} rows.")
        except Exception as e:
            logger.error(f"Failed to load data after simulation: {e}")
            sys.exit(1)

    # 2. Normality Check (Audit only)
    try:
        log_normality_test(df, str(normality_log))
    except Exception as e:
        logger.warning(f"Normality test failed: {e}")

    # 3. Run ANOVA and Generate Metrics Summary
    # This calls T023a and T024 logic
    try:
        # We need to call the function that writes metrics_summary.csv
        from analysis.generate_metrics_summary import generate_metrics_summary as gen_summary
        gen_summary(df, str(metrics_csv))
        logger.info("ANOVA and metrics summary completed.")
    except Exception as e:
        logger.error(f"ANOVA pipeline failed: {e}")
        traceback.print_exc()
        sys.exit(1)

    # 4. Power Analysis
    try:
        calculator = PowerCalculator()
        calculator.compute_power(df, str(power_flags))
        logger.info("Power analysis completed.")
    except Exception as e:
        logger.warning(f"Power analysis failed: {e}")

    # 5. Generate Report
    try:
        generator = ReportGenerator()
        generator.generate_report(metrics_csv, str(report_txt))
        logger.info("Report generation completed.")
    except Exception as e:
        logger.warning(f"Report generation failed: {e}")

    # 6. Write Methodology Notes
    try:
        with open(methodology_txt, 'w') as f:
            f.write("Methodology Notes\n")
            f.write("=" * 20 + "\n\n")
            f.write("Statistical Tests Used:\n")
            f.write("- Repeated Measures ANOVA (per Spec FR-002 Amended by T035a)\n")
            f.write("- Holm-Bonferroni Correction for multiple comparisons\n")
            f.write("- Shapiro-Wilk Normality Test (Audit only)\n\n")
            f.write("Spec Reference:\n")
            f.write("FR-002 (Amended): System MUST implement Repeated Measures ANOVA.\n")
            f.write("Constitution Principle VII: Scientific rigor supersedes original spec text.\n")
        logger.info("Methodology notes written.")
    except Exception as e:
        logger.error(f"Failed to write methodology notes: {e}")

    logger.info("Pipeline execution finished.")

def main():
    parser = argparse.ArgumentParser(description="Run the full statistical analysis pipeline.")
    parser.add_argument("--input", type=str, default="data/processed/cleaned_sessions.csv",
                        help="Path to cleaned sessions CSV.")
    parser.add_argument("--output", type=str, default="data/processed",
                        help="Output directory for results.")
    parser.add_argument("--simulate", action="store_true",
                        help="Generate deterministic simulated data if input is missing. "
                             "ONLY for CI/local validation. Production runs will fail if data is missing.")
    
    args = parser.parse_args()
    
    execute_pipeline(args.input, args.output, simulate=args.simulate)

if __name__ == "__main__":
    main()