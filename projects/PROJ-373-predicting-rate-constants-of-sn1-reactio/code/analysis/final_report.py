import os
import sys
import json
import csv
import logging
import argparse
from pathlib import Path
from typing import Dict, Any, Optional, List

# Ensure project root is in path for imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from config import DataConfig, AnalysisConfig, ensure_dirs
from utils.logger import get_logger

def setup_logging():
    """Setup logging for the final report generation."""
    logger = get_logger("final_report", log_file="artifacts/final_report_generation.log")
    return logger

def load_json_file(file_path: str, logger: logging.Logger) -> Optional[Dict]:
    """Load a JSON file and return its contents."""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.warning(f"File not found: {file_path}")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding JSON from {file_path}: {e}")
        return None

def load_csv_file(file_path: str, logger: logging.Logger) -> List[Dict]:
    """Load a CSV file and return its contents as a list of dicts."""
    try:
        with open(file_path, 'r') as f:
            reader = csv.DictReader(f)
            return list(reader)
    except FileNotFoundError:
        logger.warning(f"File not found: {file_path}")
        return []
    except Exception as e:
        logger.error(f"Error reading CSV from {file_path}: {e}")
        return []

def load_md_file(file_path: str, logger: logging.Logger) -> str:
    """Load a Markdown file and return its contents."""
    try:
        with open(file_path, 'r') as f:
            return f.read()
    except FileNotFoundError:
        logger.warning(f"File not found: {file_path}")
        return ""
    except Exception as e:
        logger.error(f"Error reading Markdown from {file_path}: {e}")
        return ""

def evaluate_sc001(metrics_data: Optional[Dict], logger: logging.Logger) -> Dict[str, Any]:
    """
    Evaluate SC-001: MPNN R2 - Linear R2 > 0.05 AND p < 0.05.
    Returns a dict with 'status' (PASS/FAIL) and 'details'.
    """
    details = []
    passed = False
    
    if not metrics_data:
        details.append("Metrics data (metrics.json) is missing.")
        return {"status": "FAIL", "details": "; ".join(details)}

    # Assuming metrics_data has structure: {'mpnn': {'r2': ...}, 'linear': {'r2': ...}, 'bootstrap': {'p_value': ...}}
    # Or similar structure as defined in T021/T022.
    # We need to be robust. Let's look for keys.
    mpnn_r2 = None
    linear_r2 = None
    p_value = None

    # Attempt to extract values
    if 'mpnn' in metrics_data and isinstance(metrics_data['mpnn'], dict):
        mpnn_r2 = metrics_data['mpnn'].get('r2')
    if 'linear' in metrics_data and isinstance(metrics_data['linear'], dict):
        linear_r2 = metrics_data['linear'].get('r2')
    if 'bootstrap' in metrics_data and isinstance(metrics_data['bootstrap'], dict):
        p_value = metrics_data['bootstrap'].get('p_value')
    
    # Fallback: check top level if structure is flat
    if mpnn_r2 is None and 'mpnn_r2' in metrics_data:
        mpnn_r2 = metrics_data['mpnn_r2']
    if linear_r2 is None and 'linear_r2' in metrics_data:
        linear_r2 = metrics_data['linear_r2']
    if p_value is None and 'p_value' in metrics_data:
        p_value = metrics_data['p_value']

    if mpnn_r2 is None or linear_r2 is None:
        details.append("Could not find MPNN or Linear R2 values.")
        return {"status": "FAIL", "details": "; ".join(details)}

    diff = mpnn_r2 - linear_r2
    details.append(f"MPNN R2: {mpnn_r2}, Linear R2: {linear_r2}, Difference: {diff:.4f}")

    if p_value is None:
        details.append("Could not find p-value from bootstrap comparison.")
        return {"status": "FAIL", "details": "; ".join(details)}
    
    details.append(f"P-value: {p_value:.4f}")

    if diff > 0.05 and p_value < 0.05:
        passed = True
    
    return {"status": "PASS" if passed else "FAIL", "details": "; ".join(details)}

