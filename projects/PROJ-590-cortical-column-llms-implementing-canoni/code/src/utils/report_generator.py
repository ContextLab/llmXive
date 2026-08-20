"""
Report generation utilities for cost curve analysis and ablation summaries.
"""
import json
import os
import logging
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
import pandas as pd
from pathlib import Path

from src.experiments.ablation import load_ablation_configs
from src.utils.statistics import calculate_scaling_exponent

logger = logging.getLogger(__name__)

def load_ablation_results(results_dir: str) -> List[Dict[str, Any]]:
    """
    Load all ablation result JSON files from a directory.
    
    Args:
        results_dir: Path to directory containing result JSON files.
        
    Returns:
        List of dictionaries containing ablation results.
    """
    results = []
    results_path = Path(results_dir)
    
    if not results_path.exists():
        logger.warning(f"Results directory does not exist: {results_dir}")
        return results
        
    for json_file in results_path.glob("*.json"):
        try:
            with open(json_file, 'r') as f:
                result = json.load(f)
                result['_source_file'] = json_file.name
                results.append(result)
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Failed to load {json_file}: {e}")
            
    return results

def load_ablation_stats(results_dir: str) -> Dict[str, Any]:
    """
    Aggregate statistics from ablation results.
    
    Args:
        results_dir: Path to directory containing result JSON files.
        
    Returns:
        Dictionary with aggregated statistics.
    """
    results = load_ablation_results(results_dir)
    
    if not results:
        return {}
        
    stats = {
        'count': len(results),
        'configs': [],
        'metrics': {},
        'parameter_counts': [],
        'training_times': [],
        'mae_scores': []
    }
    
    for r in results:
        if 'config' in r:
            stats['configs'].append(r['config'])
        if 'metrics' in r:
            stats['metrics'].update(r['metrics'])
        if 'parameter_count' in r:
            stats['parameter_counts'].append(r['parameter_count'])
        if 'training_time' in r:
            stats['training_times'].append(r['training_time'])
        if 'mae' in r:
            stats['mae_scores'].append(r['mae'])
            
    return stats

def count_active_constraints(config: Dict[str, Any]) -> int:
    """
    Count the number of active constraints in an ablation configuration.
    
    Args:
        config: Ablation configuration dictionary.
        
    Returns:
        Number of active constraints.
    """
    active_count = 0
    
    # Check common constraint fields
    constraint_fields = [
        'ei_balance_enabled',
        'homeostatic_scaling',
        'laminar_connectivity',
        'local_inhibition',
        'synaptic_scaling',
        'gradient_clipping',
        'activity_regulation'
    ]
    
    for field in constraint_fields:
        if config.get(field, False):
            active_count += 1
            
    # Also check for explicit constraints list
    if 'constraints' in config and isinstance(config['constraints'], list):
        active_count += len([c for c in config['constraints'] if c.get('enabled', False)])
        
    return active_count

def generate_cost_curve_data(
    ablation_results_dir: str,
    scaling_results_dir: str,
    output_path: str
) -> str:
    """
    Generate cost curve data combining ablation and scaling study results.
    
    This function creates a CSV file containing:
    - Model size (parameter count)
    - Training cost (time)
    - Performance (MAE)
    - Number of active biological constraints
    - Scaling exponent estimates
    
    Args:
        ablation_results_dir: Directory containing ablation study results.
        scaling_results_dir: Directory containing scaling study results.
        output_path: Path for the output CSV file.
        
    Returns:
        Path to the generated CSV file.
    """
    # Load ablation results
    ablation_stats = load_ablation_stats(ablation_results_dir)
    ablation_results = load_ablation_results(ablation_results_dir)
    
    # Load scaling results
    scaling_results = []
    scaling_path = Path(scaling_results_dir)
    if scaling_path.exists():
        for json_file in scaling_path.glob("*.json"):
            try:
                with open(json_file, 'r') as f:
                    result = json.load(f)
                    scaling_results.append(result)
            except (json.JSONDecodeError, IOError) as e:
                logger.error(f"Failed to load scaling result {json_file}: {e}")
    
    # Build cost curve data
    cost_curve_data = []
    
    # Process ablation results
    for result in ablation_results:
        config = result.get('config', {})
        constraints_count = count_active_constraints(config)
        
        row = {
            'experiment_type': 'ablation',
            'parameter_count': result.get('parameter_count', 0),
            'training_time': result.get('training_time', 0),
            'mae': result.get('mae', float('inf')),
            'active_constraints': constraints_count,
            'config_name': config.get('name', 'unknown'),
            'scaling_exponent': None
        }
        
        # Try to calculate scaling exponent if we have multiple results
        if len(ablation_results) > 1:
            try:
                params = [r.get('parameter_count', 0) for r in ablation_results]
                maes = [r.get('mae', 0) for r in ablation_results]
                if all(p > 0 for p in params) and all(m < float('inf') for m in maes):
                    exp = calculate_scaling_exponent(params, maes)
                    row['scaling_exponent'] = exp
            except Exception as e:
                logger.warning(f"Could not calculate scaling exponent: {e}")
                
        cost_curve_data.append(row)
    
    # Process scaling results
    for result in scaling_results:
        config = result.get('config', {})
        constraints_count = count_active_constraints(config)
        
        row = {
            'experiment_type': 'scaling',
            'parameter_count': result.get('parameter_count', 0),
            'training_time': result.get('training_time', 0),
            'mae': result.get('mae', float('inf')),
            'active_constraints': constraints_count,
            'config_name': config.get('name', 'unknown'),
            'scaling_exponent': result.get('scaling_exponent', None)
        }
        
        cost_curve_data.append(row)
    
    # Convert to DataFrame and save
    if cost_curve_data:
        df = pd.DataFrame(cost_curve_data)
        
        # Sort by parameter count
        df = df.sort_values('parameter_count')
        
        # Ensure output directory exists
        output_path_obj = Path(output_path)
        output_path_obj.parent.mkdir(parents=True, exist_ok=True)
        
        # Save to CSV
        df.to_csv(output_path, index=False)
        logger.info(f"Cost curve data saved to {output_path}")
        
        # Log summary statistics
        logger.info(f"Generated {len(df)} cost curve entries")
        logger.info(f"Parameter range: {df['parameter_count'].min()} - {df['parameter_count'].max()}")
        logger.info(f"MAE range: {df['mae'].min():.4f} - {df['mae'].max():.4f}")
        
        return output_path
    else:
        logger.warning("No cost curve data generated - no results found")
        # Create empty file with headers
        output_path_obj = Path(output_path)
        output_path_obj.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            f.write("experiment_type,parameter_count,training_time,mae,active_constraints,config_name,scaling_exponent\n")
        return output_path

def main():
    """Main entry point for cost curve generation."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate cost curve data from ablation and scaling studies')
    parser.add_argument('--ablation-dir', type=str, default='data/results/ablation',
                      help='Directory containing ablation results')
    parser.add_argument('--scaling-dir', type=str, default='data/results/scaling',
                      help='Directory containing scaling results')
    parser.add_argument('--output', type=str, default='data/results/cost_curve.csv',
                      help='Output CSV file path')
    
    args = parser.parse_args()
    
    logging.basicConfig(level=logging.INFO)
    
    output_path = generate_cost_curve_data(
        args.ablation_dir,
        args.scaling_dir,
        args.output
    )
    
    print(f"Cost curve data generated at: {output_path}")

if __name__ == '__main__':
    main()