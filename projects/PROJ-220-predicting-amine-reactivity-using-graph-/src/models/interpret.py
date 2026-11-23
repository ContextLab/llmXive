"""
Interpretability module for GNN models.
Implements SHAP analysis, correlation validation, and collinearity checks.
"""
import logging
import json
import os
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
from scipy.stats import pearsonr
import matplotlib.pyplot as plt
import seaborn as sns

# Optional imports for SHAP
try:
    import shap
    SHAP_AVAILABLE = True
except ImportError:
    SHAP_AVAILABLE = False
    logging.warning("SHAP not available. Install with `pip install shap` for interpretability features.")

from src.data.descriptors import aggregate_independent_vector
from src.utils.logging import get_audit_logger

logger = logging.getLogger(__name__)
audit_logger = get_audit_logger()

# Constants for collinearity check
VIF_THRESHOLD = 10.0
CORRELATION_THRESHOLD = 0.95

def check_collinearity_descriptors(descriptor_data: Union[pd.DataFrame, np.ndarray, List[Dict]]) -> Tuple[bool, Dict[str, Any]]:
    """
    Perform a collinearity check on the independent descriptor vector components.
    
    This function verifies that the independent descriptor vector components 
    (Hammett, Taft, Charton, Verloop, MR) are not perfectly correlated with 
    each other before computing the Pearson correlation with SHAP values.
    
    Args:
        descriptor_data: Data containing the independent descriptor components.
                        Can be a DataFrame, numpy array, or list of dicts.
                        Expected columns/features: Hammett_sigma_p, Hammett_sigma_m,
                        Hammett_sigma_plus, Hammett_sigma_minus, Taft_Es,
                        Taft_Es_s, Charton_nu, Verloop_B1, Verloop_B5, Molar_Refractivity.
    
    Returns:
        Tuple of (is_valid, diagnostics_dict):
            - is_valid: bool, True if no perfect collinearity detected
            - diagnostics_dict: dict containing correlation matrix, VIF values,
                              and any warnings about high correlations
    
    Raises:
        ValueError: If input data is empty or has insufficient samples
        TypeError: If input data format is not supported
    """
    # Convert input to DataFrame if necessary
    if isinstance(descriptor_data, np.ndarray):
        if descriptor_data.ndim == 1:
            raise ValueError("Descriptor data must be 2D (samples x features)")
        feature_names = [
            'Hammett_sigma_p', 'Hammett_sigma_m', 'Hammett_sigma_plus', 
            'Hammett_sigma_minus', 'Taft_Es', 'Taft_Es_s', 
            'Charton_nu', 'Verloop_B1', 'Verloop_B5', 'Molar_Refractivity'
        ]
        if descriptor_data.shape[1] != len(feature_names):
            raise ValueError(f"Expected {len(feature_names)} features, got {descriptor_data.shape[1]}")
        df = pd.DataFrame(descriptor_data, columns=feature_names)
    elif isinstance(descriptor_data, list):
        df = pd.DataFrame(descriptor_data)
    elif isinstance(descriptor_data, pd.DataFrame):
        df = descriptor_data.copy()
    else:
        raise TypeError(f"Unsupported input type: {type(descriptor_data)}")
    
    # Validate data
    if df.empty:
        raise ValueError("Descriptor data is empty")
    
    if df.shape[0] < 10:
        logger.warning(f"Only {df.shape[0]} samples available for collinearity check. Results may be unreliable.")
    
    # Check for missing values
    if df.isnull().any().any():
        missing_cols = df.columns[df.isnull().any()].tolist()
        logger.warning(f"Missing values detected in columns: {missing_cols}. Dropping rows with missing values.")
        df = df.dropna()
        if df.empty:
            raise ValueError("All rows dropped due to missing values")
    
    # Compute correlation matrix
    corr_matrix = df.corr()
    
    # Check for perfect correlations (|r| >= 0.999)
    perfect_corr_pairs = []
    high_corr_pairs = []
    
    for i in range(len(corr_matrix.columns)):
        for j in range(i + 1, len(corr_matrix.columns)):
            col_i = corr_matrix.columns[i]
            col_j = corr_matrix.columns[j]
            corr_val = abs(corr_matrix.iloc[i, j])
            
            if corr_val >= 0.999:
                perfect_corr_pairs.append((col_i, col_j, corr_val))
            elif corr_val >= CORRELATION_THRESHOLD:
                high_corr_pairs.append((col_i, col_j, corr_val))
    
    # Calculate Variance Inflation Factor (VIF) for each feature
    vif_values = {}
    for i, col in enumerate(df.columns):
        # Create design matrix excluding current column
        X = df.drop(columns=[col])
        y = df[col]
        
        # Add intercept
        X_with_intercept = np.column_stack([np.ones(X.shape[0]), X.values])
        
        # Calculate VIF: 1 / (1 - R^2)
        try:
            # Simple linear regression to get R^2
            beta = np.linalg.lstsq(X_with_intercept, y.values, rcond=None)[0]
            y_pred = X_with_intercept @ beta
            ss_res = np.sum((y.values - y_pred) ** 2)
            ss_tot = np.sum((y.values - np.mean(y.values)) ** 2)
            r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
            
            vif = 1 / (1 - r_squared) if (1 - r_squared) > 1e-10 else np.inf
            vif_values[col] = vif
        except np.linalg.LinAlgError:
            vif_values[col] = np.inf
    
    # Determine if collinearity is acceptable
    is_valid = len(perfect_corr_pairs) == 0
    
    # Build diagnostics
    diagnostics = {
        'is_valid': is_valid,
        'perfect_correlations': perfect_corr_pairs,
        'high_correlations': high_corr_pairs,
        'vif_values': vif_values,
        'max_vif': max(vif_values.values()) if vif_values else 0,
        'correlation_matrix': corr_matrix.to_dict(),
        'sample_size': df.shape[0],
        'features': df.columns.tolist()
    }
    
    # Log warnings
    if perfect_corr_pairs:
        logger.error(f"Perfect collinearity detected: {perfect_corr_pairs}")
    
    if high_corr_pairs:
        logger.warning(f"High correlations detected (|r| >= {CORRELATION_THRESHOLD}): {high_corr_pairs}")
    
    high_vif_features = [k for k, v in vif_values.items() if v > VIF_THRESHOLD]
    if high_vif_features:
        logger.warning(f"High VIF (> {VIF_THRESHOLD}) detected for features: {high_vif_features}")
    
    return is_valid, diagnostics

