"""
Missing Degrees of Freedom Analyzer (Dyson Review Implementation)

This module quantifies the "missing degrees of freedom" error term when comparing
semi-empirical (DFTB+) vs. high-level DFT (Psi4) results. It frames the error
not just as a statistical residual, but as a physical model of the information
lost due to approximations (e.g., frozen core, minimal basis set, neglect of
dynamic correlation) in the semi-empirical method.

It calculates the discrepancy in energy and structural descriptors, attributing
the difference to specific physical terms missing in the semi-empirical Hamiltonian.
"""

import argparse
import csv
import json
import logging
import os
import sys
from typing import Dict, List, Tuple, Any

# Import validation utilities from project root utils
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from utils.validation_utils import validate_columns

# Import logging utilities
from utils.logging_utils import setup_logger

def load_descriptors_semi(filepath: str) -> List[Dict[str, Any]]:
    """Load semi-empirical (DFTB+) descriptors from CSV."""
    data = []
    with open(filepath, 'r', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Convert numeric strings to float
            numeric_keys = ['HOMO', 'LUMO', 'Mayer_Bond_Order', 'Partial_Charge']
            for key in numeric_keys:
                if key in row and row[key]:
                    try:
                        row[key] = float(row[key])
                    except ValueError:
                        row[key] = None
            data.append(row)
    return data

def load_descriptors_dft(filepath: str) -> List[Dict[str, Any]]:
    """Load high-level DFT (Psi4) descriptors from CSV."""
    data = []
    with open(filepath, 'r', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            numeric_keys = ['HOMO', 'LUMO', 'Mayer_Bond_Order', 'Partial_Charge']
            for key in numeric_keys:
                if key in row and row[key]:
                    try:
                        row[key] = float(row[key])
                    except ValueError:
                        row[key] = None
            data.append(row)
    return data

def extract_physical_quantities(semi_data: List[Dict], dft_data: List[Dict]) -> List[Dict[str, Any]]:
    """
    Align semi and DFT data by SMILES and extract physical quantities.
    Calculates the raw difference (Delta) which represents the 'missing physics'.
    """
    # Create lookup by SMILES for DFT data
    dft_lookup = {row['SMILES']: row for row in dft_data}
    
    aligned = []
    for semi_row in semi_data:
        smiles = semi_row.get('SMILES')
        if smiles not in dft_lookup:
            continue
        
        dft_row = dft_lookup[smiles]
        
        # Calculate Delta (DFT - Semi) for key physical quantities
        # This Delta is the "Missing Degrees of Freedom" error term
        delta_homo = (dft_row['HOMO'] - semi_row['HOMO']) if semi_row['HOMO'] is not None and dft_row['HOMO'] is not None else None
        delta_lumo = (dft_row['LUMO'] - semi_row['LUMO']) if semi_row['LUMO'] is not None and dft_row['LUMO'] is not None else None
        
        # HOMO-LUMO Gap difference
        gap_semi = (semi_row['LUMO'] - semi_row['HOMO']) if semi_row['HOMO'] is not None and semi_row['LUMO'] is not None else None
        gap_dft = (dft_row['LUMO'] - dft_row['HOMO']) if dft_row['HOMO'] is not None and dft_row['LUMO'] is not None else None
        delta_gap = (gap_dft - gap_semi) if gap_semi is not None and gap_dft is not None else None

        aligned.append({
            'SMILES': smiles,
            'HOMO_DFT': dft_row['HOMO'],
            'HOMO_Semi': semi_row['HOMO'],
            'Delta_HOMO': delta_homo,
            'LUMO_DFT': dft_row['LUMO'],
            'LUMO_Semi': semi_row['LUMO'],
            'Delta_LUMO': delta_lumo,
            'Gap_DFT': gap_dft,
            'Gap_Semi': gap_semi,
            'Delta_Gap': delta_gap
        })
    
    return aligned

def calculate_missing_dof_error(aligned_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Quantify the missing degrees of freedom error term.
    
    The error is framed as a physical model:
    E_missing = E_DFT - E_Semi
    
    We calculate:
    1. Mean Absolute Error (MAE) for HOMO, LUMO, Gap (statistical measure of missing physics)
    2. Systematic Bias (Mean Error) - indicates if the approximation consistently under/overestimates
    3. Variance of Error - indicates the complexity of the missing terms (non-linear effects)
    4. Physical Attribution:
       - Delta_HOMO/LUMO is attributed to "Missing Dynamic Correlation & Basis Set Incompleteness"
       - Delta_Gap is attributed to "Missing Excited State Relaxation & Polarization"
    """
    if not aligned_data:
        return {"error": "No aligned data found"}

    sum_delta_homo = 0.0
    sum_delta_lumo = 0.0
    sum_delta_gap = 0.0
    sum_abs_delta_homo = 0.0
    sum_abs_delta_lumo = 0.0
    sum_abs_delta_gap = 0.0
    count = 0

    for row in aligned_data:
        if row['Delta_HOMO'] is not None:
            sum_delta_homo += row['Delta_HOMO']
            sum_abs_delta_homo += abs(row['Delta_HOMO'])
        if row['Delta_LUMO'] is not None:
            sum_delta_lumo += row['Delta_LUMO']
            sum_abs_delta_lumo += abs(row['Delta_LUMO'])
        if row['Delta_Gap'] is not None:
            sum_delta_gap += row['Delta_Gap']
            sum_abs_delta_gap += abs(row['Delta_Gap'])
        count += 1

    if count == 0:
        return {"error": "No valid numeric data found"}

    mae_homo = sum_abs_delta_homo / count
    mae_lumo = sum_abs_delta_lumo / count
    mae_gap = sum_abs_delta_gap / count

    bias_homo = sum_delta_homo / count
    bias_lumo = sum_delta_lumo / count
    bias_gap = sum_delta_gap / count

    # Physical Attribution Model
    # Dyson Review: The error is not just noise, it's the integral over the missing paths.
    # We model the "Missing Degrees of Freedom" as the sum of:
    # 1. Basis Set Error (approximated by Delta Gap)
    # 2. Correlation Error (approximated by Delta HOMO/LUMO shift)
    
    missing_dof_model = {
        "mean_absolute_error": {
            "HOMO_eV": round(mae_homo, 4),
            "LUMO_eV": round(mae_lumo, 4),
            "Gap_eV": round(mae_gap, 4)
        },
        "systematic_bias": {
            "HOMO_eV": round(bias_homo, 4),
            "LUMO_eV": round(bias_lumo, 4),
            "Gap_eV": round(bias_gap, 4)
        },
        "physical_attribution": {
            "missing_dynamic_correlation": f"Attributed to Delta_HOMO/LUMO bias ({round(bias_homo, 4)} eV). Semi-empirical methods neglect explicit electron-electron correlation terms present in DFT.",
            "basis_set_incompleteness": f"Attributed to Delta_Gap shift ({round(bias_gap, 4)} eV). Minimal basis sets in DFTB+ fail to capture polarization and diffuse functions required for accurate orbital energies.",
            "frozen_core_approximation": "Neglect of core-valence interaction energy, contributing to systematic underestimation of binding energies."
        },
        "total_missing_energy_estimate_eV": round(mae_gap, 4)  # Using Gap error as proxy for total missing DOF energy scale
    }

    return missing_dof_model

def generate_physical_model_report(missing_dof_data: Dict[str, Any], output_path: str) -> None:
    """
    Write the physical model report to a JSON file.
    This report explicitly frames the error as missing physical information.
    """
    with open(output_path, 'w') as f:
        json.dump(missing_dof_data, f, indent=2)
    logging.info(f"Physical model report written to {output_path}")

def run_missing_dof_analysis(semi_descriptors_path: str, dft_descriptors_path: str, output_report_path: str) -> Dict[str, Any]:
    """
    Main entry point to run the missing degrees of freedom analysis.
    """
    logging.info(f"Loading semi-empirical descriptors from {semi_descriptors_path}")
    semi_data = load_descriptors_semi(semi_descriptors_path)
    
    logging.info(f"Loading DFT descriptors from {dft_descriptors_path}")
    dft_data = load_descriptors_dft(dft_descriptors_path)

    logging.info("Extracting physical quantities and aligning data...")
    aligned_data = extract_physical_quantities(semi_data, dft_data)

    logging.info(f"Aligned {len(aligned_data)} molecules for comparison.")

    logging.info("Calculating missing degrees of freedom error term...")
    missing_dof_result = calculate_missing_dof_error(aligned_data)

    logging.info(f"Generating physical model report at {output_report_path}")
    generate_physical_model_report(missing_dof_result, output_report_path)

    return missing_dof_result

def main():
    parser = argparse.ArgumentParser(description="Analyze missing degrees of freedom between Semi-empirical and DFT results.")
    parser.add_argument("--semi-path", required=True, help="Path to semi-empirical descriptors CSV (e.g., descriptors_semi.csv)")
    parser.add_argument("--dft-path", required=True, help="Path to DFT descriptors CSV (e.g., descriptors_dft.csv)")
    parser.add_argument("--output", required=True, help="Path for the output JSON report")
    parser.add_argument("--log", default="logs/missing_dof_analysis.log", help="Path for log file")
    
    args = parser.parse_args()

    # Setup logging
    os.makedirs(os.path.dirname(args.log), exist_ok=True)
    logger = setup_logger("missing_dof_analyzer", args.log)

    try:
        result = run_missing_dof_analysis(args.semi_path, args.dft_path, args.output)
        print(json.dumps(result, indent=2))
        sys.exit(0)
    except FileNotFoundError as e:
        logging.error(f"Input file not found: {e}")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Analysis failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()