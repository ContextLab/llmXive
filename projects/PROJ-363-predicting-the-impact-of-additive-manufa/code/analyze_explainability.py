import os
import sys
import json
import logging
import pickle
import time
import numpy as np
import pandas as pd
import shap
from sklearn.inspection import permutation_importance
from pathlib import Path

# Import from local utils if needed, otherwise define minimal helpers
try:
    from utils import setup_logging, load_state, update_state, compute_file_hash
except ImportError:
    # Fallback for standalone execution if utils is not in path
    def setup_logging():
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        return logging.getLogger(__name__)
    
    def load_state(path):
        import yaml
        with open(path, 'r') as f:
            return yaml.safe_load(f)
    
    def update_state(state, path):
        import yaml
        with open(path, 'w') as f:
            yaml.dump(state, f)
    
    def compute_file_hash(path):
        import hashlib
        hasher = hashlib.sha256()
        with open(path, 'rb') as f:
            hasher.update(f.read())
        return hasher.hexdigest()

def load_state_file(state_path="state/selected_model.yaml"):
    """Load the selected model configuration from state."""
    try:
        with open(state_path, 'r') as f:
            import yaml
            return yaml.safe_load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"State file not found: {state_path}. Ensure T028 has run.")

def load_model_from_path(path):
    """Load a pickled model."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Model file not found: {path}")
    with open(path, 'rb') as f:
        return pickle.load(f)

def load_data_from_path(path):
    """Load feature data from CSV."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Data file not found: {path}")
    return pd.read_csv(path)

def find_best_model(state_config):
    """Determine which model and dataset to use based on T028 selection."""
    selected_type = state_config.get('selected_model_type', 'derived')
    if selected_type == 'raw':
        model_path = 'models/artifacts/best_raw_model.pkl'
        data_path = 'data/processed/X_raw.csv'
    elif selected_type == 'derived':
        model_path = 'models/artifacts/best_derived_model.pkl'
        data_path = 'data/processed/X_derived.csv'
    else:
        raise ValueError(f"Unknown selected model type: {selected_type}")
    return model_path, data_path, selected_type

def calculate_shap_and_plot(model, X_data, subset_name, output_dir="results/plots"):
    """Calculate SHAP values and generate summary plot."""
    os.makedirs(output_dir, exist_ok=True)
    explainer = shap.Explainer(model, X_data)
    shap_values = explainer(X_data)
    
    plot_path = os.path.join(output_dir, f"shap_summary_{subset_name}.png")
    shap.summary_plot(shap_values, X_data, show=False)
    import matplotlib.pyplot as plt
    plt.savefig(plot_path)
    plt.close()
    
    logging.info(f"SHAP summary plot saved to {plot_path}")
    return shap_values

