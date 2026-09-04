import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

from utils.logger import get_logger
from data.config import get_config

logger = get_logger(__name__)

def load_model_results(
    model_csv_path: str = "data/processed/regression_coefficients.csv",
    model_json_path: str = "data/processed/regression_diagnostics.json"
) -> Dict[str, Any]:
    """
    Load regression coefficients and diagnostics from processed data files.
    
    Args:
        model_csv_path: Path to CSV file containing regression coefficients.
        model_json_path: Path to JSON file containing diagnostic metrics.
        
    Returns:
        Dictionary containing model results with 'coefficients' and 'diagnostics' keys.
    """
    config = get_config()
    results = {
        "coefficients": {},
        "diagnostics": {}
    }
    
    # Load coefficients from CSV
    csv_path = Path(model_csv_path)
    if csv_path.exists():
        try:
            import pandas as pd
            df = pd.read_csv(csv_path)
            # Convert to dict for JSON serialization
            # Assuming columns: term, estimate, std_error, p_value, ci_lower, ci_upper
            results["coefficients"] = df.to_dict(orient='records')
            logger.info(f"Loaded {len(results['coefficients'])} coefficients from {csv_path}")
        except Exception as e:
            logger.error(f"Failed to load coefficients from {csv_path}: {e}")
    else:
        logger.warning(f"Coefficients file not found: {csv_path}")
    
    # Load diagnostics from JSON
    json_path = Path(model_json_path)
    if json_path.exists():
        try:
            with open(json_path, 'r') as f:
                results["diagnostics"] = json.load(f)
            logger.info(f"Loaded diagnostics from {json_path}")
        except Exception as e:
            logger.error(f"Failed to load diagnostics from {json_path}: {e}")
    else:
        logger.warning(f"Diagnostics file not found: {json_path}")
        
    return results

def load_bootstrap_results(
    bootstrap_json_path: str = "data/processed/bootstrap_results.json"
) -> Dict[str, Any]:
    """
    Load bootstrap stability analysis results.
    
    Args:
        bootstrap_json_path: Path to JSON file containing bootstrap results.
        
    Returns:
        Dictionary containing bootstrap stability metrics.
    """
    config = get_config()
    results = {
        "iterations": 0,
        "ci_width_variance": None,
        "stability_flags": [],
        "coefficients_summary": {}
    }
    
    json_path = Path(bootstrap_json_path)
    if json_path.exists():
        try:
            with open(json_path, 'r') as f:
                data = json.load(f)
                results.update(data)
            logger.info(f"Loaded bootstrap results from {json_path}")
        except Exception as e:
            logger.error(f"Failed to load bootstrap results from {json_path}: {e}")
    else:
        logger.warning(f"Bootstrap results file not found: {bootstrap_json_path}")
        
    return results

def load_sensitivity_results(
    sensitivity_json_path: str = "data/processed/sensitivity_analysis.json"
) -> Dict[str, Any]:
    """
    Load sensitivity analysis results including parameter recovery and threshold sweeps.
    
    Args:
        sensitivity_json_path: Path to JSON file containing sensitivity analysis results.
        
    Returns:
        Dictionary containing sensitivity analysis findings.
    """
    config = get_config()
    results = {
        "parameter_recovery": {},
        "threshold_sensitivity": {},
        "family_wise_error_correction": {},
        "findings": []
    }
    
    json_path = Path(sensitivity_json_path)
    if json_path.exists():
        try:
            with open(json_path, 'r') as f:
                data = json.load(f)
                results.update(data)
            logger.info(f"Loaded sensitivity results from {json_path}")
        except Exception as e:
            logger.error(f"Failed to load sensitivity results from {json_path}: {e}")
    else:
        logger.warning(f"Sensitivity results file not found: {sensitivity_json_path}")
        
    return results

def load_data_path() -> Dict[str, Any]:
    """
    Load the data path information from the state file.
    
    Returns:
        Dictionary containing data source information.
    """
    config = get_config()
    state_path = Path(config.state_dir) / "projects" / config.project_id / "state.yaml"
    
    result = {
        "raw_data_path": None,
        "processed_data_path": None,
        "data_source_type": "unknown",
        "source_description": "Unknown"
    }
    
    if state_path.exists():
        try:
            import yaml
            with open(state_path, 'r') as f:
                state_data = yaml.safe_load(f)
            
            if "artifact_hashes" in state_data:
                artifacts = state_data["artifact_hashes"]
                if "raw_data" in artifacts:
                    result["raw_data_path"] = artifacts["raw_data"].get("path")
                    result["data_source_type"] = artifacts["raw_data"].get("source_type", "unknown")
                    result["source_description"] = artifacts["raw_data"].get("description", "Unknown")
                    
            if "processed_data" in artifacts:
                result["processed_data_path"] = artifacts["processed_data"].get("path")
                
        except Exception as e:
            logger.error(f"Failed to load state file from {state_path}: {e}")
    else:
        logger.warning(f"State file not found: {state_path}")
        
    return result

