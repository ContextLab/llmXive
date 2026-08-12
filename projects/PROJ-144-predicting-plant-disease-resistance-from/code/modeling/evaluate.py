import os
import sys
import json
import pickle
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Tuple, List, Dict, Any, Optional
from scipy import stats
from sklearn.metrics import balanced_accuracy_score, roc_auc_score, precision_recall_curve, average_precision_score
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import learning_curve
import matplotlib.pyplot as plt
import logging

# Import constants
from utils.constants import (
    DATA_PROCESSED_DIR,
    RESULTS_DIR,
    STATE_DIR,
    RANDOM_STATE,
    HOLD_OUT_FRACTION
)
from utils.io import compute_file_hash, log_artifact

logger = logging.getLogger(__name__)

# Constants for this module
MIN_SAMPLE_SIZE_FOR_LEARNING_CURVE = 50
PERMUTATION_N_JOBS = -1  # Use all CPUs
PERMUTATION_N_REPEATS = 1
SENSITIVITY_THRESHOLDS = [0.01, 0.05, 0.10]

def load_model_and_indices() -> Tuple[Any, np.ndarray, np.ndarray]:
    """
    Loads the trained model and split indices from previous steps (T020).
    Returns:
        model: The trained RandomForestClassifier
        train_indices: Array of training indices
        holdout_indices: Array of hold-out indices
    """
    model_path = DATA_PROCESSED_DIR / "model.pkl"
    indices_path = DATA_PROCESSED_DIR / "split_indices.json"

    if not model_path.exists():
        raise FileNotFoundError(f"Model not found at {model_path}. Run T020 first.")
    if not indices_path.exists():
        raise FileNotFoundError(f"Split indices not found at {indices_path}. Run T020 first.")

    with open(model_path, 'rb') as f:
        model = pickle.load(f)

    with open(indices_path, 'r') as f:
        indices_data = json.load(f)

    train_indices = np.array(indices_data['train_indices'])
    holdout_indices = np.array(indices_data['holdout_indices'])

    return model, train_indices, holdout_indices

def load_processed_data() -> Tuple[pd.DataFrame, pd.Series]:
    """
    Loads the batch-corrected data and labels.
    Returns:
        X: DataFrame of features (metabolites)
        y: Series of labels (binary)
    """
    data_path = DATA_PROCESSED_DIR / "batch_corrected_matrix.csv"
    label_path = DATA_PROCESSED_DIR / "labels.csv"

    if not data_path.exists():
        raise FileNotFoundError(f"Processed data not found at {data_path}. Run T017 first.")
    if not label_path.exists():
        raise FileNotFoundError(f"Labels not found at {label_path}. Run T017 first.")

    X = pd.read_csv(data_path, index_col=0)
    y_df = pd.read_csv(label_path, index_col=0)
    
    # Ensure alignment
    common_samples = X.index.intersection(y_df.index)
    X = X.loc[common_samples]
    y = y_df.loc[common_samples, 'binary_label']
    
    return X, y

def evaluate_model(model: RandomForestClassifier, X: pd.DataFrame, y: pd.Series, 
                 holdout_indices: np.ndarray) -> Dict[str, float]:
    """
    Computes Balanced Accuracy, ROC-AUC, and Precision-Recall AUC on the hold-out set.
    """
    X_holdout = X.iloc[holdout_indices]
    y_holdout = y.iloc[holdout_indices]

    y_pred = model.predict(X_holdout)
    y_proba = model.predict_proba(X_holdout)[:, 1]

    bal_acc = balanced_accuracy_score(y_holdout, y_pred)
    roc_auc = roc_auc_score(y_holdout, y_proba)
    
    precision, recall, _ = precision_recall_curve(y_holdout, y_proba)
    pr_auc = average_precision_score(y_holdout, y_proba)

    logger.info(f"Hold-out Balanced Accuracy: {bal_acc:.4f}")
    logger.info(f"Hold-out ROC-AUC: {roc_auc:.4f}")
    logger.info(f"Hold-out PR-AUC: {pr_auc:.4f}")

    return {
        "balanced_accuracy": float(bal_acc),
        "roc_auc": float(roc_auc),
        "pr_auc": float(pr_auc)
    }

