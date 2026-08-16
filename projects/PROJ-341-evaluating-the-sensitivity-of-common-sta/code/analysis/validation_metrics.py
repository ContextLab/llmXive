"""
Validation metrics calculation and saving for User Story 3.

This module computes validation metrics and KS statistics comparing
simulated results with real-world dataset results, and saves them to
data/simulation/validation_metrics.json.
"""
import os
import json
import csv
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
from scipy import stats
from code.simulation.logging_config import get_logger, log_operation
from code.analysis.bootstrapper import calculate_ks_distance
from code.analysis.validator import load_p_values_to_csv_safe
from code.analysis.aggregator import load_error_rates
from code.simulation.output_writer import load_p_values_raw_safe


logger = get_logger(__name__)


def load_simulated_pvalues_for_comparison(
    test_type: str,
    alpha: float = 0.05
) -> List[float]:
    """
    Load simulated p-values for a specific test type and hypothesis state.
    
    Args:
        test_type: One of 't-test', 'anova', 'chi-squared'
        alpha: Significance level (default 0.05)
        
    Returns:
        List of p-values from simulations where null hypothesis was true
    """
    try:
        p_values = load_p_values_raw_safe()
        if p_values is None:
            logger.log("error_loading_simulated_pvalues", error="No simulated p-values found")
            return []
        
        # Filter for the specific test type and null hypothesis
        filtered = [
            row['p_value'] for row in p_values
            if row['test_type'] == test_type and row['hypothesis'] == 'null_true'
        ]
        return filtered
    except Exception as e:
        logger.log("error_loading_simulated_pvalues", error=str(e))
        return []


def calculate_real_data_power(
    real_p_values: List[float],
    alpha: float = 0.05
) -> Dict[str, Any]:
    """
    Calculate power metrics from real data p-values.
    
    Args:
        real_p_values: List of p-values from real dataset tests
        alpha: Significance level
        
    Returns:
        Dictionary with power metrics
    """
    if not real_p_values:
        return {
            'power': 0.0,
            'type_i_error_rate': 0.0,
            'type_ii_error_rate': 0.0,
            'sample_size': 0
        }
    
    n = len(real_p_values)
    significant = sum(1 for p in real_p_values if p < alpha)
    non_significant = n - significant
    
    # For real data, we estimate power as the proportion of significant results
    # (assuming most real datasets have some effect)
    power = significant / n if n > 0 else 0.0
    
    # Type I error rate estimate (proportion of non-significant when we expect effects)
    # This is a heuristic since we don't know ground truth for real data
    type_ii_rate = non_significant / n if n > 0 else 0.0
    
    return {
        'power': float(power),
        'type_i_error_rate': float(1.0 - type_ii_rate),  # Heuristic
        'type_ii_error_rate': float(type_ii_rate),
        'sample_size': n,
        'significant_count': significant,
        'non_significant_count': non_significant
    }


def calculate_validation_metrics(
    simulated_power: Dict[str, Any],
    real_data_power: Dict[str, Any],
    ks_distance: float,
    test_type: str,
    effect_size: Optional[float] = None
) -> Dict[str, Any]:
    """
    Calculate comprehensive validation metrics comparing simulation and real data.
    
    Args:
        simulated_power: Power metrics from simulation
        real_data_power: Power metrics from real data
        ks_distance: Kolmogorov-Smirnov distance between distributions
        test_type: The statistical test being validated
        effect_size: Effect size used in simulation (if applicable)
        
    Returns:
        Dictionary containing all validation metrics
    """
    metrics = {
        'test_type': test_type,
        'effect_size': effect_size,
        'ks_distance': float(ks_distance),
        'simulated_power': simulated_power.get('power', 0.0),
        'real_data_power': real_data_power.get('power', 0.0),
        'power_difference': abs(simulated_power.get('power', 0.0) - real_data_power.get('power', 0.0)),
        'simulated_type_i_error': simulated_power.get('type_i_error_rate', 0.0),
        'real_data_type_i_error': real_data_power.get('type_i_error_rate', 0.0),
        'type_i_error_difference': abs(simulated_power.get('type_i_error_rate', 0.0) - real_data_power.get('type_i_error_rate', 0.0)),
        'simulated_type_ii_error': simulated_power.get('type_ii_error_rate', 0.0),
        'real_data_type_ii_error': real_data_power.get('type_ii_error_rate', 0.0),
        'type_ii_error_difference': abs(simulated_power.get('type_ii_error_rate', 0.0) - real_data_power.get('type_ii_error_rate', 0.0)),
        'ks_threshold_met': ks_distance <= 0.10,
        'validation_status': 'PASSED' if ks_distance <= 0.10 else 'FAILED',
        'timestamp': __import__('datetime').datetime.utcnow().isoformat()
    }
    
    return metrics


