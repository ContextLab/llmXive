import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union

import numpy as np

# Import from sibling modules based on API surface
from analysis.aggregation_utils import aggregate_power_results
from analysis.fdr_corrector import apply_fdr_to_power_curves, FDRCorrectionError
from analysis.glm_fitter import fit_glm, estimate_effect_size, GLMFitError
from analysis.split_half_validator import run_split_half_validation, validate_split_half
from models.simulation_config import SimulationConfig
from utils.seed_manager import set_global_seed

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)


def bootstrap_single_iteration(
    paradigm_data: Dict[str, Any],
    sample_size: int,
    smoothing_kernel: float,
    seed: int
) -> Dict[str, Any]:
    """
    Perform a single bootstrap iteration for power analysis.
    
    Args:
        paradigm_data: Dictionary containing preprocessed ROI data for a paradigm.
        sample_size: Number of subjects to sample.
        smoothing_kernel: Temporal smoothing kernel size (mm).
        seed: Random seed for reproducibility.
        
    Returns:
        Dictionary with replication success flag and effect size.
    """
    set_global_seed(seed)
    
    try:
        # Simulate splitting data (in real implementation, this would sample subjects)
        # For this task, we assume paradigm_data contains a list of subjects
        subjects = paradigm_data.get('subjects', [])
        if len(subjects) < sample_size:
            # Clamp to available data
            sample_size = len(subjects)
            logger.warning(f"Requested N={sample_size}, but only {len(subjects)} available. Clamping.")
        
        if sample_size == 0:
            raise ValueError("No subjects available for sampling.")
        
        sampled_subjects = np.random.choice(subjects, size=sample_size, replace=False)
        
        # Run split-half validation on sampled data
        # This is a simplified call; real implementation would pass actual data
        validation_result = run_split_half_validation(
            data=sampled_subjects,
            smoothing_kernel=smoothing_kernel,
            seed=seed
        )
        
        return {
            'replication_success': validation_result.get('replication_success', 0),
            'effect_size': validation_result.get('effect_size', 0.0),
            'p_value': validation_result.get('p_value', 1.0),
            'sample_size': sample_size
        }
        
    except Exception as e:
        logger.error(f"Bootstrap iteration failed: {e}")
        return {
            'replication_success': 0,
            'effect_size': 0.0,
            'p_value': 1.0,
            'sample_size': sample_size,
            'error': str(e)
        }


def run_bootstrap_loop(
    paradigm_data: Dict[str, Any],
    sample_sizes: List[int],
    smoothing_kernel: float,
    num_iterations: int,
    seed: int
) -> Dict[str, Any]:
    """
    Run bootstrap loop across multiple sample sizes.
    
    Args:
        paradigm_data: Preprocessed data for a specific paradigm.
        sample_sizes: List of sample sizes to test.
        smoothing_kernel: Smoothing kernel size.
        num_iterations: Number of bootstrap iterations per sample size.
        seed: Base random seed.
        
    Returns:
        Aggregated results for all sample sizes.
    """
    results = {
        'sample_sizes': sample_sizes,
        'empirical_rates': [],
        'effect_sizes': [],
        'iterations': num_iterations,
        'kernel': smoothing_kernel
    }
    
    for n in sample_sizes:
        iteration_results = []
        for i in range(num_iterations):
            iter_seed = seed + i
            result = bootstrap_single_iteration(
                paradigm_data, n, smoothing_kernel, iter_seed
            )
            iteration_results.append(result)
        
        # Aggregate results for this sample size
        successful_replications = sum(1 for r in iteration_results if r['replication_success'] == 1)
        power_rate = successful_replications / num_iterations
        
        # Average effect size
        avg_effect = np.mean([r['effect_size'] for r in iteration_results])
        
        results['empirical_rates'].append(power_rate)
        results['effect_sizes'].append(avg_effect)
        
        logger.info(f"Sample size N={n}: Power={power_rate:.3f}, Effect={avg_effect:.3f}")
        
    return results


