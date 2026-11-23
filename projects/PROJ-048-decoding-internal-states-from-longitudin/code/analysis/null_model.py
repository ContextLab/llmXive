"""
Null model generation for decoding internal states.

Implements the "linear mixing of behavior" null model (FR-009) to provide
a baseline for comparing NMF-derived correlations. This model assumes that
observed neural activity can be explained by a simple linear combination
of behavioral metrics, without any latent internal state structure.
"""

import numpy as np
import logging
from typing import Dict, Any, List, Tuple, Optional
from pathlib import Path
import json
from utils.logger import get_logger, log_stage_start, log_stage_end

class NullModelError(Exception):
    """Custom exception for null model generation errors."""
    pass

def generate_linear_mixing_null(
    component_weights: np.ndarray,
    behavioral_metrics: np.ndarray,
    n_components: int,
    random_seed: int = 42
) -> np.ndarray:
    """
    Generate a null model by creating synthetic neural activity as a linear
    mixture of behavioral metrics.
    
    This implements FR-009: The null model assumes that neural activity is
    simply a linear combination of observed behaviors, with no latent
    internal state structure.
    
    Args:
        component_weights: N x T matrix of NMF component weights (N components, T timepoints)
        behavioral_metrics: M x T matrix of behavioral metrics (M behaviors, T timepoints)
        n_components: Number of components to generate in the null model
        random_seed: Random seed for reproducibility
        
    Returns:
        np.ndarray: Synthetic neural activity matrix (N x T) generated from
                   linear mixing of behavioral metrics
                   
    Raises:
        NullModelError: If input dimensions are incompatible or data is invalid
    """
    if component_weights.ndim != 2:
        raise NullModelError(f"component_weights must be 2D, got {component_weights.ndim}D")
    if behavioral_metrics.ndim != 2:
        raise NullModelError(f"behavioral_metrics must be 2D, got {behavioral_metrics.ndim}D")
    
    n_weights, t_weights = component_weights.shape
    n_behaviors, t_behaviors = behavioral_metrics.shape
    
    if t_weights != t_behaviors:
        raise NullModelError(
            f"Time dimensions must match: weights={t_weights}, behavior={t_behaviors}"
        )
    
    if n_components <= 0:
        raise NullModelError(f"n_components must be positive, got {n_components}")
    
    # Set random seed for reproducibility
    rng = np.random.default_rng(random_seed)
    
    # Generate random mixing coefficients (M behaviors -> N components)
    # Each null component is a random linear combination of behaviors
    mixing_matrix = rng.standard_normal((n_components, n_behaviors))
    
    # Generate synthetic neural activity: X_null = Mixing * Behavioral
    # Shape: (n_components, n_behaviors) @ (n_behaviors, t_weights) -> (n_components, t_weights)
    synthetic_activity = mixing_matrix @ behavioral_metrics
    
    # Add small Gaussian noise to make it more realistic (but still linear)
    noise_std = 0.01 * np.std(synthetic_activity)
    synthetic_activity += rng.normal(0, noise_std, synthetic_activity.shape)
    
    # Ensure non-negativity (neural activity is typically non-negative)
    synthetic_activity = np.maximum(synthetic_activity, 0)
    
    return synthetic_activity

def run_null_model_comparison(
    component_weights: np.ndarray,
    behavioral_metrics: np.ndarray,
    original_correlations: np.ndarray,
    n_components: int,
    output_path: Path,
    random_seed: int = 42
) -> Dict[str, Any]:
    """
    Run the null model comparison analysis.
    
    Generates the linear mixing null model and compares its correlation
    structure against the original NMF-derived correlations.
    
    Args:
        component_weights: N x T matrix of NMF component weights
        behavioral_metrics: M x T matrix of behavioral metrics
        original_correlations: N x M matrix of original Spearman correlations
                             between NMF components and behaviors
        n_components: Number of components in the NMF solution
        output_path: Path to write the comparison results JSON
        random_seed: Random seed for reproducibility
        
    Returns:
        Dict with comparison results including:
            - null_correlations: N x M matrix of null model correlations
            - correlation_difference: N x M matrix of (original - null)
            - mean_difference: Mean absolute difference across all pairs
            - max_difference: Maximum absolute difference
            - null_p_values: P-values for the difference (placeholder for T035)
            - summary: Overall assessment of whether NMF outperforms null
    """
    logger = get_logger(__name__)
    
    logger.info("Generating linear mixing null model")
    
    # Generate null model synthetic activity
    synthetic_activity = generate_linear_mixing_null(
        component_weights=component_weights,
        behavioral_metrics=behavioral_metrics,
        n_components=n_components,
        random_seed=random_seed
    )
    
    logger.info(f"Null model generated: shape {synthetic_activity.shape}")
    
    # Compute correlations for the null model
    # We need to correlate synthetic activity with behavioral metrics
    from scipy.stats import spearmanr
    
    n_components, n_timepoints = synthetic_activity.shape
    n_behaviors, _ = behavioral_metrics.shape
    
    null_correlations = np.zeros((n_components, n_behaviors))
    
    for i in range(n_components):
        for j in range(n_behaviors):
            corr, _ = spearmanr(
                synthetic_activity[i, :],
                behavioral_metrics[j, :]
            )
            null_correlations[i, j] = corr if not np.isnan(corr) else 0.0
    
    # Calculate difference
    correlation_difference = original_correlations - null_correlations
    
    # Summary statistics
    mean_abs_diff = np.mean(np.abs(correlation_difference))
    max_abs_diff = np.max(np.abs(correlation_difference))
    
    # Check if NMF correlations are significantly stronger
    # (Simple heuristic: mean absolute correlation in NMF > null)
    nmf_mean_abs_corr = np.mean(np.abs(original_correlations))
    null_mean_abs_corr = np.mean(np.abs(null_correlations))
    
    nmf_outperforms = nmf_mean_abs_corr > null_mean_abs_corr
    
    results = {
        "null_correlations": null_correlations.tolist(),
        "original_correlations": original_correlations.tolist(),
        "correlation_difference": correlation_difference.tolist(),
        "mean_absolute_difference": float(mean_abs_diff),
        "max_absolute_difference": float(max_abs_diff),
        "nmf_mean_absolute_correlation": float(nmf_mean_abs_corr),
        "null_mean_absolute_correlation": float(null_mean_abs_corr),
        "nmf_outperforms_null": nmf_outperforms,
        "n_components": n_components,
        "n_behaviors": n_behaviors,
        "random_seed": random_seed,
        "summary": (
            "NMF correlations are stronger than null model"
            if nmf_outperforms
            else "NMF correlations are not stronger than null model"
        )
    }
    
    # Write results to file
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Null model comparison results written to {output_path}")
    
    return results

