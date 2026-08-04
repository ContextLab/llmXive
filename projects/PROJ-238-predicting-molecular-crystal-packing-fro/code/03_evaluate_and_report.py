import os
import sys
import json
import logging
import pickle
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for server environments
import matplotlib.pyplot as plt
from pathlib import Path
from typing import List, Dict, Any, Tuple

# Import config for logging setup
from code.config import setup_logging, get_config

# Ensure the code directory is in the path for relative imports if running as script
# but the API surface expects imports like `from code.utils.metrics import ...`
# The project structure seems to be code/ at root, so we adjust sys.path if necessary
# However, the provided API surface shows imports like `from code.config import ...`
# which implies the root is the parent of `code`.
# Let's ensure we can import from code.utils if needed, though this task focuses on plotting.

def load_test_data() -> pd.DataFrame:
    """Load the test dataset from the processed directory."""
    import pandas as pd
    config = get_config()
    test_path = config.get('DATA_PATH', 'data/processed') / 'test.csv'
    if not isinstance(test_path, Path):
        test_path = Path(test_path)
    
    if not test_path.exists():
        raise FileNotFoundError(f"Test data file not found: {test_path}")
    
    df = pd.read_csv(test_path)
    return df

def load_model() -> Any:
    """Load the trained Random Forest model from the state directory."""
    config = get_config()
    # Assuming the model is saved in state/projects/PROJ-238.../models/
    # We need to find the specific model file. The task implies we use the RF model.
    # Let's look for a file named 'rf_model.pkl' or similar in the expected state path.
    state_path = config.get('STATE_PATH', 'state/projects/PROJ-238-predicting-molecular-crystal-packing-fro')
    if not isinstance(state_path, Path):
        state_path = Path(state_path)
    
    model_dir = state_path / 'models'
    if not model_dir.exists():
        raise FileNotFoundError(f"Model directory not found: {model_dir}")
    
    model_file = model_dir / 'rf_model.pkl'
    if not model_file.exists():
        # Try to find any .pkl file if exact name is unknown
        pkl_files = list(model_dir.glob('*.pkl'))
        if not pkl_files:
            raise FileNotFoundError(f"No model files found in {model_dir}")
        model_file = pkl_files[0]
    
    with open(model_file, 'rb') as f:
        model = pickle.load(f)
    return model

def calculate_permutation_importance(model, X: np.ndarray, y: np.ndarray, n_repeats: int = 10, random_state: int = 42) -> Dict[str, float]:
    """
    Calculate permutation importance for the given model and data.
    Returns a dictionary mapping feature names to their importance scores.
    """
    from sklearn.inspection import permutation_importance
    
    # Ensure inputs are numpy arrays
    X = np.array(X)
    y = np.array(y)
    
    result = permutation_importance(model, X, y, n_repeats=n_repeats, random_state=random_state, scoring='r2')
    
    # The result.importances_mean gives the mean importance for each feature
    # We need to map these to feature names. The caller must provide the feature names.
    return result.importances_mean

def generate_feature_importance_plot(importance_scores: np.ndarray, feature_names: List[str], output_path: Path):
    """
    Generate a bar plot of feature importance, highlighting the top 3 features
    and showing their cumulative importance.
    """
    # Sort features by importance descending
    indices = np.argsort(importance_scores)[::-1]
    sorted_importances = importance_scores[indices]
    sorted_features = [feature_names[i] for i in indices]
    
    # Calculate cumulative importance
    cumulative_importance = np.cumsum(sorted_importances)
    total_importance = np.sum(sorted_importances)
    
    # Normalize to percentage
    cumulative_percentage = (cumulative_importance / total_importance) * 100
    
    # Create the plot
    plt.figure(figsize=(12, 8))
    
    # Plot bar chart
    bars = plt.barh(range(len(sorted_features)), sorted_importances, color='skyblue', edgecolor='black')
    
    # Highlight top 3 features
    for i in range(min(3, len(sorted_features))):
        bars[i].set_color('coral')
        bars[i].set_edgecolor('darkred')
        bars[i].set_linewidth(2)
    
    # Add labels
    plt.yticks(range(len(sorted_features)), sorted_features, fontsize=10)
    plt.xlabel('Permutation Importance (Mean Decrease in R²)', fontsize=12)
    plt.title('Feature Importance for Molecular Crystal Packing Prediction', fontsize=14, fontweight='bold')
    
    # Add text annotations for top 3 features and cumulative percentage
    for i, (bar, imp, feat) in enumerate(zip(bars, sorted_importances, sorted_features)):
        if i < 3:
            # Annotate the bar with the importance value
            plt.text(imp, i, f'  {imp:.4f}', va='center', fontsize=9, fontweight='bold')
            
            # Annotate cumulative percentage on the right side
            cum_pct = cumulative_percentage[i]
            plt.text(max(sorted_importances) * 1.05, i, f'  Cum: {cum_pct:.1f}%', va='center', fontsize=9, color='darkred', fontweight='bold')
    
    # Add a horizontal line indicating the 60% cumulative threshold
    # Find the index where cumulative percentage first exceeds 60%
    threshold_idx = np.argmax(cumulative_percentage >= 60)
    if cumulative_percentage[threshold_idx] >= 60:
        # Calculate the cumulative importance value at that index
        threshold_val = cumulative_importance[threshold_idx]
        plt.axvline(x=threshold_val, color='green', linestyle='--', linewidth=1.5, label=f'60% Cumulative Threshold ({cumulative_percentage[threshold_idx]:.1f}%)')
        plt.legend()
    
    # Ensure the output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save the plot
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    logging.info(f"Feature importance plot saved to {output_path}")
    
    # Verify the top 3 cumulative importance is > 60%
    top3_cum = cumulative_percentage[2] if len(cumulative_percentage) >= 3 else cumulative_percentage[-1]
    if top3_cum <= 60:
        logging.warning(f"Top 3 features only account for {top3_cum:.1f}% of total importance (expected > 60%)")
    else:
        logging.info(f"Top 3 features account for {top3_cum:.1f}% of total importance (> 60% requirement met)")

def main():
    """Main entry point for the feature importance generation task."""
    # Setup logging
    logger = setup_logging('T033_feature_importance')
    logger.info("Starting T033: Generate feature importance plot")
    
    try:
        # Load test data
        logger.info("Loading test data...")
        test_df = load_test_data()
        
        # Define feature columns (excluding ID and target)
        # Assuming the target is 'packing_coefficient' and ID is 'ID'
        feature_cols = [col for col in test_df.columns if col not in ['ID', 'packing_coefficient', 'dipole_imputed', 'interaction_type', 'interaction_confidence']]
        
        if not feature_cols:
            raise ValueError("No feature columns found in test data. Check column names.")
        
        logger.info(f"Using {len(feature_cols)} features: {feature_cols}")
        
        # Prepare X and y
        X = test_df[feature_cols].values
        y = test_df['packing_coefficient'].values
        
        # Load the trained Random Forest model
        logger.info("Loading trained Random Forest model...")
        model = load_model()
        
        # Calculate permutation importance
        logger.info("Calculating permutation importance...")
        importance_scores = calculate_permutation_importance(model, X, y, n_repeats=10, random_state=42)
        
        # Generate the plot
        output_path = Path("results/feature_importance.png")
        logger.info(f"Generating feature importance plot at {output_path}...")
        generate_feature_importance_plot(importance_scores, feature_cols, output_path)
        
        logger.info("T033 completed successfully.")
        
    except Exception as e:
        logger.error(f"Error during T033 execution: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