def evaluate_sc002(feasibility_data: Optional[Dict], logger: logging.Logger) -> Dict[str, Any]:
    """
    Evaluate SC-002: runtime <= 6 hours.
    Returns a dict with 'status' (PASS/FAIL) and 'details'.
    """
    details = []
    passed = False
    
    if not feasibility_data:
        details.append("Feasibility test log (feasibility_test_log.json) is missing.")
        return {"status": "FAIL", "details": "; ".join(details)}

    runtime_hours = feasibility_data.get('runtime_hours')
    if runtime_hours is None:
        details.append("Runtime data not found in feasibility log.")
        return {"status": "FAIL", "details": "; ".join(details)}

    details.append(f"Total runtime: {runtime_hours:.2f} hours")

    if runtime_hours <= 6.0:
        passed = True
        details.append("Runtime is within the 6-hour limit.")
    else:
        details.append("Runtime exceeded the 6-hour limit.")

    return {"status": "PASS" if passed else "FAIL", "details": "; ".join(details)}

def evaluate_sc003(sensitivity_data: Optional[Dict], logger: logging.Logger) -> Dict[str, Any]:
    """
    Evaluate SC-003: variance < 0.01.
    Sensitivity data comes from sensitivity_report.csv or similar aggregation.
    Returns a dict with 'status' (PASS/FAIL) and 'details'.
    """
    details = []
    passed = False

    # Try to load from artifacts/sensitivity_report.csv
    # The file should have an 'overall_variance' column or similar.
    # If not found, try to aggregate from other sources if needed, but spec says aggregate from T036/T037.
    # Assuming T027 produced artifacts/sensitivity_report.csv with 'overall_variance'.
    
    # Check if we have the aggregated data passed directly or load it.
    # For this function, we assume sensitivity_data is the parsed content of sensitivity_report.csv
    # or a dict containing the relevant variance.
    
    if not sensitivity_data:
        details.append("Sensitivity data (sensitivity_report.csv) is missing or empty.")
        return {"status": "FAIL", "details": "; ".join(details)}

    # If sensitivity_data is a list (from CSV), look for 'overall_variance'
    variance = None
    if isinstance(sensitivity_data, list) and len(sensitivity_data) > 0:
        row = sensitivity_data[0] # Assuming single row summary
        if 'overall_variance' in row:
            try:
                variance = float(row['overall_variance'])
            except ValueError:
                details.append("Could not parse 'overall_variance' as float.")
        elif 'variance' in row:
             # Fallback if column name is just 'variance'
             try:
                 variance = float(row['variance'])
             except ValueError:
                 details.append("Could not parse 'variance' as float.")
    
    # If passed as a dict directly
    if variance is None and isinstance(sensitivity_data, dict):
        variance = sensitivity_data.get('overall_variance') or sensitivity_data.get('variance')

    if variance is None:
        details.append("Could not find 'overall_variance' or 'variance' in sensitivity data.")
        return {"status": "FAIL", "details": "; ".join(details)}

    details.append(f"Overall variance: {variance:.6f}")

    if variance < 0.01:
        passed = True
        details.append("Variance is below the 0.01 threshold.")
    else:
        details.append("Variance exceeded the 0.01 threshold.")

    return {"status": "PASS" if passed else "FAIL", "details": "; ".join(details)}