def main():
    """
    Main entry point for null model generation.
    
    This script is designed to be run after NMF decomposition and
    correlation analysis. It loads the necessary inputs and generates
    the linear mixing null model for comparison.
    
    Expected inputs (from previous pipeline stages):
        - data/nmf_results/{seed}/component_weights.npy
        - data/behavioral/behavioral_metrics.npy
        - data/stats/correlation_results.json
        
    Output:
        - data/null_model/null_comparison.json
    """
    logger = get_logger(__name__)
    log_stage_start(logger, "Null Model Generation")
    
    try:
        # Load configuration
        from config import get_config_value, get_random_seed
        random_seed = get_random_seed()
        
        # Define paths
        base_path = Path("data")
        nmf_weights_path = base_path / "nmf_results" / "seed_42" / "component_weights.npy"
        behavior_path = base_path / "behavioral" / "behavioral_metrics.npy"
        corr_results_path = base_data / "stats" / "correlation_results.json"
        output_path = base_path / "null_model" / "null_comparison.json"
        
        # Check if inputs exist (for demonstration, we'll use synthetic data if not found)
        # In production, this should fail loudly if real data is missing
        if not nmf_weights_path.exists():
            logger.warning(f"NMF weights not found at {nmf_weights_path}")
            logger.info("This is expected if NMF has not been run yet.")
            raise FileNotFoundError("NMF component weights not found. Run NMF pipeline first.")
        
        if not behavior_path.exists():
            logger.warning(f"Behavioral metrics not found at {behavior_path}")
            raise FileNotFoundError("Behavioral metrics not found. Run preprocessing first.")
        
        if not corr_results_path.exists():
            logger.warning(f"Correlation results not found at {corr_results_path}")
            raise FileNotFoundError("Correlation results not found. Run stats analysis first.")
        
        # Load data
        component_weights = np.load(nmf_weights_path)
        behavioral_metrics = np.load(behavior_path)
        
        with open(corr_results_path, 'r') as f:
            corr_data = json.load(f)
        
        # Extract original correlations (assuming schema has 'correlation_matrix' key)
        if 'correlation_matrix' in corr_data:
            original_correlations = np.array(corr_data['correlation_matrix'])
        elif 'results' in corr_data and len(corr_data['results']) > 0:
            # Extract from results list if format differs
            results_list = corr_data['results']
            n_comp = len(results_list)
            n_beh = len(results_list[0]['correlations']) if results_list else 0
            original_correlations = np.zeros((n_comp, n_beh))
            for i, res in enumerate(results_list):
                for j, val in enumerate(res['correlations']):
                    original_correlations[i, j] = val
        else:
            raise NullModelError("Could not extract correlation matrix from results file")
        
        # Determine number of components
        n_components = component_weights.shape[0]
        
        # Run comparison
        results = run_null_model_comparison(
            component_weights=component_weights,
            behavioral_metrics=behavioral_metrics,
            original_correlations=original_correlations,
            n_components=n_components,
            output_path=output_path,
            random_seed=random_seed
        )
        
        log_stage_end(logger, "Null Model Generation", success=True)
        return results
        
    except FileNotFoundError as e:
        logger.error(f"Input data missing: {e}")
        log_stage_end(logger, "Null Model Generation", success=False)
        raise
    except Exception as e:
        logger.error(f"Error during null model generation: {e}")
        log_stage_end(logger, "Null Model Generation", success=False)
        raise NullModelError(f"Null model generation failed: {e}")

if __name__ == "__main__":
    main()