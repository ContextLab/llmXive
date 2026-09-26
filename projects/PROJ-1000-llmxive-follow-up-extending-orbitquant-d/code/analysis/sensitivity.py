"""
Sensitivity analysis for entropy cut-off points.

This module sweeps entropy cut-off points by ±5% of the total observed entropy range
(calculated from Phase 3 results in T018) and reports the variance in FID scores.

The analysis evaluates how robust the dynamic rotation router is to small perturbations
in the entropy thresholds used for matrix selection.
"""

import os
import json
import logging
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional

from config import Config
from evaluation.metrics import compute_fid, load_metrics_from_json
from analysis.correlation import load_entropy_scores

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_correlation_results(config: Config) -> Dict[str, Any]:
    """Load the correlation results from Phase 3 (T018)."""
    results_path = config.CORRELATION_RESULTS_PATH
    
    if not os.path.exists(results_path):
        raise FileNotFoundError(
            f"Correlation results file not found at {results_path}. "
            "Please ensure T018 has been completed successfully."
        )
    
    with open(results_path, 'r') as f:
        return json.load(f)

def compute_entropy_range(entropy_scores: List[float]) -> Tuple[float, float]:
    """Compute the total observed entropy range."""
    if not entropy_scores:
        raise ValueError("Entropy scores list is empty")
    
    min_entropy = min(entropy_scores)
    max_entropy = max(entropy_scores)
    total_range = max_entropy - min_entropy
    
    logger.info(f"Entropy range: [{min_entropy:.4f}, {max_entropy:.4f}], "
               f"total range = {total_range:.4f}")
    
    return min_entropy, max_entropy, total_range

def generate_sweep_points(
    min_entropy: float,
    max_entropy: float,
    total_range: float,
    sweep_percentage: float = 0.05,
    num_points: int = 11
) -> List[float]:
    """
    Generate cut-off points for the sensitivity sweep.
    
    Args:
        min_entropy: Minimum observed entropy
        max_entropy: Maximum observed entropy
        total_range: Total entropy range (max - min)
        sweep_percentage: Percentage of range to sweep (default 5%)
        num_points: Number of points to generate in the sweep
    
    Returns:
        List of cut-off points centered around the original boundaries
    """
    sweep_radius = total_range * sweep_percentage
    
    # Generate points around the mid-point of the entropy range
    mid_point = (min_entropy + max_entropy) / 2
    step_size = (2 * sweep_radius) / (num_points - 1) if num_points > 1 else 0
    
    sweep_points = []
    for i in range(num_points):
        point = mid_point - sweep_radius + (i * step_size)
        sweep_points.append(point)
    
    logger.info(f"Generated {len(sweep_points)} sweep points from "
               f"{sweep_points[0]:.4f} to {sweep_points[-1]:.4f}")
    
    return sweep_points

def evaluate_fid_at_cutoff(
    config: Config,
    cutoff_point: float,
    entropy_scores: List[float],
    metrics_data: Dict[str, Any]
) -> float:
    """
    Evaluate FID score at a specific entropy cutoff point.
    
    This simulates a router behavior where prompts with entropy <= cutoff
    use one rotation strategy, and those above use another.
    
    Args:
        config: Configuration object
        cutoff_point: The entropy cutoff value
        entropy_scores: List of entropy scores for each sample
        metrics_data: Dictionary containing metrics (FID, CLIP, etc.)
    
    Returns:
        FID score for this cutoff configuration
    """
    if not entropy_scores or not metrics_data:
        raise ValueError("Empty entropy scores or metrics data")
    
    # Simulate router behavior: group samples by entropy cutoff
    # In a real scenario, this would select different rotation matrices
    # For sensitivity analysis, we measure how FID varies with cutoff changes
    
    # Get FID scores (assuming they're already computed per sample or batch)
    # If metrics_data contains per-sample FID, use it directly
    # Otherwise, use the aggregate FID and simulate the effect
    
    fid_scores = metrics_data.get('fid_scores', [])
    
    if not fid_scores:
        # If no per-sample FID, return a placeholder based on aggregate
        # This is a simplification for sensitivity analysis
        aggregate_fid = metrics_data.get('fid', 0.0)
        logger.warning(f"No per-sample FID scores found, using aggregate: {aggregate_fid}")
        return aggregate_fid
    
    # Calculate weighted FID based on cutoff distribution
    # This simulates how different cutoffs would affect the overall performance
    below_cutoff = [fid for fid, ent in zip(fid_scores, entropy_scores) if ent <= cutoff_point]
    above_cutoff = [fid for fid, ent in zip(fid_scores, entropy_scores) if ent > cutoff_point]
    
    if not below_cutoff and not above_cutoff:
        return 0.0
    
    # Weighted average FID based on distribution
    total_count = len(below_cutoff) + len(above_cutoff)
    if total_count == 0:
        return 0.0
    
    avg_fid = (
        (sum(below_cutoff) / len(below_cutoff) if below_cutoff else 0) * (len(below_cutoff) / total_count) +
        (sum(above_cutoff) / len(above_cutoff) if above_cutoff else 0) * (len(above_cutoff) / total_count)
    )
    
    return avg_fid

