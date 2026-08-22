"""
Topological Consistency Score (TCS) calculation module.

Implements partial match ratio logic to compare predicted vs experimental
phase boundaries at fixed composition slices.

Methodology:
- Sort phase boundaries by temperature for each composition
- Compare sorted slices to calculate matching ratio
- TCS >= 0.8 indicates good topological consistency (SC-004)
"""

import os
import sys
import numpy as np
from typing import Dict, List, Tuple, Optional

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from utils.logging import get_logger, log_info, log_error, log_warning

logger = get_logger(__name__)


def extract_phase_boundaries(
    data: List[Dict], 
    composition_col: str = 'composition_at%', 
    temperature_col: str = 'temperature_K',
    phase_col: str = 'phase'
) -> Dict[float, List[float]]:
    """
    Extract phase boundaries as temperature values at fixed compositions.
    
    Args:
        data: List of dictionaries with composition, temperature, and phase info
        composition_col: Column name for composition percentage
        temperature_col: Column name for temperature
        phase_col: Column name for phase identifier
        
    Returns:
        Dictionary mapping composition values to sorted list of boundary temperatures
    """
    composition_boundaries = {}
    
    for row in data:
        comp = float(row[composition_col])
        temp = float(row[temperature_col])
        
        if comp not in composition_boundaries:
            composition_boundaries[comp] = []
        
        composition_boundaries[comp].append(temp)
    
    # Sort temperatures for each composition to get ordered boundaries
    for comp in composition_boundaries:
        composition_boundaries[comp] = sorted(composition_boundaries[comp])
    
    return composition_boundaries


def calculate_partial_match_ratio(
    exp_boundaries: Dict[float, List[float]],
    pred_boundaries: Dict[float, List[float]],
    tolerance: float = 50.0  # 50K tolerance for boundary matching
) -> Tuple[float, int, int]:
    """
    Calculate Topological Consistency Score using partial match ratio.
    
    The score is computed as: matching_slices / total_slices
    where a slice matches if the sorted boundary temperatures are within tolerance.
    
    Args:
        exp_boundaries: Experimental boundaries {composition: [sorted temps]}
        pred_boundaries: Predicted boundaries {composition: [sorted temps]}
        tolerance: Temperature tolerance in Kelvin for matching boundaries
        
    Returns:
        Tuple of (tcs_score, matching_count, total_count)
    """
    # Find common compositions
    common_compositions = set(exp_boundaries.keys()) & set(pred_boundaries.keys())
    
    if not common_compositions:
        logger.warning("No common compositions found between experimental and predicted data")
        return 0.0, 0, 0
    
    matching_count = 0
    total_count = len(common_compositions)
    
    for comp in sorted(common_compositions):
        exp_temps = exp_boundaries[comp]
        pred_temps = pred_boundaries[comp]
        
        # Check if number of boundaries matches
        if len(exp_temps) != len(pred_temps):
            logger.debug(
                f"Composition {comp}: boundary count mismatch "
                f"(exp={len(exp_temps)}, pred={len(pred_temps)})"
            )
            continue
        
        # Check if all corresponding boundaries are within tolerance
        all_match = True
        for exp_t, pred_t in zip(exp_temps, pred_temps):
            if abs(exp_t - pred_t) > tolerance:
                all_match = False
                logger.debug(
                    f"Composition {comp}: temperature mismatch "
                    f"(exp={exp_t:.1f}, pred={pred_t:.1f}, diff={abs(exp_t-pred_t):.1f})"
                )
                break
        
        if all_match:
            matching_count += 1
    
    tcs_score = matching_count / total_count if total_count > 0 else 0.0
    
    return tcs_score, matching_count, total_count


