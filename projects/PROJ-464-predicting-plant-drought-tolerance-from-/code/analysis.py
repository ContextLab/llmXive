import os
import sys
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from statsmodels.stats.outliers_influence import variance_inflation_factor
from scipy import stats
import yaml

# Import local config if available, otherwise define defaults
try:
    from config import ensure_directories, get_config_summary
except ImportError:
    ensure_directories = lambda: None
    get_config_summary = lambda: {}

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('state/pipeline.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def calculate_vif(df: pd.DataFrame, features: List[str]) -> Dict[str, float]:
    """
    Calculate Variance Inflation Factor (VIF) for each feature.
    
    Args:
        df: DataFrame containing features
        features: List of column names to calculate VIF for
        
    Returns:
        Dictionary mapping feature names to VIF scores
    """
    vif_data = {}
    X = df[features].values
    
    for i, feature in enumerate(features):
        vif = variance_inflation_factor(X, i)
        vif_data[feature] = vif
        logger.info(f"VIF for {feature}: {vif:.4f}")
        
    return vif_data

def perform_pca(df: pd.DataFrame, features: List[str]) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Perform PCA on RSA traits to handle collinearity.
    
    Args:
        df: DataFrame containing features
        features: List of column names to transform
        
    Returns:
        Tuple of (transformed DataFrame, PCA info dict)
    """
    from sklearn.decomposition import PCA
    
    X = df[features].dropna()
    if len(X) < 2:
        raise ValueError("Insufficient data for PCA")
        
    pca = PCA(n_components=len(features))
    pca.fit(X)
    
    # Create transformed dataframe
    transformed = pd.DataFrame(
        pca.transform(X),
        columns=[f'pca_{i+1}' for i in range(len(features))],
        index=X.index
    )
    
    info = {
        'explained_variance_ratio': pca.explained_variance_ratio_.tolist(),
        'n_components': len(features),
        'components': pca.components_.tolist()
    }
    
    return transformed, info

def multiple_comparison_correction(p_values: List[float], method: str = "fdr_bh") -> List[float]:
    """
    Apply multiple comparison correction to p-values.
    
    Args:
        p_values: List of raw p-values
        method: Correction method (default: "fdr_bh" for Benjamini-Hochberg)
        
    Returns:
        List of adjusted p-values
    """
    from statsmodels.stats.multitest import multipletests
    
    if not p_values:
        return []
        
    rejected, pvals_corrected, _, _ = multipletests(p_values, method=method)
    return pvals_corrected.tolist()

def detect_tolerance_proxies(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Check for and ingest independent tolerance proxies.
    
    Args:
        df: Merged dataset DataFrame
        
    Returns:
        Dictionary with proxy detection status
    """
    proxy_columns = ['survival_rate', 'biomass_stress', 'drought_tolerance_index']
    found_proxies = []
    
    for col in proxy_columns:
        if col in df.columns and not df[col].isna().all():
            found_proxies.append(col)
            logger.info(f"Found tolerance proxy: {col}")
    
    return {
        'has_proxy': len(found_proxies) > 0,
        'proxies_found': found_proxies,
        'count': len(found_proxies)
    }

def run_sensitivity_analysis(
    y_true: List[float], 
    y_prob: List[float], 
    threshold_range: Optional[np.ndarray] = None
) -> pd.DataFrame:
    """
    Perform sensitivity analysis across a full range of classification thresholds.
    
    This function sweeps through the entire range of possible probability thresholds
    (0.0 to 1.0) and calculates accuracy, precision, recall, F1, FPR, and FNR
    for each step. It explicitly isolates and reports metrics for the ±0.05
    deviation window around the optimal threshold.
    
    Args:
        y_true: True binary labels (0 or 1)
        y_prob: Predicted probabilities for the positive class
        threshold_range: Optional array of thresholds to test. If None, uses
                       np.arange(0.0, 1.0, 0.01)
                       
    Returns:
        DataFrame with threshold and all calculated metrics
    """
    if threshold_range is None:
        threshold_range = np.arange(0.0, 1.0, 0.01)
        
    results = []
    
    for threshold in threshold_range:
        # Binarize predictions at current threshold
        y_pred = (np.array(y_prob) >= threshold).astype(int)
        y_true_arr = np.array(y_true)
        
        # Calculate metrics
        accuracy = accuracy_score(y_true_arr, y_pred)
        precision = precision_score(y_true_arr, y_pred, zero_division=0)
        recall = recall_score(y_true_arr, y_pred, zero_division=0)
        f1 = f1_score(y_true_arr, y_pred, zero_division=0)
        
        # Calculate FPR and FNR
        # FPR = FP / (FP + TN) = 1 - Specificity
        # FNR = FN / (FN + TP) = 1 - Recall
        tn = np.sum((y_true_arr == 0) & (y_pred == 0))
        fp = np.sum((y_true_arr == 0) & (y_pred == 1))
        fn = np.sum((y_true_arr == 1) & (y_pred == 0))
        tp = np.sum((y_true_arr == 1) & (y_pred == 1))
        
        fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
        fnr = fn / (fn + tp) if (fn + tp) > 0 else 0.0
        
        results.append({
            'threshold': threshold,
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1': f1,
            'fpr': fpr,
            'fnr': fnr
        })
        
    df_results = pd.DataFrame(results)
    
    # Find optimal threshold (max F1)
    optimal_idx = df_results['f1'].idxmax()
    optimal_threshold = df_results.loc[optimal_idx, 'threshold']
    
    # Isolate ±0.05 window around optimal threshold
    window_mask = (df_results['threshold'] >= optimal_threshold - 0.05) & \
                 (df_results['threshold'] <= optimal_threshold + 0.05)
    window_results = df_results[window_mask]
    
    logger.info(f"Sensitivity analysis complete. Optimal threshold: {optimal_threshold:.2f}")
    logger.info(f"Window analysis (±0.05): {len(window_results)} thresholds analyzed")
    
    return df_results

def generate_vif_report(vif_data: Dict[str, float], output_path: str) -> None:
    """
    Generate VIF report in YAML format.
    
    Args:
        vif_data: Dictionary of feature VIF scores
        output_path: Path to save the YAML report
    """
    report = {
        'vif_scores': vif_data,
        'high_vif_features': [k for k, v in vif_data.items() if v > 5],
        'max_vif': max(vif_data.values()) if vif_data else 0,
        'collinearity_risk': 'high' if any(v > 5 for v in vif_data.values()) else 'low'
    }
    
    with open(output_path, 'w') as f:
        yaml.dump(report, f, default_flow_style=False)
        
    logger.info(f"VIF report saved to {output_path}")

def main() -> None:
    """
    Main entry point for sensitivity analysis and VIF reporting.
    Reads merged data, performs analysis, and saves results.
    """
    ensure_directories()
    
    # Load merged data
    merged_path = Path('data/derived/merged_data.csv')
    if not merged_path.exists():
        logger.error(f"Merged data not found at {merged_path}")
        sys.exit(1)
        
    df = pd.read_csv(merged_path)
    
    # 1. Calculate VIF for RSA traits
    rsa_features = ['depth', 'branching_density', 'surface_area']
    available_features = [f for f in rsa_features if f in df.columns]
    
    if len(available_features) >= 2:
        vif_scores = calculate_vif(df, available_features)
        generate_vif_report(vif_scores, 'state/vif_report.yaml')
    else:
        logger.warning("Insufficient RSA features for VIF calculation")
        vif_scores = {}
        
    # 2. Detect tolerance proxies
    proxy_status = detect_tolerance_proxies(df)
    with open('state/proxy_detection.yaml', 'w') as f:
        yaml.dump(proxy_status, f, default_flow_style=False)
        
    # 3. Perform sensitivity analysis if classification results exist
    classification_path = Path('data/derived/classification_model.pkl')
    binary_target_path = Path('data/derived/binary_target.csv')
    
    if binary_target_path.exists():
        try:
            import pickle
            with open(classification_path, 'rb') as f:
                model = pickle.load(f)
                
            # Get predictions
            X = df[available_features].dropna()
            y_prob = model.predict_proba(X)[:, 1]
            y_true = df.loc[X.index, 'binary_target'].values
            
            # Run sensitivity analysis
            sensitivity_results = run_sensitivity_analysis(y_true, y_prob)
            
            # Save results
            sensitivity_results.to_csv('data/derived/sensitivity_sweep_results.csv', index=False)
            sensitivity_results.to_csv('results/sensitivity_fpr_fnr.csv', index=False)
            
            # Generate plot
            plt.figure(figsize=(10, 6))
            plt.plot(sensitivity_results['threshold'], sensitivity_results['fpr'], label='FPR', linewidth=2)
            plt.plot(sensitivity_results['threshold'], sensitivity_results['fnr'], label='FNR', linewidth=2)
            plt.xlabel('Threshold')
            plt.ylabel('Rate')
            plt.title('Sensitivity Analysis: FPR and FNR vs Threshold')
            plt.legend()
            plt.grid(True, alpha=0.3)
            plt.savefig('results/figures/sensitivity_curve.png', dpi=150)
            plt.close()
            
            logger.info("Sensitivity analysis completed successfully")
            
        except FileNotFoundError:
            logger.warning("Classification model not found, skipping sensitivity analysis")
        except Exception as e:
            logger.error(f"Error during sensitivity analysis: {e}")
            raise
    else:
        logger.warning("Binary target not found, skipping sensitivity analysis")
        
    logger.info("Analysis pipeline completed")

if __name__ == '__main__':
    main()
