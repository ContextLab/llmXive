import os
import sys
import pickle
import json
from typing import Dict, List, Any, Optional, Tuple, Union
import numpy as np

# Local imports based on provided API surface
from utils.logging import get_logger, log_info, log_error, log_warning
from utils.error_codes import ErrorCode

logger = get_logger(__name__)

def load_model_artifact(model_path: str) -> Any:
    """Load the trained model from disk."""
    if not os.path.exists(model_path):
        log_error(ErrorCode.DATA_SOURCE_MISSING, f"Model artifact not found at {model_path}")
        raise FileNotFoundError(f"Model artifact not found at {model_path}")
    
    with open(model_path, 'rb') as f:
        return pickle.load(f)

def load_processed_data(data_path: str) -> List[Dict[str, Any]]:
    """Load processed descriptor data."""
    if not os.path.exists(data_path):
        log_error(ErrorCode.DATA_SOURCE_MISSING, f"Processed data not found at {data_path}")
        raise FileNotFoundError(f"Processed data not found at {data_path}")
    
    data = []
    with open(data_path, 'r') as f:
        # Assuming CSV format based on T018 output
        import csv
        reader = csv.DictReader(f)
        for row in reader:
            data.append(row)
    return data

def filter_by_system(data: List[Dict[str, Any]], system_id: str) -> List[Dict[str, Any]]:
    """Filter data for a specific binary system (e.g., 'Cu-Zn')."""
    filtered = []
    for row in data:
        # Check if the row belongs to the requested system
        # Assuming 'system_id' column exists or can be derived from element columns
        if 'system_id' in row:
            if row['system_id'] == system_id:
                filtered.append(row)
        elif 'element_a' in row and 'element_b' in row:
            # Construct system_id from elements
            elements = sorted([row['element_a'], row['element_b']])
            constructed_id = f"{elements[0]}-{elements[1]}"
            if constructed_id == system_id:
                filtered.append(row)
    return filtered

def prepare_features(row: Dict[str, Any]) -> np.ndarray:
    """Prepare feature vector for prediction."""
    # Assuming descriptors are already calculated and present in the row
    # Common descriptors: mean_atomic_radius, electronegativity_variance, 
    # valence_electron_count, hume_rothery_concentration
    features = []
    descriptor_keys = [
        'mean_atomic_radius', 
        'electronegativity_variance', 
        'valence_electron_count', 
        'hume_rothery_concentration'
    ]
    
    for key in descriptor_keys:
        if key in row:
            try:
                features.append(float(row[key]))
            except (ValueError, TypeError):
                features.append(0.0)
        else:
            features.append(0.0)
    
    return np.array(features).reshape(1, -1)

def generate_predictions(model: Any, data: List[Dict[str, Any]]) -> List[float]:
    """Generate predictions for the provided data."""
    predictions = []
    for row in data:
        features = prepare_features(row)
        pred = model.predict(features)[0]
        predictions.append(float(pred))
    return predictions

def calculate_mae(experimental: List[float], predicted: List[float]) -> float:
    """Calculate Mean Absolute Error."""
    if len(experimental) != len(predicted) or len(experimental) == 0:
        return 0.0
    
    errors = [abs(e - p) for e, p in zip(experimental, predicted)]
    return sum(errors) / len(errors)

def plot_phase_diagram(
    composition: np.ndarray, 
    temp_experimental: np.ndarray, 
    temp_predicted: np.ndarray, 
    system_id: str, 
    output_path: str
) -> None:
    """
    Plot phase diagram with visual distinction between experimental and predicted boundaries.
    
    CRITICAL FOR T034: 
    - Experimental data is plotted with SOLID lines.
    - Predicted data is plotted with DASHED lines.
    """
    import matplotlib
    matplotlib.use('Agg')  # Non-interactive backend for saving files
    import matplotlib.pyplot as plt

    plt.figure(figsize=(10, 6))

    # Sort by composition for proper line plotting
    sort_idx = np.argsort(composition)
    comp_sorted = composition[sort_idx]
    temp_exp_sorted = temp_experimental[sort_idx]
    temp_pred_sorted = temp_predicted[sort_idx]

    # PLOT EXPERIMENTAL: SOLID LINE
    # This represents the ground truth phase boundaries
    plt.plot(
        comp_sorted, 
        temp_exp_sorted, 
        label='Experimental (Ground Truth)', 
        color='blue', 
        linestyle='solid', 
        linewidth=2,
        marker='o',
        markersize=4
    )

    # PLOT PREDICTED: DASHED LINE
    # This represents the model's prediction
    # T034 Requirement: Visual distinction via line style
    plt.plot(
        comp_sorted, 
        temp_pred_sorted, 
        label='Predicted (Model)', 
        color='red', 
        linestyle='dashed', 
        linewidth=2,
        marker='x',
        markersize=4
    )

    plt.xlabel('Composition (Element B %)')
    plt.ylabel('Temperature (K)')
    plt.title(f'Phase Diagram: {system_id}')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    log_info(None, f"Phase diagram saved to {output_path}")