def evaluate_sc004(consistency_data: Optional[Dict], perturbation_data: Optional[List], logger: logging.Logger) -> Dict[str, Any]:
    """
    Evaluate SC-004: consistency_score > threshold AND delta_r2 > threshold.
    Consistency from shap_consistency_report.md or json if parsed.
    Perturbation from perturbation_results.csv.
    Returns a dict with 'status' (PASS/FAIL) and 'details'.
    """
    details = []
    passed = False
    
    # SC-004 has two parts: consistency and perturbation drop.
    # We need to extract a consistency score and a delta_r2.
    
    # 1. Consistency Score
    consistency_score = None
    if consistency_data:
        # If consistency_data is a dict parsed from a JSON report
        if isinstance(consistency_data, dict):
            consistency_score = consistency_data.get('consistency_score') or consistency_data.get('kendall_tau')
        # If it's a string (from MD), we can't easily parse it here without regex, assuming JSON source or structured dict passed.
        # Given T035 outputs a .md, but we might have parsed it or a corresponding json.
        # Let's assume the caller provides a parsed dict if available, or we try to parse the MD string if passed.
        elif isinstance(consistency_data, str):
            # Very basic parsing for "consistency_score: 0.85"
            import re
            match = re.search(r'consistency_score[:\s]+([0-9.]+)', consistency_data, re.IGNORECASE)
            if match:
                try:
                    consistency_score = float(match.group(1))
                except ValueError:
                    pass
    
    # 2. Delta R2 from Perturbation
    delta_r2 = None
    if perturbation_data and len(perturbation_data) > 0:
        row = perturbation_data[0]
        if 'delta_r2' in row:
            try:
                delta_r2 = float(row['delta_r2'])
            except ValueError:
                details.append("Could not parse delta_r2 from perturbation results.")
        elif 'delta' in row:
             try:
                 delta_r2 = float(row['delta'])
             except ValueError:
                 details.append("Could not parse delta from perturbation results.")

    if consistency_score is None:
        details.append("Could not determine consistency score.")
        return {"status": "FAIL", "details": "; ".join(details)}
    
    if delta_r2 is None:
        details.append("Could not determine delta R2 from perturbation study.")
        return {"status": "FAIL", "details": "; ".join(details)}

    details.append(f"Consistency Score (Kendall's Tau): {consistency_score:.4f}")
    details.append(f"Perturbation Delta R2: {delta_r2:.4f}")

    # Thresholds: Usually > 0.7 for consistency, and > 0.01 or similar for delta (drop).
    # The spec says "consistency_score > threshold AND delta_r2 > threshold".
    # Assuming thresholds are 0.7 and 0.01 respectively based on typical ML robustness checks.
    # If delta_r2 is a drop, it should be positive (performance decrease).
    # If delta_r2 is negative (improvement), it might be a failure of the perturbation logic or unexpected.
    # We assume delta_r2 represents the magnitude of drop (positive value).
    
    threshold_consistency = 0.7
    threshold_delta = 0.01

    if consistency_score > threshold_consistency and delta_r2 > threshold_delta:
        passed = True
        details.append("Both consistency and perturbation drop meet thresholds.")
    else:
        details.append(f"Failed thresholds: Consistency > {threshold_consistency}, Delta > {threshold_delta}.")

    return {"status": "PASS" if passed else "FAIL", "details": "; ".join(details)}

def evaluate_sc005(success_rate_data: Optional[Dict], logger: logging.Logger) -> Dict[str, Any]:
    """
    Evaluate SC-005: success_rate >= 0.95.
    Data from success_rate.json.
    Returns a dict with 'status' (PASS/FAIL) and 'details'.
    """
    details = []
    passed = False

    if not success_rate_data:
        details.append("Success rate data (success_rate.json) is missing.")
        return {"status": "FAIL", "details": "; ".join(details)}

    rate = success_rate_data.get('success_rate')
    if rate is None:
        details.append("Could not find 'success_rate' in data.")
        return {"status": "FAIL", "details": "; ".join(details)}

    try:
        rate = float(rate)
    except ValueError:
        details.append("Could not parse 'success_rate' as float.")
        return {"status": "FAIL", "details": "; ".join(details)}

    details.append(f"Success Rate: {rate:.4f}")

    if rate >= 0.95:
        passed = True
        details.append("Success rate meets the 95% threshold.")
    else:
        details.append("Success rate is below the 95% threshold.")

    return {"status": "PASS" if passed else "FAIL", "details": "; ".join(details)}

def generate_limitations_section(logger: logging.Logger) -> str:
    """Generate the Limitations section of the report."""
    limitations = [
        "This study relies on the quality and completeness of the public SN1 kinetic datasets (DTS-SN1-15-01-2024, SN18-All-20240204).",
        "The use of Gasteiger charges as a substitute for PM7 calculations, while CPU-tractable, may introduce approximations in electronic description.",
        "The model's performance is bounded by the diversity of the training data; extrapolation to novel chemical spaces is not guaranteed.",
        "The perturbation study provides an associational robustness check, not a causal proof of mechanism.",
        "Computational constraints (CPU-only, 6-hour limit) restricted the depth of hyperparameter search and model architecture complexity."
    ]
    return "\n".join(["- " + line for line in limitations])

