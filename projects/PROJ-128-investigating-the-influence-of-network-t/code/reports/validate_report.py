"""
Validation script for the final report against the output schema.
Ensures all required fields (r, p, FDR, sensitivity, absolute difference) are present.
"""
import os
import sys
import json
import yaml
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "code"))

from config import get_config_dict


def load_schema(schema_path: Path) -> Dict[str, Any]:
    """Load the YAML schema definition."""
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    with open(schema_path, "r") as f:
        return yaml.safe_load(f)


def validate_field_presence(data: Dict[str, Any], required_fields: List[str], path_prefix: str = "") -> List[str]:
    """Recursively check for required fields in the data dictionary."""
    missing = []
    for field in required_fields:
        # Handle nested fields like "correlation.r"
        parts = field.split(".")
        current = data
        found = True
        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                found = False
                break
        
        if not found:
            full_path = f"{path_prefix}.{field}" if path_prefix else field
            missing.append(full_path)
    return missing


def validate_report_structure(report_data: Dict[str, Any], schema: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate the report data against the schema requirements.
    
    Checks for:
    - Top-level required sections (summary, correlations, sensitivity)
    - Specific fields within sections (r, p, FDR, absolute difference)
    """
    errors = []
    
    # Define required top-level keys based on typical report structure
    required_top_level = ["summary", "correlations", "sensitivity_analysis"]
    
    for key in required_top_level:
        if key not in report_data:
            errors.append(f"Missing top-level section: {key}")
    
    # Validate correlations section
    if "correlations" in report_data:
        corr_data = report_data["correlations"]
        # Check for required correlation metrics
        corr_fields = ["r_value", "p_value", "fdr_corrected_p"]
        missing_corr = validate_field_presence(corr_data, corr_fields, "correlations")
        errors.extend(missing_corr)
        
        # If it's a list of correlations, check each
        if isinstance(corr_data, list) and len(corr_data) > 0:
            for i, item in enumerate(corr_data):
                missing_item = validate_field_presence(item, corr_fields, f"correlations[{i}]")
                errors.extend(missing_item)
    
    # Validate sensitivity analysis section
    if "sensitivity_analysis" in report_data:
        sens_data = report_data["sensitivity_analysis"]
        # Check for sensitivity metrics
        sens_fields = ["window_length_comparison", "density_threshold_comparison"]
        missing_sens = validate_field_presence(sens_data, sens_fields, "sensitivity_analysis")
        errors.extend(missing_sens)
        
        # Check for absolute difference calculation (SC-002 requirement)
        if "window_length_comparison" in sens_data:
            wlc = sens_data["window_length_comparison"]
            if isinstance(wlc, dict):
                if "absolute_difference" not in wlc:
                    errors.append("sensitivity_analysis.window_length_comparison.absolute_difference: Missing required field for SC-002")
                if "baseline_30tr" not in wlc:
                    errors.append("sensitivity_analysis.window_length_comparison.baseline_30tr: Missing required field")
                if "sensitivity_20tr" not in wlc:
                    errors.append("sensitivity_analysis.window_length_comparison.sensitivity_20tr: Missing required field")
    
    # Validate summary section
    if "summary" in report_data:
        summary_data = report_data["summary"]
        summary_fields = ["total_subjects", "excluded_subjects", "significant_correlations"]
        missing_summary = validate_field_presence(summary_data, summary_fields, "summary")
        errors.extend(missing_summary)
    
    return len(errors) == 0, errors


def validate_report_file(report_path: Path, schema_path: Path) -> Tuple[bool, List[str]]:
    """
    Main validation function that loads the report and schema, then validates.
    """
    if not report_path.exists():
        return False, [f"Report file not found: {report_path}"]
    
    try:
        with open(report_path, "r") as f:
            report_data = json.load(f)
    except json.JSONDecodeError as e:
        return False, [f"Invalid JSON in report: {str(e)}"]
    
    schema = load_schema(schema_path)
    is_valid, errors = validate_report_structure(report_data, schema)
    
    return is_valid, errors


def main():
    """
    Entry point for report validation.
    Validates the final report against the output schema.
    """
    config = get_config_dict()
    
    report_path = Path(config["paths"]["output_dir"]) / config["paths"]["final_report"]
    schema_path = Path(config["paths"]["contracts_dir"]) / "output.schema.yaml"
    
    print(f"Validating report: {report_path}")
    print(f"Against schema: {schema_path}")
    
    is_valid, errors = validate_report_file(report_path, schema_path)
    
    if is_valid:
        print("✅ Report validation PASSED")
        print("All required fields (r, p, FDR, sensitivity, absolute difference) are present.")
        return 0
    else:
        print("❌ Report validation FAILED")
        print("Missing or invalid fields:")
        for error in errors:
            print(f"  - {error}")
        return 1


if __name__ == "__main__":
    sys.exit(main())