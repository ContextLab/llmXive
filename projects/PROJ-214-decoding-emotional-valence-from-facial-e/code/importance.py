"""
code/importance.py

Implements permutation importance and SHAP analysis for the trained Random Forest model.
This module fulfills FR-006: Quantify feature contributions and generate interpretability reports.

Dependencies:
  - sklearn: permutation_importance, RandomForestClassifier
  - shap: TreeExplainer, summary_plot
  - joblib: load
  - numpy, pandas, matplotlib
  - code.config: CONFIG paths and hyperparameters
  - code.train: load_model_bundle (if needed for model retrieval)
"""
import os
import logging
import pickle
import gc
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional, Union

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.inspection import permutation_importance
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import log_loss
import shap

from code.config import CONFIG
from code.train import load_model_bundle, load_preprocessed_data

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(CONFIG['paths']['logs'], 'importance.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def load_features_and_labels(data_path: str) -> Tuple[np.ndarray, np.ndarray, List[str]]:
    """
    Load processed features and labels from the preprocessed data.
    
    Args:
        data_path: Path to the processed data directory or file.
        
    Returns:
        X: Feature matrix (n_samples, n_features)
        y: Label vector (n_samples,)
        feature_names: List of feature names
    """
    # Expecting a specific structure based on preprocessing output
    # Assuming data is stored as parquet or csv in data/processed/features/
    feature_file = Path(data_path) / "features.parquet"
    label_file = Path(data_path) / "labels.npy"
    meta_file = Path(data_path) / "feature_names.json" # Or .pkl

    if not feature_file.exists():
        # Fallback to CSV if parquet not found, though parquet is preferred for speed
        feature_file = Path(data_path) / "features.csv"
    
    if not feature_file.exists() or not label_file.exists():
        raise FileNotFoundError(f"Processed data not found at {data_path}. "
                                f"Expected {feature_file} and {label_file}. "
                                "Run preprocessing and training first.")

    logger.info(f"Loading features from {feature_file} and labels from {label_file}")
    
    # Load features
    if feature_file.suffix == '.parquet':
        df = pd.read_parquet(feature_file)
    else:
        df = pd.read_csv(feature_file)
    
    # Separate features and target if target is in the same file, 
    # but we expect separate files based on typical pipeline separation
    # Assuming 'target' column exists if loaded from single file, 
    # otherwise we load y separately.
    # Based on T019/T022, we likely have a merged dataset for training.
    # Let's assume the feature file contains the features and a 'subject_id' and 'label'.
    
    # If labels are separate:
    y = np.load(label_file)
    
    # Extract features (drop subject_id if present, assume last column or specific name is target)
    # We need to ensure we are only loading the EMG features.
    # Let's assume the dataframe has a 'label' column if merged, or we construct y.
    if 'label' in df.columns:
        y_from_df = df['label'].values
        X = df.drop(columns=['label', 'subject_id', 'trial_id'], errors='ignore').values
        feature_names = [c for c in df.columns if c not in ['label', 'subject_id', 'trial_id']]
    else:
        # If y is separate, we need to know which columns are features.
        # Assuming all numeric columns except metadata are features.
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        # Exclude subject_id if it's numeric
        feature_cols = [c for c in numeric_cols if c != 'subject_id']
        X = df[feature_cols].values
        feature_names = feature_cols
    
    # Ensure alignment if y was separate and df has rows
    if 'label' not in df.columns:
        # If y is separate, we assume row order matches. 
        # In a real robust implementation, we'd match on subject/trial IDs.
        # For now, assume alignment.
        pass

    logger.info(f"Loaded {X.shape[0]} samples with {X.shape[1]} features.")
    return X, y, feature_names

def calculate_permutation_importance(
    model: Union[RandomForestClassifier, LogisticRegression],
    X: np.ndarray,
    y: np.ndarray,
    feature_names: List[str],
    n_repeats: int = 10,
    scoring: str = 'accuracy',
    random_state: int = 42
) -> pd.DataFrame:
    """
    Calculate permutation importance for the given model.
    
    Args:
        model: Trained scikit-learn model.
        X: Feature matrix.
        y: Target vector.
        feature_names: List of feature names.
        n_repeats: Number of times to permute a feature.
        scoring: Scoring strategy.
        random_state: Random seed.
        
    Returns:
        DataFrame with feature names and importance scores.
    """
    logger.info(f"Calculating permutation importance with {n_repeats} repeats...")
    
    result = permutation_importance(
        model, X, y, 
        n_repeats=n_repeats, 
        random_state=random_state, 
        scoring=scoring,
        n_jobs=4
    )
    
    importance_df = pd.DataFrame({
        'feature': feature_names,
        'importance_mean': result.importances_mean,
        'importance_std': result.importances_std
    })
    
    # Sort by importance
    importance_df = importance_df.sort_values(by='importance_mean', ascending=False)
    
    logger.info(f"Permutation importance calculated. Top feature: {importance_df.iloc[0]['feature']}")
    return importance_df

def group_importance_by_muscle(importance_df: pd.DataFrame, feature_names: List[str]) -> pd.DataFrame:
    """
    Aggregate feature importance by muscle group (Corrugator, Zygomaticus, Orbicularis).
    
    Assumes feature names follow the pattern: {muscle}_{feature}_{channel} or similar.
    e.g., 'corr_rms', 'zyg_zcr', 'orb_wamp'
    """
    # Define muscle prefixes based on data model
    muscle_prefixes = {
        'Corrugator': ['corr', 'corrugator'],
        'Zygomaticus': ['zyg', 'zygomaticus'],
        'Orbicularis': ['orb', 'orbicularis']
    }
    
    muscle_importance = {}
    
    for muscle, prefixes in muscle_prefixes.items():
        mask = importance_df['feature'].str.lower().str.contains('|'.join(prefixes), na=False)
        if mask.any():
            muscle_importance[muscle] = importance_df.loc[mask, 'importance_mean'].sum()
        else:
            muscle_importance[muscle] = 0.0
            
    return pd.DataFrame(list(muscle_importance.items()), columns=['Muscle', 'Total_Importance'])

def calculate_shap_values(
    model: RandomForestClassifier,
    X: np.ndarray,
    feature_names: List[str],
    max_samples: int = 500
) -> Tuple[Any, Dict]:
    """
    Calculate SHAP values for the Random Forest model.
    
    Args:
        model: Trained Random Forest.
        X: Feature matrix.
        feature_names: List of feature names.
        max_samples: Maximum samples to use for SHAP calculation (for speed).
        
    Returns:
        shap_values: SHAP values object.
        summary_data: Dictionary with summary stats for plotting.
    """
    logger.info(f"Calculating SHAP values (max_samples={max_samples})...")
    
    # Use a subset for speed if dataset is large
    if X.shape[0] > max_samples:
        indices = np.random.choice(X.shape[0], max_samples, replace=False)
        X_sample = X[indices]
        logger.info(f"Using subset of {max_samples} samples for SHAP.")
    else:
        X_sample = X
    
    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X_sample)
    
    # Handle multi-class (binary here)
    if isinstance(shap_values, list):
        # Binary classification: shap_values is a list of arrays (one per class)
        # We are interested in the positive class (usually index 1 for 0/1 labels)
        shap_values = shap_values[1] if len(shap_values) > 1 else shap_values[0]
    
    # Create summary plot data
    summary_data = {
        'values': shap_values,
        'features': X_sample,
        'feature_names': feature_names
    }
    
    logger.info("SHAP values calculated.")
    return shap_values, summary_data