def perform_statistical_analysis(model, X_data, y_data, subset_name, n_permutations=1000, output_dir="results/reports"):
    """
    Perform Permutation Importance with p-value calculation.
    Implements T033b (Selected Model) and T033d (Non-Selected Model) logic.
    
    Args:
        model: Trained sklearn model.
        X_data: Feature DataFrame.
        y_data: Target Series.
        subset_name: Identifier for the subset (e.g., 'raw', 'derived').
        n_permutations: Number of permutations (default 1000).
        output_dir: Directory to save reports.
    
    Returns:
        dict: Results dictionary containing importance scores and p-values.
    """
    os.makedirs(output_dir, exist_ok=True)
    logging.info(f"Starting Permutation Importance for {subset_name} model with {n_permutations} permutations...")
    
    # Calculate permutation importance
    # Using 'r2' as the scoring metric for regression
    perm_result = permutation_importance(
        model, X_data, y_data, 
        n_repeats=n_permutations, 
        random_state=42, 
        n_jobs=-1, 
        scoring='r2'
    )
    
    importance_scores = perm_result.importances_mean
    std_scores = perm_result.importances_std
    
    # Calculate p-values
    # Null hypothesis: Permutation importance is 0 (no effect)
    # We test if the mean importance is significantly different from 0.
    # Since permutation_importance returns (n_samples, n_features), we can test the distribution of importances per feature against 0.
    # However, standard permutation importance calculates the drop in score. 
    # A positive drop means the feature is important.
    # We will perform a one-sample t-test against 0 for each feature's distribution of importance values.
    
    from scipy.stats import ttest_1samp
    
    p_values = []
    feature_names = X_data.columns.tolist()
    significant_features = []
    
    for i, feature in enumerate(feature_names):
        # Get the distribution of importance for this feature across permutations
        feature_importances = perm_result.importances[:, i]
        
        # One-sample t-test: H0: mean = 0
        # We want to know if the mean importance is significantly > 0 (one-tailed) or != 0 (two-tailed)
        # Given the context of "statistical significance" in feature importance, 
        # we usually care if it's significantly positive (feature matters).
        # Let's use two-tailed to detect any significant deviation, then check direction.
        t_stat, p_val = ttest_1samp(feature_importances, 0.0)
        
        # Adjust for one-tailed if we strictly care about positive importance
        # If t_stat > 0, one-tailed p is p_val / 2. If t_stat < 0, it's 1 - p_val/2.
        # But standard practice often uses the two-tailed p-value as a threshold for "non-zero effect".
        # Let's stick to two-tailed for robustness unless specified otherwise.
        p_values.append(p_val)
        
        if p_val < 0.05:
            significant_features.append(feature)
    
    results = {
        "subset": subset_name,
        "n_permutations": n_permutations,
        "features": feature_names,
        "importance_mean": importance_scores.tolist(),
        "importance_std": std_scores.tolist(),
        "p_values": p_values,
        "significant_features": significant_features,
        "significance_threshold": 0.05
    }
    
    # Determine output filename based on whether this is the selected or non-selected model
    # The caller (main) will decide the filename, but we can infer here for logging
    output_filename = f"{subset_name}_permutation.json"
    output_path = os.path.join(output_dir, output_filename)
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logging.info(f"Permutation Importance report saved to {output_path}")
    logging.info(f"Significant features ({subset_name}): {significant_features}")
    
    return results

def run_comparison_analysis(perm_selected, perm_non_selected):
    """
    Compare feature importance ranks between selected and non-selected models.
    Implements T035.
    """
    from scipy.stats import spearmanr
    
    features_sel = perm_selected['features']
    features_non = perm_non_selected['features']
    
    # Only compare common features
    common_features = list(set(features_sel) & set(features_non))
    if not common_features:
        logging.warning("No common features to compare.")
        return None
    
    # Sort by common features to align indices
    imp_sel = np.array([perm_selected['importance_mean'][features_sel.index(f)] for f in common_features])
    imp_non = np.array([perm_non_selected['importance_mean'][features_non.index(f)] for f in common_features])
    
    rank_sel = pd.Series(imp_sel).rank(ascending=False)
    rank_non = pd.Series(imp_non).rank(ascending=False)
    
    corr, p_value = spearmanr(rank_sel, rank_non)
    
    comparison = {
        "spearman_correlation": float(corr),
        "p_value": float(p_value),
        "common_features": common_features,
        "significant_features_raw": perm_selected.get('significant_features', []),
        "significant_features_derived": perm_non_selected.get('significant_features', [])
    }
    
    output_path = "results/reports/feature_comparison.json"
    with open(output_path, 'w') as f:
        json.dump(comparison, f, indent=2)
    
    logging.info(f"Feature comparison saved to {output_path}")
    return comparison

