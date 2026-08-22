import os
import sys
import pickle
import argparse
import numpy as np
import matplotlib.pyplot as plt
from typing import Dict, Any, List, Optional, Tuple

# Add project root to path for imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from utils.logging import get_logger, log_info, log_error, log_warning
from utils.error_codes import ErrorCode

logger = get_logger(__name__)

def load_model_artifact(model_path: str) -> Any:
    """Load the trained model artifact from disk."""
    if not os.path.exists(model_path):
        log_error(f"Model artifact not found at {model_path}", ErrorCode.DATA_SOURCE_MISSING)
        raise FileNotFoundError(f"Model artifact not found at {model_path}")
    
    with open(model_path, 'rb') as f:
        model = pickle.load(f)
    log_info(f"Successfully loaded model artifact from {model_path}")
    return model

def load_processed_data(data_path: str) -> List[Dict[str, Any]]:
    """Load processed descriptor data from CSV."""
    if not os.path.exists(data_path):
        log_error(f"Processed data not found at {data_path}", ErrorCode.DATA_SOURCE_MISSING)
        raise FileNotFoundError(f"Processed data not found at {data_path}")
    
    data = []
    with open(data_path, 'r') as f:
        import csv
        reader = csv.DictReader(f)
        for row in reader:
            # Convert numeric fields
            numeric_row = {}
            for k, v in row.items():
                try:
                    numeric_row[k] = float(v)
                except (ValueError, TypeError):
                    numeric_row[k] = v
            data.append(numeric_row)
    
    log_info(f"Loaded {len(data)} records from {data_path}")
    return data

def filter_by_system(data: List[Dict[str, Any]], system_id: str) -> List[Dict[str, Any]]:
    """Filter dataset by system ID (e.g., 'Cu-Zn', 'Al-Cu')."""
    filtered = [row for row in data if row.get('system_id') == system_id]
    log_info(f"Filtered to {len(filtered)} records for system {system_id}")
    return filtered

def prepare_features(data: List[Dict[str, Any]]) -> np.ndarray:
    """Extract feature matrix from data."""
    feature_cols = ['mean_atomic_radius', 'electronegativity_variance', 
                    'valence_electron_count', 'hume_rothery_concentration']
    
    X = []
    for row in data:
        features = [row.get(col, 0.0) for col in feature_cols]
        X.append(features)
    
    return np.array(X)

def generate_predictions(model: Any, X: np.ndarray) -> np.ndarray:
    """Generate predictions using the trained model."""
    predictions = model.predict(X)
    log_info(f"Generated {len(predictions)} predictions")
    return predictions

def calculate_mae(predictions: np.ndarray, actuals: np.ndarray) -> float:
    """Calculate Mean Absolute Error."""
    return np.mean(np.abs(predictions - actuals))

def plot_phase_diagram(
    system_id: str,
    composition_data: np.ndarray,
    temperature_actual: np.ndarray,
    temperature_predicted: np.ndarray,
    output_path: str,
    title: Optional[str] = None
) -> None:
    """
    Plot experimental vs predicted phase boundaries.
    
    CRITICAL FOR T034: Implements visual distinction:
    - Experimental (ground truth): SOLID line
    - Predicted: DASHED line
    """
    if title is None:
        title = f"Phase Diagram: {system_id}"
    
    plt.figure(figsize=(10, 6))
    
    # Sort by composition for smooth line plotting
    sort_indices = np.argsort(composition_data)
    comp_sorted = composition_data[sort_indices]
    temp_actual_sorted = temperature_actual[sort_indices]
    temp_pred_sorted = temperature_predicted[sort_indices]
    
    # Plot Experimental (Ground Truth) as SOLID line
    # Color: Blue, Line style: Solid
    plt.plot(comp_sorted, temp_actual_sorted, 
             color='#1f77b4', linestyle='-', linewidth=2.5, 
             label='Experimental (Ground Truth)', marker='o', markersize=4)
    
    # Plot Predicted as DASHED line
    # Color: Orange, Line style: Dashed
    plt.plot(comp_sorted, temp_pred_sorted, 
             color='#ff7f0e', linestyle='--', linewidth=2.5, 
             label='Predicted', marker='s', markersize=4)
    
    plt.xlabel('Composition (%)', fontsize=12)
    plt.ylabel('Temperature (K)', fontsize=12)
    plt.title(title, fontsize=14, fontweight='bold')
    plt.legend(loc='best', fontsize=10)
    plt.grid(True, linestyle=':', alpha=0.6)
    plt.xlim(-5, 105)  # Composition 0-100% with padding
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    log_info(f"Phase diagram plot saved to {output_path}")
    log_info(f"Visual distinction applied: Solid line for Experimental, Dashed line for Predicted")

