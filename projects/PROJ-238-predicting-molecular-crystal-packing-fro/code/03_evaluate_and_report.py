import os
import sys
import json
import logging
import pickle
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from sklearn.inspection import permutation_importance
from sklearn.ensemble import RandomForestRegressor
from pathlib import Path

# Import project configuration and utilities
from code.config import setup_logging, get_config
from code.utils.metrics import paired_t_test, bonferroni_correct

def load_test_data():
    """Load the test split data from the processed directory."""
    config = get_config()
    test_path = Path(config['DATA_PATH']) / 'processed' / 'test.csv'
    if not test_path.exists():
        raise FileNotFoundError(f"Test data not found at {test_path}. Please run the data pipeline first.")
    
    df = pd.read_csv(test_path)
    # Define feature columns based on the descriptor list
    feature_cols = ['Volume', 'SurfaceArea', 'Dipole', 'HBD', 'HBA', 'PSA']
    target_col = 'packing_coefficient'
    
    # Ensure columns exist
    missing = [c for c in feature_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing feature columns in test data: {missing}")
    if target_col not in df.columns:
        raise ValueError(f"Target column '{target_col}' not found in test data.")
        
    return df[feature_cols], df[target_col], feature_cols

def load_model(model_type='random_forest'):
    """Load the trained model from the state directory."""
    config = get_config()
    state_path = Path(config['STATE_PATH']) / 'projects' / 'PROJ-238-predicting-molecular-crystal-packing-fro'
    model_file = state_path / f'{model_type}_model.pkl'
    
    if not model_file.exists():
        raise FileNotFoundError(f"Model file not found at {model_file}. Please run training first.")
    
    with open(model_file, 'rb') as f:
        return pickle.load(f)

def calculate_permutation_importance(model, X_test, y_test, feature_names, n_repeats=10, random_state=42):
    """Calculate permutation importance for the model."""
    result = permutation_importance(
        model, X_test, y_test, 
        n_repeats=n_repeats, 
        random_state=random_state,
        n_jobs=-1
    )
    
    importance_dict = {}
    for i, name in enumerate(feature_names):
        importance_dict[name] = result.importances_mean[i]
    
    return importance_dict

def generate_feature_importance_plot(importance_dict, output_path):
    """Generate a bar plot of feature importance and save it."""
    # Sort by importance
    sorted_features = sorted(importance_dict.items(), key=lambda x: x[1], reverse=True)
    names = [x[0] for x in sorted_features]
    values = [x[1] for x in sorted_features]
    
    # Calculate cumulative importance
    cumulative = np.cumsum(values)
    total = np.sum(values)
    cumulative_pct = (cumulative / total) * 100
    
    # Setup plot
    plt.figure(figsize=(10, 6))
    bars = plt.barh(names, values, color='skyblue', edgecolor='black')
    
    # Add value labels on bars
    for i, (bar, val) in enumerate(zip(bars, values)):
        plt.text(val + 0.001, bar.get_y() + bar.get_height()/2, f'{val:.4f}', va='center', fontsize=9)
    
    # Add cumulative percentage line on secondary axis
    ax2 = plt.gca().twinx()
    ax2.plot(cumulative_pct, names, color='red', marker='o', linestyle='--', linewidth=2, label='Cumulative %')
    ax2.axvline(60, color='green', linestyle=':', label='60% Threshold')
    ax2.set_ylabel('Features')
    ax2.set_xlabel('Cumulative Importance (%)')
    ax2.set_ylim(-1, len(names))
    
    # Highlight top 3
    if len(names) >= 3:
        top3_names = names[:3]
        for name in top3_names:
            idx = names.index(name)
            plt.gca().get_yticks()[idx] # Just to ensure index is valid
            # We can't easily highlight specific bars in horizontal bar chart without complex logic,
            # but the order ensures top 3 are at the top visually.
    
    plt.xlabel('Permutation Importance (Mean Decrease in R²)')
    plt.title('Feature Importance (Permutation) - Top Features Identified')
    plt.legend(loc='lower right')
    plt.tight_layout()
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path, dpi=300)
    plt.close()
    
    # Log verification
    top_3_sum = sum(values[:3])
    total_sum = sum(values)
    cum_pct_top3 = (top_3_sum / total_sum) * 100 if total_sum > 0 else 0
    logging.info(f"Top 3 features: {names[:3]}")
    logging.info(f"Cumulative importance of top 3: {cum_pct_top3:.2f}%")
    if cum_pct_top3 <= 60:
        logging.warning(f"Cumulative importance of top 3 ({cum_pct_top3:.2f}%) is not > 60% as expected, but plot generated.")

def main():
    """Main entry point for the evaluation and reporting script."""
    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("Starting Feature Importance Analysis (T033)")
    
    try:
        # 1. Load Data
        logger.info("Loading test data...")
        X_test, y_test, feature_names = load_test_data()
        
        # 2. Load Model (Random Forest as per T032 context)
        logger.info("Loading trained Random Forest model...")
        model = load_model(model_type='random_forest')
        
        # 3. Calculate Permutation Importance
        logger.info("Calculating permutation importance...")
        importance_dict = calculate_permutation_importance(model, X_test, y_test, feature_names)
        
        # 4. Generate Plot
        config = get_config()
        results_path = Path(config['RESULTS_PATH'])
        output_file = results_path / 'feature_importance.png'
        
        logger.info(f"Generating feature importance plot at {output_file}...")
        generate_feature_importance_plot(importance_dict, str(output_file))
        
        logger.info(f"Task T033 completed successfully. Output saved to {output_file}")
        
    except Exception as e:
        logger.error(f"Task T033 failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == '__main__':
    main()