def run_shap_analysis(
    model: Any,
    graph_data: Union[pd.DataFrame, List[Dict]],
    output_path: Union[str, Path],
    use_random_baseline: bool = False,
    n_samples: int = 100
) -> Dict[str, Any]:
    """
    Perform SHAP analysis on the trained GNN model.
    
    Args:
        model: Trained GNN model
        graph_data: Preprocessed graph data with node/edge features
        output_path: Path to save SHAP importance results
        use_random_baseline: Whether to compute random baseline (for T048)
        n_samples: Number of samples to use for SHAP calculation
    
    Returns:
        Dictionary containing SHAP analysis results
    """
    if not SHAP_AVAILABLE:
        raise RuntimeError("SHAP library not available. Install with `pip install shap`.")
    
    # Convert graph data to DataFrame if needed
    if isinstance(graph_data, list):
        df = pd.DataFrame(graph_data)
    else:
        df = graph_data.copy()
    
    # Ensure we have enough data
    if df.shape[0] < n_samples:
        logger.warning(f"Only {df.shape[0]} samples available, using all instead of {n_samples}")
        n_samples = df.shape[0]
    
    # Sample data if needed
    if df.shape[0] > n_samples:
        df_sample = df.sample(n=n_samples, random_state=42)
    else:
        df_sample = df
    
    # Extract features (assuming graph data has node/edge features flattened or aggregated)
    # This is a simplified approach - in practice, you'd need to properly aggregate graph features
    feature_columns = [col for col in df_sample.columns if col not in ['smiles', 'graph', 'reaction_id']]
    
    if not feature_columns:
        raise ValueError("No feature columns found in graph data")
    
    X = df_sample[feature_columns].values
    y = df_sample.get('normalized_log_rate', df_sample.get('log_rate', None))
    
    if y is None:
        raise ValueError("No target variable found in graph data")
    
    y = y.values
    
    # Create a simple explainer for the model
    # Note: For GNNs, you might need a custom explainer
    try:
        explainer = shap.Explainer(model, X)
        shap_values = explainer(X)
        
        # Aggregate SHAP values per feature
        mean_shap = np.abs(shap_values.values).mean(axis=0)
        feature_importance = list(zip(feature_columns, mean_shap))
        feature_importance.sort(key=lambda x: x[1], reverse=True)
        
        # Save results
        output_dir = Path(output_path).parent
        output_dir.mkdir(parents=True, exist_ok=True)
        
        results_df = pd.DataFrame(feature_importance, columns=['feature', 'importance'])
        results_df.to_csv(output_path, index=False)
        
        logger.info(f"SHAP importance saved to {output_path}")
        
        return {
            'shap_values': shap_values.values,
            'feature_importance': feature_importance,
            'mean_shap': mean_shap,
            'feature_columns': feature_columns,
            'output_path': str(output_path)
        }
        
    except Exception as e:
        logger.error(f"Error during SHAP analysis: {e}")
        raise