def generate_shap_plots(
    shap_values: np.ndarray,
    X: np.ndarray,
    feature_names: List[str],
    output_dir: str
):
    """
    Generate SHAP summary plot and save to disk.
    """
    os.makedirs(output_dir, exist_ok=True)
    plot_path = os.path.join(output_dir, 'shap_summary.png')
    
    plt.figure(figsize=(12, 10))
    shap.summary_plot(shap_values, X, feature_names=feature_names, plot_size=10, show=False)
    plt.tight_layout()
    plt.savefig(plot_path, dpi=300)
    plt.close()
    
    logger.info(f"SHAP summary plot saved to {plot_path}")
    
    # Also save a bar plot of mean absolute SHAP values
    mean_abs_shap = np.mean(np.abs(shap_values), axis=0)
    indices = np.argsort(mean_abs_shap)[::-1]
    
    plt.figure(figsize=(10, 8))
    plt.barh(range(len(indices)), mean_abs_shap[indices])
    plt.yticks(range(len(indices)), [feature_names[i] for i in indices])
    plt.xlabel('Mean |SHAP Value|')
    plt.title('Top Features by SHAP Importance')
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'shap_barplot.png'), dpi=300)
    plt.close()
    logger.info(f"SHAP bar plot saved to {os.path.join(output_dir, 'shap_barplot.png')}")

