"""
Main analysis orchestration script.

This script orchestrates the full analysis pipeline:
1. Data Loading and Validation
2. Statistical Analysis (ANOVA, Holm-Bonferroni)
3. Power Analysis
4. Report Generation

Constitution Principle VII: Reproducibility and Transparency.
Spec FR-002 (Amended by T035a): Repeated Measures ANOVA is the required statistical test.
"""

import sys
import argparse
import json
import os
import traceback
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

import pandas as pd
import numpy as np

# Import from existing API surface
from analysis.data_cleaner import DataCleaner, main as clean_main
from analysis.stat_utils import (
    run_anova_pipeline,
    run_holm_bonferroni,
    calculate_effect_size,
    verify_primary_anova_pvalue,
    generate_metrics_summary
)
from analysis.power_analysis import PowerCalculator, main as power_main
from utils.logger import get_logger

# Configure logging
logger = get_logger(__name__)

class DataValidationError(Exception):
    """Custom exception for data validation failures."""
    pass

def load_and_validate_data(input_path: str) -> pd.DataFrame:
    """
    Load raw session data and validate it against the schema.

    Args:
        input_path: Path to the raw data directory or file.

    Returns:
        Cleaned DataFrame ready for analysis.

    Raises:
        DataValidationError: If data is missing or invalid.
    """
    input_dir = Path(input_path)
    
    if not input_dir.exists():
        raise DataValidationError(f"Input path does not exist: {input_path}")
    
    # Check for raw data files
    json_files = list(input_dir.glob("*.json"))
    if not json_files:
        raise DataValidationError(f"No JSON session files found in {input_path}")
    
    logger.info(f"Loading {len(json_files)} session files from {input_path}")
    
    # Load and concatenate all sessions
    sessions = []
    for json_file in json_files:
        try:
            with open(json_file, 'r') as f:
                session_data = json.load(f)
                sessions.append(session_data)
        except Exception as e:
            logger.warning(f"Failed to load {json_file}: {e}")
            continue
    
    if not sessions:
        raise DataValidationError("No valid session data could be loaded.")
    
    # Convert to DataFrame
    df = pd.DataFrame(sessions)
    
    # Validate required columns
    required_cols = ['participant_id', 'interface_type', 'completion_time', 'error_count']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise DataValidationError(f"Missing required columns: {missing_cols}")
    
    logger.info(f"Loaded {len(df)} sessions with columns: {list(df.columns)}")
    return df