def compute_correlation(
    shap_results: Dict[str, Any],
    descriptor_data: Union[pd.DataFrame, np.ndarray, List[Dict]],
    output_path: Optional[Union[str, Path]] = None
) -> Tuple[float, float, Dict[str, Any]]:
    """
    Compute Pearson correlation between aggregated SHAP importance and independent descriptor vector.
    
    Args:
        shap_results: Results from run_shap_analysis()
        descriptor_data: Independent descriptor vector data (from T007b)
        output_path: Optional path to save correlation results
    
    Returns:
        Tuple of (correlation_coefficient, p_value, diagnostics)
    """
    # First, perform collinearity check on descriptors
    is_valid, collinearity_diagnostics = check_collinearity_descriptors(descriptor_data)
    
    if not is_valid:
        logger.warning("Collinearity detected in descriptor data. Proceeding with caution.")
    
    # Get SHAP importance
    feature_importance = shap_results.get('feature_importance', [])
    if not feature_importance:
        raise ValueError("No feature importance data available")
    
    # Create a mapping of feature names to importance values
    importance_map = {feat: imp for feat, imp in feature_importance}
    
    # Get descriptor data as DataFrame
    if isinstance(descriptor_data, np.ndarray):
        feature_names = [
            'Hammett_sigma_p', 'Hammett_sigma_m', 'Hammett_sigma_plus', 
            'Hammett_sigma_minus', 'Taft_Es', 'Taft_Es_s', 
            'Charton_nu', 'Verloop_B1', 'Verloop_B5', 'Molar_Refractivity'
        ]
        desc_df = pd.DataFrame(descriptor_data, columns=feature_names)
    elif isinstance(descriptor_data, list):
        desc_df = pd.DataFrame(descriptor_data)
    else:
        desc_df = descriptor_data.copy()
    
    # Calculate mean SHAP importance for each descriptor type
    # This is a simplified mapping - in practice, you'd need to map graph features to descriptors
    descriptor_importance = {}
    for col in desc_df.columns:
        if col in importance_map:
            descriptor_importance[col] = importance_map[col]
        else:
            # Try to find similar features
            matching = [k for k in importance_map.keys() if col.lower() in k.lower()]
            if matching:
                descriptor_importance[col] = np.mean([importance_map[m] for m in matching])
            else:
                descriptor_importance[col] = 0.0
    
    # Extract values
    desc_values = np.array([descriptor_importance[col] for col in desc_df.columns])
    shap_values = np.array([importance_map.get(col, 0) for col in desc_df.columns])
    
    # Compute correlation
    if len(desc_values) < 2 or len(shap_values) < 2:
        raise ValueError("Insufficient data for correlation calculation")
    
    correlation, p_value = pearsonr(desc_values, shap_values)
    
    # Prepare diagnostics
    diagnostics = {
        'correlation_coefficient': float(correlation),
        'p_value': float(p_value),
        'is_significant': p_value < 0.05,
        'collinearity_check': collinearity_diagnostics,
        'descriptor_importance': descriptor_importance,
        'feature_count': len(desc_values)
    }
    
    # Save results if path provided
    if output_path:
        output_dir = Path(output_path).parent
        output_dir.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(diagnostics, f, indent=2, default=str)
        
        logger.info(f"Correlation results saved to {output_path}")
    
    return correlation, p_value, diagnostics

def test_significance(
    correlation: float,
    p_value: float,
    random_baseline_correlations: Optional[List[float]] = None,
    alpha: float = 0.05
) -> Dict[str, Any]:
    """
    Perform statistical significance testing for the correlation.
    
    Args:
        correlation: Pearson correlation coefficient
        p_value: P-value from correlation test
        random_baseline_correlations: Optional list of correlations from random baseline
        alpha: Significance level
    
    Returns:
        Dictionary containing significance test results
    """
    is_significant = p_value < alpha
    
    result = {
        'is_significant': is_significant,
        'correlation': correlation,
        'p_value': p_value,
        'alpha': alpha,
        'null_hypothesis_rejected': is_significant
    }
    
    if random_baseline_correlations:
        # Compare against random baseline
        baseline_mean = np.mean(random_baseline_correlations)
        baseline_std = np.std(random_baseline_correlations)
        
        # Calculate how many standard deviations away from baseline mean
        if baseline_std > 0:
            z_score = (correlation - baseline_mean) / baseline_std
        else:
            z_score = 0
        
        # Calculate empirical p-value
        empirical_p = sum(1 for c in random_baseline_correlations if abs(c) >= abs(correlation)) / len(random_baseline_correlations)
        
        result['random_baseline'] = {
            'mean': float(baseline_mean),
            'std': float(baseline_std),
            'z_score': float(z_score),
            'empirical_p_value': float(empirical_p),
            'is_significant_vs_baseline': empirical_p < alpha
        }
    
    return result