def run_hierarchical_analysis(
    model: RandomForestClassifier,
    X: np.ndarray,
    y: np.ndarray,
    feature_names: List[str],
    output_path: str
):
    """
    Perform hierarchical feature addition analysis (FR-007 deviation: dual model strategy).
    Fits Logistic Regression on subsets: Corrugator -> +Zygomaticus -> +Orbicularis.
    Calculates Nagelkerke's R² change.
    """
    logger.info("Running hierarchical feature analysis...")
    
    # Define muscle groups
    muscle_groups = {
        'Corrugator': [f for f in feature_names if f.lower().startswith('corr')],
        'Zygomaticus': [f for f in feature_names if f.lower().startswith('zyg')],
        'Orbicularis': [f for f in feature_names if f.lower().startswith('orb')]
    }
    
    # Verify groups exist
    missing = [k for k, v in muscle_groups.items() if not v]
    if missing:
        logger.warning(f"Missing features for groups: {missing}. Skipping hierarchical analysis.")
        return
    
    # Sequence of feature sets
    sequence = [
        ('Baseline', []),
        ('Corrugator', muscle_groups['Corrugator']),
        ('Corrugator+Zygomaticus', muscle_groups['Corrugator'] + muscle_groups['Zygomaticus']),
        ('Full', muscle_groups['Corrugator'] + muscle_groups['Zygomaticus'] + muscle_groups['Orbicularis'])
    ]
    
    results = []
    baseline_model = None
    baseline_r2 = 0.0
    
    # Train Logistic Regression for each step
    for step_name, features in sequence:
        if not features:
            # Baseline: intercept only (log odds of prior)
            # Nagelkerke R2 for intercept-only is 0
            r2 = 0.0
            results.append({'step': step_name, 'n_features': 0, 'r2': r2, 'r2_change': 0.0})
            continue
        
        X_subset = X[:, [feature_names.index(f) for f in features]]
        
        # Train Logistic Regression
        lr = LogisticRegression(max_iter=1000, random_state=42)
        lr.fit(X_subset, y)
        
        # Predict log-odds and probabilities
        log_odds = lr.decision_function(X_subset)
        probs = lr.predict_proba(X_subset)[:, 1]
        
        # Calculate Nagelkerke's R²
        # R² = (L_full^(2/N) - L_null^(2/N)) / (1 - L_null^(2/N))
        # L_null is likelihood of intercept-only model
        # L_full is likelihood of current model
        
        # Log-likelihood
        eps = 1e-15
        ll_full = np.sum(y * np.log(probs + eps) + (1 - y) * np.log(1 - probs + eps))
        
        # Null model likelihood (prior probability)
        p_null = np.mean(y)
        ll_null = np.sum(y * np.log(p_null + eps) + (1 - y) * np.log(1 - p_null + eps))
        
        n = len(y)
        # Nagelkerke R2
        if ll_null == 0:
            r2 = 0.0
        else:
            # Cox & Snell R2
            r2_cs = 1 - np.exp((2 / n) * (ll_null - ll_full))
            # Max possible R2 for Cox & Snell
            max_r2_cs = 1 - np.exp((2 / n) * ll_null)
            if max_r2_cs == 0:
                r2 = 0.0
            else:
                r2 = r2_cs / max_r2_cs
        
        # Calculate change
        r2_change = r2 - baseline_r2
        baseline_r2 = r2
        
        results.append({
            'step': step_name,
            'n_features': len(features),
            'r2': r2,
            'r2_change': r2_change
        })
        
        logger.info(f"Step {step_name}: R²={r2:.4f}, ΔR²={r2_change:.4f}")
    
    # Save results
    results_df = pd.DataFrame(results)
    results_df.to_csv(output_path, index=False)
    logger.info(f"Hierarchical analysis results saved to {output_path}")
    
    return results_df

def main():
    """
    Main entry point for importance analysis.
    """
    logger.info("Starting importance analysis pipeline...")
    
    # Paths
    model_bundle_path = os.path.join(CONFIG['paths']['models'], 'model_bundle.pkl')
    data_path = CONFIG['paths']['processed']
    output_dir = os.path.join(CONFIG['paths']['processed'], 'importance')
    importance_csv = os.path.join(output_dir, 'permutation_importance.csv')
    muscle_csv = os.path.join(output_dir, 'muscle_importance.csv')
    hierarchical_csv = os.path.join(output_dir, 'hierarchical_analysis.csv')
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Load Model
    if not os.path.exists(model_bundle_path):
        logger.error(f"Model bundle not found at {model_bundle_path}. Run training first.")
        return
    
    logger.info(f"Loading model bundle from {model_bundle_path}")
    bundle = load_model_bundle(model_bundle_path)
    rf_model = bundle['random_forest']
    
    # Load Data
    try:
        X, y, feature_names = load_features_and_labels(data_path)
    except FileNotFoundError as e:
        logger.error(str(e))
        return
    
    # 1. Permutation Importance
    perm_imp = calculate_permutation_importance(rf_model, X, y, feature_names)
    perm_imp.to_csv(importance_csv, index=False)
    logger.info(f"Permutation importance saved to {importance_csv}")
    
    # 2. Group by Muscle
    muscle_imp = group_importance_by_muscle(perm_imp, feature_names)
    muscle_imp.to_csv(muscle_csv, index=False)
    logger.info(f"Muscle importance saved to {muscle_csv}")
    
    # 3. SHAP Analysis
    shap_values, _ = calculate_shap_values(rf_model, X, feature_names)
    generate_shap_plots(shap_values, X, feature_names, output_dir)
    
    # 4. Hierarchical Analysis (Logistic Regression based)
    run_hierarchical_analysis(rf_model, X, y, feature_names, hierarchical_csv)
    
    logger.info("Importance analysis pipeline completed successfully.")

if __name__ == "__main__":
    main()
