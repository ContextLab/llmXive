"""
Generate the final report YAML (data/processed/report.yaml) for the solder hardness analysis.

This script aggregates model metrics, SHAP rankings, and validation status to produce
a comprehensive report with inherent associational framing and power limitation warnings.

Dependencies:
  - T025 (XGBoost training results)
  - T026 (Linear Regression training results)
  - T030 (SHAP analysis results)
  - T027a (Paired t-test results)
  - T014 (Ingestion status for power limitation check)
"""
import os
import sys
import json
import yaml
import logging
from pathlib import Path
from typing import Dict, Any, Optional

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from config import get_data_processed_dir, get_data_outputs_dir
from utils.logging_config import get_logger

logger = get_logger(__name__)

# Constants for framing
ASSOCIATIONAL_WARNING = "Findings are associational, not causal."
POWER_LIMITATION_WARNING = "Statistical power limited due to N < 100."


def load_json_file(file_path: Path) -> Optional[Dict[str, Any]]:
    """Load a JSON file and return its contents as a dictionary."""
    if not file_path.exists():
        logger.warning(f"File not found: {file_path}. Skipping.")
        return None
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON from {file_path}: {e}")
        return None


def load_yaml_file(file_path: Path) -> Optional[Dict[str, Any]]:
    """Load a YAML file and return its contents as a dictionary."""
    if not file_path.exists():
        logger.warning(f"File not found: {file_path}. Skipping.")
        return None
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except yaml.YAMLError as e:
        logger.error(f"Failed to parse YAML from {file_path}: {e}")
        return None


def load_ingestion_status() -> Optional[Dict[str, Any]]:
    """Load the ingestion status to check for power limitations."""
    status_path = get_data_processed_dir() / ".ingestion_status.json"
    return load_json_file(status_path)


def load_model_metrics() -> Dict[str, Any]:
    """Load model metrics from training outputs."""
    metrics = {}
    
    # Try to load XGBoost metrics
    xgb_path = get_data_processed_dir() / "xgboost_metrics.json"
    if xgb_path.exists():
        metrics['xgboost'] = load_json_file(xgb_path)
    
    # Try to load Linear Regression metrics
    lr_path = get_data_processed_dir() / "linear_metrics.json"
    if lr_path.exists():
        metrics['linear'] = load_json_file(lr_path)
        
    # Try to load test set metrics if available
    test_metrics_path = get_data_processed_dir() / "test_metrics.yaml"
    if test_metrics_path.exists():
        metrics['test_set'] = load_yaml_file(test_metrics_path)
        
    return metrics


def load_shap_ranking() -> Optional[Dict[str, Any]]:
    """Load SHAP feature ranking."""
    shap_path = get_data_processed_dir() / "shap_ranking.yaml"
    return load_yaml_file(shap_path)


def load_ttest_results() -> Optional[Dict[str, Any]]:
    """Load paired t-test results."""
    ttest_path = get_data_processed_dir() / "paired_ttest_results.yaml"
    return load_yaml_file(ttest_path)


def determine_power_limitation(ingestion_status: Optional[Dict[str, Any]]) -> Optional[str]:
    """
    Determine if a power limitation warning is needed based on ingestion status.
    
    Returns the warning string if N < 100, otherwise None.
    """
    if not ingestion_status:
        logger.warning("Ingestion status not found. Cannot determine power limitation.")
        return POWER_LIMITATION_WARNING  # Default to warning if status is missing
        
    exact_n = ingestion_status.get('exact_N', 0)
    if exact_n < 100:
        return POWER_LIMITATION_WARNING
    return None


def generate_report() -> Dict[str, Any]:
    """
    Generate the comprehensive report dictionary.
    
    Returns a dictionary with the following structure:
    {
        "metadata": {
            "associational_framing_warning": str,
            "power_limitation_warning": str | None
        },
        "model_comparison": {
            "xgboost_metrics": dict,
            "linear_metrics": dict,
            "ttest_results": dict | None
        },
        "feature_importance": {
            "shap_ranking": list | None
        },
        "summary": {
            "best_model": str,
            "key_findings": list
        }
    }
    """
    # Load all required data
    ingestion_status = load_ingestion_status()
    model_metrics = load_model_metrics()
    shap_ranking = load_shap_ranking()
    ttest_results = load_ttest_results()
    
    # Determine warnings
    power_warning = determine_power_limitation(ingestion_status)
    
    # Build the report
    report = {
        "metadata": {
            "associational_framing_warning": ASSOCIATIONAL_WARNING,
            "power_limitation_warning": power_warning
        },
        "model_comparison": {
            "xgboost_metrics": model_metrics.get('xgboost'),
            "linear_metrics": model_metrics.get('linear'),
            "ttest_results": ttest_results
        },
        "feature_importance": {
            "shap_ranking": shap_ranking
        },
        "summary": {
            "best_model": "xgboost" if model_metrics.get('xgboost') else "linear",
            "key_findings": []
        }
    }
    
    # Add key findings based on available data
    findings = []
    
    if model_metrics.get('xgboost'):
        xgb_r2 = model_metrics['xgboost'].get('r2_score', 'N/A')
        findings.append(f"XGBoost model achieved R² = {xgb_r2}")
        
    if model_metrics.get('linear'):
        lr_r2 = model_metrics['linear'].get('r2_score', 'N/A')
        findings.append(f"Linear Regression model achieved R² = {lr_r2}")
        
    if ttest_results:
        p_value = ttest_results.get('p_value', 'N/A')
        significant = ttest_results.get('significant', False)
        findings.append(f"Model comparison t-test: p = {p_value}, significant = {significant}")
        
    if shap_ranking:
        top_features = shap_ranking.get('top_features', [])
        if top_features:
            top_feature_names = [f['feature_name'] for f in top_features[:3]]
            findings.append(f"Top predictive features: {', '.join(top_feature_names)}")
            
    report['summary']['key_findings'] = findings
    
    return report


def save_report(report: Dict[str, Any], output_path: Path) -> None:
    """Save the report to a YAML file."""
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            yaml.dump(report, f, default_flow_style=False, sort_keys=False)
        logger.info(f"Report successfully saved to {output_path}")
    except IOError as e:
        logger.error(f"Failed to save report to {output_path}: {e}")
        raise


def main():
    """Main entry point for the report generation script."""
    logger.info("Starting report generation (T031c)...")
    
    # Ensure output directory exists
    output_dir = get_data_processed_dir()
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_path = output_dir / "report.yaml"
    
    try:
        # Generate the report
        report = generate_report()
        
        # Save the report
        save_report(report, output_path)
        
        logger.info("Report generation completed successfully.")
        return 0
        
    except Exception as e:
        logger.error(f"Report generation failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())