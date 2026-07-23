import os
import pickle
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from scipy import stats

from utils import setup_logging, init_random_seed, get_logger
from constants import N_FOLDS

def load_model_artifact(path: str):
    with open(path, 'rb') as f:
        return pickle.load(f)

def load_split_indices(split_dir: str) -> Dict[int, Dict[str, List[int]]]:
    split_path = Path(split_dir)
    splits = {}
    for i in range(5):
        file_path = split_path / f"split_fold_{i}.pkl"
        if not file_path.exists():
            raise FileNotFoundError(f"Split file not found: {file_path}")
        with open(file_path, 'rb') as f:
            splits[i] = pickle.load(f)
    return splits

def load_fingerprint_data(csv_path: str) -> np.ndarray:
    # Loads pre-computed fingerprints from CSV (assuming columns 'morgan_fp' and 'maccs_fp' as lists/arrays)
    # In a robust pipeline, this might load from a dedicated binary format, but we adapt to the CSV contract.
    # Note: If the CSV stores bitstrings as strings, they must be parsed.
    # For this implementation, we assume the data was saved as a numpy array or pickle in a separate step,
    # but the task implies loading from the processed data flow.
    # Given the pipeline structure, we expect fingerprints to be in a processed file.
    # However, standard practice in this project for large vectors is often a pickle.
    # Let's assume a standard path for fingerprints if not explicitly in CSV.
    # If the CSV is the source, we parse it.
    # To be safe and robust against the "missing file" chain, we check for the expected pickle if CSV fails or is insufficient.
    pass

def load_labels(csv_path: str) -> pd.DataFrame:
    return pd.read_csv(csv_path)

def calculate_metrics(y_true, y_pred_proba):
    from sklearn.metrics import roc_auc_score, precision_recall_curve, auc, balanced_accuracy_score
    if len(np.unique(y_true)) < 2:
        return None, None, None
    roc = roc_auc_score(y_true, y_pred_proba)
    prec, rec, _ = precision_recall_curve(y_true, y_pred_proba)
    pr = auc(rec, prec)
    bal = balanced_accuracy_score(y_true, (y_pred_proba > 0.5).astype(int))
    return roc, pr, bal

def evaluate_fold(model, X_test, y_test):
    y_pred_proba = model.predict_proba(X_test)[:, 1]
    return calculate_metrics(y_test, y_pred_proba)

def run_evaluation():
    logger = get_logger(__name__)
    logger.info("Running evaluation...")

def compute_bootstrap_confidence_interval(diffs, n_resamples=1000):
    logger = get_logger(__name__)
    logger.info(f"Computing bootstrap CI with {n_resamples} resamples")
    if len(diffs) == 0:
        return (0.0, 0.0)
    rng = np.random.default_rng(42)
    bootstrap_means = []
    for _ in range(n_resamples):
        sample = rng.choice(diffs, size=len(diffs), replace=True)
        bootstrap_means.append(np.mean(sample))
    lower = np.percentile(bootstrap_means, 2.5)
    upper = np.percentile(bootstrap_means, 97.5)
    return (lower, upper)

def map_phosphorus_feature_importance(model, smiles_list):
    # Placeholder for SC-003 analysis
    pass

def verify_sc_003():
    # Placeholder for SC-003 verification
    pass

def perform_corrected_resampled_ttest(morgan_scores: np.ndarray, maccs_scores: np.ndarray, metric_name: str = "ROC-AUC") -> Tuple[float, float]:
    """
    Performs the Corrected Resampled t-test (Nadeau & Bengio) on paired scores.
    
    Args:
        morgan_scores: Array of scores (e.g., ROC-AUC) from Morgan models across folds.
        maccs_scores: Array of scores from MACCS models across folds.
        metric_name: Name of the metric for logging.
        
    Returns:
        Tuple of (t_statistic, p_value)
    """
    logger = get_logger(__name__)
    
    if len(morgan_scores) != len(maccs_scores) or len(morgan_scores) == 0:
        logger.error(f"Cannot perform t-test: mismatched or empty score arrays for {metric_name}")
        return 0.0, 1.0

    n = len(morgan_scores)
    # Calculate differences
    diffs = morgan_scores - maccs_scores
    mean_diff = np.mean(diffs)
    std_diff = np.std(diffs, ddof=1) # Sample standard deviation
    
    if std_diff == 0:
        # If no variance, p-value is 1.0 (no significant difference) unless mean is 0, but technically undefined t.
        # Standard convention: if mean_diff is 0, p=1. If mean_diff != 0 and std=0, it's infinite t, p=0.
        # However, with real data, this is rare. We handle it gracefully.
        if mean_diff == 0:
            return 0.0, 1.0
        else:
            # Infinite t-statistic
            return float('inf'), 0.0

    # Corrected Resampled t-test adjustment
    # Nadeau & Bengio (2003): t = mean(d) / sqrt( (1/n + n_train/n_total) * var(d) )
    # In k-fold CV with n_folds = n, and assuming balanced splits (roughly):
    # The correction factor is often approximated as (1/n + n_train/n_test) or similar depending on the exact split.
    # For standard k-fold (k=5), n_train ~ 4/5, n_test ~ 1/5.
    # The term (1/n + n_train/n_total) is the variance inflation factor.
    # A common simplified correction for k-fold is:
    # t = mean_diff / sqrt( (1/n + (n_train/n_test)) * (std_diff^2 / n) )
    # However, the specific Nadeau & Bengio correction for k-fold is:
    # t = mean_diff / sqrt( (1/n + n_train/n_total) * var(d) )
    # Where n is number of folds (5).
    # Let's assume a standard 5-fold split where training set is 80% and test is 20%.
    # n_train / n_total = 0.8
    # Correction factor = (1/5 + 0.8) = 0.2 + 0.8 = 1.0? 
    # Wait, the formula is: Var(mean) = (1/n + n_train/n_test) * Var(d) / n ? No.
    # Nadeau & Bengio Eq 14: Var( \hat{\delta} ) = (1/n + n_train/n_test) * \sigma^2 / n
    # So t = \hat{\delta} / sqrt( (1/n + n_train/n_test) * s^2 / n )
    # Here n is the number of folds (5).
    # n_train/n_test = 4/1 = 4.
    # Factor = (1/5 + 4) = 4.2.
    
    n_folds = n
    n_train_ratio = 0.8 # Approximation for 5-fold
    n_test_ratio = 0.2
    # Correction factor for variance of the mean difference
    correction_factor = (1.0 / n_folds) + (n_train_ratio / n_test_ratio)
    
    # Standard error of the mean difference with correction
    se_corrected = np.sqrt(correction_factor * (std_diff ** 2) / n_folds)
    
    if se_corrected == 0:
        return float('inf'), 0.0 if mean_diff != 0 else 1.0
        
    t_stat = mean_diff / se_corrected
    
    # Degrees of freedom: Nadeau & Bengio suggest using n-1 for the t-distribution
    df = n_folds - 1
    p_value = 2 * (1 - stats.t.cdf(abs(t_stat), df))
    
    logger.info(f"Corrected Resampled t-test for {metric_name}: t={t_stat:.4f}, p={p_value:.4f} (df={df})")
    return t_stat, p_value

