import os
import sys
import json
import logging
import pickle
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from typing import Dict, Any, List, Tuple
from sklearn.inspection import permutation_importance

# Import project config
from code.config import get_config, setup_logging

# Ensure matplotlib uses non-interactive backend for headless environments
plt.switch_backend('Agg')

def load_test_data() -> Tuple[np.ndarray, np.ndarray, List[str]]:
    """
    Loads the test set data from data/processed/test.csv.
    Returns features (X), target (y), and feature names (feature_names).
    """
    config = get_config()
    test_path = Path(config.get('DATA_PATH', 'data/processed')) / 'test.csv'
    
    if not test_path.exists():
        raise FileNotFoundError(f"Test data file not found: {test_path}")
    
    import pandas as pd
    df = pd.read_csv(test_path)
    
    # Expected target column
    target_col = 'packing_coefficient'
    if target_col not in df.columns:
        raise ValueError(f"Target column '{target_col}' not found in {test_path}")
    
    # Identify feature columns (exclude ID and target)
    exclude_cols = [target_col, 'id', 'dipole_imputed', 'interaction_type', 'interaction_confidence']
    feature_cols = [c for c in df.columns if c not in exclude_cols]
    
    X = df[feature_cols].values
    y = df[target_col].values
    feature_names = feature_cols
    
    return X, y, feature_names

def load_model(model_path: str = None) -> Any:
    """
    Loads the trained Random Forest model from the default path.
    """
    if model_path is None:
        config = get_config()
        # Default path based on project structure
        model_path = Path('state/projects/PROJ-238-predicting-molecular-crystal-packing-fro/models/random_forest_model.pkl')
    else:
        model_path = Path(model_path)
        
    if not model_path.exists():
        raise FileNotFoundError(f"Model file not found: {model_path}")
    
    with open(model_path, 'rb') as f:
        return pickle.load(f)

def calculate_permutation_importance(model: Any, X: np.ndarray, y: np.ndarray, 
                                     feature_names: List[str], 
                                     scoring: str = 'r2', n_repeats: int = 10, 
                                     random_state: int = 42) -> Dict[str, float]:
    """
    Calculates permutation importance for the given model.
    Returns a dictionary mapping feature names to their importance scores.
    """
    result = permutation_importance(model, X, y, n_repeats=n_repeats, 
                                    random_state=random_state, scoring=scoring)
    
    importance_dict = {}
    for i, name in enumerate(feature_names):
        importance_dict[name] = result.importances_mean[i]
        
    return importance_dict

def generate_feature_importance_plot(importance_dict: Dict[str, float], 
                                     output_path: str) -> None:
    """
    Generates a bar plot of feature importance, highlighting the top 3 features
    and displaying their cumulative importance percentage.
    Saves the plot to output_path.
    """
    # Sort features by importance (descending)
    sorted_features = sorted(importance_dict.items(), key=lambda x: x[1], reverse=True)
    names = [k for k, v in sorted_features]
    values = [v for k, v in sorted_features]
    
    # Calculate cumulative importance
    total_importance = sum(values)
    if total_importance == 0:
        raise ValueError("Total importance is zero; cannot calculate percentages.")
    
    cumulative_percentages = []
    current_sum = 0
    for v in values:
        current_sum += v
        cumulative_percentages.append((current_sum / total_importance) * 100)
    
    # Determine top 3 features
    top_3_count = min(3, len(names))
    top_3_names = names[:top_3_count]
    top_3_cumulative = cumulative_percentages[top_3_count - 1]
    
    # Create plot
    plt.figure(figsize=(12, 8))
    colors = ['#1f77b4' if name in top_3_names else '#d6d6d6' for name in names]
    
    bars = plt.barh(names, values, color=colors)
    
    # Annotate top 3 bars with cumulative percentage
    for i, (name, val, cum_pct) in enumerate(zip(names, values, cumulative_percentages)):
        if name in top_3_names:
            # Position text to the right of the bar
            plt.text(val + 0.002, i, f'{cum_pct:.1f}%', va='center', fontsize=10, fontweight='bold')
    
    plt.xlabel('Permutation Importance (R² decrease)')
    plt.title(f'Feature Importance (Top 3 highlighted, Cumulative: {top_3_cumulative:.1f}%)')
    plt.gca().invert_yaxis()
    plt.tight_layout()
    
    # Ensure output directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    plt.savefig(output_path, dpi=300)
    plt.close()

def main():
    """
    Main entry point for Task T033: Generate feature importance visualization.
    """
    logger = setup_logging()
    logger.info("Starting T033: Feature Importance Generation")
    
    try:
        # 1. Load Test Data
        logger.info("Loading test data...")
        X, y, feature_names = load_test_data()
        logger.info(f"Loaded {X.shape[0]} samples with {X.shape[1]} features.")
        
        # 2. Load Model
        logger.info("Loading Random Forest model...")
        model = load_model()
        logger.info("Model loaded successfully.")
        
        # 3. Calculate Permutation Importance
        logger.info("Calculating permutation importance...")
        importance_dict = calculate_permutation_importance(model, X, y, feature_names)
        
        # 4. Generate Plot
        config = get_config()
        output_dir = Path(config.get('RESULTS_PATH', 'results'))
        output_file = output_dir / 'feature_importance.png'
        
        logger.info(f"Generating plot at {output_file}...")
        generate_feature_importance_plot(importance_dict, str(output_file))
        
        # 5. Verification
        if not output_file.exists():
            raise FileNotFoundError(f"Failed to generate output file: {output_file}")
        
        # Check top 3 cumulative importance
        sorted_features = sorted(importance_dict.items(), key=lambda x: x[1], reverse=True)
        top_3_vals = [v for _, v in sorted_features[:3]]
        total = sum(importance_dict.values())
        cumulative_top_3 = sum(top_3_vals) / total
        
        logger.info(f"Top 3 features: {[f[0] for f in sorted_features[:3]]}")
        logger.info(f"Cumulative importance of top 3: {cumulative_top_3*100:.2f}%")
        
        if cumulative_top_3 <= 0.60:
            logger.warning(f"Cumulative importance ({cumulative_top_3*100:.2f}%) is <= 60%. Check data or model.")
        else:
            logger.info(f"Success: Cumulative importance ({cumulative_top_3*100:.2f}%) > 60%.")
        
        logger.info("T033 completed successfully.")
        
    except Exception as e:
        logger.error(f"Error during T033 execution: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()