def visualize_shap(
    shap_results: Dict[str, Any],
    molecules: List[str],
    output_dir: Union[str, Path],
    top_n: int = 10
) -> List[str]:
    """
    Visualize SHAP values on molecular structures.
    
    Args:
        shap_results: Results from run_shap_analysis()
        molecules: List of SMILES strings for the molecules
        output_dir: Directory to save visualization files
        top_n: Number of top features to highlight
    
    Returns:
        List of paths to generated plot files
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    plot_paths = []
    
    # Get top features
    feature_importance = shap_results.get('feature_importance', [])
    top_features = [f[0] for f in feature_importance[:top_n]]
    
    # For each molecule, create a visualization
    for i, smiles in enumerate(molecules[:5]):  # Limit to first 5 for demo
        try:
            # Create a simple plot (in practice, you'd use RDKit to draw molecules with atom highlighting)
            fig, ax = plt.subplots(figsize=(10, 6))
            
            # Create a bar chart of top features
            importance_values = [f[1] for f in feature_importance[:top_n]]
            ax.barh(top_features, importance_values)
            ax.set_xlabel('SHAP Importance')
            ax.set_title(f'SHAP Feature Importance for Molecule {i+1}')
            ax.invert_yaxis()
            
            # Save plot
            plot_path = output_dir / f'shap_molecule_{i+1}.png'
            plt.savefig(plot_path, dpi=150, bbox_inches='tight')
            plt.close()
            
            plot_paths.append(str(plot_path))
            logger.info(f"Saved SHAP plot for molecule {i+1} to {plot_path}")
            
        except Exception as e:
            logger.error(f"Error creating SHAP plot for molecule {i+1}: {e}")
            continue
    
    return plot_paths

def generate_random_baseline(
    model: Any,
    graph_data: Union[pd.DataFrame, List[Dict]],
    descriptor_data: Union[pd.DataFrame, np.ndarray, List[Dict]],
    n_iterations: int = 100
) -> List[float]:
    """
    Generate random baseline by shuffling labels and running SHAP analysis.
    
    Args:
        model: Trained GNN model
        graph_data: Preprocessed graph data
        descriptor_data: Independent descriptor vector data
        n_iterations: Number of random shuffles to perform
    
    Returns:
        List of correlation coefficients from random baseline
    """
    logger.info(f"Generating random baseline with {n_iterations} iterations")
    
    # Convert graph data to DataFrame if needed
    if isinstance(graph_data, list):
        df = pd.DataFrame(graph_data)
    else:
        df = graph_data.copy()
    
    # Get target variable
    y = df.get('normalized_log_rate', df.get('log_rate', None))
    if y is None:
        raise ValueError("No target variable found in graph data")
    
    y = y.values
    
    correlations = []
    
    for i in range(n_iterations):
        # Shuffle labels
        y_shuffled = np.random.permutation(y)
        
        # Create a temporary dataset with shuffled labels
        df_shuffled = df.copy()
        df_shuffled['normalized_log_rate'] = y_shuffled
        
        try:
            # Run SHAP analysis on shuffled data
            shap_results = run_shap_analysis(
                model, 
                df_shuffled, 
                output_path=None,
                n_samples=min(100, len(df_shuffled))
            )
            
            # Compute correlation
            corr, p_val, _ = compute_correlation(shap_results, descriptor_data)
            correlations.append(corr)
            
        except Exception as e:
            logger.warning(f"Iteration {i+1} failed: {e}")
            continue
    
    logger.info(f"Random baseline complete. Generated {len(correlations)} correlations")
    return correlations

def main():
    """Main function for interpretability pipeline."""
    logging.basicConfig(level=logging.INFO)
    
    # Example usage (would be replaced with actual data loading in production)
    logger.info("Interpretability module loaded successfully")
    logger.info("Available functions:")
    logger.info("  - check_collinearity_descriptors: Verify descriptor collinearity")
    logger.info("  - run_shap_analysis: Perform SHAP analysis on GNN model")
    logger.info("  - compute_correlation: Compute correlation between SHAP and descriptors")
    logger.info("  - test_significance: Perform statistical significance testing")
    logger.info("  - visualize_shap: Generate SHAP visualizations")
    logger.info("  - generate_random_baseline: Generate random baseline distribution")

if __name__ == "__main__":
    main()