def generate_power_curve(
    paradigm_data: Dict[str, Any],
    sample_sizes: List[int],
    smoothing_kernel: float,
    num_iterations: int,
    seed: int
) -> Dict[str, Any]:
    """
    Generate a full power curve for a paradigm and kernel.
    
    Args:
        paradigm_data: Preprocessed data.
        sample_sizes: List of sample sizes.
        smoothing_kernel: Smoothing kernel size.
        num_iterations: Bootstrap iterations.
        seed: Random seed.
        
    Returns:
        Power curve data structure.
    """
    logger.info(f"Generating power curve for kernel={smoothing_kernel}mm")
    
    curve_data = run_bootstrap_loop(
        paradigm_data, sample_sizes, smoothing_kernel, num_iterations, seed
    )
    
    # Fit logistic regression model (simplified)
    try:
        model_info = fit_power_curve_model(
            sample_sizes, curve_data['empirical_rates']
        )
        curve_data['model'] = model_info
    except Exception as e:
        logger.warning(f"Failed to fit power curve model: {e}")
        curve_data['model'] = None
        
    return curve_data


def fit_power_curve_model(
    sample_sizes: List[int],
    power_rates: List[float]
) -> Dict[str, Any]:
    """
    Fit a logistic regression model to power curve data.
    
    Args:
        sample_sizes: X values.
        power_rates: Y values (probabilities).
        
    Returns:
        Model parameters and statistics.
    """
    import statsmodels.api as sm
    
    X = np.array(sample_sizes)
    y = np.array(power_rates)
    
    # Add constant for intercept
    X = sm.add_constant(X)
    
    # Fit logistic regression
    model = sm.Logit(y, X)
    result = model.fit(disp=False)
    
    return {
        'coefficients': result.params.tolist(),
        'pvalues': result.pvalues.tolist(),
        'log_likelihood': result.llf,
        'pseudo_r2': result.prsquared
    }


def save_power_curves(
    results: Dict[str, Any],
    output_path: Path
) -> None:
    """
    Save power curve results to JSON file.
    
    Args:
        results: Dictionary of power curve data.
        output_path: Path to save the JSON file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Saved power curves to {output_path}")


def get_fdr_justification() -> str:
    """
    Return justification for using FDR over Bonferroni.
    
    Returns:
        String justification.
    """
    return (
        "Benjamini-Hochberg FDR correction was chosen over Bonferroni because "
        "it provides greater statistical power while controlling the expected "
        "proportion of false discoveries. Given the exploratory nature of "
        "comparing multiple cognitive paradigms, FDR is more appropriate than "
        "the overly conservative Bonferroni method which assumes independence "
        "and controls family-wise error rate."
    )


def calculate_kernel_sensitivity(
    results_4mm: Dict[str, Any],
    results_8mm: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Calculate sensitivity between different smoothing kernels.
    
    This function compares replication rates across 4mm and 8mm kernels
    and flags "High Sensitivity" if the difference exceeds 10 percentage points.
    
    Args:
        results_4mm: Power curve results for 4mm kernel.
        results_8mm: Power curve results for 8mm kernel.
        
    Returns:
        Dictionary with sensitivity analysis including "high_sensitivity" flag.
    """
    sensitivity_data = {
        'kernel_4mm': results_4mm.get('kernel', 4),
        'kernel_8mm': results_8mm.get('kernel', 8),
        'sample_sizes_tested': results_4mm.get('sample_sizes', []),
        'replication_rates_4mm': results_4mm.get('empirical_rates', []),
        'replication_rates_8mm': results_8mm.get('empirical_rates', []),
        'differences': [],
        'max_difference': 0.0,
        'high_sensitivity': False,
        'analysis_note': ''
    }
    
    rates_4 = np.array(results_4mm.get('empirical_rates', []))
    rates_8 = np.array(results_8mm.get('empirical_rates', []))
    
    if len(rates_4) != len(rates_8):
        logger.warning("Sample sizes differ between kernels. Aligning by index.")
        min_len = min(len(rates_4), len(rates_8))
        rates_4 = rates_4[:min_len]
        rates_8 = rates_8[:min_len]
    
    # Calculate absolute differences in percentage points
    differences = np.abs(rates_4 - rates_8) * 100  # Convert to percentage points
    sensitivity_data['differences'] = differences.tolist()
    
    if len(differences) > 0:
        max_diff = float(np.max(differences))
        sensitivity_data['max_difference'] = max_diff
        
        # Check for High Sensitivity (US-3 Scenario 2)
        if max_diff > 10.0:
            sensitivity_data['high_sensitivity'] = True
            sensitivity_data['analysis_note'] = (
                f"HIGH SENSITIVITY DETECTED: Maximum difference in replication rates "
                f"between 4mm and 8mm kernels is {max_diff:.2f} percentage points, "
                f"exceeding the 10 percentage point threshold. This indicates that "
                f"preprocessing smoothing choices significantly impact statistical power."
            )
            logger.warning(sensitivity_data['analysis_note'])
        else:
            sensitivity_data['analysis_note'] = (
                f"Replication rate differences between 4mm and 8mm kernels are within "
                f"tolerance (max {max_diff:.2f} pp). Preprocessing smoothing has "
                f"modest impact on power in this analysis."
            )
            logger.info(sensitivity_data['analysis_note'])
    
    return sensitivity_data


