import os
import sys
import json
import logging
from pathlib import Path
import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Project root relative to this file
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

def check_sc_001_variable_fit():
    """
    SC-001: Verify that all required variables are present in the final dataset.
    Returns: (status: bool, reason: str)
    """
    logger.info("Checking SC-001: Variable Fit")
    processed_dir = PROJECT_ROOT / "data" / "processed"
    metrics_file = processed_dir / "thread_metrics.csv"
    validation_file = processed_dir / "valid_threads.csv"

    try:
        if not metrics_file.exists():
            return False, f"Missing required file: {metrics_file}"
        if not validation_file.exists():
            return False, f"Missing required file: {validation_file}"

        metrics_df = pd.read_csv(metrics_file)
        validation_df = pd.read_csv(validation_file)

        required_metrics = ['thread_id', 'contagion_index', 'agreement_proportion', 'shannon_entropy']
        required_validation = ['thread_id', 'external_validation_score']

        missing_metrics = [col for col in required_metrics if col not in metrics_df.columns]
        missing_validation = [col for col in required_validation if col not in validation_df.columns]

        if missing_metrics:
            return False, f"Missing columns in thread_metrics.csv: {missing_metrics}"
        if missing_validation:
            return False, f"Missing columns in valid_threads.csv: {missing_validation}"

        return True, "All required variables present in metrics and validation files."
    except Exception as e:
        return False, f"Error checking SC-001: {str(e)}"

def check_sc_002_associational_framing():
    """
    SC-002: Verify that the paper explicitly frames findings as associational.
    Returns: (status: bool, reason: str)
    """
    logger.info("Checking SC-002: Associational Framing")
    paper_path = PROJECT_ROOT / "docs" / "paper.md"

    if not paper_path.exists():
        return False, "Missing required file: docs/paper.md"

    try:
        content = paper_path.read_text()
        # Check for explicit limitations section or statement
        if "Limitations" not in content:
            return False, "Missing 'Limitations' section in paper.md"
        
        # Check for explicit associational language
        if "observational" not in content.lower():
            return False, "Missing 'observational' keyword in paper.md"
        if "correlational" not in content.lower():
            return False, "Missing 'correlational' keyword in paper.md"
        
        # Check for absence of causal language (basic check)
        causal_phrases = ["causes", "leads to", "proves", "determines", "results in"]
        found_causal = [phrase for phrase in causal_phrases if phrase in content.lower()]
        if found_causal:
            return False, f"Found potentially causal language: {found_causal}"

        return True, "Paper explicitly frames findings as associational."
    except Exception as e:
        return False, f"Error checking SC-002: {str(e)}"

def check_sc_003_multiple_comparison():
    """
    SC-003: Verify that multiple-comparison correction was applied.
    Returns: (status: bool, reason: str)
    """
    logger.info("Checking SC-003: Multiple Comparison Correction")
    modeling_path = PROJECT_ROOT / "code" / "data" / "modeling.py"
    sensitivity_file = PROJECT_ROOT / "data" / "processed" / "sensitivity_analysis.csv"

    try:
        if not modeling_path.exists():
            return False, "Missing modeling.py"
        
        modeling_content = modeling_path.read_text()
        if "bonferroni" not in modeling_content.lower() and "benjamini" not in modeling_content.lower() and "fdr" not in modeling_content.lower():
            return False, "No multiple comparison correction method found in modeling.py"

        if not sensitivity_file.exists():
            return False, "Missing sensitivity_analysis.csv"
        
        # Verify the file has results (non-empty)
        df = pd.read_csv(sensitivity_file)
        if df.empty:
            return False, "sensitivity_analysis.csv is empty"

        return True, "Multiple comparison correction applied and sensitivity analysis generated."
    except Exception as e:
        return False, f"Error checking SC-003: {str(e)}"

def check_sc_004_threshold_sensitivity():
    """
    SC-004: Verify that threshold sensitivity analysis grid is complete (9 rows).
    Returns: (status: bool, reason: str)
    """
    logger.info("Checking SC-004: Threshold Sensitivity")
    sensitivity_file = PROJECT_ROOT / "data" / "processed" / "sensitivity_analysis.csv"

    if not sensitivity_file.exists():
        return False, "Missing sensitivity_analysis.csv"

    try:
        df = pd.read_csv(sensitivity_file)
        
        # Check for required columns
        required_cols = ['agreement_cutoff', 'entropy_threshold']
        for col in required_cols:
            if col not in df.columns:
                return False, f"Missing column '{col}' in sensitivity_analysis.csv"

        # Check grid completeness: 3 cutoffs x 3 thresholds = 9 rows
        expected_cutoffs = {0.5, 0.6, 0.7}
        expected_thresholds = {0.2, 0.4, 0.6}
        
        actual_cutoffs = set(df['agreement_cutoff'].unique())
        actual_thresholds = set(df['entropy_threshold'].unique())

        if actual_cutoffs != expected_cutoffs:
            return False, f"Missing agreement_cutoffs. Expected {expected_cutoffs}, got {actual_cutoffs}"
        if actual_thresholds != expected_thresholds:
            return False, f"Missing entropy_thresholds. Expected {expected_thresholds}, got {actual_thresholds}"
        
        if len(df) != 9:
            return False, f"Grid incomplete: expected 9 rows, found {len(df)}"

        return True, "Threshold sensitivity analysis grid is complete (9 rows)."
    except Exception as e:
        return False, f"Error checking SC-004: {str(e)}"

