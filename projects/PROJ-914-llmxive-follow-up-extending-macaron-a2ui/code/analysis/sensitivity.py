"""
Sensitivity analysis for router confidence cutoffs.

This module implements FR-007 and SC-005 by sweeping router confidence
thresholds and reporting inconsistency rates in routing decisions.
"""
import os
import sys
import json
import argparse
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple, Any

# Local imports
from config import get_processed_data_path, ensure_dirs
from utils.logging import get_experiment_logger
from simulation.metrics import load_simulation_results

logger = get_experiment_logger(__name__)


def load_simulation_data() -> pd.DataFrame:
    """
    Load simulation results from the standard output location.
    
    Returns:
        DataFrame with routing decisions and confidence scores.
        
    Raises:
        FileNotFoundError: If simulation results are not found.
        ValueError: If required columns are missing.
    """
    sim_data_path = get_processed_data_path() / "simulation_results.json"
    
    if not sim_data_path.exists():
        raise FileNotFoundError(
            f"Simulation results not found at {sim_data_path}. "
            "Please run the simulation pipeline first (T024-T028)."
        )
    
    logger.info(f"Loading simulation data from {sim_data_path}")
    results = load_simulation_results()
    
    if not results:
        raise ValueError("Simulation results are empty.")
    
    df = pd.DataFrame(results)
    
    required_cols = ['confidence', 'intent', 'ground_truth_intent']
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
        
    return df


def calculate_inconsistency_rate(
    df: pd.DataFrame, 
    threshold: float
) -> Tuple[float, int, int]:
    """
    Calculate the inconsistency rate for a given confidence threshold.
    
    A query is considered "routed to LLM" if confidence >= threshold.
    Inconsistency occurs when:
    - High-Confidence queries are routed to fallback (false negative)
    - Ambiguous queries are routed to LLM (false positive)
    
    Args:
        df: DataFrame with confidence scores and ground truth.
        threshold: Confidence cutoff for routing to LLM.
        
    Returns:
        Tuple of (inconsistency_rate, count_inconsistent, count_total)
    """
    if df.empty:
        return 0.0, 0, 0
        
    # Define routing decisions based on threshold
    df['routed_to_llm'] = df['confidence'] >= threshold
    
    # Define correct routing logic:
    # - High-Confidence queries should be routed to LLM (routed_to_llm=True)
    # - Ambiguous queries should be routed to fallback (routed_to_llm=False)
    # Inconsistency = when routing decision doesn't match ground truth intent
    
    # Create expected routing based on ground truth
    # Assuming ground_truth_intent is either 'high_confidence' or 'ambiguous'
    df['expected_llm'] = df['ground_truth_intent'] == 'high_confidence'
    
    # Inconsistency: routing decision != expected routing
    df['inconsistent'] = df['routed_to_llm'] != df['expected_llm']
    
    count_inconsistent = df['inconsistent'].sum()
    count_total = len(df)
    inconsistency_rate = count_inconsistent / count_total if count_total > 0 else 0.0
    
    return inconsistency_rate, int(count_inconsistent), count_total


