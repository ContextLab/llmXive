import os
import sys
import json
import numpy as np
from typing import Dict, List, Tuple, Optional

from utils.logging import get_logger, log_info, log_error, log_warning

logger = get_logger(__name__)

def extract_phase_boundaries(
    df: List[Dict[str, any]],
    system_id: str
) -> List[Tuple[float, float]]:
    """
    Extract phase boundary points (composition, temperature) for a specific system.
    
    Args:
        df: List of dictionaries representing processed data rows
        system_id: String identifier for the alloy system (e.g., "Cu-Zn")
        
    Returns:
        List of (composition, temperature) tuples representing the phase boundary
    """
    boundaries = []
    for row in df:
        if row.get("system_id") == system_id:
            # Assuming 'composition' is 0-1 (fraction) and 'temperature' is in Kelvin
            comp = row.get("composition")
            temp = row.get("temperature")
            if comp is not None and temp is not None:
                boundaries.append((float(comp), float(temp)))
    
    # Sort by composition for consistent comparison
    boundaries.sort(key=lambda x: x[0])
    return boundaries

def calculate_partial_match_ratio(
    boundaries_exp: List[Tuple[float, float]],
    boundaries_pred: List[Tuple[float, float]],
    temp_tolerance: float = 50.0,
    comp_tolerance: float = 0.05
) -> float:
    """
    Calculate the Topological Consistency Score (TCS) using partial match ratio.
    
    The TCS is defined as the ratio of predicted boundary points that have a 
    corresponding experimental point within specified tolerances.
    
    Args:
        boundaries_exp: Experimental phase boundary points [(comp, temp), ...]
        boundaries_pred: Predicted phase boundary points [(comp, temp), ...]
        temp_tolerance: Temperature tolerance in Kelvin (default 50K)
        comp_tolerance: Composition tolerance (default 0.05 = 5%)
        
    Returns:
        Partial match ratio (0.0 to 1.0)
    """
    if not boundaries_exp or not boundaries_pred:
        return 0.0
    
    matches = 0
    used_indices = set()
    
    for pred_comp, pred_temp in boundaries_pred:
        best_match_idx = None
        min_distance = float('inf')
        
        for i, (exp_comp, exp_temp) in enumerate(boundaries_exp):
            if i in used_indices:
                continue
            
            # Calculate weighted distance
            comp_diff = abs(pred_comp - exp_comp)
            temp_diff = abs(pred_temp - exp_temp)
            
            # Check if within tolerance
            if comp_diff <= comp_tolerance and temp_diff <= temp_tolerance:
                # Normalize distance for matching priority (closer is better)
                distance = (comp_diff / comp_tolerance) + (temp_diff / temp_tolerance)
                if distance < min_distance:
                    min_distance = distance
                    best_match_idx = i
        
        if best_match_idx is not None:
            matches += 1
            used_indices.add(best_match_idx)
    
    # Partial match ratio: matches / total predicted points
    ratio = matches / len(boundaries_pred)
    return ratio