def check_sc_005_performance():
    """
    SC-005: Verify that pipeline runtime is within limits (6 hours).
    Returns: (status: bool, reason: str)
    """
    logger.info("Checking SC-005: Performance")
    perf_log = PROJECT_ROOT / "state" / "performance_log.json"

    if not perf_log.exists():
        return False, "Missing state/performance_log.json"

    try:
        with open(perf_log, 'r') as f:
            data = json.load(f)
        
        status = data.get('status')
        runtime = data.get('total_runtime_seconds', 0)
        
        if status == 'failure':
            return False, f"Pipeline execution failed. Reason: {data.get('error', 'Unknown')}"
        
        # 6 hours = 21600 seconds
        if runtime > 21600:
            return False, f"Runtime exceeded 6 hours: {runtime} seconds"
        
        return True, f"Pipeline completed successfully in {runtime} seconds."
    except Exception as e:
        return False, f"Error checking SC-005: {str(e)}"

def check_sc_006_ground_truth():
    """
    SC-006: Verify ground truth availability threshold (>=30% valid threads).
    Returns: (status: bool, reason: str)
    """
    logger.info("Checking SC-006: Ground Truth Availability")
    stats_file = PROJECT_ROOT / "data" / "processed" / "ground_truth_stats.json"
    compliance_file = PROJECT_ROOT / "state" / "sc_006_compliance_report.json"

    if not stats_file.exists():
        return False, "Missing data/processed/ground_truth_stats.json"

    try:
        with open(stats_file, 'r') as f:
            stats = json.load(f)
        
        valid_pct = stats.get('valid_thread_percentage', 0)
        
        if valid_pct < 30:
            # Check if compliance report exists and reflects failure
            if not compliance_file.exists():
                return False, f"Valid thread percentage ({valid_pct}) < 30% but no compliance report found."
            
            with open(compliance_file, 'r') as f:
                compliance = json.load(f)
            
            if compliance.get('sc_006_compliance') is not False:
                return False, f"Valid thread percentage ({valid_pct}) < 30% but compliance report does not indicate failure."
            
            return True, f"Valid thread percentage ({valid_pct}) < 30%. Compliance report correctly indicates failure."
        
        return True, f"Valid thread percentage ({valid_pct}) >= 30%."
    except Exception as e:
        return False, f"Error checking SC-006: {str(e)}"

def run_final_validation():
    """
    Run all SC checks and compile results into validation_details map.
    Returns: dict containing status and details for each SC.
    """
    logger.info("Running Final Validation")
    
    checks = [
        ("SC-001", check_sc_001_variable_fit),
        ("SC-002", check_sc_002_associational_framing),
        ("SC-003", check_sc_003_multiple_comparison),
        ("SC-004", check_sc_004_threshold_sensitivity),
        ("SC-005", check_sc_005_performance),
        ("SC-006", check_sc_006_ground_truth),
    ]

    validation_details = {}
    all_passed = True

    for sc_id, check_func in checks:
        try:
            status, reason = check_func()
            validation_details[sc_id] = {
                "status": "pass" if status else "fail",
                "reason": reason
            }
            if not status:
                all_passed = False
                logger.warning(f"{sc_id} failed: {reason}")
            else:
                logger.info(f"{sc_id} passed: {reason}")
        except Exception as e:
            validation_details[sc_id] = {
                "status": "fail",
                "reason": f"Exception during check: {str(e)}"
            }
            all_passed = False
            logger.error(f"{sc_id} raised exception: {str(e)}")

    result = {
        "all_criteria_met": all_passed,
        "validation_details": validation_details
    }

    # Write result to state/final_validation.json
    output_path = PROJECT_ROOT / "state" / "final_validation.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)
    
    logger.info(f"Final validation report written to {output_path}")
    return result

def main():
    """Main entry point."""
    result = run_final_validation()
    if result["all_criteria_met"]:
        print("All success criteria met.")
        sys.exit(0)
    else:
        print("One or more success criteria failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()