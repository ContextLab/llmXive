"""
Experimental Validator Module

Compares model predictions against the physical experimental barrier dataset.
Calculates error margins against measured reality and defines the standard of evidence.
"""
import argparse
import csv
import json
import logging
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional

# Import existing utilities from the project
from utils.validation_utils import ValidationError
from utils.logging_utils import setup_logger

# Constants for the standard of evidence
EXPERIMENTAL_TOLERANCE_KCAL_MOL = 0.5  # kcal/mol
MAX_ALLOWED_MAE_KCAL_MOL = 2.0         # kcal/mol (from FR-010)
MIN_CORRELATION_THRESHOLD = 0.8        # Minimum R^2 to claim predictive validity

logger = logging.getLogger(__name__)

def load_experimental_data(experimental_csv_path: str) -> List[Dict[str, Any]]:
    """
    Load the experimental barrier dataset (ground truth).
    
    Args:
        experimental_csv_path: Path to the CSV file containing experimental data.
        
    Returns:
        List of dictionaries with experimental measurements.
    """
    data = []
    if not os.path.exists(experimental_csv_path):
        raise FileNotFoundError(f"Experimental data file not found: {experimental_csv_path}")
    
    with open(experimental_csv_path, 'r', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                # Parse numeric fields
                row['experimental_barrier'] = float(row['experimental_barrier'])
                if 'net_charge' in row:
                    row['net_charge'] = int(float(row['net_charge']))
                data.append(row)
            except (ValueError, KeyError) as e:
                logger.warning(f"Skipping malformed row in experimental data: {e}")
                continue
    
    if not data:
        raise ValueError("Experimental data file is empty or contains no valid rows")
    
    logger.info(f"Loaded {len(data)} experimental data points from {experimental_csv_path}")
    return data

def load_predictions(predictions_csv_path: str) -> List[Dict[str, Any]]:
    """
    Load model predictions.
    
    Args:
        predictions_csv_path: Path to the CSV file containing predictions.
        
    Returns:
        List of dictionaries with predicted values.
    """
    data = []
    if not os.path.exists(predictions_csv_path):
        raise FileNotFoundError(f"Predictions file not found: {predictions_csv_path}")
    
    with open(predictions_csv_path, 'r', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                # Parse numeric fields
                if 'predicted_barrier' in row:
                    row['predicted_barrier'] = float(row['predicted_barrier'])
                if 'experimental_barrier' in row:
                    row['experimental_barrier'] = float(row['experimental_barrier'])
                data.append(row)
            except (ValueError, KeyError) as e:
                logger.warning(f"Skipping malformed row in predictions: {e}")
                continue
    
    if not data:
        raise ValueError("Predictions file is empty or contains no valid rows")
    
    logger.info(f"Loaded {len(data)} predictions from {predictions_csv_path}")
    return data

def align_data(experimental: List[Dict], predictions: List[Dict], key_field: str = 'smiles') -> Tuple[List[Dict], List[Dict]]:
    """
    Align experimental and predicted data by a common key (e.g., SMILES).
    
    Args:
        experimental: List of experimental data dictionaries.
        predictions: List of prediction dictionaries.
        key_field: Field name to join on.
        
    Returns:
        Tuple of (aligned_experimental, aligned_predictions) lists.
    """
    exp_map = {row.get(key_field): row for row in experimental if row.get(key_field)}
    pred_map = {row.get(key_field): row for row in predictions if row.get(key_field)}
    
    aligned_exp = []
    aligned_pred = []
    missing = []
    
    for key in exp_map:
        if key in pred_map:
            aligned_exp.append(exp_map[key])
            aligned_pred.append(pred_map[key])
        else:
            missing.append(key)
    
    if missing:
        logger.warning(f"Missing predictions for {len(missing)} molecules: {missing[:5]}...")
    
    logger.info(f"Aligned {len(aligned_exp)} molecules between experimental and prediction sets")
    return aligned_exp, aligned_pred

def calculate_error_margin(predictions: List[Dict], experimental: List[Dict], 
                           pred_key: str = 'predicted_barrier', 
                           exp_key: str = 'experimental_barrier') -> Dict[str, float]:
    """
    Calculate error margin metrics against measured reality.
    
    Args:
        predictions: List of prediction dictionaries.
        experimental: List of experimental data dictionaries.
        pred_key: Key for predicted values.
        exp_key: Key for experimental values.
        
    Returns:
        Dictionary with MAE, RMSE, and Max Error.
    """
    if len(predictions) != len(experimental):
        raise ValueError("Prediction and experimental lists must be of equal length")
    
    errors = []
    for p, e in zip(predictions, experimental):
        pred_val = p.get(pred_key)
        exp_val = e.get(exp_key)
        
        if pred_val is None or exp_val is None:
            continue
        
        errors.append(abs(pred_val - exp_val))
    
    if not errors:
        raise ValueError("No valid errors could be calculated")
    
    mae = sum(errors) / len(errors)
    rmse = (sum(e**2 for e in errors) / len(errors)) ** 0.5
    max_error = max(errors)
    
    return {
        'mae_kcal_mol': round(mae, 4),
        'rmse_kcal_mol': round(rmse, 4),
        'max_error_kcal_mol': round(max_error, 4),
        'n_samples': len(errors)
    }

def verify_standard_of_evidence(metrics: Dict[str, float]) -> Dict[str, Any]:
    """
    Verify the model meets the standard of evidence.
    
    Args:
        metrics: Dictionary with error metrics.
        
    Returns:
        Dictionary with validation status and details.
    """
    mae = metrics.get('mae_kcal_mol', float('inf'))
    n_samples = metrics.get('n_samples', 0)
    
    status = 'pass'
    details = []
    
    # Check MAE threshold (FR-010)
    if mae > MAX_ALLOWED_MAE_KCAL_MOL:
        status = 'fail'
        details.append(f"MAE ({mae:.2f} kcal/mol) exceeds threshold ({MAX_ALLOWED_MAE_KCAL_MOL} kcal/mol)")
    else:
        details.append(f"MAE ({mae:.2f} kcal/mol) within threshold ({MAX_ALLOWED_MAE_KCAL_MOL} kcal/mol)")
    
    # Check sample size
    if n_samples < 30:
        status = 'fail'
        details.append(f"Sample size ({n_samples}) below minimum (30)")
    else:
        details.append(f"Sample size ({n_samples}) sufficient")
    
    # Check experimental tolerance
    if metrics.get('max_error_kcal_mol', float('inf')) > EXPERIMENTAL_TOLERANCE_KCAL_MOL * 10:
        details.append(f"Max error ({metrics['max_error_kcal_mol']:.2f} kcal/mol) indicates outliers")
    
    return {
        'status': status,
        'details': details,
        'metrics': metrics
    }

def generate_validation_report(experimental_data: List[Dict], predictions: List[Dict], 
                               output_path: str) -> Dict[str, Any]:
    """
    Generate a comprehensive validation report.
    
    Args:
        experimental_data: List of experimental data dictionaries.
        predictions: List of prediction dictionaries.
        output_path: Path to write the JSON report.
        
    Returns:
        The validation report dictionary.
    """
    # Align data
    aligned_exp, aligned_pred = align_data(experimental_data, predictions)
    
    if len(aligned_exp) == 0:
        raise ValidationError("No overlapping molecules between experimental and prediction sets")
    
    # Calculate metrics
    metrics = calculate_error_margin(aligned_pred, aligned_exp)
    
    # Verify standard of evidence
    verification = verify_standard_of_evidence(metrics)
    
    # Build report
    report = {
        'standard_of_evidence': {
            'description': 'Comparison of model predictions against physical experimental barrier dataset',
            'experimental_source': 'Zenodo experimental barrier dataset (downloaded via T004)',
            'tolerance_kcal_mol': EXPERIMENTAL_TOLERANCE_KCAL_MOL,
            'max_allowed_mae_kcal_mol': MAX_ALLOWED_MAE_KCAL_MOL
        },
        'alignment': {
            'total_experimental': len(experimental_data),
            'total_predictions': len(predictions),
            'aligned_count': len(aligned_exp),
            'missing_predictions': len(experimental_data) - len(aligned_exp)
        },
        'error_margin': metrics,
        'verification': verification
    }
    
    # Write report
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Validation report written to {output_path}")
    return report

def main():
    """Main entry point for the experimental validator."""
    parser = argparse.ArgumentParser(description='Validate model predictions against experimental data')
    parser.add_argument('--experimental', type=str, required=True, 
                        help='Path to experimental data CSV')
    parser.add_argument('--predictions', type=str, required=True,
                        help='Path to predictions CSV')
    parser.add_argument('--output', type=str, required=True,
                        help='Path to output validation report JSON')
    parser.add_argument('--log-file', type=str, default='logs/experimental_validation.log',
                        help='Path to log file')
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logger('experimental_validator', args.log_file)
    
    try:
        # Load data
        logger.info("Loading experimental data...")
        experimental_data = load_experimental_data(args.experimental)
        
        logger.info("Loading predictions...")
        predictions = load_predictions(args.predictions)
        
        # Generate report
        logger.info("Generating validation report...")
        report = generate_validation_report(experimental_data, predictions, args.output)
        
        # Print summary
        print(f"\n=== Experimental Validation Summary ===")
        print(f"Status: {report['verification']['status'].upper()}")
        print(f"Aligned Samples: {report['alignment']['aligned_count']}")
        print(f"MAE: {report['error_margin']['mae_kcal_mol']:.4f} kcal/mol")
        print(f"RMSE: {report['error_margin']['rmse_kcal_mol']:.4f} kcal/mol")
        print(f"Max Error: {report['error_margin']['max_error_kcal_mol']:.4f} kcal/mol")
        print(f"Details: {'; '.join(report['verification']['details'])}")
        
        # Exit with error if verification failed
        if report['verification']['status'] == 'fail':
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Validation failed: {e}")
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