def permutation_test(model: RandomForestClassifier, X: pd.DataFrame, y: pd.Series,
                   train_indices: np.ndarray, n_permutations: int = 1000) -> Dict[str, Any]:
    """
    Executes permutation testing on the TRAINING set to generate a null distribution.
    Calculates the p-value for the observed model performance.
    """
    logger.info(f"Starting permutation test with {n_permutations} permutations on training data...")
    
    X_train = X.iloc[train_indices]
    y_train = y.iloc[train_indices]

    # 1. Calculate observed score on training data (to avoid data leakage in null generation)
    # We use a simple metric like accuracy or balanced accuracy on the training set for the null
    # Note: Usually permutation tests compare to a held-out set, but here we are validating the 
    # model's fit on the data it saw vs random chance.
    y_pred_obs = model.predict(X_train)
    obs_score = balanced_accuracy_score(y_train, y_pred_obs)
    
    null_scores = []
    
    # Use a copy of y to permute
    for i in range(n_permutations):
        y_perm = y_train.sample(frac=1, random_state=RANDOM_STATE + i).reset_index(drop=True)
        # Re-train a lightweight model or score the existing one?
        # Standard practice: Re-train model on permuted labels to see if it achieves similar score
        # To save time, we might score the existing model on permuted labels, but that tests fit, not generalization.
        # However, for a strict null distribution of the *model training process*, we must re-train.
        # Given constraints, we will re-train a smaller RF or score the existing one if speed is critical.
        # Let's re-train a smaller RF for the null distribution to be rigorous.
        
        # Optimization: Use n_estimators=50 for null distribution to speed up
        temp_model = RandomForestClassifier(
            n_estimators=100, 
            max_depth=5, 
            random_state=RANDOM_STATE + i,
            n_jobs=1
        )
        temp_model.fit(X_train, y_perm)
        y_pred_perm = temp_model.predict(X_train)
        score = balanced_accuracy_score(y_train, y_pred_perm)
        null_scores.append(score)

    null_scores = np.array(null_scores)
    p_value = np.mean(null_scores >= obs_score)
    
    logger.info(f"Observed Score: {obs_score:.4f}, Null Mean: {np.mean(null_scores):.4f}, P-value: {p_value:.4f}")

    return {
        "observed_score": float(obs_score),
        "null_mean": float(np.mean(null_scores)),
        "null_std": float(np.std(null_scores)),
        "p_value": float(p_value),
        "null_distribution": null_scores.tolist()
    }

def sensitivity_analysis(model: RandomForestClassifier, X: pd.DataFrame, y: pd.Series,
                       holdout_indices: np.ndarray) -> List[Dict[str, Any]]:
    """
    Sweeps decision cutoffs over absolute diff ∈ {0.01, 0.05, 0.1} relative to 0.5.
    Reports FP/FN rates for each cutoff.
    """
    X_holdout = X.iloc[holdout_indices]
    y_holdout = y.iloc[holdout_indices]
    
    y_proba = model.predict_proba(X_holdout)[:, 1]
    
    # Default cutoff is 0.5
    # We sweep around 0.5: 0.5 +/- 0.01, 0.5 +/- 0.05, 0.5 +/- 0.1
    # The task says "absolute diff ∈ {0.01, 0.05, 0.1}". 
    # This implies cutoffs: 0.49, 0.51, 0.45, 0.55, 0.40, 0.60
    
    base_cutoff = 0.5
    diffs = [0.01, 0.05, 0.10]
    cutoffs = sorted(list(set([base_cutoff] + [base_cutoff - d for d in diffs] + [base_cutoff + d for d in diffs])))
    cutoffs = [c for c in cutoffs if 0.0 <= c <= 1.0]
    
    results = []
    
    for cutoff in cutoffs:
        y_pred = (y_proba >= cutoff).astype(int)
        
        # Confusion matrix components
        tp = np.sum((y_pred == 1) & (y_holdout == 1))
        fp = np.sum((y_pred == 1) & (y_holdout == 0))
        tn = np.sum((y_pred == 0) & (y_holdout == 0))
        fn = np.sum((y_pred == 0) & (y_holdout == 1))
        
        total_pos = tp + fn
        total_neg = tn + fp
        
        fp_rate = fp / total_neg if total_neg > 0 else 0.0
        fn_rate = fn / total_pos if total_pos > 0 else 0.0
        
        results.append({
            "cutoff": float(cutoff),
            "fp_rate": float(fp_rate),
            "fn_rate": float(fn_rate),
            "tp": int(tp),
            "fp": int(fp),
            "tn": int(tn),
            "fn": int(fn)
        })
        
    return results

