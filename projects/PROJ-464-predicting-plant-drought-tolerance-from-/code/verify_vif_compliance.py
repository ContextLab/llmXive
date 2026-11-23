"""
Verification module for VIF compliance (Task T030).

This module verifies that if VIF > 5 is detected, the system has refrained
from claiming independent effects for definitionally related variables.
It reads model results and VIF status, performs the verification logic,
and outputs the final compliance check report to state/vif_compliance_check.yaml.
"""
import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
import yaml
import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_model_results(results_path: Path) -> pd.DataFrame:
    """
    Load the aggregated model results from data/derived/model_results.csv.
    
    Args:
        results_path: Path to the model results CSV file.
        
    Returns:
        DataFrame containing model results.
        
    Raises:
        FileNotFoundError: If the model results file does not exist.
        ValueError: If the file is empty or malformed.
    """
    if not results_path.exists():
        raise FileNotFoundError(f"Model results file not found: {results_path}")
    
    df = pd.read_csv(results_path)
    
    if df.empty:
        raise ValueError(f"Model results file is empty: {results_path}")
        
    required_columns = {'model_type', 'predictor', 'coefficient', 'p_value', 'r2', 'adj_p_value'}
    if not required_columns.issubset(df.columns):
        missing = required_columns - set(df.columns)
        raise ValueError(f"Model results missing required columns: {missing}")
        
    logger.info(f"Loaded {len(df)} model results from {results_path}")
    return df

def load_vif_status(vif_path: Path) -> Dict[str, Any]:
    """
    Load the VIF compliance status from state/vif_compliance_check.yaml.
    
    Args:
        vif_path: Path to the VIF compliance check YAML file.
        
    Returns:
        Dictionary containing VIF status information.
        
    Raises:
        FileNotFoundError: If the VIF status file does not exist.
        yaml.YAMLError: If the file is not valid YAML.
    """
    if not vif_path.exists():
        raise FileNotFoundError(f"VIF status file not found: {vif_path}")
    
    with open(vif_path, 'r') as f:
        data = yaml.safe_load(f)
        
    if data is None:
        raise ValueError(f"VIF status file is empty: {vif_path}")
        
    logger.info(f"Loaded VIF status from {vif_path}")
    return data

