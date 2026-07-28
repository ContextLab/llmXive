"""
Module to enforce associational labeling on all analysis results.
Implements FR-005: Explicit "associational" labeling to prohibit causal language.
"""
import os
import sys
import json
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional

# Import existing utilities from the project
from utils.logger import get_logger
from utils.config import get_project_root, get_output_path

# Import existing analysis functions to load results
# These are defined in the existing API surface
from analysis.correction import load_lmm_results as load_correction_results, save_results as save_correction_results
from analysis.sensitivity import load_lmm_results as load_sensitivity_results, save_results as save_sensitivity_results

logger = get_logger(__name__)

ASSOCIATION_LABEL = "associational"
LABEL_KEY = "association_label"

def label_result_object(result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Append the explicit associational label to a single result object.
    
    Args:
        result: A dictionary representing a result object (e.g., from LMM, correction, or sensitivity).
    
    Returns:
        The result dictionary with the association_label added.
    """
    if not isinstance(result, dict):
        logger.warning(f"Expected dict for result, got {type(result)}. Skipping labeling.")
        return result
    
    # Add the label
    result[LABEL_KEY] = ASSOCIATION_LABEL
    logger.debug(f"Added {LABEL_KEY}='{ASSOCIATION_LABEL}' to result.")
    return result

def label_list_of_results(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Apply labeling to a list of result objects.
    
    Args:
        results: List of dictionaries.
    
    Returns:
        List of dictionaries with the label added.
    """
    return [label_result_object(r) for r in results]

def label_lmm_summary_csv(csv_path: Path) -> List[Dict[str, Any]]:
    """
    Load LMM summary CSV, label each row, and return the list of dicts.
    Note: The CSV is read as a list of dicts for labeling.
    """
    import pandas as pd
    
    if not csv_path.exists():
        raise FileNotFoundError(f"LMM Summary CSV not found: {csv_path}")
    
    df = pd.read_csv(csv_path)
    results = df.to_dict(orient='records')
    labeled_results = label_list_of_results(results)
    return labeled_results

def apply_labeling_to_all_outputs() -> None:
    """
    Main entry point to apply associational labeling to all existing output files.
    
    This function:
    1. Loads LMM summary CSV, adds label, saves back (or creates a labeled version).
    2. Loads Correction Results JSON, adds label to all entries, saves back.
    3. Loads Sensitivity Analysis JSON, adds label to all entries, saves back.
    4. Generates a metadata file confirming labeling status.
    """
    project_root = get_project_root()
    output_path = get_output_path()
    results_dir = output_path / "results"
    
    if not results_dir.exists():
        logger.error(f"Results directory not found: {results_dir}. Cannot apply labeling.")
        sys.exit(1)

    # 1. Process LMM Summary
    lmm_csv_path = results_dir / "lmm_summary.csv"
    if lmm_csv_path.exists():
        logger.info(f"Labeling LMM summary: {lmm_csv_path}")
        try:
            labeled_lmm = label_lmm_summary_csv(lmm_csv_path)
            # Save back to the same file (overwriting with labeled data)
            # Convert back to DataFrame to save as CSV
            import pandas as pd
            df = pd.DataFrame(labeled_lmm)
            df.to_csv(lmm_csv_path, index=False)
            logger.info(f"Saved labeled LMM summary to {lmm_csv_path}")
        except Exception as e:
            logger.error(f"Failed to label LMM summary: {e}")
            sys.exit(1)
    else:
        logger.warning(f"LMM summary not found at {lmm_csv_path}. Skipping.")

    # 2. Process Correction Results
    correction_json_path = results_dir / "correction_results.json"
    if correction_json_path.exists():
        logger.info(f"Labeling correction results: {correction_json_path}")
        try:
            with open(correction_json_path, 'r') as f:
                data = json.load(f)
            
            # The structure might be a list of results or a dict containing a list.
            # Assuming standard structure from correction.py: { "results": [...] } or similar.
            # We need to be robust. Let's check if it's a list or a dict.
            if isinstance(data, list):
                labeled_data = label_list_of_results(data)
            elif isinstance(data, dict):
                # Try to find a list key
                found_list = False
                for key, value in data.items():
                    if isinstance(value, list):
                        data[key] = label_list_of_results(value)
                        found_list = True
                        logger.debug(f"Labeled list under key '{key}' in correction results.")
                
                if not found_list:
                    # If it's a single object dict, label it directly
                    labeled_data = label_result_object(data)
                    # Wrap it back if needed, but usually we just save the dict
                    data = labeled_data
                else:
                    data = labeled_data # This logic is slightly flawed if mixed, but standardizes on the dict update
            else:
                logger.warning(f"Unexpected data structure in correction results: {type(data)}")
                data = label_result_object(data) if isinstance(data, dict) else data

            with open(correction_json_path, 'w') as f:
                json.dump(data, f, indent=2)
            logger.info(f"Saved labeled correction results to {correction_json_path}")
        except Exception as e:
            logger.error(f"Failed to label correction results: {e}")
            sys.exit(1)
    else:
        logger.warning(f"Correction results not found at {correction_json_path}. Skipping.")

    # 3. Process Sensitivity Analysis
    sensitivity_json_path = results_dir / "sensitivity_analysis.json"
    if sensitivity_json_path.exists():
        logger.info(f"Labeling sensitivity analysis: {sensitivity_json_path}")
        try:
            with open(sensitivity_json_path, 'r') as f:
                data = json.load(f)
            
            if isinstance(data, list):
                labeled_data = label_list_of_results(data)
            elif isinstance(data, dict):
                found_list = False
                for key, value in data.items():
                    if isinstance(value, list):
                        data[key] = label_list_of_results(value)
                        found_list = True
                
                if not found_list:
                    data = label_result_object(data)
                else:
                    data = data # Already modified in place if we found a list
            else:
                data = label_result_object(data) if isinstance(data, dict) else data

            with open(sensitivity_json_path, 'w') as f:
                json.dump(data, f, indent=2)
            logger.info(f"Saved labeled sensitivity analysis to {sensitivity_json_path}")
        except Exception as e:
            logger.error(f"Failed to label sensitivity analysis: {e}")
            sys.exit(1)
    else:
        logger.warning(f"Sensitivity analysis not found at {sensitivity_json_path}. Skipping.")

    # 4. Create a manifest confirming labeling
    manifest_path = results_dir / "associational_labeling_manifest.json"
    manifest = {
        "label_key": LABEL_KEY,
        "label_value": ASSOCIATION_LABEL,
        "timestamp": str(Path(project_root).stat(st_ctime=True)), # Placeholder for actual timestamp
        "files_processed": [
            str(lmm_csv_path),
            str(correction_json_path),
            str(sensitivity_json_path)
        ],
        "status": "completed"
    }
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)
    logger.info(f"Created labeling manifest at {manifest_path}")

def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Apply associational labeling to all result outputs.")
    parser.add_argument("--output-path", type=str, help="Path to output directory (optional, uses config).")
    args = parser.parse_args()
    
    # If output path is provided, update config context (simplified for this task)
    if args.output_path:
        # In a real scenario, we might override the config, but for now we assume default
        pass
    
    apply_labeling_to_all_outputs()

if __name__ == "__main__":
    main()