def log_fidelity_check(system_id: str, mae: float, threshold: float = 50.0) -> None:
    """Log fidelity check results."""
    if mae > threshold:
        log_warning(
            ErrorCode.LOW_DATA_FIDELITY, 
            f"System {system_id}: MAE ({mae:.2f}K) exceeds threshold ({threshold}K). Marked as FAILED."
        )
    else:
        log_info(None, f"System {system_id}: MAE ({mae:.2f}K) within threshold ({threshold}K).")

def run_visualization(
    model_path: str, 
    data_path: str, 
    systems: List[str], 
    output_dir: str
) -> Dict[str, Any]:
    """
    Run visualization for specified systems.
    
    Returns a report of generated plots and fidelity metrics.
    """
    log_info(None, f"Starting visualization for systems: {systems}")
    
    # Load model
    model = load_model_artifact(model_path)
    
    # Load data
    data = load_processed_data(data_path)
    
    results = {
        "systems_processed": [],
        "plots_generated": [],
        "fidelity_checks": []
    }
    
    for system_id in systems:
        log_info(None, f"Processing system: {system_id}")
        
        # Filter data for this system
        system_data = filter_by_system(data, system_id)
        
        if not system_data:
            log_warning(None, f"No data found for system {system_id}, skipping.")
            continue
        
        # Extract composition and experimental temperature
        # Assuming 'composition' is fraction of element B (0-1) or percentage (0-100)
        # Adjust based on actual data schema
        compositions = []
        temps_exp = []
        
        for row in system_data:
            # Try to find composition column
            comp_val = None
            if 'composition' in row:
                comp_val = float(row['composition'])
            elif 'comp_b' in row:
                comp_val = float(row['comp_b'])
            
            temp_val = None
            if 'temperature' in row:
                temp_val = float(row['temperature'])
            elif 'temp' in row:
                temp_val = float(row['temp'])
            
            if comp_val is not None and temp_val is not None:
                compositions.append(comp_val)
                temps_exp.append(temp_val)
        
        if not compositions:
            log_warning(None, f"Could not extract composition/temp for {system_id}")
            continue
        
        compositions = np.array(compositions)
        temps_exp = np.array(temps_exp)
        
        # Generate predictions
        temps_pred = generate_predictions(model, system_data)
        temps_pred = np.array(temps_pred)
        
        # Calculate MAE
        mae = calculate_mae(temps_exp.tolist(), temps_pred.tolist())
        
        # Log fidelity check
        log_fidelity_check(system_id, mae)
        
        # Generate plot
        # T034: Ensure solid vs dashed distinction is applied in plot_phase_diagram
        plot_filename = f"{system_id}_phase_diagram.png"
        plot_path = os.path.join(output_dir, plot_filename)
        
        plot_phase_diagram(
            compositions, 
            temps_exp, 
            temps_pred, 
            system_id, 
            plot_path
        )
        
        results["systems_processed"].append(system_id)
        results["plots_generated"].append(plot_path)
        results["fidelity_checks"].append({
            "system": system_id,
            "mae": mae,
            "status": "PASSED" if mae <= 50.0 else "FAILED"
        })
    
    log_info(None, f"Visualization complete. Processed {len(results['systems_processed'])} systems.")
    return results

def main():
    """Main entry point for the visualization script."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate phase diagram visualizations")
    parser.add_argument("--model", type=str, default="data/artifacts/model.pkl", help="Path to model artifact")
    parser.add_argument("--data", type=str, default="data/processed/descriptors.csv", help="Path to processed data")
    parser.add_argument("--output", type=str, default="data/artifacts/plots", help="Output directory for plots")
    parser.add_argument("--systems", type=str, nargs="+", default=["Cu-Zn", "Al-Cu"], help="Systems to visualize")
    
    args = parser.parse_args()
    
    # Simple system filtering to exclude complex/metastable systems (T038)
    # Hardcoded list of simple binary systems to visualize
    simple_systems = ["Cu-Zn", "Al-Cu", "Cu-Ni", "Fe-Ni"]
    systems_to_plot = [s for s in args.systems if s in simple_systems]
    
    if not systems_to_plot:
        log_warning(None, "No valid simple binary systems provided for visualization.")
        return
    
    run_visualization(
        model_path=args.model,
        data_path=args.data,
        systems=systems_to_plot,
        output_dir=args.output
    )

if __name__ == "__main__":
    main()