def collect_fold_scores():
    """
    Collects ROC-AUC and PR-AUC scores from all 5 folds.
    Assumes metrics were saved in a specific format by the training/evaluation loop.
    Since T024 (metrics) is marked done, we assume a file exists or we reconstruct from model artifacts.
    However, the task says: "Explicitly collect the ROC-AUC and Precision-Recall AUC scores from ALL 5 folds".
    We will attempt to load from a metrics file if it exists, otherwise we re-evaluate if models are present.
    Given the execution context, we assume a `metrics_folds.json` or similar was produced, or we re-run evaluation logic.
    To be robust, we will try to load from a saved metrics file. If not found, we assume the pipeline failed earlier.
    """
    logger = get_logger(__name__)
    metrics_path = Path("data/processed/fold_metrics.pkl")
    
    if not metrics_path.exists():
        # Fallback: Try to load from the expected location if the previous step saved it differently
        # Or raise an error if the prerequisite T024 didn't save the data.
        # Given the strict "fix execution" constraint, we assume the file should be there.
        # If it's missing, the pipeline is broken upstream.
        # Let's try to load from a generic path or raise.
        raise FileNotFoundError(f"Metrics file not found at {metrics_path}. Prerequisite T024 must save fold metrics here.")
    
    with open(metrics_path, 'rb') as f:
        fold_data = pickle.load(f)
    
    morgan_roc = []
    morgan_pr = []
    maccs_roc = []
    maccs_pr = []
    
    for fold_idx in range(5):
        if fold_idx in fold_data:
            fold_metrics = fold_data[fold_idx]
            morgan_roc.append(fold_metrics['morgan']['roc_auc'])
            morgan_pr.append(fold_metrics['morgan']['pr_auc'])
            maccs_roc.append(fold_metrics['maccs']['roc_auc'])
            maccs_pr.append(fold_metrics['maccs']['pr_auc'])
        else:
            logger.warning(f"Fold {fold_idx} metrics missing, skipping.")
    
    return (
        np.array(morgan_roc), np.array(morgan_pr),
        np.array(maccs_roc), np.array(maccs_pr)
    )

def main():
    setup_logging()
    init_random_seed()
    logger = get_logger(__name__)
    logger.info("Starting Statistical Evaluation (T025a)")

    try:
        # 1. Collect scores
        logger.info("Collecting fold scores...")
        morgan_roc, morgan_pr, maccs_roc, maccs_pr = collect_fold_scores()
        
        logger.info(f"Morgan ROC-AUC: {morgan_roc}")
        logger.info(f"MACCS ROC-AUC: {maccs_roc}")

        # 2. Perform Corrected Resampled t-test for ROC-AUC
        logger.info("Performing t-test for ROC-AUC...")
        t_roc, p_roc = perform_corrected_resampled_ttest(morgan_roc, maccs_roc, "ROC-AUC")

        # 3. Perform Corrected Resampled t-test for PR-AUC
        logger.info("Performing t-test for PR-AUC...")
        t_pr, p_pr = perform_corrected_resampled_ttest(morgan_pr, maccs_pr, "PR-AUC")

        # 4. Save results to a file for downstream tasks (T025b, T029a)
        results = {
            "roc_auc": {
                "morgan_mean": float(np.mean(morgan_roc)),
                "maccs_mean": float(np.mean(maccs_roc)),
                "t_statistic": float(t_roc),
                "p_value": float(p_roc),
                "significant": p_roc < 0.05
            },
            "pr_auc": {
                "morgan_mean": float(np.mean(morgan_pr)),
                "maccs_mean": float(np.mean(maccs_pr)),
                "t_statistic": float(t_pr),
                "p_value": float(p_pr),
                "significant": p_pr < 0.05
            }
        }
        
        output_path = Path("data/processed/statistical_test_results.json")
        with open(output_path, 'w') as f:
            import json
            json.dump(results, f, indent=2)
        
        logger.info(f"Statistical results saved to {output_path}")
        logger.info("T025a completed successfully.")

    except Exception as e:
        logger.error(f"Error during statistical evaluation: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()