def main():
    """
    Main entry point for power curve generation and sensitivity analysis.
    
    This function orchestrates the generation of power curves for multiple
    smoothing kernels and performs sensitivity analysis.
    """
    parser = argparse.ArgumentParser(description='Power Curve Generator')
    parser.add_argument('--config', type=str, required=True, help='Path to config JSON')
    parser.add_argument('--output', type=str, required=True, help='Output path for results')
    args = parser.parse_args()
    
    # Load config
    with open(args.config, 'r') as f:
        config = json.load(f)
    
    logger.info(f"Loaded config from {args.config}")
    
    # Extract parameters
    sample_sizes = config.get('sample_sizes', [10, 20, 30, 40])
    kernels = config.get('kernels', [4.0, 8.0])
    num_iterations = config.get('num_iterations', 100)
    seed = config.get('random_seed', 42)
    paradigm_data_path = config.get('paradigm_data_path')
    
    if not paradigm_data_path:
        logger.error("paradigm_data_path not specified in config")
        sys.exit(1)
        
    # Load paradigm data (simplified for this task)
    # In real implementation, this would load from file
    try:
        with open(paradigm_data_path, 'r') as f:
            paradigm_data = json.load(f)
    except FileNotFoundError:
        logger.error(f"Paradigm data file not found: {paradigm_data_path}")
        sys.exit(1)
    
    # Generate power curves for each kernel
    all_curves = {}
    for kernel in kernels:
        curve = generate_power_curve(
            paradigm_data, sample_sizes, kernel, num_iterations, seed
        )
        all_curves[f'kernel_{int(kernel)}mm'] = curve
    
    # Perform sensitivity analysis if multiple kernels exist
    sensitivity_results = None
    if len(kernels) >= 2:
        # Assuming first two kernels are 4mm and 8mm
        if 'kernel_4mm' in all_curves and 'kernel_8mm' in all_curves:
            sensitivity_results = calculate_kernel_sensitivity(
                all_curves['kernel_4mm'], all_curves['kernel_8mm']
            )
    
    # Prepare final output
    output_data = {
        'config': {
            'sample_sizes': sample_sizes,
            'kernels': kernels,
            'num_iterations': num_iterations,
            'seed': seed
        },
        'power_curves': all_curves,
        'sensitivity_analysis': sensitivity_results,
        'fdr_justification': get_fdr_justification()
    }
    
    # Save results
    output_path = Path(args.output)
    save_power_curves(output_data, output_path)
    
    print(f"Analysis complete. Results saved to {output_path}")
    if sensitivity_results and sensitivity_results.get('high_sensitivity'):
        print("WARNING: High sensitivity to smoothing kernel detected!")
        
    return 0


if __name__ == '__main__':
    sys.exit(main())