import os
import sys
import json
import logging
import argparse
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.cross_decomposition import PLSRegression
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from scipy import stats
from typing import Dict, List, Tuple, Optional, Any

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('state/regression_analysis.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def load_data(networks_path: str, energy_path: str) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Load network metrics and energy decay results."""
    logger.info(f"Loading network data from {networks_path}")
    networks_df = pd.read_csv(networks_path)
    
    logger.info(f"Loading energy decay data from {energy_path}")
    energy_df = pd.read_csv(energy_path)
    
    return networks_df, energy_df

def merge_data(networks_df: pd.DataFrame, energy_df: pd.DataFrame) -> pd.DataFrame:
    """Merge network metrics with energy decay results on graph_id."""
    logger.info("Merging network and energy data")
    merged_df = pd.merge(
        networks_df,
        energy_df,
        left_on='id',
        right_on='graph_id',
        how='inner'
    )
    logger.info(f"Merged dataset size: {len(merged_df)} rows")
    return merged_df

def filter_resonant(dataset: pd.DataFrame) -> pd.DataFrame:
    """Filter out rows where status='resonant'."""
    logger.info("Filtering out resonant instances")
    filtered_df = dataset[dataset['status'] != 'resonant'].copy()
    logger.info(f"Filtered dataset size: {len(filtered_df)} rows (removed {len(dataset) - len(filtered_df)} resonant)")
    return filtered_df

def perform_pca(metrics_df: pd.DataFrame, n_components: int = 2) -> Tuple[Dict[str, Any], PCA]:
    """Perform PCA on topological metrics and return loadings."""
    logger.info("Performing PCA on topological metrics")
    
    # Select metric columns (exclude non-metric columns)
    metric_cols = [col for col in metrics_df.columns if col not in ['id', 'class', 'graph_id', 'status', 'decay_rate', 'r_squared']]
    X = metrics_df[metric_cols].dropna()
    
    if X.shape[0] == 0:
        raise ValueError("No valid metric data available for PCA")
    
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    pca = PCA(n_components=n_components)
    pca.fit(X_scaled)
    
    # Calculate loadings (correlation between original variables and PCs)
    loadings = {}
    for i, pc in enumerate(['PC1', 'PC2'][:n_components]):
        loadings[pc] = {}
        for j, col in enumerate(X.columns):
          loadings[pc][col] = float(pca.components_[i, j] * np.sqrt(pca.explained_variance_[i]))
    
    logger.info(f"PCA explained variance: {pca.explained_variance_ratio_}")
    
    return loadings, pca

def perform_pls_regression(X: np.ndarray, y: np.ndarray, n_components: int = 2) -> Dict[str, Any]:
    """Perform PLS Regression and return coefficients, VIP scores, and p-values."""
    logger.info("Performing PLS Regression")
    
    scaler_X = StandardScaler()
    scaler_y = StandardScaler()
    
    X_scaled = scaler_X.fit_transform(X)
    y_scaled = scaler_y.fit_transform(y.reshape(-1, 1)).ravel()
    
    pls = PLSRegression(n_components=n_components)
    pls.fit(X_scaled, y_scaled)
    
    # Calculate VIP scores
    t = pls.x_scores_
    w = pls.x_weights_
    q = pls.y_loadings_
    
    p, h = w.shape
    vip_scores = np.zeros(p)
    s = np.diag(t.T @ t @ q.T @ q).reshape(-1, 1)
    total_s = np.sum(s)
    
    for i in range(p):
        weight = np.array([ (w[i, j] ** 2) * np.sum(s[:j+1]) for j in range(h) ])
        vip_scores[i] = np.sqrt(p * np.sum(weight) / total_s)
    
    # Calculate coefficients (on original scale)
    coeffs = scaler_X.scale_ * pls.coef_.ravel() / scaler_y.scale_
    
    # Calculate p-values using permutation test (simplified)
    p_values = np.zeros(p)
    for i in range(p):
        # Simple permutation test
        perm_coeffs = []
        for _ in range(100):
            y_perm = np.random.permutation(y_scaled)
            pls_perm = PLSRegression(n_components=n_components)
            pls_perm.fit(X_scaled, y_perm)
            perm_coef = scaler_X.scale_[i] * pls_perm.coef_[i] / scaler_y.scale_
            perm_coeffs.append(abs(perm_coef))
        
        observed_coef = abs(coeffs[i])
        p_values[i] = np.sum(np.array(perm_coeffs) >= observed_coef) / 100
    
    return {
        'coefficients': coeffs.tolist(),
        'vip_scores': vip_scores.tolist(),
        'p_values': p_values.tolist(),
        'explained_variance_x': pls.x_explained_variance_.tolist(),
        'explained_variance_y': pls.y_explained_variance_.tolist()
    }

def calculate_vif(X: pd.DataFrame) -> Dict[str, float]:
    """Calculate Variance Inflation Factor for each predictor."""
    logger.info("Calculating VIF for predictors")
    
    vif_data = {}
    for i, col in enumerate(X.columns):
        y = X[col]
        X_other = X.drop(columns=[col])
        
        if X_other.shape[1] > 0:
            model = stats.linregress(X_other.values, y.values)
            # R-squared from auxiliary regression
            r_squared = model.rvalue ** 2 if len(model.rvalue.shape) == 0 else model.rvalue[0] ** 2
            vif = 1 / (1 - r_squared)
        else:
            vif = 1.0
        
        vif_data[col] = vif
        logger.info(f"VIF for {col}: {vif:.4f}")
    
    return vif_data

def bonferroni_correction(p_values: List[float], alpha: float = 0.05) -> List[Tuple[str, float, bool]]:
    """Apply Bonferroni correction to p-values."""
    logger.info(f"Applying Bonferroni correction (alpha={alpha})")
    
    n = len(p_values)
    corrected_alpha = alpha / n if n > 0 else alpha
    corrected_p_values = [p * n for p in p_values]
    
    results = []
    for i, (p, corrected_p) in enumerate(zip(p_values, corrected_p_values)):
        is_significant = corrected_p < alpha
        results.append((f"feature_{i}", corrected_p, is_significant))
    
    logger.info(f"Significant features after correction: {sum(1 for _, _, sig in results if sig)}")
    return results

def generate_loadings_report(loadings: Dict[str, Any], output_path: str) -> None:
    """Generate markdown table of PC loadings."""
    logger.info(f"Generating loadings report to {output_path}")
    
    with open(output_path, 'w') as f:
        f.write("# PCA Loadings Report\n\n")
        f.write("## PC1 and PC2 Loadings for Topological Metrics\n\n")
        f.write("| Metric | PC1 Loading | PC2 Loading | Association PC1 | Association PC2 |\n")
        f.write("|--------|-------------|-------------|-----------------|-----------------|\n")
        
        metrics = list(loadings['PC1'].keys())
        for metric in metrics:
            pc1_loading = loadings['PC1'][metric]
            pc2_loading = loadings['PC2'][metric]
            
            # Determine association strength
            pc1_assoc = "Strong" if abs(pc1_loading) > 0.5 else ("Moderate" if abs(pc1_loading) > 0.3 else "Weak")
            pc2_assoc = "Strong" if abs(pc2_loading) > 0.5 else ("Moderate" if abs(pc2_loading) > 0.3 else "Weak")
            
            f.write(f"| {metric} | {pc1_loading:.4f} | {pc2_loading:.4f} | {pc1_assoc} | {pc2_assoc} |\n")
    
    logger.info("Loadings report generated successfully")

def generate_interpretation_report(loadings: Dict[str, Any], output_path: str) -> None:
    """Generate interpretation report based on loading thresholds."""
    logger.info(f"Generating interpretation report to {output_path}")
    
    with open(output_path, 'w') as f:
        f.write("# PCA Interpretation Report\n\n")
        f.write("## Metric Associations with Principal Components\n\n")
        
        metrics = list(loadings['PC1'].keys())
        for metric in metrics:
            pc1_loading = loadings['PC1'][metric]
            pc2_loading = loadings['PC2'][metric]
            
            pc1_str = "PC1" if abs(pc1_loading) >= abs(pc2_loading) else "PC2"
            pc2_str = "PC2" if abs(pc1_loading) >= abs(pc2_loading) else "PC1"
            
            pc1_val = pc1_loading if abs(pc1_loading) >= abs(pc2_loading) else pc2_loading
            pc2_val = pc2_loading if abs(pc1_loading) >= abs(pc2_loading) else pc1_loading
            
            pc1_assoc = "Strong" if abs(pc1_val) > 0.5 else ("Moderate" if abs(pc1_val) > 0.3 else "Weak")
            pc2_assoc = "Strong" if abs(pc2_val) > 0.5 else ("Moderate" if abs(pc2_val) > 0.3 else "Weak")
            
            f.write(f"### {metric}\n")
            f.write(f"- **{pc1_str}**: {pc1_assoc} association (loading: {pc1_val:.4f})\n")
            f.write(f"- **{pc2_str}**: {pc2_assoc} association (loading: {pc2_val:.4f})\n\n")
    
    logger.info("Interpretation report generated successfully")

def run_analysis(networks_path: str, energy_path: str, output_dir: str) -> Dict[str, Any]:
    """Run full PLS regression analysis pipeline."""
    logger.info("Starting full regression analysis pipeline")
    
    # Load and merge data
    networks_df, energy_df = load_data(networks_path, energy_path)
    merged_df = merge_data(networks_df, energy_df)
    
    # Filter resonant instances
    filtered_df = filter_resonant(merged_df)
    
    # Save filtered dataset
    filtered_path = os.path.join(output_dir, 'filtered_decay.csv')
    filtered_df.to_csv(filtered_path, index=False)
    logger.info(f"Filtered dataset saved to {filtered_path}")
    
    # Prepare features and target
    metric_cols = [col for col in filtered_df.columns if col not in ['id', 'class', 'graph_id', 'status', 'decay_rate', 'r_squared']]
    X = filtered_df[metric_cols].values
    y = filtered_df['decay_rate'].values
    
    # Perform PCA
    loadings, pca = perform_pca(filtered_df[metric_cols])
    
    # Save PCA loadings
    pca_loadings_path = os.path.join(output_dir, 'pca_loadings.json')
    with open(pca_loadings_path, 'w') as f:
        json.dump(loadings, f, indent=2)
    logger.info(f"PCA loadings saved to {pca_loadings_path}")
    
    # Generate loadings table
    loadings_table_path = os.path.join(output_dir, 'loadings_table.md')
    generate_loadings_report(loadings, loadings_table_path)
    
    # Generate interpretation report
    interpretation_path = os.path.join(output_dir, 'interpretation_report.md')
    generate_interpretation_report(loadings, interpretation_path)
    
    # Perform PLS Regression
    pls_results = perform_pls_regression(X, y, n_components=2)
    
    # Calculate VIF
    vif_results = calculate_vif(filtered_df[metric_cols])
    
    # Apply Bonferroni correction
    corrected_results = bonferroni_correction(pls_results['p_values'])
    
    # Prepare final results
    final_results = {
        'pls_coefficients': pls_results['coefficients'],
        'vip_scores': pls_results['vip_scores'],
        'p_values': pls_results['p_values'],
        'corrected_p_values': [r[1] for r in corrected_results],
        'significant_features': [r[0] for r in corrected_results if r[2]],
        'vif_scores': vif_results,
        'pca_loadings': loadings,
        'explained_variance_x': pls_results['explained_variance_x'],
        'explained_variance_y': pls_results['explained_variance_y'],
        'n_samples': len(filtered_df),
        'n_features': len(metric_cols),
        'n_resonant_filtered': len(merged_df) - len(filtered_df)
    }
    
    # Save final results
    results_path = os.path.join(output_dir, 'regression_results.json')
    with open(results_path, 'w') as f:
        json.dump(final_results, f, indent=2)
    logger.info(f"Final regression results saved to {results_path}")
    
    # Generate markdown report
    report_path = os.path.join(output_dir, 'regression_results.md')
    with open(report_path, 'w') as f:
        f.write("# Regression Analysis Results\n\n")
        f.write("## Summary\n\n")
        f.write(f"- **Samples**: {final_results['n_samples']}\n")
        f.write(f"- **Features**: {final_results['n_features']}\n")
        f.write(f"- **Resonant instances filtered**: {final_results['n_resonant_filtered']}\n\n")
        
        f.write("## PLS Regression Coefficients\n\n")
        f.write("| Feature | Coefficient | VIP Score | P-value | Corrected P-value | Significant |\n")
        f.write("|---------|-------------|-----------|---------|-------------------|-------------|\n")
        for i, metric in enumerate(metric_cols):
            sig = "Yes" if corrected_results[i][2] else "No"
            f.write(f"| {metric} | {final_results['pls_coefficients'][i]:.4f} | {final_results['vip_scores'][i]:.4f} | {final_results['p_values'][i]:.4f} | {final_results['corrected_p_values'][i]:.4f} | {sig} |\n")
        
        f.write("\n## VIF Scores\n\n")
        for metric, vif in vif_results.items():
            f.write(f"- **{metric}**: {vif:.4f}\n")
    
    logger.info(f"Regression report saved to {report_path}")
    
    return final_results

def main():
    parser = argparse.ArgumentParser(description='Run PLS regression analysis on network topology and energy decay data')
    parser.add_argument('--networks', type=str, default='data/raw/networks.csv',
                      help='Path to networks CSV file')
    parser.add_argument('--energy', type=str, default='data/processed/energy_decay.csv',
                      help='Path to energy decay CSV file')
    parser.add_argument('--output-dir', type=str, default='data/analysis',
                      help='Output directory for results')
    
    args = parser.parse_args()
    
    # Ensure output directory exists
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Run analysis
    results = run_analysis(args.networks, args.energy, args.output_dir)
    
    logger.info("Analysis completed successfully")
    print(json.dumps(results, indent=2))

if __name__ == '__main__':
    main()