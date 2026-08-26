"""
Regression Analysis Module for User Story 3.
Implements PLS Regression, PCA, and statistical validation.
"""
import os
import sys
import json
import logging
import argparse
from pathlib import Path
from typing import Dict, List, Tuple, Optional

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.decomposition import PCA
from sklearn.cross_decomposition import PLSRegression
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
from scipy import stats
from scipy.stats import zscore

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_data(networks_path: str, energy_path: str) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Load network metrics and energy decay results."""
    if not os.path.exists(networks_path):
        raise FileNotFoundError(f"Network data not found: {networks_path}")
    if not os.path.exists(energy_path):
        raise FileNotFoundError(f"Energy data not found: {energy_path}")
    
    networks_df = pd.read_csv(networks_path)
    energy_df = pd.read_csv(energy_path)
    
    logger.info(f"Loaded {len(networks_df)} network records and {len(energy_df)} energy records.")
    return networks_df, energy_df

def merge_data(networks_df: pd.DataFrame, energy_df: pd.DataFrame) -> pd.DataFrame:
    """Merge network metrics with energy decay rates."""
    # Filter resonant instances
    energy_df = energy_df[energy_df['status'] != 'resonant']
    logger.info(f"Filtered resonant instances. Remaining: {len(energy_df)}")
    
    # Merge on graph_id
    merged = pd.merge(networks_df, energy_df, left_on='id', right_on='graph_id', how='inner')
    logger.info(f"Merged dataset size: {len(merged)}")
    return merged

def perform_pca(X: np.ndarray, n_components: int = 2) -> Tuple[PCA, np.ndarray, np.ndarray]:
    """Perform PCA and return fitted model, transformed data, and loadings."""
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    pca = PCA(n_components=n_components)
    T = pca.fit_transform(X_scaled)
    
    # Loadings are the correlation between original variables and components
    # loadings = pca.components_.T * sqrt(explained_variance)
    loadings = pca.components_.T * np.sqrt(pca.explained_variance_)
    
    return pca, T, loadings, scaler

def perform_pls_regression(X: np.ndarray, y: np.ndarray, n_components: int = 2) -> Tuple[PLSRegression, Dict]:
    """Perform PLS Regression and return model and coefficients."""
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
    s = np.diag(t.T @ t @ q.T @ q).reshape(h, -1)
    vip = np.sqrt(p * (w ** 2 @ s) / np.sum(s))
    
    # Coefficients in original scale
    beta = pls.coef_.ravel()
    # Unscale: beta_original = beta_scaled * (y_std / x_std)
    beta_original = beta * (scaler_y.scale_ / scaler_X.scale_)
    
    return pls, {
        "coefficients": beta_original,
        "vip_scores": vip,
        "explained_variance_x": pls.explained_variance_ratio_[0],
        "explained_variance_y": pls.y_variance_[0]
    }

def calculate_vif(X: np.ndarray, feature_names: List[str]) -> Dict[str, float]:
    """Calculate Variance Inflation Factor for each feature."""
    vif_data = {}
    for i, name in enumerate(feature_names):
        y_i = X[:, i]
        X_others = np.delete(X, i, axis=1)
        
        reg = LinearRegression()
        reg.fit(X_others, y_i)
        r_squared = reg.score(X_others, y_i)
        
        vif = 1 / (1 - r_squared)
        vif_data[name] = vif
        
    return vif_data

def bonferroni_correction(p_values: np.ndarray, alpha: float = 0.05) -> Tuple[np.ndarray, np.ndarray]:
    """Apply Bonferroni correction to p-values."""
    n_tests = len(p_values)
    corrected_p = p_values * n_tests
    corrected_p = np.minimum(corrected_p, 1.0)
    significant = corrected_p < alpha
    return corrected_p, significant

def generate_loadings_report(loadings: np.ndarray, feature_names: List[str], output_path: str) -> str:
    """Generate a markdown table of PCA loadings with interpretation."""
    md_content = "## PCA Loadings Interpretation\n\n"
    md_content += "The following table shows the loadings of topological metrics on the first two principal components (PC1 and PC2).\n\n"
    md_content += "| Metric | PC1 Loading | PC2 Loading | Physical Interpretation |\n"
    md_content += "|---|---|---|---|\n"
    
    interpretations = {
        "clustering_coefficient": "Local clustering / Triadic closure",
        "average_path_length": "Global connectivity / Efficiency",
        "average_degree": "Overall connectivity density",
        "degree_std": "Degree heterogeneity / Hub presence",
        "eigenvector_centrality": "Influence of high-degree nodes"
    }
    
    for i, name in enumerate(feature_names):
        # Normalize feature name for lookup
        key = name.lower().replace("_", "")
        interp = interpretations.get(key, "Structural metric")
        
        pc1_val = f"{loadings[i, 0]:.4f}" if loadings.shape[1] > 0 else "N/A"
        pc2_val = f"{loadings[i, 1]:.4f}" if loadings.shape[1] > 1 else "N/A"
        
        md_content += f"| {name} | {pc1_val} | {pc2_val} | {interp} |\n"
    
    md_content += "\n### Interpretation of Physical Meaning\n\n"
    md_content += "- **PC1** typically captures the trade-off between **local clustering** and **global connectivity**. High positive loadings on clustering and negative on path length suggest a community-driven structure.\n"
    md_content += "- **PC2** often represents **degree heterogeneity** or the presence of **hubs**. Metrics with high loadings here indicate networks with significant degree disparity.\n"
    
    # Save to file
    with open(output_path, 'w') as f:
        f.write(md_content)
    
    logger.info(f"PCA loadings report saved to {output_path}")
    return md_content

def run_analysis(
    networks_path: str, 
    energy_path: str, 
    output_dir: str,
    n_components: int = 2
) -> Dict:
    """Run the full regression analysis pipeline."""
    os.makedirs(output_dir, exist_ok=True)
    
    # 1. Load and merge data
    networks_df, energy_df = load_data(networks_path, energy_path)
    merged_df = merge_data(networks_df, energy_df)
    
    if len(merged_df) == 0:
        raise ValueError("No valid data after filtering resonant instances.")
    
    # 2. Prepare features
    feature_cols = ['clustering_coefficient', 'average_path_length', 'average_degree', 'degree_std', 'eigenvector_centrality']
    # Filter columns that actually exist
    available_cols = [c for c in feature_cols if c in merged_df.columns]
    
    X = merged_df[available_cols].values
    y = merged_df['decay_rate'].values
    
    # 3. Check VIF
    vif_scores = calculate_vif(X, available_cols)
    logger.info(f"VIF Scores: {vif_scores}")
    high_vif = {k: v for k, v in vif_scores.items() if v > 5}
    if high_vif:
        logger.warning(f"High VIF detected for: {list(high_vif.keys())}. Consider removing these features.")
    
    # 4. Perform PCA
    pca, T, loadings, scaler = perform_pca(X, n_components=n_components)
    
    # 5. Perform PLS Regression
    pls_model, pls_results = perform_pls_regression(X, y, n_components=n_components)
    
    # 6. Calculate P-values (approximate via permutation or standard error)
    # For simplicity, using permutation test approximation
    n_permutations = 1000
    observed_r2 = pls_model.score(X, y.reshape(-1, 1))
    null_r2 = []
    
    for _ in range(n_permutations):
        y_perm = np.random.permutation(y)
        pls_perm = PLSRegression(n_components=n_components)
        pls_perm.fit(X, y_perm.reshape(-1, 1))
        null_r2.append(pls_perm.score(X, y_perm.reshape(-1, 1)))
    
    p_value = (np.sum(np.array(null_r2) >= observed_r2) + 1) / (n_permutations + 1)
    corrected_p, significant = bonferroni_correction(np.array([p_value]), alpha=0.05)
    
    # 7. Generate Reports
    loadings_md_path = os.path.join(output_dir, "pca_loadings_interpretation.md")
    generate_loadings_report(loadings, available_cols, loadings_md_path)
    
    results = {
        "n_samples": len(merged_df),
        "features_used": available_cols,
        "vif_scores": vif_scores,
        "pca_explained_variance": pca.explained_variance_ratio_.tolist(),
        "pls_coefficients": pls_results["coefficients"].tolist(),
        "pls_vip_scores": pls_results["vip_scores"].tolist(),
        "p_value": p_value,
        "corrected_p_value": corrected_p[0],
        "is_significant": bool(significant[0]),
        "model_r2": observed_r2
    }
    
    # Save JSON
    json_path = os.path.join(output_dir, "regression_results.json")
    with open(json_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Analysis complete. Results saved to {json_path}")
    return results

def main():
    parser = argparse.ArgumentParser(description="Run regression analysis on network and energy data.")
    parser.add_argument("--networks", type=str, default="data/raw/networks.csv", help="Path to networks CSV")
    parser.add_argument("--energy", type=str, default="data/processed/energy_decay.csv", help="Path to energy CSV")
    parser.add_argument("--output", type=str, default="data/analysis", help="Output directory")
    parser.add_argument("--components", type=int, default=2, help="Number of PCA/PLS components")
    
    args = parser.parse_args()
    
    try:
        results = run_analysis(args.networks, args.energy, args.output, args.components)
        print(json.dumps(results, indent=2))
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()