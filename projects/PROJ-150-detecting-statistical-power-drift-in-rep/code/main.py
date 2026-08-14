"""
Main pipeline orchestrator for the Statistical Power Drift Detection project.
Sequences: Download -> Validation -> LMM Fitting -> Robustness Checks -> Reporting.
"""
import os
import sys
import json
import logging
import pickle
from pathlib import Path
from datetime import datetime

# Project root setup
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DERIVED = PROJECT_ROOT / "data" / "derived"
RESULTS_DIR = PROJECT_ROOT / "results"
STATE_DIR = PROJECT_ROOT / "state"

# Ensure directories exist
DATA_DERIVED.mkdir(parents=True, exist_ok=True)
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
STATE_DIR.mkdir(parents=True, exist_ok=True)

# Import pipeline components based on API surface
from download import main as run_download, get_file_hash
from validate_source import main as run_validation
from compute_trends import load_and_prepare_data, fit_mixed_linear_model, save_results as save_trends_results
from analyze_drift import load_models, get_data_for_reduced_model, fit_reduced_model, perform_lrt, save_results as save_lrt_results
from robustness import load_lmm_summary, load_lrt_results, run_sensitivity_analysis, save_sensitivity_results, main as run_robustness
from visualize import main as run_visualization
from update_state import compute_sha256, find_artifacts, load_state, save_state
from logging_config import setup_logging, get_module_logger, log_operation_start, log_operation_complete

def generate_final_report(lmm_summary_path, lrt_results_path, permutation_results_path, sensitivity_results_path):
    """
    Integrates results from LMM, LRT, Permutation, and Sensitivity analyses
    into a single final report JSON.
    """
    log_operation_start("Final Report Generation")
    
    # Load LMM Summary
    lmm_data = None
    if os.path.exists(lmm_summary_path):
        with open(lmm_summary_path, 'r') as f:
            import csv
            reader = csv.DictReader(f)
            lmm_data = next(reader)
    else:
        logging.warning(f"LMM Summary not found at {lmm_summary_path}")

    # Load LRT Results
    lrt_data = None
    if os.path.exists(lrt_results_path):
        with open(lrt_results_path, 'r') as f:
            lrt_data = json.load(f)
    else:
        logging.warning(f"LRT Results not found at {lrt_results_path}")

    # Load Permutation Results
    perm_data = None
    if os.path.exists(permutation_results_path):
        with open(permutation_results_path, 'r') as f:
            perm_data = json.load(f)
    else:
        logging.warning(f"Permutation Results not found at {permutation_results_path}")

    # Load Sensitivity Results
    sens_data = None
    if os.path.exists(sensitivity_results_path):
        with open(sensitivity_results_path, 'r') as f:
            sens_data = json.load(f)
    else:
        logging.warning(f"Sensitivity Results not found at {sensitivity_results_path}")

    # Construct Report
    report = {
        "generated_at": datetime.now().isoformat(),
        "project_id": "PROJ-150-detecting-statistical-power-drift-in-rep",
        "analysis_summary": {
            "lmm_slope_year": float(lmm_data['slope_year']) if lmm_data else None,
            "lmm_se_year": float(lmm_data['se_year']) if lmm_data else None,
            "lmm_ci_lower": float(lmm_data['ci_lower']) if lmm_data else None,
            "lmm_ci_upper": float(lmm_data['ci_upper']) if lmm_data else None,
            "lrt_chi2": float(lrt_data['chi2_statistic']) if lrt_data else None,
            "lrt_p_value": float(lrt_data['p_value']) if lrt_data else None,
            "lrt_significant": bool(lrt_data.get('significant', False)) if lrt_data else None
        },
        "robustness_checks": {
            "permutation": {
                "p_value": float(perm_data.get('p_value')) if perm_data else None,
                "iterations": perm_data.get('iterations_run') if perm_data else None,
                "status": perm_data.get('status') if perm_data else None
            } if perm_data else None,
            "sensitivity": {
                "results": sens_data.get('results') if sens_data else None,
                "stable_across_alphas": sens_data.get('stable_across_alphas') if sens_data else None
            } if sens_data else None
        },
        "conclusion": {
            "drift_detected": False,
            "confidence": "high" if (lrt_data and perm_data and lrt_data.get('significant') and perm_data.get('p_value', 1.0) < 0.05) else "low",
            "notes": "Final integration of LMM, LRT, Permutation, and Sensitivity results."
        }
    }

    # Determine conclusion based on statistical evidence
    if lrt_data and perm_data:
        if lrt_data.get('significant') and perm_data.get('p_value', 1.0) < 0.05:
            report["conclusion"]["drift_detected"] = True
            report["conclusion"]["notes"] = "Statistical power drift detected with high confidence (LRT significant and Permutation p < 0.05)."
        elif lrt_data.get('significant'):
            report["conclusion"]["notes"] = "LRT indicates drift, but permutation test did not confirm at standard alpha."
        else:
            report["conclusion"]["notes"] = "No strong evidence of power drift detected."

    output_path = RESULTS_DIR / "final_report.json"
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    log_operation_complete("Final Report Generation", f"Report saved to {output_path}")
    return output_path