def run_sensitivity_analysis(
    df: pd.DataFrame,
    thresholds: List[float] = None
) -> Dict[str, Any]:
    """
    Run sensitivity analysis across a range of confidence thresholds.
    
    Args:
        df: DataFrame with simulation results.
        thresholds: List of confidence thresholds to evaluate. 
                   Defaults to [0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9].
                   
    Returns:
        Dictionary containing analysis results.
    """
    if thresholds is None:
        thresholds = [0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
        
    results = []
    
    for threshold in sorted(thresholds):
        rate, inconsistent, total = calculate_inconsistency_rate(df, threshold)
        results.append({
            'threshold': threshold,
            'inconsistency_rate': rate,
            'count_inconsistent': inconsistent,
            'count_total': total,
            'count_routed_to_llm': int((df['confidence'] >= threshold).sum()),
            'count_routed_to_fallback': int((df['confidence'] < threshold).sum())
        })
        
    analysis_df = pd.DataFrame(results)
    
    # Calculate additional metrics
    analysis_df['optimal'] = analysis_df['inconsistency_rate'] == analysis_df['inconsistency_rate'].min()
    
    return {
        'thresholds_tested': thresholds,
        'results': analysis_df.to_dict(orient='records'),
        'summary': {
            'total_samples': len(df),
            'min_inconsistency_rate': float(analysis_df['inconsistency_rate'].min()),
            'optimal_threshold': float(analysis_df.loc[analysis_df['optimal'], 'threshold'].iloc[0]) if analysis_df['optimal'].any() else None,
            'threshold_range': [min(thresholds), max(thresholds)]
        }
    }


def save_sensitivity_report(
    analysis_results: Dict[str, Any],
    output_path: Path
) -> None:
    """
    Save the sensitivity analysis report to a JSON file.
    
    Args:
        analysis_results: Dictionary containing analysis results.
        output_path: Path to save the report.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(analysis_results, f, indent=2)
        
    logger.info(f"Sensitivity analysis report saved to {output_path}")


def print_sensitivity_summary(analysis_results: Dict[str, Any]) -> None:
    """
    Print a human-readable summary of the sensitivity analysis.
    
    Args:
        analysis_results: Dictionary containing analysis results.
    """
    summary = analysis_results['summary']
    results_df = pd.DataFrame(analysis_results['results'])
    
    print("\n" + "="*60)
    print("SENSITIVITY ANALYSIS: ROUTER CONFIDENCE THRESHOLDS")
    print("="*60)
    print(f"Total samples analyzed: {summary['total_samples']}")
    print(f"Threshold range tested: {summary['threshold_range'][0]:.2f} - {summary['threshold_range'][1]:.2f}")
    print(f"Minimum inconsistency rate: {summary['min_inconsistency_rate']:.4f}")
    if summary['optimal_threshold'] is not None:
        print(f"Optimal threshold: {summary['optimal_threshold']:.2f}")
    
    print("\nDetailed Results:")
    print("-"*60)
    print(f"{'Threshold':>10} {'Inconsistency':>12} {'Inconsistent':>12} {'Routed LLM':>12} {'Routed Fallback':>14}")
    print("-"*60)
    
    for _, row in results_df.iterrows():
        marker = " <-- OPTIMAL" if row['optimal'] else ""
        print(f"{row['threshold']:>10.2f} {row['inconsistency_rate']:>12.4f} {row['count_inconsistent']:>12} "
              f"{row['count_routed_to_llm']:>12} {row['count_routed_to_fallback']:>14}{marker}")
              
    print("="*60 + "\n")


def main() -> int:
    """
    Main entry point for sensitivity analysis.
    
    Returns:
        Exit code (0 for success, 1 for failure).
    """
    parser = argparse.ArgumentParser(
        description='Run sensitivity analysis on router confidence cutoffs.'
    )
    parser.add_argument(
        '--thresholds',
        type=str,
        default='0.3,0.4,0.5,0.6,0.7,0.8,0.9',
        help='Comma-separated list of confidence thresholds to test.'
    )
    parser.add_argument(
        '--output',
        type=str,
        default=None,
        help='Output path for the report (default: data/analysis/sensitivity_report.json)'
    )
    
    args = parser.parse_args()
    
    try:
        # Parse thresholds
        thresholds = [float(t.strip()) for t in args.thresholds.split(',')]
        
        # Load simulation data
        logger.info("Loading simulation data...")
        df = load_simulation_data()
        logger.info(f"Loaded {len(df)} samples for analysis.")
        
        # Run sensitivity analysis
        logger.info("Running sensitivity analysis...")
        analysis_results = run_sensitivity_analysis(df, thresholds)
        
        # Determine output path
        output_dir = get_processed_data_path() / "analysis"
        ensure_dirs([output_dir])
        output_path = args.output if args.output else str(output_dir / "sensitivity_report.json")
        
        # Save report
        save_sensitivity_report(analysis_results, Path(output_path))
        
        # Print summary
        print_sensitivity_summary(analysis_results)
        
        logger.info("Sensitivity analysis completed successfully.")
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"Data file not found: {e}")
        print(f"ERROR: {e}")
        return 1
    except ValueError as e:
        logger.error(f"Invalid data: {e}")
        print(f"ERROR: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error during sensitivity analysis: {e}", exc_info=True)
        print(f"ERROR: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
