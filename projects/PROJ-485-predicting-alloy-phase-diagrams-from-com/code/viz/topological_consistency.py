import os
import sys
import json
import numpy as np
from typing import Dict, List, Tuple, Optional

from utils.logging import get_logger, log_info, log_error, log_warning
from models.loso_checks import load_elemental_properties
from viz.plot_phase_diagrams import load_model_artifact, load_processed_data, filter_by_system, prepare_features, generate_predictions

logger = get_logger(__name__)

def extract_phase_boundaries(system_data: List[Dict]) -> Dict[float, List[float]]:
    """
    Extract phase boundary temperatures for a given system.
    Returns a dict mapping composition (0.0-1.0) to list of temperatures.
    """
    boundaries = {}
    for row in system_data:
        comp = float(row['composition'])
        temp = float(row['temperature'])
        if comp not in boundaries:
            boundaries[comp] = []
        boundaries[comp].append(temp)
    return boundaries

def calculate_partial_match_ratio(predicted_temps: List[float], experimental_temps: List[float]) -> bool:
    """
    Check if sorted lists of temperatures match.
    Returns True if the sorted order is identical.
    """
    if len(predicted_temps) != len(experimental_temps):
        return False
    sorted_pred = sorted(predicted_temps)
    sorted_exp = sorted(experimental_temps)
    return sorted_pred == sorted_exp

def calculate_tcs_for_system(
    system_id: str,
    model,
    processed_data: List[Dict],
    composition_slices: Optional[List[float]] = None
) -> Dict[str, any]:
    """
    Calculate Topological Consistency Score (TCS) for a specific system.
    
    TCS = (Number of slices where sorted(predicted) == sorted(experimental)) / (Total slices)
    """
    if composition_slices is None:
        composition_slices = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
    
    system_data = filter_by_system(processed_data, system_id)
    if not system_data:
        log_warning(f"No data found for system {system_id}")
        return {"system": system_id, "tcs_score": 0.0, "slices_evaluated": 0}
    
    # Extract experimental boundaries
    experimental_boundaries = extract_phase_boundaries(system_data)
    
    # Prepare features and generate predictions
    features = prepare_features(system_data)
    predictions = generate_predictions(model, features)
    
    # Build predicted boundaries
    predicted_boundaries = {}
    for i, row in enumerate(system_data):
        comp = float(row['composition'])
        pred_temp = float(predictions[i])
        if comp not in predicted_boundaries:
            predicted_boundaries[comp] = []
        predicted_boundaries[comp].append(pred_temp)
    
    # Calculate TCS
    slices_evaluated = 0
    matching_slices = 0
    
    for slice_comp in composition_slices:
        # Find closest composition in data
        closest_comp = None
        min_dist = float('inf')
        
        for comp in experimental_boundaries.keys():
            dist = abs(comp - slice_comp)
            if dist < min_dist:
                min_dist = dist
                closest_comp = comp
        
        if closest_comp is None or min_dist > 0.05:  # Skip if too far
            continue
        
        slices_evaluated += 1
        
        exp_temps = experimental_boundaries.get(closest_comp, [])
        pred_temps = predicted_boundaries.get(closest_comp, [])
        
        if not exp_temps or not pred_temps:
            continue
        
        if calculate_partial_match_ratio(pred_temps, exp_temps):
            matching_slices += 1
    
    tcs_score = matching_slices / slices_evaluated if slices_evaluated > 0 else 0.0
    
    log_info(f"TCS for {system_id}: {tcs_score:.4f} ({matching_slices}/{slices_evaluated} slices)")
    
    if tcs_score < 0.8:
        log_warning(f"TCS for {system_id} is below threshold (0.8): {tcs_score:.4f}")
    
    return {
        "system": system_id,
        "tcs_score": float(tcs_score),
        "slices_evaluated": slices_evaluated
    }

def calculate_tcs_from_files(
    system_ids: List[str],
    model_path: str = "data/artifacts/model.pkl",
    data_path: str = "data/processed/descriptors.csv",
    output_path: str = "data/artifacts/tcs_report.json"
) -> List[Dict]:
    """
    Calculate TCS for multiple systems and save report to file.
    """
    # Load model
    model = load_model_artifact(model_path)
    
    # Load processed data
    processed_data = load_processed_data(data_path)
    
    # Calculate TCS for each system
    results = []
    for system_id in system_ids:
        result = calculate_tcs_for_system(system_id, model, processed_data)
        results.append(result)
    
    # Save report
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    log_info(f"TCS report saved to {output_path}")
    return results

def calculate_tcs_from_results(
    system_ids: List[str],
    model,
    processed_data: List[Dict],
    output_path: str = "data/artifacts/tcs_report.json"
) -> List[Dict]:
    """
    Calculate TCS from already loaded model and data objects.
    """
    results = []
    for system_id in system_ids:
        result = calculate_tcs_for_system(system_id, model, processed_data)
        results.append(result)
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    log_info(f"TCS report saved to {output_path}")
    return results

def main():
    """
    Main entry point for TCS calculation.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Calculate Topological Consistency Score')
    parser.add_argument('--systems', nargs='+', default=['Cu-Zn', 'Al-Cu'],
                      help='System IDs to evaluate')
    parser.add_argument('--model-path', default='data/artifacts/model.pkl',
                      help='Path to model artifact')
    parser.add_argument('--data-path', default='data/processed/descriptors.csv',
                      help='Path to processed data')
    parser.add_argument('--output-path', default='data/artifacts/tcs_report.json',
                      help='Output path for TCS report')
    
    args = parser.parse_args()
    
    try:
        results = calculate_tcs_from_files(
            system_ids=args.systems,
            model_path=args.model_path,
            data_path=args.data_path,
            output_path=args.output_path
        )
        
        print(f"TCS Calculation Complete:")
        for result in results:
            print(f"  {result['system']}: TCS = {result['tcs_score']:.4f} "
                 f"(evaluated {result['slices_evaluated']} slices)")
        
    except Exception as e:
        log_error(f"Error calculating TCS: {str(e)}")
        raise

if __name__ == '__main__':
    main()