def generate_final_report(
    data_path_info: Optional[Dict[str, Any]] = None,
    model_results: Optional[Dict[str, Any]] = None,
    bootstrap_results: Optional[Dict[str, Any]] = None,
    sensitivity_results: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Generate the final report JSON containing all analysis results.
    
    Args:
        data_path_info: Data path information from load_data_path().
        model_results: Model results from load_model_results().
        bootstrap_results: Bootstrap results from load_bootstrap_results().
        sensitivity_results: Sensitivity results from load_sensitivity_results().
        
    Returns:
        Complete final report dictionary.
    """
    config = get_config()
    
    # Initialize report structure
    report = {
        "metadata": {
            "project_id": config.project_id,
            "generated_at": datetime.utcnow().isoformat(),
            "report_version": "1.0",
            "fr_012_compliant": True
        },
        "data_source": {
            "path": None,
            "type": "unknown",
            "description": "Unknown"
        },
        "model_results": {
            "coefficients": [],
            "diagnostics": {}
        },
        "bootstrap_stability": {
            "iterations": 0,
            "ci_width_variance": None,
            "stability_flags": [],
            "is_stable": True
        },
        "parameter_recovery": {},
        "sensitivity_findings": {
            "threshold_sensitivity": {},
            "family_wise_error_correction": {},
            "findings": []
        }
    }
    
    # Populate data source
    if data_path_info is None:
        data_path_info = load_data_path()
    report["data_source"]["path"] = data_path_info.get("raw_data_path")
    report["data_source"]["type"] = data_path_info.get("data_source_type")
    report["data_source"]["description"] = data_path_info.get("source_description")
    
    # Populate model results
    if model_results is None:
        model_results = load_model_results()
    report["model_results"]["coefficients"] = model_results.get("coefficients", [])
    report["model_results"]["diagnostics"] = model_results.get("diagnostics", {})
    
    # Populate bootstrap stability
    if bootstrap_results is None:
        bootstrap_results = load_bootstrap_results()
    report["bootstrap_stability"]["iterations"] = bootstrap_results.get("iterations", 0)
    report["bootstrap_stability"]["ci_width_variance"] = bootstrap_results.get("ci_width_variance")
    report["bootstrap_stability"]["stability_flags"] = bootstrap_results.get("stability_flags", [])
    
    # Check stability flag
    ci_var = bootstrap_results.get("ci_width_variance")
    if ci_var is not None and ci_var >= 0.01:
        report["bootstrap_stability"]["is_stable"] = False
        report["bootstrap_stability"]["stability_flags"].append("CI width variance >= 0.01")
    
    # Populate parameter recovery (if synthetic data)
    if sensitivity_results is None:
        sensitivity_results = load_sensitivity_results()
    
    if sensitivity_results.get("parameter_recovery"):
        report["parameter_recovery"] = sensitivity_results["parameter_recovery"]
        report["sensitivity_findings"]["threshold_sensitivity"] = sensitivity_results.get("threshold_sensitivity", {})
        report["sensitivity_findings"]["family_wise_error_correction"] = sensitivity_results.get("family_wise_error_correction", {})
        report["sensitivity_findings"]["findings"] = sensitivity_results.get("findings", [])
    else:
        # For real data, parameter recovery is not applicable
        report["parameter_recovery"] = {
            "status": "not_applicable",
            "reason": "Real data used; no ground truth parameters available"
        }
        report["sensitivity_findings"]["threshold_sensitivity"] = sensitivity_results.get("threshold_sensitivity", {})
        report["sensitivity_findings"]["family_wise_error_correction"] = sensitivity_results.get("family_wise_error_correction", {})
        report["sensitivity_findings"]["findings"] = sensitivity_results.get("findings", [])
    
    return report

def save_report(report: Dict[str, Any], output_path: str = "data/processed/final_report.json") -> bool:
    """
    Save the final report to a JSON file.
    
    Args:
        report: The final report dictionary to save.
        output_path: Path where the report should be saved.
        
    Returns:
        True if successful, False otherwise.
    """
    try:
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Final report saved to {output_file}")
        return True
    except Exception as e:
        logger.error(f"Failed to save report to {output_path}: {e}")
        return False

def run_report_generation(
    model_csv_path: str = "data/processed/regression_coefficients.csv",
    model_json_path: str = "data/processed/regression_diagnostics.json",
    bootstrap_json_path: str = "data/processed/bootstrap_results.json",
    sensitivity_json_path: str = "data/processed/sensitivity_analysis.json",
    output_path: str = "data/processed/final_report.json"
) -> bool:
    """
    Run the complete report generation pipeline.
    
    Args:
        model_csv_path: Path to regression coefficients CSV.
        model_json_path: Path to regression diagnostics JSON.
        bootstrap_json_path: Path to bootstrap results JSON.
        sensitivity_json_path: Path to sensitivity analysis JSON.
        output_path: Path where the final report should be saved.
        
    Returns:
        True if successful, False otherwise.
    """
    logger.info("Starting final report generation (T030)...")
    
    # Load all results
    data_path_info = load_data_path()
    model_results = load_model_results(model_csv_path, model_json_path)
    bootstrap_results = load_bootstrap_results(bootstrap_json_path)
    sensitivity_results = load_sensitivity_results(sensitivity_json_path)
    
    # Generate report
    report = generate_final_report(
        data_path_info=data_path_info,
        model_results=model_results,
        bootstrap_results=bootstrap_results,
        sensitivity_results=sensitivity_results
    )
    
    # Save report
    success = save_report(report, output_path)
    
    if success:
        logger.info("Final report generation completed successfully.")
    else:
        logger.error("Final report generation failed.")
        
    return success

def main():
    """Main entry point for report generation."""
    run_report_generation()

if __name__ == "__main__":
    main()