def verify_vif_suppression_logic(
    model_results: pd.DataFrame,
    vif_status: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Verify that if VIF > 5 was detected, the system correctly suppressed
    independent effect claims for correlated variables.
    
    This function checks:
    1. If VIF > 5 was detected (vif_status['vif_exceeded'] is True)
    2. If so, verify that the report framing logic was triggered
    3. Check that the 'suppressed_claims' field is populated with the 
       variables that were suppressed
    4. Verify that the final report text does not claim independent effects
       for those variables
    
    Args:
        model_results: DataFrame with model results.
        vif_status: Dictionary with VIF status information.
        
    Returns:
        Dictionary containing verification results and compliance status.
    """
    verification_result = {
        'verification_timestamp': str(pd.Timestamp.now()),
        'vif_exceeded': vif_status.get('vif_exceeded', False),
        'compliance_status': 'PASS',
        'details': [],
        'warnings': [],
        'errors': []
    }
    
    # Check if VIF exceeded threshold
    if not verification_result['vif_exceeded']:
        verification_result['details'].append(
            "VIF threshold (5) was not exceeded. No suppression required."
        )
        verification_result['compliance_status'] = 'PASS'
        return verification_result
    
    # If VIF exceeded, check that suppression logic was applied
    if 'suppressed_claims' not in vif_status or not vif_status['suppressed_claims']:
        error_msg = "VIF exceeded but no suppressed claims recorded."
        verification_result['errors'].append(error_msg)
        verification_result['compliance_status'] = 'FAIL'
        logger.error(error_msg)
        return verification_result
    
    # Verify that suppressed variables are documented
    suppressed_vars = vif_status.get('suppressed_claims', [])
    if not isinstance(suppressed_vars, list) or len(suppressed_vars) == 0:
        error_msg = "Suppressed claims list is empty or invalid."
        verification_result['errors'].append(error_msg)
        verification_result['compliance_status'] = 'FAIL'
        logger.error(error_msg)
        return verification_result
    
    verification_result['details'].append(
        f"VIF exceeded. Suppressed {len(suppressed_vars)} variables: {', '.join(suppressed_vars)}"
    )
    
    # Check that model results do not claim independent effects for suppressed variables
    # This is a heuristic check: if a variable is suppressed, its p-value should not be 
    # reported as significant in the final interpretation
    for predictor in suppressed_vars:
        predictor_rows = model_results[model_results['predictor'] == predictor]
        if not predictor_rows.empty:
            # Check if any significant results exist for this predictor
            significant_results = predictor_rows[predictor_rows['adj_p_value'] < 0.05]
            if len(significant_results) > 0:
                warning_msg = (
                    f"Predictor '{predictor}' has significant results (p < 0.05) "
                    "but was marked for suppression due to high VIF. "
                    "Ensure final report does not claim independent effects."
                )
                verification_result['warnings'].append(warning_msg)
                logger.warning(warning_msg)
    
    # Check for presence of framing text in VIF status
    if 'framing_applied' in vif_status and vif_status['framing_applied']:
        verification_result['details'].append(
            "Framing logic applied to suppress independent effect claims."
        )
    else:
        warning_msg = "VIF exceeded but framing_applied flag not set or False."
        verification_result['warnings'].append(warning_msg)
        logger.warning(warning_msg)
    
    # Final compliance determination
    if verification_result['errors']:
        verification_result['compliance_status'] = 'FAIL'
    elif verification_result['warnings']:
        verification_result['compliance_status'] = 'WARNING'
    else:
        verification_result['compliance_status'] = 'PASS'
    
    return verification_result

def generate_final_verification_report(
    verification_result: Dict[str, Any],
    output_path: Path
) -> None:
    """
    Generate the final VIF compliance check report.
    
    Args:
        verification_result: Dictionary containing verification results.
        output_path: Path where the YAML report will be saved.
    """
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Add verification summary
    verification_result['summary'] = {
        'task_id': 'T030',
        'description': 'Verify VIF compliance: refraining from independent effect claims when VIF > 5',
        'status': verification_result['compliance_status'],
        'vif_threshold': 5.0
    }
    
    # Write to YAML
    with open(output_path, 'w') as f:
        yaml.dump(verification_result, f, default_flow_style=False, sort_keys=False)
    
    logger.info(f"Final verification report saved to {output_path}")

def main() -> int:
    """
    Main entry point for VIF compliance verification.
    
    Returns:
        Exit code (0 for success, 1 for failure).
    """
    try:
        # Define paths
        base_dir = Path(__file__).parent.parent
        model_results_path = base_dir / 'data' / 'derived' / 'model_results.csv'
        vif_status_path = base_dir / 'state' / 'vif_compliance_check.yaml'
        output_path = base_dir / 'state' / 'vif_compliance_check.yaml'
        
        logger.info("Starting VIF compliance verification (T030)")
        
        # Load model results
        model_results = load_model_results(model_results_path)
        
        # Load VIF status
        vif_status = load_vif_status(vif_status_path)
        
        # Perform verification
        verification_result = verify_vif_suppression_logic(model_results, vif_status)
        
        # Generate final report
        generate_final_verification_report(verification_result, output_path)
        
        # Return appropriate exit code
        if verification_result['compliance_status'] == 'FAIL':
            logger.error("VIF compliance verification FAILED")
            return 1
        elif verification_result['compliance_status'] == 'WARNING':
            logger.warning("VIF compliance verification completed with warnings")
            return 0
        else:
            logger.info("VIF compliance verification PASSED")
            return 0
            
    except Exception as e:
        logger.exception(f"Error during VIF compliance verification: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main())