def save_validation_metrics(
    metrics_list: List[Dict[str, Any]],
    output_path: str = 'data/simulation/validation_metrics.json'
) -> bool:
    """
    Save validation metrics to a JSON file.
    
    Args:
        metrics_list: List of validation metric dictionaries
        output_path: Path to save the JSON file
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Ensure output directory exists
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
            logger.log("directory_created", path=output_dir)
        
        # Create metadata wrapper
        output_data = {
            'validation_metrics': metrics_list,
            'summary': {
                'total_tests': len(metrics_list),
                'passed_count': sum(1 for m in metrics_list if m.get('validation_status') == 'PASSED'),
                'failed_count': sum(1 for m in metrics_list if m.get('validation_status') == 'FAILED'),
                'average_ks_distance': np.mean([m.get('ks_distance', 0.0) for m in metrics_list]) if metrics_list else 0.0
            },
            'timestamp': __import__('datetime').datetime.utcnow().isoformat()
        }
        
        with open(output_path, 'w') as f:
            json.dump(output_data, f, indent=2)
        
        logger.log("validation_metrics_saved", path=output_path, count=len(metrics_list))
        return True
        
    except Exception as e:
        logger.log("error_saving_validation_metrics", error=str(e), path=output_path)
        return False


@log_operation
def main() -> int:
    """
    Main entry point for calculating and saving validation metrics.
    
    This function:
    1. Loads simulated p-values for comparison
    2. Loads real data p-values
    3. Calculates power metrics for both
    4. Computes KS distance between distributions
    5. Generates validation metrics
    6. Saves results to data/simulation/validation_metrics.json
    
    Returns:
        0 on success, 1 on failure
    """
    logger.log("validation_metrics_start")
    
    try:
        # Define test types to validate
        test_types = ['t-test', 'anova', 'chi-squared']
        alpha = 0.05
        metrics_list = []
        
        for test_type in test_types:
            logger.log("processing_test_type", test_type=test_type)
            
            # Load simulated p-values for this test type
            simulated_pvalues = load_simulated_pvalues_for_comparison(test_type, alpha)
            if not simulated_pvalues:
                logger.log("warning_no_simulated_data", test_type=test_type)
                continue
            
            # Load real data p-values for this test type
            real_pvalues = load_p_values_to_csv_safe(test_type)
            if not real_pvalues:
                logger.log("warning_no_real_data", test_type=test_type)
                continue
            
            # Calculate power metrics
            simulated_power = calculate_real_data_power(simulated_pvalues, alpha)
            real_data_power = calculate_real_data_power(real_pvalues, alpha)
            
            # Calculate KS distance
            ks_stat, ks_pvalue = stats.ks_2samp(simulated_pvalues, real_pvalues)
            ks_distance = float(ks_stat)
            
            # Determine effect size (heuristic: use median absolute difference)
            effect_size = None
            if simulated_pvalues and real_pvalues:
                # For simplicity, we don't have a direct effect size here
                # In a full implementation, this would come from the simulation params
                pass
            
            # Calculate validation metrics
            metrics = calculate_validation_metrics(
                simulated_power=simulated_power,
                real_data_power=real_data_power,
                ks_distance=ks_distance,
                test_type=test_type,
                effect_size=effect_size
            )
            
            metrics_list.append(metrics)
            logger.log("metrics_calculated", test_type=test_type, ks_distance=ks_distance, status=metrics['validation_status'])
        
        # Save all metrics
        output_path = 'data/simulation/validation_metrics.json'
        if save_validation_metrics(metrics_list, output_path):
            logger.log("validation_metrics_complete", path=output_path, total=len(metrics_list))
            return 0
        else:
            logger.log("error_saving_metrics")
            return 1
            
    except Exception as e:
        logger.log("error_in_validation_metrics", error=str(e))
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    import sys
    sys.exit(main())