def main():
    """
    Main entry point for Explainability Analysis.
    Executes T030, T031, T031b, T033a, T033b, T033c, T033d, T035.
    """
    logger = setup_logging()
    logger.info("Starting Explainability Analysis (US3)")
    
    # 1. Load Selection State (T030)
    try:
        state_config = load_state_file("state/selected_model.yaml")
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)
    
    selected_type = state_config.get('selected_model_type', 'derived')
    logger.info(f"Selected model type: {selected_type}")
    
    # Determine paths for selected and non-selected models
    if selected_type == 'raw':
        selected_model_path, selected_data_path, _ = find_best_model(state_config)
        non_selected_model_path = 'models/artifacts/best_derived_model.pkl'
        non_selected_data_path = 'data/processed/X_derived.csv'
        non_selected_type = 'derived'
    else:
        selected_model_path, selected_data_path, _ = find_best_model(state_config)
        non_selected_model_path = 'models/artifacts/best_raw_model.pkl'
        non_selected_data_path = 'data/processed/X_raw.csv'
        non_selected_type = 'raw'
    
    # Log model load (T030 output)
    load_log = {
        "selected_model_path": selected_model_path,
        "selected_data_path": selected_data_path,
        "non_selected_model_path": non_selected_model_path,
        "non_selected_data_path": non_selected_data_path
    }
    with open("results/reports/model_load_log.json", 'w') as f:
        json.dump(load_log, f, indent=2)
    
    # 2. Load Selected Model and Data (T030)
    try:
        model_sel = load_model_from_path(selected_model_path)
        X_sel = load_data_from_path(selected_data_path)
    except FileNotFoundError as e:
        logger.error(f"Failed to load selected model/data: {e}")
        sys.exit(1)
    
    # Extract target from the original cleaned dataset if not present in X subsets
    # The X subsets (X_raw, X_derived) usually contain only features.
    # We need the target 'porosity'.
    # We assume the cleaned dataset 'cleaned_316L.csv' exists and has 'porosity' column.
    try:
        full_data = pd.read_csv('data/processed/cleaned_316L.csv')
        y_sel = full_data['porosity']
        # Align y_sel with X_sel index if necessary
        # If X_sel was created by filtering, we need to ensure y_sel matches.
        # For simplicity, assuming X_sel rows correspond to the first N rows of full_data or same index.
        # A robust way: if X_sel has an index column, use it. Otherwise, assume order matches.
        # Given the pipeline flow, X_sel is likely a subset of columns from cleaned_316L.csv rows.
        # We will assume the row order is preserved.
        if len(X_sel) != len(y_sel):
            logger.warning(f"Row count mismatch: X_sel={len(X_sel)}, y_sel={len(y_sel)}. Aligning by index.")
            # If index exists in both, align. If not, this is a risk.
            # For now, we assume they are aligned or X_sel is a slice of the same dataframe.
            # If X_sel was created by `df[features]`, the index is preserved.
            y_sel = y_sel.loc[X_sel.index]
    except Exception as e:
        logger.error(f"Failed to load target data: {e}")
        sys.exit(1)
    
    # 3. Calculate SHAP for Selected Model (T031)
    try:
        shap_sel = calculate_shap_and_plot(model_sel, X_sel, selected_type)
    except Exception as e:
        logger.error(f"SHAP calculation failed for selected model: {e}")
        sys.exit(1)
    
    # 4. Perform Permutation Importance for Selected Model (T033b)
    try:
        perm_sel = perform_statistical_analysis(model_sel, X_sel, y_sel, selected_type, n_permutations=1000)
    except Exception as e:
        logger.error(f"Permutation Importance failed for selected model: {e}")
        sys.exit(1)
    
    # 5. Load Non-Selected Model and Data (T031b, T033c, T033d)
    # Check if non-selected files exist (X_raw might not exist if Ev-only path was taken)
    if not os.path.exists(non_selected_data_path):
        logger.warning(f"Non-selected data path {non_selected_data_path} not found. Skipping non-selected analysis.")
    else:
        try:
            model_non = load_model_from_path(non_selected_model_path)
            X_non = load_data_from_path(non_selected_data_path)
            y_non = full_data['porosity'].loc[X_non.index] # Align
            
            # 6. Calculate SHAP for Non-Selected Model (T031b)
            shap_non = calculate_shap_and_plot(model_non, X_non, non_selected_type)
            
            # 7. Perform Permutation Importance for Non-Selected Model (T033d)
            perm_non = perform_statistical_analysis(model_non, X_non, y_non, non_selected_type, n_permutations=1000)
            
            # 8. Run Comparison (T035)
            if 'perm_non' in locals():
                run_comparison_analysis(perm_sel, perm_non)
            
        except FileNotFoundError as e:
            logger.warning(f"Non-selected model or data not found: {e}. Skipping non-selected analysis.")
        except Exception as e:
            logger.error(f"Error processing non-selected model: {e}")
    
    # 9. Update State (Optional, but good practice)
    # Update state.yaml with hashes of new reports
    try:
        state = load_state("state.yaml")
        state['artifact_hashes'] = state.get('artifact_hashes', {})
        # Add hashes for the new reports
        for report in ['selected_model_permutation.json', 'non_selected_model_permutation.json', 'feature_comparison.json']:
            path = f"results/reports/{report}"
            if os.path.exists(path):
                state['artifact_hashes'][report] = compute_file_hash(path)
        update_state(state, "state.yaml")
    except Exception as e:
        logger.warning(f"Failed to update state: {e}")
    
    logger.info("Explainability Analysis completed successfully.")

if __name__ == "__main__":
    main()