def execute_pipeline(
    input_path: str,
    output_dir: str,
    state_file: Optional[str] = None,
    simulate: bool = False
) -> Dict[str, Any]:
    """
    Execute the full analysis pipeline.

    Args:
        input_path: Path to raw data.
        output_dir: Path to output directory.
        state_file: Path to state file for checksums.
        simulate: If True, allow simulation mode (dev only).

    Returns:
        Dictionary with pipeline results and paths.
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    results = {
        'cleaned_data': None,
        'metrics_summary': None,
        'power_flags': None,
        'report': None
    }
    
    try:
        # Step 1: Load and validate data
        logger.info("Step 1: Loading and validating data...")
        raw_data = load_and_validate_data(input_path)
        
        # Step 2: Clean data (filter incomplete, impute SUS)
        logger.info("Step 2: Cleaning data...")
        cleaner = DataCleaner()
        cleaned_data = cleaner.clean(raw_data)
        
        # Save cleaned data
        cleaned_csv_path = output_path / "cleaned_sessions.csv"
        cleaned_data.to_csv(cleaned_csv_path, index=False)
        logger.info(f"Saved cleaned data to {cleaned_csv_path}")
        results['cleaned_data'] = str(cleaned_csv_path)
        
        # Step 3: Statistical Analysis (Repeated Measures ANOVA)
        logger.info("Step 3: Running statistical analysis...")
        
        # Prepare data for ANOVA (long format)
        anova_data = cleaner.prepare_for_anova(cleaned_data)
        
        # Run ANOVA pipeline
        anova_results = run_anova_pipeline(anova_data)
        
        # Apply Holm-Bonferroni correction
        logger.info("Applying Holm-Bonferroni correction...")
        corrected_results = run_holm_bonferroni(anova_results)
        
        # Calculate effect sizes
        logger.info("Calculating effect sizes...")
        effect_sizes = calculate_effect_size(anova_data, corrected_results)
        
        # Verify primary ANOVA p-value
        logger.info("Verifying primary ANOVA p-value...")
        primary_verified = verify_primary_anova_pvalue(anova_results)
        
        # Generate metrics summary
        metrics_summary = generate_metrics_summary(
            corrected_results, 
            effect_sizes, 
            primary_verified
        )
        
        # Save metrics summary
        metrics_csv_path = output_path / "metrics_summary.csv"
        metrics_summary.to_csv(metrics_csv_path, index=False)
        logger.info(f"Saved metrics summary to {metrics_csv_path}")
        results['metrics_summary'] = str(metrics_csv_path)
        
        # Step 4: Power Analysis
        logger.info("Step 4: Running power analysis...")
        power_calculator = PowerCalculator()
        power_flags = power_calculator.analyze(cleaned_data, metrics_summary)
        
        # Save power flags
        power_json_path = output_path / "power_flags.json"
        with open(power_json_path, 'w') as f:
            json.dump(power_flags, f, indent=2)
        logger.info(f"Saved power flags to {power_json_path}")
        results['power_flags'] = str(power_json_path)
        
        # Check for underpowered subgroups
        underpowered = [k for k, v in power_flags.items() if v.get('flag') == 'UNDERPOWERED']
        if underpowered:
            logger.warning(f"UNDERPOWERED subgroups detected: {underpowered}")
        
        # Step 5: Write Report
        logger.info("Step 5: Writing report...")
        report_path = write_report(
            output_path,
            metrics_summary,
            power_flags,
            cleaned_data
        )
        results['report'] = str(report_path)
        
        # Update state file with checksums
        if state_file:
            from analysis.clean_data import compute_checksum
            checksums = {}
            for key, path in results.items():
                if path:
                    checksums[key] = compute_checksum(path)
            
            state_path = Path(state_file)
            state_path.parent.mkdir(parents=True, exist_ok=True)
            
            current_state = {}
            if state_path.exists():
                with open(state_path, 'r') as f:
                    current_state = json.load(f)
            
            current_state['artifact_hashes'] = checksums
            
            with open(state_path, 'w') as f:
                json.dump(current_state, f, indent=2)
            logger.info(f"Updated state file: {state_path}")
        
        return results
        
    except Exception as e:
        logger.error(f"Pipeline execution failed: {e}")
        traceback.print_exc()
        
        # Log error to file
        error_log_path = output_path / "error_log.txt"
        with open(error_log_path, 'w') as f:
            f.write(f"Pipeline Error: {str(e)}\n")
            f.write(traceback.format_exc())
        
        raise

def write_report(
    output_path: Path,
    metrics_summary: pd.DataFrame,
    power_flags: Dict[str, Any],
    cleaned_data: pd.DataFrame
) -> Path:
    """
    Write the final analysis report.

    Constitution Principle VII: Reproducibility and Transparency.
    Spec FR-002 (Amended by T035a): Repeated Measures ANOVA is the required statistical test.

    Args:
        output_path: Directory to write report.
        metrics_summary: DataFrame with ANOVA results.
        power_flags: Dictionary with power analysis results.
        cleaned_data: Cleaned session data.

    Returns:
        Path to the written report file.
    """
    report_path = output_path / "report_summary.txt"
    
    with open(report_path, 'w') as f:
        f.write("=" * 80 + "\n")
        f.write("USABILITY RESEARCH ANALYSIS REPORT\n")
        f.write("Project: Improving Accessibility and Usability of Complex Computer Systems\n")
        f.write("Spec Reference: FR-002 (Amended by T035a) - Repeated Measures ANOVA\n")
        f.write("Principle: Constitution Principle VII - Reproducibility and Transparency\n")
        f.write("=" * 80 + "\n\n")
        
        # Descriptive Statistics
        f.write("1. DESCRIPTIVE STATISTICS\n")
        f.write("-" * 40 + "\n")
        desc_stats = cleaned_data.groupby('interface_type').agg({
            'completion_time': ['mean', 'std', 'count'],
            'error_count': ['mean', 'std', 'count'],
            'sus_score': ['mean', 'std', 'count']
        })
        f.write(desc_stats.to_string())
        f.write("\n\n")
        
        # Statistical Analysis Results
        f.write("2. STATISTICAL ANALYSIS RESULTS\n")
        f.write("-" * 40 + "\n")
        f.write("Method: Repeated Measures ANOVA (within-subjects design)\n")
        f.write("Correction: Holm-Bonferroni for multiple comparisons\n")
        f.write("\n")
        f.write(metrics_summary.to_string())
        f.write("\n\n")
        
        # Power Analysis
        f.write("3. POWER ANALYSIS\n")
        f.write("-" * 40 + "\n")
        for subgroup, flags in power_flags.items():
            f.write(f"Subgroup: {subgroup}\n")
            f.write(f"  N: {flags.get('N', 'N/A')}\n")
            f.write(f"  Power: {flags.get('power', 'N/A'):.4f}\n")
            f.write(f"  Required N: {flags.get('required_N', 'N/A')}\n")
            f.write(f"  Status: {flags.get('flag', 'N/A')}\n")
            f.write("\n")
        
        # Conclusion
        f.write("4. CONCLUSION\n")
        f.write("-" * 40 + "\n")
        
        # Check if any significant results
        significant = metrics_summary[metrics_summary['adjusted_p_value'] < 0.05]
        if not significant.empty:
            f.write("Significant differences found between interface types:\n")
            for _, row in significant.iterrows():
                f.write(f"  - {row['metric_name']}: p = {row['adjusted_p_value']:.4f}\n")
        else:
            f.write("No statistically significant differences found at alpha = 0.05.\n")
        
        # Check power
        underpowered = [k for k, v in power_flags.items() if v.get('flag') == 'UNDERPOWERED']
        if underpowered:
            f.write(f"\nWARNING: Study may be underpowered for: {', '.join(underpowered)}\n")
        
        f.write("\n" + "=" * 80 + "\n")
        f.write("END OF REPORT\n")
        f.write("=" * 80 + "\n")
    
    logger.info(f"Report written to {report_path}")
    
    # Verify CSV has required columns
    required_cols = ['metric_name', 'interface_type', 'F_statistic', 'p_value', 'adjusted_p_value', 'effect_size']
    missing_cols = [col for col in required_cols if col not in metrics_summary.columns]
    if missing_cols:
        logger.warning(f"Metrics summary missing columns: {missing_cols}")
    else:
        logger.info("Metrics summary contains all required columns.")
    
    return report_path

def check_readiness(output_dir: str) -> bool:
    """
    Check if all required artifacts exist.

    Args:
        output_dir: Path to output directory.

    Returns:
        True if all artifacts exist, False otherwise.
    """
    output_path = Path(output_dir)
    required_files = [
        "cleaned_sessions.csv",
        "metrics_summary.csv",
        "power_flags.json",
        "report_summary.txt",
        "figures/completion_time.png",
        "figures/error_count.png",
        "figures/sus_score.png"
    ]
    
    missing = []
    for file in required_files:
        if not (output_path / file).exists():
            missing.append(file)
    
    if missing:
        logger.warning(f"Missing artifacts: {missing}")
        return False
    
    logger.info("All required artifacts present.")
    return True

def main():
    """Main entry point for the analysis pipeline."""
    parser = argparse.ArgumentParser(
        description="Run the full usability analysis pipeline."
    )
    parser.add_argument(
        "--input",
        type=str,
        required=True,
        help="Path to raw data directory"
    )
    parser.add_argument(
        "--output",
        type=str,
        required=True,
        help="Path to output directory"
    )
    parser.add_argument(
        "--state-file",
        type=str,
        default=None,
        help="Path to state file for checksums"
    )
    parser.add_argument(
        "--simulate",
        action="store_true",
        help="Enable simulation mode (dev only)"
    )
    
    args = parser.parse_args()
    
    try:
        results = execute_pipeline(
            input_path=args.input,
            output_dir=args.output,
            state_file=args.state_file,
            simulate=args.simulate
        )
        
        logger.info("Pipeline completed successfully!")
        logger.info(f"Results: {results}")
        
        # Check readiness
        if check_readiness(args.output):
            logger.info("Readiness check passed.")
        else:
            logger.warning("Readiness check failed.")
            sys.exit(1)
            
    except DataValidationError as e:
        logger.error(f"Data validation error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()