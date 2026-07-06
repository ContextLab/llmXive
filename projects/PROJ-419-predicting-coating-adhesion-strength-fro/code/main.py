import os
import sys
import logging
import yaml
import pandas as pd
from pathlib import Path
from typing import Dict, Any, Optional

# Import from sibling modules based on provided API surface
from utils import (
    write_halt_signal,
    calculate_exclusion_ratio,
    calculate_processing_success_rate,
    check_sample_size_power_analysis
)
from evaluation import (
    load_processed_data,
    run_baseline_evaluation_pipeline,
    execute_nadeau_bengio_ttest,
    apply_bonferroni_correction,
    flag_informative_null
)
from preprocessing import create_preprocessing_pipeline_full

# Constants
LOG_LEVEL = logging.INFO
PROJECT_ROOT = Path(__file__).resolve().parent.parent
STATE_DIR = PROJECT_ROOT / "state"
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
OUTPUT_REPORT_PATH = PROJECT_ROOT / "data" / "processed" / "final_statistical_comparison_report.yaml"
HALT_SIGNAL_PATH = STATE_DIR / "HALT_SIGNAL.yaml"

logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(PROJECT_ROOT / "logs" / "main.log", mode="a")
    ]
)
logger = logging.getLogger(__name__)

def check_halt_signal() -> bool:
    """Check if a halt signal exists and return True if found."""
    if HALT_SIGNAL_PATH.exists():
        logger.error("HALT SIGNAL DETECTED. Aborting execution.")
        return True
    return False

def calculate_validation_metrics(df: pd.DataFrame) -> Dict[str, float]:
    """Calculate validation metrics: exclusion ratio and success rate."""
    total_records = len(df)
    if total_records == 0:
        return {"exclusion_ratio": 1.0, "success_rate": 0.0}

    # Assuming 'target' column exists and we check for missing values
    # This logic aligns with T011/T024/T028 requirements
    missing_target = df['target'].isna().sum()
    exclusion_ratio = calculate_exclusion_ratio(missing_target, total_records)
    success_rate = calculate_processing_success_rate(total_records, missing_target)

    return {
        "exclusion_ratio": exclusion_ratio,
        "success_rate": success_rate,
        "total_records": total_records,
        "missing_target_count": int(missing_target)
    }

def enforce_validation_gate(metrics: Dict[str, float]) -> bool:
    """
    Enforce safety gates:
    - Success rate >= 95%
    - Exclusion ratio < 10%
    - Sample size N >= 1000 (Power Analysis)
    Returns True if gate passes, False otherwise.
    """
    success_rate = metrics.get("success_rate", 0.0)
    exclusion_ratio = metrics.get("exclusion_ratio", 1.0)
    total_records = metrics.get("total_records", 0)

    if success_rate < 0.95:
        logger.error(f"Validation Failed: Success rate {success_rate:.2%} < 95%")
        return False

    if exclusion_ratio >= 0.10:
        logger.error(f"Validation Failed: Exclusion ratio {exclusion_ratio:.2%} >= 10%")
        return False

    if not check_sample_size_power_analysis(total_records):
        logger.error(f"Validation Failed: Sample size {total_records} < 1000")
        return False

    logger.info("All validation gates passed.")
    return True

def write_halt_signal(reason: str):
    """Write a halt signal YAML file with the reason."""
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    signal_data = {
        "halted": True,
        "reason": reason,
        "timestamp": str(pd.Timestamp.now())
    }
    with open(HALT_SIGNAL_PATH, 'w') as f:
        yaml.dump(signal_data, f)
    logger.critical(f"Halt signal written to {HALT_SIGNAL_PATH}: {reason}")

