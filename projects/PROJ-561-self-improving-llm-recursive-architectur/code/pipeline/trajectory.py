"""
Pipeline module for trajectory analysis and capacity normalization.

Implements capacity normalization analysis to determine if performance 
improvements correlate with parameter count or topology changes.
"""
import json
import os
from typing import Dict, Any, List, Optional
import numpy as np
from scipy import stats
from results.trajectory_schema import read_trajectory, write_trajectory, get_latest_entry
import logging

logger = logging.getLogger(__name__)

def analyze_capacity_normalization(trajectory_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze if performance improvements correlate with parameter count or topology.
    
    This function implements the "Capacity Normalization" analysis required by 
    Plan Step 4.3. It examines the relationship between model capacity (parameter 
    count) and performance metrics to determine if improvements are due to 
    increased capacity or architectural efficiency.
    
    Args:
        trajectory_data: The full trajectory data including cycle metrics.
    
    Returns:
        A dictionary containing:
        - correlation_coefficient: Pearson correlation between params and performance
        - p_value: Statistical significance of the correlation
        - normalization_factor: Average performance per million parameters
        - analysis_summary: Text summary of findings
        - cycle_data: List of (params, performance) tuples for plotting
    """
    cycles = trajectory_data.get('cycles', [])
    if not cycles:
        return {
            'error': 'No cycles found in trajectory data',
            'correlation_coefficient': None,
            'p_value': None,
            'normalization_factor': None,
            'analysis_summary': 'No data to analyze'
        }
    
    # Extract parameter counts and performance metrics
    param_counts = []
    performance_scores = []
    cycle_info = []
    
    for cycle in cycles:
        # Get parameter count
        param_count = cycle.get('parameter_count', cycle.get('params', 0))
        if param_count is None or param_count == 0:
            continue
        
        # Get performance score (weighted average of benchmarks)
        # Use GSM8K as primary metric for consistency
        gsm8k_score = cycle.get('gsm8k_accuracy', 0)
        arc_score = cycle.get('arc_challenge_accuracy', 0)
        boolq_score = cycle.get('boolq_ece', 0)
        
        # Use weighted average with GSM8K as primary (weight 0.5)
        performance = 0.5 * gsm8k_score + 0.25 * arc_score + 0.25 * (1 - boolq_score)
        
        param_counts.append(param_count)
        performance_scores.append(performance)
        cycle_info.append({
            'cycle': cycle.get('cycle_number', 0),
            'params': param_count,
            'performance': performance,
            'gsm8k': gsm8k_score,
            'arc': arc_score,
            'boolq': boolq_score
        })
    
    if len(param_counts) < 2:
        return {
            'error': 'Insufficient data points for correlation analysis',
            'correlation_coefficient': None,
            'p_value': None,
            'normalization_factor': None,
            'analysis_summary': 'Need at least 2 cycles for correlation analysis',
            'cycle_data': cycle_info
        }
    
    # Convert to numpy arrays
    params_arr = np.array(param_counts)
    perf_arr = np.array(performance_scores)
    
    # Calculate Pearson correlation
    correlation, p_value = stats.pearsonr(params_arr, perf_arr)
    
    # Calculate normalization factor (performance per million parameters)
    params_millions = params_arr / 1e6
    normalization_factor = np.mean(perf_arr / params_millions)
    
    # Determine if improvements are capacity-driven or efficiency-driven
    if correlation > 0.5:
        trend = "Capacity-driven: Performance improves with parameter count"
    elif correlation < -0.5:
        trend = "Efficiency-driven: Performance improves with fewer parameters"
    else:
        trend = "Mixed: No strong correlation between capacity and performance"
    
    # Statistical significance check
    if p_value < 0.05:
        significance = "Statistically significant (p < 0.05)"
    else:
        significance = "Not statistically significant (p >= 0.05)"
    
    analysis_summary = (
        f"Capacity Normalization Analysis: {trend}. {significance}. "
        f"Correlation coefficient: {correlation:.4f} (p={p_value:.4f}). "
        f"Average performance per million parameters: {normalization_factor:.6f}. "
        f"Based on {len(cycle_info)} cycles."
    )
    
    return {
        'correlation_coefficient': float(correlation),
        'p_value': float(p_value),
        'normalization_factor': float(normalization_factor),
        'analysis_summary': analysis_summary,
        'cycle_data': cycle_info,
        'trend': trend,
        'significance': significance,
        'num_cycles': len(cycle_info)
    }

def update_trajectory_with_capacity_analysis(trajectory_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Update the trajectory file with capacity normalization analysis.
    
    Args:
        trajectory_path: Path to trajectory.json. If None, uses default path from config.
    
    Returns:
        The updated trajectory data including the analysis results.
    """
    # Read trajectory data
    trajectory_data = read_trajectory(trajectory_path)
    
    if not trajectory_data:
        logger.warning("Could not read trajectory data. Creating new structure.")
        trajectory_data = {
            'metadata': {
                'created_at': str(np.datetime64('now')),
                'version': '1.0'
            },
            'cycles': [],
            'capacity_normalization_analysis': None
        }
    
    # Perform analysis
    analysis_results = analyze_capacity_normalization(trajectory_data)
    
    # Update trajectory data with analysis
    trajectory_data['capacity_normalization_analysis'] = analysis_results
    
    # Write back to file
    write_trajectory(trajectory_data, trajectory_path)
    
    logger.info(f"Capacity normalization analysis complete: {analysis_results['analysis_summary']}")
    
    return trajectory_data

def main():
    """Main entry point for capacity normalization analysis."""
    import sys
    from config import get_trajectory_path
    
    trajectory_path = get_trajectory_path()
    
    if not os.path.exists(trajectory_path):
        print(f"Error: Trajectory file not found at {trajectory_path}")
        print("Please ensure at least one cycle has been completed (T050).")
        sys.exit(1)
    
    try:
        result = update_trajectory_with_capacity_analysis(trajectory_path)
        
        if result.get('capacity_normalization_analysis', {}).get('error'):
            print(f"Analysis error: {result['capacity_normalization_analysis']['error']}")
            sys.exit(1)
        
        print("Capacity Normalization Analysis Results:")
        print("-" * 50)
        print(result['capacity_normalization_analysis']['analysis_summary'])
        print("-" * 50)
        
        # Print detailed metrics
        analysis = result['capacity_normalization_analysis']
        print(f"\nCorrelation Coefficient: {analysis['correlation_coefficient']:.4f}")
        print(f"P-value: {analysis['p_value']:.4f}")
        print(f"Normalization Factor: {analysis['normalization_factor']:.6f}")
        print(f"Trend: {analysis['trend']}")
        print(f"Significance: {analysis['significance']}")
        print(f"Cycles Analyzed: {analysis['num_cycles']}")
        
        if analysis['cycle_data']:
            print("\nPer-Cycle Data:")
            for item in analysis['cycle_data']:
                print(f"  Cycle {item['cycle']}: Params={item['params']:,}, "
                      f"Performance={item['performance']:.4f}, "
                      f"GSM8K={item['gsm8k']:.4f}")
        
    except Exception as e:
        logger.error(f"Failed to run capacity normalization analysis: {e}")
        raise

if __name__ == "__main__":
    main()
