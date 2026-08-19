"""
Rubric Validation Module (T037)

Validates the rubric correlation (r >= 0.7) against the N=50 human-annotated hold-out set.
Consumes rubric logic from simulation.rubric and metrics from simulation.metrics.
Explicitly calculates the Pearson correlation coefficient between rubric scores and human scores.
"""
import os
import sys
import json
import argparse
import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional

import pandas as pd
import numpy as np
from scipy import stats

# Project imports matching API surface
from config import get_holdout_data_path, get_processed_data_path, ensure_dirs
from simulation.rubric import calculate_alignment_score, calculate_latency_penalty
from simulation.metrics import calculate_ui_completeness
from utils.logging import get_experiment_logger, log_metric, log_error

logger = get_experiment_logger(__name__)

# Constants
CORRELATION_THRESHOLD: float = 0.7
HOLDOUT_SIZE: int = 50

def load_holdout_set() -> pd.DataFrame:
    """
    Load the N=50 human-annotated hold-out set created in T015.
    Expected columns: query, ground_truth_intent, complexity_score, human_score
    """
    holdout_path = get_holdout_data_path()
    
    if not holdout_path.exists():
        raise FileNotFoundError(
            f"Hold-out set not found at {holdout_path}. "
            "Please ensure T015 (create_holdout_set) has been completed first."
        )
    
    df = pd.read_csv(holdout_path)
    
    if len(df) != HOLDOUT_SIZE:
        logger.warning(
            f"Expected {HOLDOUT_SIZE} rows in hold-out set, found {len(df)}. "
            "Proceeding with available data."
        )
    
    required_cols = ['query', 'ground_truth_intent', 'human_score']
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        raise ValueError(
            f"Hold-out set missing required columns: {missing_cols}. "
            f"Expected columns: {required_cols}"
        )
    
    return df

