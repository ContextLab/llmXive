"""
FR-007 Implementation: Associational Framing Warnings.

This module provides utilities to append mandatory associational framing warnings
to all model outputs, visualizations, and the final report.

Per FR-007: "All model outputs, visualizations, and the final report MUST include
a prominent warning that the model identifies associations, not causation, and
that predictions are valid only within the domain of the training data."
"""
import logging
import json
import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

from utils.logging_config import get_logger

logger = get_logger(__name__)

# The canonical warning text mandated by FR-007
ASSOCIATIONAL_WARNING_TEXT = (
  "⚠️ ASSOCIATIONAL FRAMING WARNING (FR-007):\n"
  "This model identifies statistical associations between solder composition and Vickers hardness.\n"
  "It DOES NOT establish causal relationships. Predictions are valid ONLY within the domain\n"
  "of the training data (composition space, measurement conditions). Extrapolation outside\n"
  "this domain is unsupported and may be invalid."
)

def get_warning_header() -> str:
    """Returns the standard warning header string."""
    return ASSOCIATIONAL_WARNING_TEXT

def inject_warning_into_json_output(output_path: Path, warning_text: Optional[str] = None) -> None:
    """
    Reads a JSON file, injects the warning into a dedicated 'warnings' key, and saves it.
    If the key already exists, it appends the warning to the list.
    """
    if warning_text is None:
        warning_text = get_warning_header()
    
    try:
        with open(output_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        logger.warning(f"File {output_path} not found. Skipping warning injection.")
        return
    except json.JSONDecodeError:
        logger.error(f"File {output_path} is not valid JSON. Cannot inject warning.")
        return

    if 'warnings' not in data:
        data['warnings'] = []
    
    # Ensure uniqueness
    if warning_text not in data['warnings']:
        data['warnings'].append(warning_text)
    
    # Add metadata about when the warning was injected
    data['fr007_warning_injected_at'] = datetime.utcnow().isoformat()

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    logger.info(f"FR-007 Warning injected into {output_path}")

def inject_warning_into_yaml_output(output_path: Path, warning_text: Optional[str] = None) -> None:
    """
    Reads a YAML file, injects the warning into a dedicated 'warnings' key, and saves it.
    """
    if warning_text is None:
        warning_text = get_warning_header()

    try:
        with open(output_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f) or {}
    except FileNotFoundError:
        logger.warning(f"File {output_path} not found. Skipping warning injection.")
        return
    except yaml.YAMLError:
        logger.error(f"File {output_path} is not valid YAML. Cannot inject warning.")
        return

    if 'warnings' not in data:
        data['warnings'] = []
    
    if warning_text not in data['warnings']:
        data['warnings'].append(warning_text)
    
    data['fr007_warning_injected_at'] = datetime.utcnow().isoformat()

    with open(output_path, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
    
    logger.info(f"FR-007 Warning injected into {output_path}")

def add_warning_to_text_file(output_path: Path, warning_text: Optional[str] = None) -> None:
    """
    Appends the warning to the end of a text file (e.g., report.txt, README).
    """
    if warning_text is None:
        warning_text = get_warning_header()

    with open(output_path, 'a', encoding='utf-8') as f:
        f.write("\n\n" + "="*80 + "\n")
        f.write(warning_text + "\n")
        f.write("="*80 + "\n")
    
    logger.info(f"FR-007 Warning appended to {output_path}")

def main():
    """
    Example runner to demonstrate FR-007 injection on standard outputs.
    This function is called by the pipeline after model training and reporting.
    """
    # Define paths based on typical project structure
    # Note: These paths assume the script is run from the project root or code/
    base_path = Path(__file__).parent.parent
    models_dir = base_path / "models"
    data_processed_dir = base_path / "data" / "processed"
    
    # List of files to update (relative to project root)
    files_to_update = [
        (models_dir / "xgboost_model_results.json", "json"),
        (models_dir / "linear_model_results.json", "json"),
        (models_dir / "comparison_report.json", "json"),
        (data_processed_dir / "sensitivity_analysis.yaml", "yaml"),
        (models_dir / "shap_analysis.json", "json"),
        # If a text report exists:
        # (base_path / "report.md", "text"), 
    ]

    for file_path, file_type in files_to_update:
        full_path = base_path / file_path if not file_path.is_absolute() else file_path
        if full_path.exists():
            if file_type == "json":
                inject_warning_into_json_output(full_path)
            elif file_type == "yaml":
                inject_warning_into_yaml_output(full_path)
            elif file_type == "text":
                add_warning_to_text_file(full_path)
        else:
            logger.info(f"Skipping {file_path} as it does not exist yet.")

if __name__ == "__main__":
    main()