def main():
    """
    Orchestrates the full pipeline.
    """
    setup_logging()
    logger = get_module_logger("main")
    logger.info("Starting Power Drift Detection Pipeline")

    try:
        # 1. Download Data (if not present)
        logger.info("Step 1: Data Download")
        # Assuming download.py handles its own existence check or we run it
        # For robustness, we might check if data/raw exists first, but per task T006,
        # download.py is the fetcher.
        run_download() 
        # Ensure we have the hash for state
        data_file = PROJECT_ROOT / "data" / "raw" / "data.csv"
        if data_file.exists():
            file_hash = get_file_hash(str(data_file))
            logger.info(f"Data hash: {file_hash}")
        else:
            raise FileNotFoundError("Data file not found after download step.")

        # 2. Validate Source
        logger.info("Step 2: Source Validation")
        run_validation()

        # 3. Compute Trends (LMM) - T012a & T012b
        logger.info("Step 3: Compute Trends (LMM)")
        # load_and_prepare_data, fit_mixed_linear_model are called inside compute_trends main usually,
        # but if main() orchestrates, we might call it directly or rely on main().
        # Based on T012a description, compute_trends.py does the fitting and saving.
        # We will call the main of compute_trends which should do the full flow.
        from compute_trends import main as run_compute_trends
        run_compute_trends()

        # 4. Analyze Drift (LRT) - T013
        logger.info("Step 4: Analyze Drift (LRT)")
        from analyze_drift import main as run_analyze_drift
        run_analyze_drift()

        # 5. Robustness Checks (Permutation & Sensitivity) - T020, T021
        logger.info("Step 5: Robustness Checks")
        # robustness.py main should handle permutation and sensitivity if implemented there.
        # T020 and T021 are implemented in robustness.py.
        run_robustness()

        # 6. Visualization - T014
        logger.info("Step 6: Visualization")
        run_visualization()

        # 7. Generate Final Report - T022
        logger.info("Step 7: Generate Final Report")
        lmm_path = DATA_DERIVED / "lmm_summary.csv"
        lrt_path = DATA_DERIVED / "lrt_results.json"
        perm_path = RESULTS_DIR / "permutation_pvalue.json"
        sens_path = RESULTS_DIR / "sensitivity_results.json"

        final_report_path = generate_final_report(lmm_path, lrt_path, perm_path, sens_path)

        # 8. Update State - T008, T031
        logger.info("Step 8: Update State")
        # Find all artifacts in derived and results
        artifacts = find_artifacts([DATA_DERIVED, RESULTS_DIR])
        state_data = load_state()
        state_data['artifacts'] = {str(p): compute_sha256(p) for p in artifacts}
        state_data['current_stage'] = 'implemented'
        state_data['last_run'] = datetime.now().isoformat()
        save_state(state_data)

        logger.info("Pipeline completed successfully.")

    except Exception as e:
        logger.error(f"Pipeline failed: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()