def generate_final_report(
    metrics_data: Optional[Dict],
    consistency_data: Optional[Dict],
    sensitivity_data: Optional[Dict],
    perturbation_data: Optional[List],
    collinearity_data: Optional[Dict],
    hyperparam_data: Optional[List],
    feasibility_data: Optional[Dict],
    success_rate_data: Optional[Dict],
    logger: logging.Logger
) -> str:
    """
    Generate the final comprehensive report string.
    """
    report_lines = []
    
    # Header
    report_lines.append("# Final Report")
    report_lines.append("")
    report_lines.append("## Executive Summary")
    report_lines.append("")
    report_lines.append("This report aggregates the results of the SN1 rate constant prediction pipeline, including model performance, interpretability, and robustness analyses. It provides a verification of the project's Success Criteria (SC-001 to SC-005).")
    report_lines.append("")

    # Evaluate SCs
    sc001 = evaluate_sc001(metrics_data, logger)
    sc002 = evaluate_sc002(feasibility_data, logger)
    sc003 = evaluate_sc003(sensitivity_data, logger)
    sc004 = evaluate_sc004(consistency_data, perturbation_data, logger)
    sc005 = evaluate_sc005(success_rate_data, logger)

    sc_results = [
        ("SC-001 (Model Superiority)", sc001),
        ("SC-002 (Runtime)", sc002),
        ("SC-003 (Sensitivity)", sc003),
        ("SC-004 (Consistency & Perturbation)", sc004),
        ("SC-005 (Data Success Rate)", sc005)
    ]

    report_lines.append("### Success Criteria Verification")
    report_lines.append("")
    report_lines.append("| Criterion | Status | Details |")
    report_lines.append("|---|---|---|")
    for name, res in sc_results:
        status_icon = "✅" if res['status'] == "PASS" else "❌"
        details = res['details']
        report_lines.append(f"| {name} | {status_icon} {res['status']} | {details} |")
    report_lines.append("")

    # Methodology
    report_lines.append("## Methodology")
    report_lines.append("")
    report_lines.append("1. **Data Ingestion**: Public SN1 kinetic datasets were ingested, validated, and preprocessed. Primary substrates were filtered out based on explicit `substrate_class` labels.")
    report_lines.append("2. **Descriptor Calculation**: Gasteiger partial charges and topological indices were computed using RDKit.")
    report_lines.append("3. **Model Training**: A Message Passing Neural Network (MPNN) was trained using random search hyperparameter optimization. Baselines (Linear Regression, Kernel Ridge Regression) were included for comparison.")
    report_lines.append("4. **Interpretability**: SHAP values were calculated to determine feature importance. Consistency across random seeds and perturbation studies were performed to assess robustness.")
    report_lines.append("5. **Collinearity**: Variance Inflation Factor (VIF) analysis was conducted to identify multicollinearity among descriptors.")
    report_lines.append("")

    # Results
    report_lines.append("## Results")
    report_lines.append("")
    
    if metrics_data:
        report_lines.append("### Model Performance")
        if 'mpnn' in metrics_data:
            mpnn = metrics_data['mpnn']
            report_lines.append(f"- **MPNN R²**: {mpnn.get('r2', 'N/A')}")
            report_lines.append(f"- **MPNN MAE**: {mpnn.get('mae', 'N/A')}")
        if 'linear' in metrics_data:
            lin = metrics_data['linear']
            report_lines.append(f"- **Linear Regression R²**: {lin.get('r2', 'N/A')}")
            report_lines.append(f"- **Linear Regression MAE**: {lin.get('mae', 'N/A')}")
        if 'bootstrap' in metrics_data:
            boot = metrics_data['bootstrap']
            report_lines.append(f"- **Bootstrap P-value**: {boot.get('p_value', 'N/A')}")
        report_lines.append("")

    if collinearity_data:
        report_lines.append("### Collinearity Analysis")
        report_lines.append("Highly correlated descriptor pairs (VIF > 5):")
        if 'pairs' in collinearity_data:
            for pair in collinearity_data['pairs']:
                report_lines.append(f"- {pair.get('descriptor_a')} & {pair.get('descriptor_b')}: VIF = {pair.get('vif_score', 'N/A')}")
        else:
            report_lines.append("- No highly correlated pairs found.")
        report_lines.append("")

    if hyperparam_data:
        report_lines.append("### Hyperparameter Search")
        report_lines.append("Top configurations from random search:")
        # Show top 3
        top_configs = sorted(hyperparam_data, key=lambda x: float(x.get('r2_val', 0)), reverse=True)[:3]
        for cfg in top_configs:
            report_lines.append(f"- Config {cfg.get('config_id')}: LR={cfg.get('learning_rate', 'N/A')}, Hidden={cfg.get('hidden_dim', 'N/A')}, Dropout={cfg.get('dropout', 'N/A')}, R²={cfg.get('r2_val', 'N/A')}")
        report_lines.append("")

    # Limitations
    report_lines.append("## Limitations")
    report_lines.append("")
    report_lines.append(generate_limitations_section(logger))
    report_lines.append("")

    # Conclusion
    report_lines.append("## Conclusion")
    report_lines.append("")
    passed_count = sum(1 for _, res in sc_results if res['status'] == "PASS")
    total_count = len(sc_results)
    report_lines.append(f"The pipeline successfully evaluated {passed_count} out of {total_count} Success Criteria.")
    if passed_count == total_count:
        report_lines.append("All project objectives have been met. The MPNN model demonstrates superior performance over basignals, and the results are robust across seeds and perturbations.")
    else:
        report_lines.append("While significant progress was made, some success criteria were not fully met. Further investigation into data quality, model architecture, or hyperparameter search space is recommended.")
    report_lines.append("")

    return "\n".join(report_lines)

