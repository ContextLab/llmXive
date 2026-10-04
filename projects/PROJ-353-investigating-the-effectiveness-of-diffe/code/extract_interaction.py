"""
Task T036: Extract Interaction Terms from Tobit and Cox Models.

This module loads the results from the Tobit Regression (T034) and
Cox Proportional Hazards (T035) analyses, extracts the specific
p-value for the interaction term (loss_type * beta) from each,
and saves them to the analysis results file.
"""
import os
import json
import sys
from pathlib import Path
from typing import Dict, Any, Optional

# Add project root to path for imports if running as script
if str(Path(__file__).parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent))

from tobit_regression import run_tobit_regression
from cox_ph_analysis import run_cox_ph
from utils import hash_artifact


def load_model_results(results_path: Path) -> Dict[str, Any]:
    """Load the JSON results file containing model outputs."""
    if not results_path.exists():
        raise FileNotFoundError(f"Model results file not found: {results_path}")
    
    with open(results_path, 'r') as f:
        return json.load(f)


def extract_tobit_interaction_pvalue(tobit_results: Dict[str, Any]) -> Optional[float]:
    """
    Extract the p-value for the interaction term from Tobit regression results.
    
    The interaction term is typically named 'C(loss_type)[T.1]:beta' or similar
    depending on the statsmodels formula expansion.
    """
    if 'tobit' not in tobit_results:
        raise ValueError("Tobit results not found in the provided dictionary")
    
    tobit_data = tobit_results['tobit']
    if 'coefficients' not in tobit_data:
        raise ValueError("Tobit coefficients not found in results")
    
    coeffs = tobit_data['coefficients']
    
    # Possible names for the interaction term based on statsmodels formula:
    # C(loss_type)[T.1]:beta
    # C(loss_type)[T.infonce]:beta (if 'infonce' is the reference)
    # We need to find the row corresponding to the interaction.
    # Usually, the main effects are 'C(loss_type)[T.1]' and 'beta',
    # and the interaction is the combination.
    
    interaction_candidates = [
        "C(loss_type)[T.1]:beta",
        "C(loss_type)[T.infonce]:beta",
        "C(loss_type)[T.ce]:beta", # Less likely if CE is reference
        "loss_type:beta"
    ]
    
    p_value = None
    found_term = None
    
    for term in coeffs:
        term_name = term.get('term', term.get('variable', str(term)))
        
        # Check if this term looks like an interaction (contains ':')
        # and involves both loss_type and beta
        if ':' in term_name and 'loss_type' in term_name and 'beta' in term_name:
            p_value = term.get('pvalue')
            found_term = term_name
            break
    
    if p_value is None:
        # Fallback: try to find any term with 'interaction' in name if specific format failed
        for term in coeffs:
            term_name = term.get('term', term.get('variable', str(term)))
            if 'interaction' in term_name.lower():
                p_value = term.get('pvalue')
                found_term = term_name
                break
    
    if p_value is None:
        raise ValueError(
            f"Could not locate interaction term p-value in Tobit results. "
            f"Available terms: {[t.get('term', t.get('variable', str(t))) for t in coeffs]}"
        )
    
    return float(p_value)


def extract_cox_interaction_pvalue(cox_results: Dict[str, Any]) -> Optional[float]:
    """
    Extract the p-value for the interaction term from Cox PH results.
    
    Similar to Tobit, looking for the term involving both loss_type and beta.
    """
    if 'cox' not in cox_results:
        raise ValueError("Cox results not found in the provided dictionary")
    
    cox_data = cox_results['cox']
    if 'coefficients' not in cox_data:
        raise ValueError("Cox coefficients not found in results")
    
    coeffs = cox_data['coefficients']
    
    p_value = None
    found_term = None
    
    for term in coeffs:
        term_name = term.get('term', term.get('variable', str(term)))
        
        # Check for interaction pattern
        if ':' in term_name and 'loss_type' in term_name and 'beta' in term_name:
            p_value = term.get('pvalue')
            found_term = term_name
            break
    
    if p_value is None:
        for term in coeffs:
            term_name = term.get('term', term.get('variable', str(term)))
            if 'interaction' in term_name.lower():
                p_value = term.get('pvalue')
                found_term = term_name
                break
    
    if p_value is None:
        raise ValueError(
            f"Could not locate interaction term p-value in Cox results. "
            f"Available terms: {[t.get('term', t.get('variable', str(t))) for t in coeffs]}"
        )
    
    return float(p_value)


def save_interaction_results(
    p_tobit: float, 
    p_cox: float, 
    output_path: Path
) -> None:
    """Save the extracted interaction p-values to the analysis results JSON."""
    results = {
        "task": "T036_Extract_Interaction_Terms",
        "tobit_interaction_pvalue": p_tobit,
        "cox_interaction_pvalue": p_cox,
        "description": "P-values for the interaction term (loss_type * beta) extracted from Tobit and Cox models."
    }
    
    # If an existing analysis results file exists, we might want to merge,
    # but per spec, we are generating the specific interaction extraction.
    # We will write to the main analysis results file location.
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"Interaction terms saved to {output_path}")


def main():
    """
    Main entry point for T036.
    Expects the results from T034 (Tobit) and T035 (Cox) to be present.
    """
    # Define paths relative to project root
    project_root = Path(__file__).parent.parent
    data_analysis_dir = project_root / "data" / "analysis"
    data_analysis_dir.mkdir(parents=True, exist_ok=True)
    
    # Paths to input results (generated by T034 and T035)
    # Assuming T034 writes to data/analysis/tobit_results.json
    # and T035 writes to data/analysis/cox_results.json
    tobit_results_path = project_root / "data" / "analysis" / "tobit_results.json"
    cox_results_path = project_root / "data" / "analysis" / "cox_results.json"
    output_path = project_root / "data" / "analysis_results.json"
    
    # Verify inputs exist
    if not tobit_results_path.exists():
        raise FileNotFoundError(
            f"T034 output not found: {tobit_results_path}. "
            "Please run T034 (Tobit Regression) first."
        )
    if not cox_results_path.exists():
        raise FileNotFoundError(
            f"T035 output not found: {cox_results_path}. "
            "Please run T035 (Cox PH) first."
        )
    
    print("Loading Tobit results...")
    tobit_data = load_model_results(tobit_results_path)
    
    print("Loading Cox results...")
    cox_data = load_model_results(cox_results_path)
    
    print("Extracting interaction term p-values...")
    
    try:
        p_tobit = extract_tobit_interaction_pvalue(tobit_data)
        print(f"  Tobit Interaction P-value: {p_tobit}")
    except ValueError as e:
        print(f"  ERROR extracting Tobit p-value: {e}")
        sys.exit(1)
    
    try:
        p_cox = extract_cox_interaction_pvalue(cox_data)
        print(f"  Cox Interaction P-value: {p_cox}")
    except ValueError as e:
        print(f"  ERROR extracting Cox p-value: {e}")
        sys.exit(1)
    
    print("Saving results...")
    save_interaction_results(p_tobit, p_cox, output_path)
    
    # Update artifact hash if state file exists
    state_file = project_root / "state" / "projects" / "PROJ-353-investigating-the-effectiveness-of-diffe.yaml"
    if state_file.exists():
        # Simple hash update logic could go here, but T036 focus is extraction
        pass
    
    print("T036 completed successfully.")


if __name__ == "__main__":
    main()
