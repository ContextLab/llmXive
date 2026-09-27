import os
import sys
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.metrics import confusion_matrix, accuracy_score, precision_score, recall_score, f1_score

from config import Hyperparameters, ensure_directories

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def calculate_vif(df: pd.DataFrame, features: List[str]) -> Dict[str, float]:
    """
    Calculate Variance Inflation Factor (VIF) for a list of features.
    """
    vif_data = {}
    for feature in features:
        # Create a dataframe with the target feature and all other features
        X = df[features].drop(columns=[feature])
        y = df[feature]
        
        # If X is empty (only one feature), VIF is 1
        if X.empty:
            vif_data[feature] = 1.0
            continue
        
        # Fit OLS to get R-squared
        from sklearn.linear_model import LinearRegression
        model = LinearRegression()
        model.fit(X, y)
        r_squared = model.score(X, y)
        
        # Calculate VIF
        if r_squared == 1.0:
            vif_data[feature] = float('inf')
        else:
            vif_data[feature] = 1.0 / (1.0 - r_squared)
    
    return vif_data

def perform_pca(df: pd.DataFrame, features: List[str]) -> Tuple[pd.DataFrame, Any]:
    """
    Perform PCA on the specified features to reduce collinearity.
    Returns the transformed dataframe and the PCA object.
    """
    from sklearn.decomposition import PCA
    from sklearn.preprocessing import StandardScaler

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(df[features])
    
    pca = PCA()
    X_pca = pca.fit_transform(X_scaled)
    
    # Create dataframe with principal components
    pca_df = pd.DataFrame(X_pca, columns=[f'PC{i+1}' for i in range(X_pca.shape[1])], index=df.index)
    
    # Add back non-feature columns if necessary
    for col in df.columns:
        if col not in features:
            pca_df[col] = df[col]
    
    return pca_df, pca

def multiple_comparison_correction(p_values: List[float], method: str = 'fdr_bh') -> List[float]:
    """
    Apply multiple comparison correction to a list of p-values.
    """
    from statsmodels.stats.multitest import multipletests
    
    if len(p_values) == 0:
        return []
    
    _, corrected_p_values, _, _ = multipletests(p_values, method=method)
    return corrected_p_values.tolist()

def detect_tolerance_proxies(df: pd.DataFrame, proxy_column: str = 'survival_rate') -> bool:
    """
    Check if an independent tolerance proxy (e.g., survival_rate) exists in the dataset.
    """
    if proxy_column in df.columns and not df[proxy_column].isna().all():
        logger.info(f"Independent tolerance proxy '{proxy_column}' detected.")
        return True
    logger.warning(f"No independent tolerance proxy '{proxy_column}' found.")
    return False