def calculate_tcs_from_files(
    experimental_path: str,
    predicted_path: str,
    composition_col: str = 'composition_at%',
    temperature_col: str = 'temperature_K',
    phase_col: str = 'phase',
    tolerance: float = 50.0
) -> Dict[str, any]:
    """
    Calculate TCS from two data files (experimental and predicted).
    
    Args:
        experimental_path: Path to experimental data CSV
        predicted_path: Path to predicted data CSV
        composition_col: Column name for composition
        temperature_col: Column name for temperature
        phase_col: Column name for phase
        tolerance: Temperature tolerance in Kelvin
        
    Returns:
        Dictionary with TCS metrics
    """
    import csv
    
    # Load experimental data
    exp_data = []
    with open(experimental_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            exp_data.append(row)
    
    # Load predicted data
    pred_data = []
    with open(predicted_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            pred_data.append(row)
    
    logger.info(f"Loaded {len(exp_data)} experimental rows and {len(pred_data)} predicted rows")
    
    # Extract boundaries
    exp_boundaries = extract_phase_boundaries(
        exp_data, composition_col, temperature_col, phase_col
    )
    pred_boundaries = extract_phase_boundaries(
        pred_data, composition_col, temperature_col, phase_col
    )
    
    logger.info(f"Extracted {len(exp_boundaries)} experimental and {len(pred_boundaries)} predicted composition slices")
    
    # Calculate TCS
    tcs_score, matching, total = calculate_partial_match_ratio(
        exp_boundaries, pred_boundaries, tolerance
    )
    
    return {
        'tcs_score': tcs_score,
        'matching_slices': matching,
        'total_slices': total,
        'tolerance_K': tolerance,
        'passes_threshold': tcs_score >= 0.8
    }


def calculate_tcs_from_results(
    experimental_data: List[Dict],
    predicted_data: List[Dict],
    tolerance: float = 50.0
) -> Dict[str, any]:
    """
    Calculate TCS directly from data lists (useful when data is already in memory).
    
    Args:
        experimental_data: List of experimental data dictionaries
        predicted_data: List of predicted data dictionaries
        tolerance: Temperature tolerance in Kelvin
        
    Returns:
        Dictionary with TCS metrics
    """
    exp_boundaries = extract_phase_boundaries(experimental_data)
    pred_boundaries = extract_phase_boundaries(predicted_data)
    
    tcs_score, matching, total = calculate_partial_match_ratio(
        exp_boundaries, pred_boundaries, tolerance
    )
    
    return {
        'tcs_score': tcs_score,
        'matching_slices': matching,
        'total_slices': total,
        'tolerance_K': tolerance,
        'passes_threshold': tcs_score >= 0.8
    }


def main():
    """
    Main entry point for TCS calculation from command line.
    
    Usage:
        python code/viz/topological_consistency.py \
            --experimental data/processed/experimental_cu_zn.csv \
            --predicted data/processed/predicted_cu_zn.csv \
            --output data/artifacts/tcs_results.json
    """
    import argparse
    import json
    
    parser = argparse.ArgumentParser(description='Calculate Topological Consistency Score')
    parser.add_argument('--experimental', required=True, help='Path to experimental data CSV')
    parser.add_argument('--predicted', required=True, help='Path to predicted data CSV')
    parser.add_argument('--output', required=True, help='Path to output JSON file')
    parser.add_argument('--tolerance', type=float, default=50.0, help='Temperature tolerance in Kelvin')
    parser.add_argument('--comp-col', default='composition_at%', help='Composition column name')
    parser.add_argument('--temp-col', default='temperature_K', help='Temperature column name')
    parser.add_argument('--phase-col', default='phase', help='Phase column name')
    
    args = parser.parse_args()
    
    log_info("Starting TCS calculation")
    
    try:
        results = calculate_tcs_from_files(
            args.experimental,
            args.predicted,
            composition_col=args.comp_col,
            temperature_col=args.temp_col,
            phase_col=args.phase_col,
            tolerance=args.tolerance
        )
        
        # Ensure output directory exists
        output_dir = os.path.dirname(args.output)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # Write results to JSON
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2)
        
        log_info(f"TCS calculation complete: {results['tcs_score']:.4f} "
                f"({results['matching_slices']}/{results['total_slices']} slices match)")
        log_info(f"Passes threshold (>= 0.8): {results['passes_threshold']}")
        
        return results
        
    except Exception as e:
        log_error(f"TCS calculation failed: {str(e)}")
        raise


if __name__ == '__main__':
    main()