def generate_final_report(
    model_results: Dict[str, Any],
    baseline_results: Dict[str, Any],
    statistical_tests: Dict[str, Any],
    validation_metrics: Dict[str, float]
) -> Dict[str, Any]:
    """
    Compile the final statistical comparison report (US-3).
    """
    report = {
        "report_type": "Final Statistical Comparison Report",
        "user_story": "US3",
        "task_id": "T050",
        "validation_metrics": validation_metrics,
        "model_performance": {
            "full_model": model_results.get("full_model_metrics", {}),
            "composition_baseline": baseline_results.get("composition_baseline_metrics", {}),
            "surface_baseline": baseline_results.get("surface_baseline_metrics", {})
        },
        "statistical_comparison": {
            "test_method": "Nadeau & Bengio Corrected T-Test",
            "bonferroni_corrected_p_values": statistical_tests.get("bonferroni_p_values", {}),
            "significant_differences": statistical_tests.get("significant_differences", []),
            "informative_null_flag": statistical_tests.get("informative_null_flag", False)
        },
        "conclusions": []
    }

    # Add conclusions based on results
    if statistical_tests.get("informative_null_flag"):
        report["conclusions"].append("Informative Null: Full model does not outperform baselines.")
    else:
        report["conclusions"].append("Full model significantly outperforms baselines.")

    return report

def main():
    """
    Main orchestration for US3: Statistical Comparison and Baseline Benchmarking.
    1. Check Halt Signal
    2. Load Processed Data
    3. Validate Data (Metrics)
    4. Run Evaluation Pipeline (Baselines + Full Model)
    5. Run Statistical Tests
    6. Generate Final Report
    """
    logger.info("Starting T050: Final Statistical Comparison Report Generation")

    # 1. Check Halt Signal
    if check_halt_signal():
        sys.exit(1)

    # Ensure output directories exist
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    (PROJECT_ROOT / "logs").mkdir(parents=True, exist_ok=True)

    try:
        # 2. Load Processed Data
        logger.info("Loading processed data...")
        data_path = DATA_PROCESSED_DIR / "coating_adhesion_dataset.csv"
        if not data_path.exists():
            error_msg = f"Processed data file not found: {data_path}"
            logger.error(error_msg)
            write_halt_signal(error_msg)
            sys.exit(1)

        df = load_processed_data(str(data_path))
        logger.info(f"Loaded {len(df)} records.")

        # 3. Validate Data
        logger.info("Calculating validation metrics...")
        metrics = calculate_validation_metrics(df)
        logger.info(f"Metrics: {metrics}")

        if not enforce_validation_gate(metrics):
            reason = "Validation Gate Failed"
            write_halt_signal(reason)
            sys.exit(1)

        # 4. Run Evaluation Pipeline
        logger.info("Running baseline evaluation pipeline...")
        # This function encapsulates training full, composition-only, and surface-only models
        # and performing cross-validation.
        evaluation_output = run_baseline_evaluation_pipeline(df)

        model_results = evaluation_output.get("model_results", {})
        baseline_results = evaluation_output.get("baseline_results", {})

        # 5. Run Statistical Tests
        logger.info("Executing statistical tests...")
        # Extract metrics from evaluation output for testing
        full_scores = model_results.get("cv_scores", [])
        comp_scores = baseline_results.get("composition_baseline_cv_scores", [])
        surf_scores = baseline_results.get("surface_baseline_cv_scores", [])

        ttest_results = execute_nadeau_bengio_ttest(full_scores, comp_scores, surf_scores)
        bonferroni_p_values = apply_bonferroni_correction(ttest_results["p_values"])
        informative_null = flag_informative_null(bonferroni_p_values)

        statistical_tests = {
            "bonferroni_p_values": bonferroni_p_values,
            "significant_differences": [k for k, v in bonferroni_p_values.items() if v < 0.05],
            "informative_null_flag": informative_null
        }

        # 6. Generate Final Report
        logger.info("Generating final statistical comparison report...")
        final_report = generate_final_report(
            model_results=model_results,
            baseline_results=baseline_results,
            statistical_tests=statistical_tests,
            validation_metrics=metrics
        )

        # Write report to disk
        with open(OUTPUT_REPORT_PATH, 'w') as f:
            yaml.dump(final_report, f, default_flow_style=False, sort_keys=False)

        logger.info(f"Final report successfully written to {OUTPUT_REPORT_PATH}")
        print(f"Success: Final report generated at {OUTPUT_REPORT_PATH}")

    except Exception as e:
        logger.critical(f"Pipeline execution failed: {str(e)}", exc_info=True)
        write_halt_signal(f"Pipeline Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()