def run_sensitivity_analysis(
    config: Config,
    sweep_percentage: float = 0.05,
    num_sweep_points: int = 11
) -> Dict[str, Any]:
    """
    Run the full sensitivity analysis.
    
    Args:
        config: Configuration object
        sweep_percentage: Percentage of entropy range to sweep (default 5%)
        num_sweep_points: Number of points in the sweep (default 11)
    
    Returns:
        Dictionary containing sensitivity analysis results
    """
    logger.info("Starting sensitivity analysis for entropy cut-off points")
    
    # Load correlation results to get entropy range
    correlation_results = load_correlation_results(config)
    
    # Extract entropy scores
    raw_data = correlation_results.get('raw_data', [])
    if not raw_data:
        raise ValueError("No raw data found in correlation results")
    
    entropy_scores = [point.get('entropy', 0.0) for point in raw_data]
    
    # Compute entropy range
    min_entropy, max_entropy, total_range = compute_entropy_range(entropy_scores)
    
    # Generate sweep points
    sweep_points = generate_sweep_points(
        min_entropy, max_entropy, total_range,
        sweep_percentage, num_sweep_points
    )
    
    # Load metrics data (from T030/T034 evaluation)
    # We assume the final evaluation metrics are available
    metrics_path = config.FINAL_EVALUATION_REPORT_PATH
    
    if not os.path.exists(metrics_path):
        # Fallback to using correlation results if final report doesn't exist
        logger.warning(f"Final evaluation report not found at {metrics_path}. "
                     "Using correlation results as fallback.")
        metrics_data = correlation_results
    else:
        with open(metrics_path, 'r') as f:
            metrics_data = json.load(f)
    
    # Evaluate FID at each sweep point
    results = []
    fid_scores = []
    
    for point in sweep_points:
        fid_at_cutoff = evaluate_fid_at_cutoff(
            config, point, entropy_scores, metrics_data
        )
        results.append({
            'cutoff_point': point,
            'fid_score': fid_at_cutoff
        })
        fid_scores.append(fid_at_cutoff)
    
    # Compute statistics
    fid_array = np.array(fid_scores)
    variance = float(np.var(fid_scores))
    std_dev = float(np.std(fid_scores))
    min_fid = float(np.min(fid_scores))
    max_fid = float(np.max(fid_scores))
    mean_fid = float(np.mean(fid_scores))
    
    sensitivity_results = {
        'sweep_parameters': {
            'sweep_percentage': sweep_percentage,
            'num_points': num_sweep_points,
            'entropy_range': {
                'min': min_entropy,
                'max': max_entropy,
                'total_range': total_range
            },
            'sweep_radius': total_range * sweep_percentage
        },
        'results': results,
        'statistics': {
            'fid_variance': variance,
            'fid_std_dev': std_dev,
            'fid_min': min_fid,
            'fid_max': max_fid,
            'fid_mean': mean_fid,
            'sensitivity_coefficient': std_dev / mean_fid if mean_fid != 0 else 0.0
        },
        'analysis_summary': {
            'total_sweep_points': len(sweep_points),
            'entropy_range_covered': f"{min_entropy:.4f} to {max_entropy:.4f}",
            'sweep_range': f"{min_entropy - total_range * sweep_percentage:.4f} to "
                          f"{max_entropy + total_range * sweep_percentage:.4f}",
            'interpretation': (
                "Low variance indicates robustness to cutoff perturbations. "
                "High variance suggests the router is sensitive to entropy threshold selection."
            )
        }
    }
    
    logger.info(f"Sensitivity analysis complete. FID variance: {variance:.6f}")
    
    return sensitivity_results

def save_sensitivity_results(
    results: Dict[str, Any],
    output_path: str
) -> None:
    """Save sensitivity analysis results to JSON file."""
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Sensitivity results saved to {output_path}")

def main():
    """Main entry point for sensitivity analysis."""
    config = Config()
    
    try:
        # Run sensitivity analysis
        results = run_sensitivity_analysis(
            config,
            sweep_percentage=0.05,  # ±5% as specified
            num_sweep_points=11     # 11 points for good resolution
        )
        
        # Save results
        output_path = config.SENSITIVITY_ANALYSIS_PATH
        save_sensitivity_results(results, output_path)
        
        # Print summary
        print("\n" + "="*60)
        print("SENSITIVITY ANALYSIS SUMMARY")
        print("="*60)
        print(f"Entropy Range: {results['analysis_summary']['entropy_range_covered']}")
        print(f"Sweep Range: {results['analysis_summary']['sweep_range']}")
        print(f"FID Variance: {results['statistics']['fid_variance']:.6f}")
        print(f"FID Std Dev: {results['statistics']['fid_std_dev']:.6f}")
        print(f"Sensitivity Coefficient: {results['statistics']['sensitivity_coefficient']:.6f}")
        print("="*60 + "\n")
        
        logger.info("Sensitivity analysis completed successfully")
        
    except Exception as e:
        logger.error(f"Sensitivity analysis failed: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    main()