def main():
    logger = setup_logging()
    logger.info("Starting final report generation.")

    # Define paths
    artifacts_dir = project_root / "artifacts"
    data_processed_dir = project_root / "data" / "processed"
    
    # Load data
    metrics_data = load_json_file(str(artifacts_dir / "metrics.json"), logger)
    feasibility_data = load_json_file(str(artifacts_dir / "feasibility_test_log.json"), logger)
    success_rate_data = load_json_file(str(data_processed_dir / "success_rate.json"), logger)
    
    # Load CSVs
    sensitivity_csv = load_csv_file(str(artifacts_dir / "sensitivity_report.csv"), logger)
    sensitivity_data = sensitivity_csv[0] if sensitivity_csv else None
    
    perturbation_csv = load_csv_file(str(artifacts_dir / "perturbation_results.csv"), logger)
    perturbation_data = perturbation_csv if perturbation_csv else None
    
    hyperparam_csv = load_csv_file(str(artifacts_dir / "hyperparameter_search.csv"), logger)
    
    collinearity_json = load_json_file(str(artifacts_dir / "collinearity_report.json"), logger)
    
    # Load MD if needed (for consistency score if not in JSON)
    consistency_md = load_md_file(str(artifacts_dir / "shap_consistency_report.md"), logger)
    # Try to parse consistency score from MD if not in a separate JSON
    consistency_data = None
    if consistency_md:
        # We'll pass the string to evaluate_sc004 which can try to parse it
        consistency_data = consistency_md

    # Generate report
    report_content = generate_final_report(
        metrics_data=metrics_data,
        consistency_data=consistency_data,
        sensitivity_data=sensitivity_data,
        perturbation_data=perturbation_data,
        collinearity_data=collinearity_json,
        hyperparam_data=hyperparam_csv,
        feasibility_data=feasibility_data,
        success_rate_data=success_rate_data,
        logger=logger
    )

    # Write report
    output_path = artifacts_dir / "final_report.md"
    ensure_dirs([artifacts_dir])
    with open(output_path, 'w') as f:
        f.write(report_content)
    
    logger.info(f"Final report generated at {output_path}")
    return 0

if __name__ == "__main__":
    sys.exit(main())