def run_visualization(
    model_path: str,
    data_path: str,
    system_ids: List[str],
    output_dir: str
) -> Dict[str, Any]:
    """
    Run the full visualization pipeline for specified systems.
    
    Returns a report of MAE values per system.
    """
    log_info(f"Starting visualization pipeline for systems: {system_ids}")
    
    # Load model
    model = load_model_artifact(model_path)
    
    # Load data
    data = load_processed_data(data_path)
    
    results = {}
    
    for system_id in system_ids:
        log_info(f"Processing system: {system_id}")
        
        # Filter data for this system
        system_data = filter_by_system(data, system_id)
        
        if len(system_data) < 2:
            log_warning(f"Insufficient data for system {system_id} (found {len(system_data)} records)")
            results[system_id] = {'status': 'skipped', 'reason': 'insufficient_data'}
            continue
        
        # Prepare features
        X = prepare_features(system_data)
        
        # Extract actual temperatures (assuming 'temperature' column exists)
        actual_temps = np.array([row.get('temperature', 0.0) for row in system_data])
        
        # Generate predictions
        predicted_temps = generate_predictions(model, X)
        
        # Extract compositions (assuming 'composition' column exists, 0-100 scale)
        compositions = np.array([row.get('composition', 0.0) for row in system_data])
        
        # Calculate MAE
        mae = calculate_mae(predicted_temps, actual_temps)
        log_info(f"MAE for {system_id}: {mae:.2f} K")
        
        # Generate plot with T034 visual distinction
        plot_filename = f"{system_id.replace('-', '_')}_phase_diagram.png"
        output_path = os.path.join(output_dir, plot_filename)
        
        plot_phase_diagram(
            system_id=system_id,
            composition_data=compositions,
            temperature_actual=actual_temps,
            temperature_predicted=predicted_temps,
            output_path=output_path,
            title=f"{system_id} Phase Boundary Comparison"
        )
        
        results[system_id] = {
            'status': 'success',
            'mae': float(mae),
            'output_file': output_path,
            'n_samples': len(system_data)
        }
    
    log_info(f"Visualization pipeline completed. Results: {results}")
    return results

def main():
    parser = argparse.ArgumentParser(description='Generate phase diagram visualizations')
    parser.add_argument('--model-path', type=str, default='data/artifacts/model.pkl',
                        help='Path to trained model artifact')
    parser.add_argument('--data-path', type=str, default='data/processed/descriptors.csv',
                        help='Path to processed descriptor data')
    parser.add_argument('--systems', type=str, nargs='+', default=['Cu-Zn', 'Al-Cu'],
                        help='System IDs to visualize (e.g., Cu-Zn Al-Cu)')
    parser.add_argument('--output-dir', type=str, default='data/artifacts/plots',
                        help='Output directory for plots')
    
    args = parser.parse_args()
    
    try:
        results = run_visualization(
            model_path=args.model_path,
            data_path=args.data_path,
            system_ids=args.systems,
            output_dir=args.output_dir
        )
        
        # Print summary
        print("\nVisualization Summary:")
        print("-" * 40)
        for sys_id, res in results.items():
            if res['status'] == 'success':
                print(f"{sys_id}: MAE={res['mae']:.2f} K, Plot: {res['output_file']}")
            else:
                print(f"{sys_id}: Skipped - {res.get('reason', 'unknown')}")
        
        return 0
    except Exception as e:
        log_error(f"Visualization pipeline failed: {str(e)}", ErrorCode.INSUFFICIENT_POWER)
        return 1

if __name__ == '__main__':
    sys.exit(main())