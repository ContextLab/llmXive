"""
T037: Implement Bonferroni Correction for multiple hypothesis testing.

This module takes the interaction p-values extracted from the Tobit and Cox models
(produced by T036), applies the Bonferroni correction, and updates the analysis
results with the corrected significance flag.

Logic:
  1. Load interaction results from `data/analysis/interaction_results.json` (output of T036).
  2. Calculate n_tests = 2 (Tobit and Cox).
  3. Apply correction: p_corr = p_raw * n_tests.
  4. Determine significance: is_significant = min(p_tobit_corr, p_cox_corr) < 0.05.
  5. Update `data/analysis_results.json` with the corrected p-values and the boolean flag.
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, Any

# Ensure code directory is in path for imports if running as script
code_dir = Path(__file__).parent
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from utils import hash_artifact

INTERACTION_RESULTS_PATH = Path("data/analysis/interaction_results.json")
ANALYSIS_RESULTS_PATH = Path("data/analysis_results.json")
STATE_FILE_PATH = Path("state/projects/PROJ-353-investigating-the-effectiveness-of-diffe.yaml")

def load_interaction_results() -> Dict[str, Any]:
    """Load the interaction p-values extracted by T036."""
    if not INTERACTION_RESULTS_PATH.exists():
        raise FileNotFoundError(
            f"Interaction results not found at {INTERACTION_RESULTS_PATH}. "
            "Ensure T036 (extract_interaction.py) has been run successfully."
        )
    
    with open(INTERACTION_RESULTS_PATH, 'r') as f:
        return json.load(f)

def apply_bonferroni_correction(interaction_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Apply Bonferroni correction to the interaction p-values.
    
    Args:
        interaction_data: Dictionary containing 'tobit_p_value' and 'cox_p_value'.
    
    Returns:
        Dictionary with corrected p-values and significance flag.
    """
    n_tests = 2  # We are testing 2 hypotheses: Tobit interaction and Cox interaction
    
    p_tobit_raw = interaction_data.get('tobit_p_value')
    p_cox_raw = interaction_data.get('cox_p_value')

    if p_tobit_raw is None or p_cox_raw is None:
        raise ValueError("Missing interaction p-values in input data.")

    # Apply correction: p_corr = p_raw * n_tests
    # Cap at 1.0 to avoid invalid probabilities
    p_tobit_corr = min(p_tobit_raw * n_tests, 1.0)
    p_cox_corr = min(p_cox_raw * n_tests, 1.0)

    # Determine significance: min(p_tobit_corr, p_cox_corr) < 0.05
    min_corr_p = min(p_tobit_corr, p_cox_corr)
    is_significant = min_corr_p < 0.05

    return {
        "p_tobit_raw": p_tobit_raw,
        "p_cox_raw": p_cox_raw,
        "p_tobit_corr": p_tobit_corr,
        "p_cox_corr": p_cox_corr,
        "n_tests": n_tests,
        "min_corrected_p": min_corr_p,
        "is_significant": is_significant
    }

def save_analysis_results(corrected_data: Dict[str, Any]) -> None:
    """
    Save the corrected analysis results to data/analysis_results.json.
    Updates the existing file if it exists, merging in the new corrected values.
    """
    # Load existing results if present, otherwise start fresh
    if ANALYSIS_RESULTS_PATH.exists():
        with open(ANALYSIS_RESULTS_PATH, 'r') as f:
            existing_data = json.load(f)
    else:
        existing_data = {}

    # Update with new corrected data
    existing_data.update(corrected_data)
    
    # Ensure the directory exists
    ANALYSIS_RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)

    with open(ANALYSIS_RESULTS_PATH, 'w') as f:
        json.dump(existing_data, f, indent=2)

def update_state_file() -> None:
    """
    Update the project state file with the hash of the new analysis results.
    This satisfies the metadata propagation constraint.
    """
    if not STATE_FILE_PATH.parent.exists():
        STATE_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    # If state file doesn't exist, create a minimal one
    if not STATE_FILE_PATH.exists():
        with open(STATE_FILE_PATH, 'w') as f:
            f.write("artifact_hashes:\n")
    
    current_hash = hash_artifact(str(ANALYSIS_RESULTS_PATH))
    
    # Simple YAML update (assuming the file structure is known or we append)
    # For robustness in this specific script, we read, parse (simple yaml), update, write.
    # Since we don't want to add 'pyyaml' if not strictly necessary and the format is simple:
    lines = []
    with open(STATE_FILE_PATH, 'r') as f:
        lines = f.readlines()
    
    # Check if artifact_hashes section exists
    found_hashes = False
    new_lines = []
    for line in lines:
        if 'artifact_hashes:' in line:
            found_hashes = True
            new_lines.append(line)
        elif found_hashes and line.strip().startswith('- ') and 'analysis_results.json' in line:
            # Update existing entry
            new_lines.append(f"  - path: {ANALYSIS_RESULTS_PATH}\n")
            new_lines.append(f"    hash: {current_hash}\n")
            found_hashes = False # Reset to avoid updating subsequent unrelated items if any
        elif found_hashes and line.strip().startswith('  - path:'):
             # If we found the header but this is a new item, we might need to insert our item first
             # For simplicity in this specific context, we assume we are appending or updating a known list
             # Let's just append if not found to be safe, or overwrite if we find the specific path
             new_lines.append(line)
        else:
            new_lines.append(line)
    
    # If we didn't find the specific entry or section, append safely
    # A simpler approach for this specific constraint:
    with open(STATE_FILE_PATH, 'w') as f:
        # Read current content
        content = ""
        if STATE_FILE_PATH.exists():
            with open(STATE_FILE_PATH, 'r') as rf:
                content = rf.read()
        
        # Check if our entry exists
        if f"path: {ANALYSIS_RESULTS_PATH}" not in content:
            # Append to artifact_hashes
            if "artifact_hashes:" not in content:
                content += "artifact_hashes:\n"
            content += f"  - path: {ANALYSIS_RESULTS_PATH}\n"
            content += f"    hash: {current_hash}\n"
        
        f.write(content)

def main():
    """Main entry point for T037."""
    print("Starting Bonferroni Correction (T037)...")
    
    # 1. Load interaction results
    try:
        interaction_data = load_interaction_results()
        print(f"Loaded interaction data: {interaction_data}")
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    
    # 2. Apply correction
    try:
        corrected_data = apply_bonferroni_correction(interaction_data)
        print(f"Applied correction: {corrected_data}")
    except ValueError as e:
        print(f"Error during correction: {e}")
        sys.exit(1)
    
    # 3. Save results
    save_analysis_results(corrected_data)
    print(f"Saved analysis results to {ANALYSIS_RESULTS_PATH}")
    
    # 4. Update state
    update_state_file()
    print(f"Updated state file at {STATE_FILE_PATH}")
    
    print("T037 completed successfully.")

if __name__ == "__main__":
    main()