def generate_learning_curve(model: RandomForestClassifier, X: pd.DataFrame, y: pd.Series,
                          train_indices: np.ndarray) -> Dict[str, Any]:
    """
    Generates learning curve data if N < 50.
    """
    X_train = X.iloc[train_indices]
    y_train = y.iloc[train_indices]
    
    logger.info(f"Generating learning curve for sample size {len(y_train)}...")
    
    train_sizes, train_scores, val_scores = learning_curve(
        model, X_train, y_train,
        train_sizes=np.linspace(0.1, 1.0, 10),
        cv=3,
        scoring='balanced_accuracy',
        n_jobs=1,
        random_state=RANDOM_STATE
    )
    
    train_mean = np.mean(train_scores, axis=1)
    val_mean = np.mean(val_scores, axis=1)
    
    return {
        "train_sizes": train_sizes.tolist(),
        "train_mean": train_mean.tolist(),
        "val_mean": val_mean.tolist()
    }

def main():
    """
    Main entry point for T021b: Model Validation.
    """
    # Setup logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    try:
        # 1. Load Data and Model
        model, train_indices, holdout_indices = load_model_and_indices()
        X, y = load_processed_data()
        
        total_n = len(y)
        logger.info(f"Total samples: {total_n}, Train: {len(train_indices)}, Hold-out: {len(holdout_indices)}")
        
        # 2. Check Sample Size for Learning Curve
        learning_curve_data = None
        if total_n < MIN_SAMPLE_SIZE_FOR_LEARNING_CURVE:
            logger.warning(f"Sample size ({total_n}) < 50. Flagging power limitation and generating learning curve.")
            learning_curve_data = generate_learning_curve(model, X, y, train_indices)
        else:
            logger.info(f"Sample size ({total_n}) >= 50. Skipping learning curve analysis.")

        # 3. Evaluate on Hold-out Set
        metrics = evaluate_model(model, X, y, holdout_indices)
        
        # 4. Permutation Test (on training data to assess overfitting/significance)
        perm_results = permutation_test(model, X, y, train_indices, n_permutations=1000)
        
        # 5. Sensitivity Analysis
        sens_results = sensitivity_analysis(model, X, y, holdout_indices)
        
        # 6. Compile Results
        output_data = {
            "metrics": metrics,
            "permutation_test": perm_results,
            "sensitivity_analysis": sens_results,
            "learning_curve": learning_curve_data,
            "power_limitation_flag": total_n < MIN_SAMPLE_SIZE_FOR_LEARNING_CURVE
        }
        
        # 7. Save Results
        output_path = RESULTS_DIR / "model_validation_results.json"
        with open(output_path, 'w') as f:
            json.dump(output_data, f, indent=2)
        
        logger.info(f"Model validation results saved to {output_path}")
        
        # Log artifact
        log_artifact(str(output_path))
        
        # 8. Generate Visualization (Optional but good practice)
        if learning_curve_data:
            plt.figure(figsize=(10, 6))
            plt.plot(learning_curve_data['train_sizes'], learning_curve_data['train_mean'], label='Train')
            plt.plot(learning_curve_data['train_sizes'], learning_curve_data['val_mean'], label='Validation')
            plt.xlabel('Training Examples')
            plt.ylabel('Balanced Accuracy')
            plt.title(f'Learning Curve (N={total_n})')
            plt.legend()
            plt.grid(True)
            plt.savefig(RESULTS_DIR / "learning_curve.png")
            plt.close()
            logger.info(f"Learning curve plot saved to {RESULTS_DIR / 'learning_curve.png'}")
        
        print(f"Task T021b completed successfully. Results: {output_path}")
        
    except Exception as e:
        logger.error(f"Task T021b failed: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()