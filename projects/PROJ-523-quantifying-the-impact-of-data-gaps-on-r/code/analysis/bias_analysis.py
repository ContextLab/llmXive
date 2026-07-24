import os
import sys
import json
import csv
import logging
from pathlib import Path
import numpy as np

from config import DATA_DERIVED_DIR, DATA_RESULTS_DIR, N_SIDE
from analysis.parameter_est import estimate_parameters_from_grid

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(DATA_RESULTS_DIR / 'bias_analysis.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def load_ground_truth_parameters():
    """
    Load ground truth cosmological parameters from metadata files.
    Returns a dictionary keyed by realization_id.
    """
    gt_params = {}
    metadata_dir = DATA_DERIVED_DIR / "metadata"
    
    if not metadata_dir.exists():
        logger.error(f"Metadata directory not found: {metadata_dir}")
        return gt_params

    for file_path in metadata_dir.glob("*.json"):
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                # Extract realization ID from filename or content
                rid = file_path.stem
                # Expected keys: H0, Omega_m, n_s, tau
                gt_params[rid] = {
                    'H0': data.get('H0'),
                    'Omega_m': data.get('Omega_m'),
                    'n_s': data.get('n_s'),
                    'tau': data.get('tau')
                }
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"Could not parse ground truth for {file_path}: {e}")
    
    return gt_params

def load_parameter_estimation_results():
    """
    Load parameter estimation results from the parameter_est output files.
    Returns a dictionary keyed by realization_id.
    """
    est_results = {}
    # Assuming results are stored in data/derived or similar based on T028b
    # The specific path might be data/derived/parameter_est/ or similar
    # Based on T028b description, we look for the output of the estimation step
    results_dir = DATA_DERIVED_DIR # Adjust if a specific subdirectory is used for results
    
    if not results_dir.exists():
        logger.warning(f"Parameter estimation results directory not found: {results_dir}")
        return est_results

    # Pattern might be {realization_id}_est_results.json or similar
    # Assuming a standard naming convention based on previous tasks
    for file_path in results_dir.glob("*_est_results.json"):
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                rid = file_path.stem.replace('_est_results', '')
                est_results[rid] = {
                    'H0': data.get('H0'),
                    'Omega_m': data.get('Omega_m'),
                    'n_s': data.get('n_s'),
                    'tau': data.get('tau'),
                    'gap_fraction': data.get('gap_fraction'),
                    'algo_name': data.get('algo_name'),
                    'morphology': data.get('morphology')
                }
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"Could not parse estimation result for {file_path}: {e}")
    
    return est_results

def calculate_bias(gt_params, est_results):
    """
    Calculate bias magnitude for each parameter and realization.
    Returns a list of dictionaries with bias details.
    """
    bias_data = []
    params = ['H0', 'Omega_m', 'n_s', 'tau']
    
    for rid, est in est_results.items():
        if rid not in gt_params:
            logger.warning(f"Ground truth missing for {rid}, skipping bias calculation.")
            continue
        
        gt = gt_params[rid]
        row = {
            'realization_id': rid,
            'gap_fraction': est.get('gap_fraction'),
            'algo_name': est.get('algo_name'),
            'morphology': est.get('morphology')
        }
        
        for p in params:
            if gt[p] is not None and est[p] is not None:
                bias_val = abs(est[p] - gt[p])
                row[f'{p}_bias'] = bias_val
            else:
                row[f'{p}_bias'] = np.nan
        
        bias_data.append(row)
    
    return bias_data

def calculate_noise_floor(n_realizations):
    """
    Calculate the statistical noise floor based on sqrt(N) scaling.
    This serves as the threshold for distinguishing real bias from noise.
    """
    if n_realizations <= 0:
        return 0.0
    # The noise floor scales with 1/sqrt(N) relative to the single-measurement variance.
    # Here we return a relative factor or a threshold value if variance is known.
    # For this implementation, we assume a standard deviation of 1 for normalization,
    # so the floor is 1/sqrt(N).
    return 1.0 / np.sqrt(n_realizations)

def apply_bias_floor_validation(bias_data, noise_floor):
    """
    Compare calculated bias against the statistical noise floor.
    Flags results as "Indistinguishable from Noise" if bias < noise_floor.
    """
    params = ['H0', 'Omega_m', 'n_s', 'tau']
    
    for row in bias_data:
        # Check each parameter bias
        for p in params:
            bias_key = f'{p}_bias'
            if bias_key in row and not np.isnan(row[bias_key]):
                if row[bias_key] < noise_floor:
                    # Flag this specific parameter bias
                    flag_key = f'{p}_flag'
                    row[flag_key] = "Indistinguishable from Noise"
                else:
                    row[flag_key] = "Significant"
            else:
                # If bias is NaN, flag as missing
                row[f'{p}_flag'] = "Missing Data"
    
    return bias_data

def run_bias_analysis():
    """
    Main pipeline to run bias analysis including the Bias Floor validation.
    """
    logger.info("Starting Bias Analysis with Bias Floor Validation")
    
    # 1. Load Data
    gt_params = load_ground_truth_parameters()
    est_results = load_parameter_estimation_results()
    
    if not gt_params:
        logger.error("No ground truth parameters found. Aborting.")
        return
    
    if not est_results:
        logger.error("No parameter estimation results found. Aborting.")
        return
    
    # 2. Calculate Bias
    bias_data = calculate_bias(gt_params, est_results)
    
    if not bias_data:
        logger.warning("No valid bias data calculated.")
        return

    # 3. Determine Noise Floor
    # Count valid realizations contributing to the specific bias calculation
    # We use the total number of valid entries in bias_data as N
    n_valid = len(bias_data)
    noise_floor = calculate_noise_floor(n_valid)
    logger.info(f"Calculated noise floor (sqrt(N) scaling) for N={n_valid}: {noise_floor:.6f}")
    
    # 4. Apply Bias Floor Validation
    validated_data = apply_bias_floor_validation(bias_data, noise_floor)
    
    # 5. Save Results
    output_path = DATA_RESULTS_DIR / "bias_summary.csv"
    if not output_path.parent.exists():
        output_path.parent.mkdir(parents=True, exist_ok=True)
    
    fieldnames = ['realization_id', 'gap_fraction', 'algo_name', 'morphology']
    params = ['H0', 'Omega_m', 'n_s', 'tau']
    for p in params:
        fieldnames.extend([f'{p}_bias', f'{p}_flag'])
    
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(validated_data)
    
    logger.info(f"Bias analysis complete. Results saved to {output_path}")
    return validated_data

def main():
    """
    Entry point for the bias analysis script.
    """
    try:
        run_bias_analysis()
    except Exception as e:
        logger.exception(f"Fatal error in bias analysis pipeline: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()