def run_sensitivity_analysis(
    model_results_path: str,
    proxy_path: str,
    output_csv_path: str,
    output_fig_path: str
) -> None:
    """
    Run sensitivity analysis on the classification model.
    
    Logic:
    1. Check if an independent tolerance proxy exists (from state/proxy_detection.yaml).
    2. If proxy exists:
       - Sweep predicted probability threshold.
       - Calculate accuracy, precision, recall, F1, FPR, FNR for each step.
       - Ensure ±0.05 sweep around baseline is reported.
    3. If no proxy:
       - Generate CSV with "N/A" and justification.
       - Do not generate a figure.
    
    Outputs:
    - data/derived/sensitivity_sweep_results.csv
    - results/figures/sensitivity_curve.png (if applicable)
    """
    from pathlib import Path
    import yaml
    
    # Ensure directories exist
    ensure_directories()
    
    # 1. Check for proxy
    proxy_exists = False
    proxy_col = 'survival_rate' # Default proxy column name as per spec
    
    # Load proxy detection status from state/proxy_detection.yaml
    try:
        proxy_file = Path("state/proxy_detection.yaml")
        if proxy_file.exists():
            with open(proxy_file, 'r') as f:
                proxy_data = yaml.safe_load(f)
                proxy_exists = proxy_data.get('has_proxy', False)
                if proxy_exists and 'proxy_column' in proxy_data:
                    proxy_col = proxy_data['proxy_column']
        else:
            logger.warning("state/proxy_detection.yaml not found. Assuming no proxy.")
    except Exception as e:
        logger.error(f"Error reading proxy detection file: {e}")
        proxy_exists = False

    output_csv = Path(output_csv_path)
    output_fig = Path(output_fig_path)

    if not proxy_exists:
        # Case: No proxy found -> Skip analysis
        logger.info("No independent tolerance proxy found. Skipping sensitivity analysis.")
        
        # Create N/A result
        na_results = pd.DataFrame([{
            'threshold': 'N/A',
            'accuracy': 'N/A',
            'precision': 'N/A',
            'recall': 'N/A',
            'f1_score': 'N/A',
            'false_positive_rate': 'N/A',
            'false_negative_rate': 'N/A',
            'justification': 'Classification model not built due to lack of independent tolerance proxy (Plan: No Circular Classification). Sensitivity analysis not applicable.'
        }])
        
        na_results.to_csv(output_csv, index=False)
        logger.info(f"Wrote N/A sensitivity results to {output_csv}")
        
        # Do not generate figure
        if output_fig.exists():
            output_fig.unlink()
        return

    # Case: Proxy exists -> Run sensitivity analysis
    logger.info("Independent tolerance proxy found. Running sensitivity analysis.")
    
    # Load classification model results
    # We expect a file containing predicted probabilities and true labels
    # Assuming the classification model output is in data/derived/classification_results.csv
    # which contains columns: 'true_label', 'predicted_prob'
    # If the file doesn't exist, we might need to infer from model_results or re-run, 
    # but per spec T027b generates the model. We assume T027b also generates the predictions file
    # or we load from a standard location.
    
    # Let's assume the predictions are stored in data/derived/classification_predictions.csv
    # Structure: species, true_label (0/1), predicted_prob (0-1)
    pred_file = Path("data/derived/classification_predictions.csv")
    
    if not pred_file.exists():
        # Fallback: Try to load from model_results if it has probabilities
        # But spec says T027b outputs model.pkl. We need to load and predict.
        # However, the task description for T028 implies we have the results to sweep.
        # If the predictions file is missing, we must halt or try to generate it.
        # Given the strict "Real Data Only" rule, we cannot fabricate.
        # We will attempt to load the model and generate predictions if the file is missing,
        # assuming the model file exists from T027b.
        model_file = Path("data/derived/classification_model.pkl")
        if model_file.exists():
            import joblib
            from sklearn.preprocessing import StandardScaler
            # We need features and true labels to generate predictions
            # This is complex without knowing the exact feature set used in T027b.
            # To keep it robust, we will assume the predictions file exists as a prerequisite
            # or fail loudly.
            logger.error("Classification predictions file not found. Cannot run sensitivity analysis.")
            raise FileNotFoundError(f"Predictions file {pred_file} not found. T027b must generate this.")
        else:
            logger.error("Classification model file not found. Cannot run sensitivity analysis.")
            raise FileNotFoundError(f"Model file {model_file} not found.")
    
    df_preds = pd.read_csv(pred_file)
    
    # Validate columns
    required_cols = ['true_label', 'predicted_prob']
    if not all(col in df_preds.columns for col in required_cols):
        logger.error(f"Predictions file missing required columns: {required_cols}")
        raise ValueError(f"Predictions file must contain columns: {required_cols}")
    
    true_labels = df_preds['true_label'].values
    probs = df_preds['predicted_prob'].values
    
    # Define threshold range
    # Sweep from 0.0 to 1.0 in uniform increments (e.g., 0.01)
    thresholds = np.arange(0.0, 1.001, 0.01)
    
    # Ensure baseline (optimal F1 or 0.5) is covered
    # Calculate optimal F1 threshold first
    best_f1 = -1
    best_thresh = 0.5
    
    temp_metrics = []
    for t in thresholds:
        preds = (probs >= t).astype(int)
        if len(np.unique(preds)) < 2: # Need both classes present for some metrics
            # If only one class predicted, F1 might be 0 or undefined
            pass
        
        tn, fp, fn, tp = confusion_matrix(true_labels, preds).ravel()
        # Avoid division by zero
        acc = accuracy_score(true_labels, preds)
        prec = precision_score(true_labels, preds, zero_division=0)
        rec = recall_score(true_labels, preds, zero_division=0)
        f1 = f1_score(true_labels, preds, zero_division=0)
        fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
        fnr = fn / (fn + tp) if (fn + tp) > 0 else 0.0
        
        if f1 > best_f1:
            best_f1 = f1
            best_thresh = t
        
        temp_metrics.append({
            'threshold': t,
            'accuracy': acc,
            'precision': prec,
            'recall': rec,
            'f1_score': f1,
            'false_positive_rate': fpr,
            'false_negative_rate': fnr
        })
    
    # Ensure ±0.05 around baseline is explicitly included
    baseline_low = max(0.0, best_thresh - 0.05)
    baseline_high = min(1.0, best_thresh + 0.05)
    
    # If our step size (0.01) already covers this, we are good.
    # We will just ensure the results are sorted and saved.
    
    results_df = pd.DataFrame(temp_metrics)
    
    # Filter to ensure we have the baseline range if not covered by step size (unlikely with 0.01)
    # But we will just save all.
    
    # Save to CSV
    results_df.to_csv(output_csv, index=False)
    logger.info(f"Sensitivity analysis results saved to {output_csv}")
    
    # Generate Figure
    plt.figure(figsize=(10, 6))
    
    plt.plot(results_df['threshold'], results_df['f1_score'], label='F1 Score', marker='o')
    plt.plot(results_df['threshold'], results_df['accuracy'], label='Accuracy', marker='s')
    plt.plot(results_df['threshold'], results_df['false_positive_rate'], label='FPR', marker='^')
    plt.plot(results_df['threshold'], results_df['false_negative_rate'], label='FNR', marker='d')
    
    plt.axvline(x=best_thresh, color='r', linestyle='--', label=f'Optimal Threshold ({best_thresh:.2f})')
    
    plt.xlabel('Threshold')
    plt.ylabel('Score / Rate')
    plt.title('Sensitivity Analysis: Classification Model Performance vs Threshold')
    plt.legend()
    plt.grid(True)
    
    # Ensure results directory exists
    output_fig.parent.mkdir(parents=True, exist_ok=True)
    
    plt.savefig(output_fig)
    plt.close()
    logger.info(f"Sensitivity curve saved to {output_fig}")

def main():
    """
    Main entry point for running sensitivity analysis.
    """
    # Paths
    proxy_path = "state/proxy_detection.yaml"
    output_csv = "data/derived/sensitivity_sweep_results.csv"
    output_fig = "results/figures/sensitivity_curve.png"
    
    try:
        run_sensitivity_analysis(
            model_results_path="data/derived/model_results.csv",
            proxy_path=proxy_path,
            output_csv_path=output_csv,
            output_fig_path=output_fig
        )
        logger.info("Sensitivity analysis completed successfully.")
    except Exception as e:
        logger.error(f"Sensitivity analysis failed: {e}")
        raise

if __name__ == "__main__":
    main()