def calculate_tcs_from_files(
    data_path: str,
    model_path: str,
    systems: List[str] = None,
    output_path: str = "data/artifacts/tcs_report.json"
) -> Dict[str, any]:
    """
    Calculate TCS for multiple systems from data and model files.
    
    Args:
        data_path: Path to processed data CSV
        model_path: Path to trained model artifact
        systems: List of system IDs to analyze (default: ["Cu-Zn", "Al-Cu"])
        output_path: Path to save the TCS report
        
    Returns:
        Dictionary containing TCS results
    """
    if systems is None:
        systems = ["Cu-Zn", "Al-Cu"]
    
    import csv
    
    # Load processed data
    data = []
    with open(data_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Convert numeric fields
            try:
                row['composition'] = float(row['composition'])
                row['temperature'] = float(row['temperature'])
                data.append(row)
            except (ValueError, KeyError):
                continue
    
    # Load model (we need predictions, but for TCS we focus on topology)
    # In a full implementation, we would generate predictions here
    # For now, we simulate the structure expected
    import pickle
    with open(model_path, 'rb') as f:
        model = pickle.load(f)
    
    results = {
        "systems": {},
        "overall_tcs": 0.0,
        "systems_analyzed": 0,
        "warning_threshold": 0.8
    }
    
    total_ratio = 0.0
    
    for system_id in systems:
        log_info(f"Calculating TCS for system: {system_id}")
        
        # Extract boundaries (in real implementation, we'd separate exp vs pred)
        # Here we assume the data contains both or we have a way to distinguish
        # For this task, we'll simulate a comparison between two subsets
        
        # In a real scenario, we would have:
        # 1. Experimental boundaries (ground truth)
        # 2. Predicted boundaries (from model)
        
        # For demonstration, we'll split the data or use a mock comparison
        # This assumes the data has a 'source' column or similar
        
        exp_boundaries = []
        pred_boundaries = []
        
        for row in data:
            if row.get("system_id") == system_id:
                comp = row.get("composition")
                temp = row.get("temperature")
                if comp is not None and temp is not None:
                    # In real implementation, distinguish between exp and pred
                    # For now, we'll use a simple heuristic or mock
                    if row.get("source") == "experimental":
                        exp_boundaries.append((comp, temp))
                    elif row.get("source") == "predicted":
                        pred_boundaries.append((comp, temp))
        
        # If no explicit source, we might need to load from separate files
        # or use a different strategy. For this task, we assume the structure exists.
        
        if not exp_boundaries or not pred_boundaries:
            log_warning(f"No boundaries found for system {system_id}. Skipping.")
            continue
        
        tcs = calculate_partial_match_ratio(exp_boundaries, pred_boundaries)
        
        results["systems"][system_id] = {
            "tcs": round(tcs, 4),
            "exp_points": len(exp_boundaries),
            "pred_points": len(pred_boundaries),
            "status": "PASS" if tcs >= 0.8 else "WARNING"
        }
        
        total_ratio += tcs
        results["systems_analyzed"] += 1
        
        if tcs < 0.8:
            log_warning(f"TCS for {system_id} is {tcs:.4f} (< 0.8). "
                      "This is an auxiliary metric; primary gate is MAE.")
    
    if results["systems_analyzed"] > 0:
        results["overall_tcs"] = round(total_ratio / results["systems_analyzed"], 4)
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Save report
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    log_info(f"TCS report saved to {output_path}")
    return results

def calculate_tcs_from_results(
    exp_boundaries: Dict[str, List[Tuple[float, float]]],
    pred_boundaries: Dict[str, List[Tuple[float, float]]],
    output_path: str = "data/artifacts/tcs_report.json"
) -> Dict[str, any]:
    """
    Calculate TCS from pre-extracted boundary dictionaries.
    
    Args:
        exp_boundaries: Dict mapping system_id to list of (comp, temp) tuples
        pred_boundaries: Dict mapping system_id to list of (comp, temp) tuples
        output_path: Path to save the TCS report
        
    Returns:
        Dictionary containing TCS results
    """
    results = {
        "systems": {},
        "overall_tcs": 0.0,
        "systems_analyzed": 0,
        "warning_threshold": 0.8
    }
    
    total_ratio = 0.0
    systems = set(exp_boundaries.keys()) & set(pred_boundaries.keys())
    
    for system_id in systems:
        log_info(f"Calculating TCS for system: {system_id}")
        
        exp_list = exp_boundaries[system_id]
        pred_list = pred_boundaries[system_id]
        
        if not exp_list or not pred_list:
            log_warning(f"No boundaries found for system {system_id}. Skipping.")
            continue
        
        tcs = calculate_partial_match_ratio(exp_list, pred_list)
        
        results["systems"][system_id] = {
            "tcs": round(tcs, 4),
            "exp_points": len(exp_list),
            "pred_points": len(pred_list),
            "status": "PASS" if tcs >= 0.8 else "WARNING"
        }
        
        total_ratio += tcs
        results["systems_analyzed"] += 1
        
        if tcs < 0.8:
            log_warning(f"TCS for {system_id} is {tcs:.4f} (< 0.8). "
                      "This is an auxiliary metric; primary gate is MAE.")
    
    if results["systems_analyzed"] > 0:
        results["overall_tcs"] = round(total_ratio / results["systems_analyzed"], 4)
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Save report
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    log_info(f"TCS report saved to {output_path}")
    return results

def main():
    """Main entry point for TCS calculation."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Calculate Topological Consistency Score")
    parser.add_argument("--data", type=str, default="data/processed/descriptors.csv",
                      help="Path to processed data CSV")
    parser.add_argument("--model", type=str, default="data/artifacts/model.pkl",
                      help="Path to trained model artifact")
    parser.add_argument("--output", type=str, default="data/artifacts/tcs_report.json",
                      help="Path to save TCS report")
    parser.add_argument("--systems", type=str, nargs="+", default=["Cu-Zn", "Al-Cu"],
                      help="Systems to analyze")
    
    args = parser.parse_args()
    
    log_info("Starting TCS calculation")
    
    # Check if required files exist
    if not os.path.exists(args.data):
        log_error(f"Data file not found: {args.data}")
        sys.exit(1)
    
    if not os.path.exists(args.model):
        log_error(f"Model file not found: {args.model}")
        sys.exit(1)
    
    results = calculate_tcs_from_files(
        data_path=args.data,
        model_path=args.model,
        systems=args.systems,
        output_path=args.output
    )
    
    log_info(f"Overall TCS: {results['overall_tcs']:.4f}")
    log_info(f"Systems analyzed: {results['systems_analyzed']}")
    
    for system, data in results["systems"].items():
        status = "✓" if data["status"] == "PASS" else "⚠"
        log_info(f"{status} {system}: TCS = {data['tcs']:.4f}")

if __name__ == "__main__":
    main()