def simulate_rubric_scoring(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply the rubric scoring logic (from T023) to the hold-out set.
    
    For each interaction in the hold-out set:
    1. Determine latency (simulated based on complexity or fixed for validation)
    2. Calculate latency penalty
    3. Calculate UI completeness (based on intent match)
    4. Calculate final alignment score using the rubric formula:
       score = 0.4 * intent_match + 0.3 * (1 - latency_penalty) + 0.3 * ui_completeness
    
    Returns DataFrame with added 'rubric_score' column.
    """
    results = []
    
    for idx, row in df.iterrows():
        # Simulate intent match (1.0 if ground truth matches expected, else 0.0)
        # For validation, we assume the "ground_truth_intent" is the target
        # and we simulate a perfect router for the rubric calculation to isolate
        # the rubric's behavior against human judgment.
        intent_match = 1.0 
        
        # Simulate latency penalty based on complexity_score
        # Assuming complexity_score is normalized 0-1, we map it to latency penalty
        # Higher complexity -> higher latency -> higher penalty
        complexity = float(row.get('complexity_score', 0.5))
        latency_penalty = calculate_latency_penalty(
            gen_time=complexity * 2.0, # Simulate generation time proportional to complexity
            target_latency=1.0
        )
        
        # UI completeness: 1.0 if intent is high confidence, 0.5 if ambiguous
        # For this validation, we map intent to a completeness score
        # In a real scenario, this would come from the UI generation step
        ui_completeness = calculate_ui_completeness(
            intent=row['ground_truth_intent'],
            ui_elements=5 # Default number of elements for calculation
        )
        
        # Calculate final alignment score using the rubric from T023
        rubric_score = calculate_alignment_score(
            intent_match=intent_match,
            latency_penalty=latency_penalty,
            ui_completeness=ui_completeness
        )
        
        results.append({
            'query': row['query'],
            'ground_truth_intent': row['ground_truth_intent'],
            'human_score': float(row['human_score']),
            'rubric_score': rubric_score,
            'latency_penalty': latency_penalty,
            'ui_completeness': ui_completeness
        })
    
    return pd.DataFrame(results)

def calculate_correlation(df: pd.DataFrame) -> Tuple[float, float]:
    """
    Calculate Pearson correlation coefficient between rubric scores and human scores.
    
    Returns:
        Tuple of (correlation_coefficient, p_value)
    """
    if len(df) < 2:
        raise ValueError("Need at least 2 data points to calculate correlation.")
    
    # Ensure no NaN values
    clean_df = df.dropna(subset=['human_score', 'rubric_score'])
    
    if len(clean_df) < 2:
        raise ValueError("Insufficient valid data points after cleaning.")
    
    r, p_value = stats.pearsonr(
        clean_df['rubric_score'],
        clean_df['human_score']
    )
    
    return float(r), float(p_value)

def validate_correlation(r: float, p_value: float) -> Dict[str, Any]:
    """
    Validate if the correlation meets the threshold (r >= 0.7).
    
    Returns validation result dictionary.
    """
    is_valid = r >= CORRELATION_THRESHOLD
    
    return {
        'correlation_coefficient': r,
        'p_value': p_value,
        'threshold': CORRELATION_THRESHOLD,
        'is_valid': is_valid,
        'message': (
            f"Correlation r={r:.4f} {'meets' if is_valid else 'does NOT meet'} "
            f"threshold of {CORRELATION_THRESHOLD}."
        )
    }

def save_validation_report(report: Dict[str, Any], output_path: Optional[Path] = None) -> Path:
    """
    Save the validation report to a JSON file.
    """
    if output_path is None:
        output_path = get_processed_data_path() / "rubric_validation_report.json"
    
    ensure_dirs()
    
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Validation report saved to {output_path}")
    return output_path

def print_validation_summary(report: Dict[str, Any]) -> None:
    """
    Print a human-readable summary of the validation results.
    """
    print("\n" + "="*60)
    print("RUBRIC VALIDATION RESULTS")
    print("="*60)
    print(f"Correlation Coefficient (r): {report['correlation_coefficient']:.4f}")
    print(f"P-value: {report['p_value']:.4f}")
    print(f"Threshold: {report['threshold']}")
    print(f"Status: {'PASS' if report['is_valid'] else 'FAIL'}")
    print(f"Message: {report['message']}")
    print("="*60 + "\n")

def main():
    """
    Main entry point for rubric validation.
    
    Usage:
        python -m code.analysis.rubric_validation
    """
    parser = argparse.ArgumentParser(description="Validate rubric correlation against human annotations.")
    parser.add_argument('--output', type=str, default=None, help='Path to save validation report JSON')
    args = parser.parse_args()
    
    try:
        logger.info("Starting rubric validation...")
        
        # Step 1: Load hold-out set
        logger.info("Loading hold-out set...")
        holdout_df = load_holdout_set()
        logger.info(f"Loaded {len(holdout_df)} samples from hold-out set.")
        
        # Step 2: Apply rubric scoring
        logger.info("Applying rubric scoring logic...")
        scored_df = simulate_rubric_scoring(holdout_df)
        
        # Step 3: Calculate correlation
        logger.info("Calculating correlation between rubric and human scores...")
        r, p_value = calculate_correlation(scored_df)
        logger.info(f"Correlation calculated: r={r:.4f}, p={p_value:.4f}")
        
        # Step 4: Validate
        validation_result = validate_correlation(r, p_value)
        
        # Step 5: Save report
        output_path = Path(args.output) if args.output else None
        report_path = save_validation_report(validation_result, output_path)
        
        # Step 6: Print summary
        print_validation_summary(validation_result)
        
        # Log metrics
        log_metric("rubric_correlation", r)
        log_metric("rubric_p_value", p_value)
        log_metric("rubric_validation_passed", validation_result['is_valid'])
        
        if not validation_result['is_valid']:
            logger.warning("Rubric validation FAILED. Correlation below threshold.")
            sys.exit(1)
        
        logger.info("Rubric validation completed successfully.")
        
    except FileNotFoundError as e:
        logger.error(f"Data file not found: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during validation: {e}")
        log_error(e)
        sys.exit(1)

if __name__ == "__main__":
    main()
