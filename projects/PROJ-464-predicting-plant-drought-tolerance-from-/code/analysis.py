import os
import sys
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
import yaml
import numpy as np
from statsmodels.stats.outliers_influence import variance_inflation_factor

from config import ensure_directories, get_config_summary

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def calculate_vif(df: pd.DataFrame, features: List[str]) -> Dict[str, float]:
    """
    Calculate Variance Inflation Factor (VIF) for a list of features.
    
    Args:
        df: DataFrame containing the features.
        features: List of column names to calculate VIF for.
        
    Returns:
        Dictionary mapping feature names to their VIF values.
    """
    vif_data = {}
    X = df[features].dropna()
    if X.empty:
        logger.warning("No valid data for VIF calculation.")
        return {f: float('inf') for f in features}
        
    # Add intercept for VIF calculation
    X_with_intercept = X.copy()
    X_with_intercept['intercept'] = 1.0
    
    for feature in features:
        try:
            vif = variance_inflation_factor(X_with_intercept.values, X_with_intercept.columns.get_loc(feature))
            vif_data[feature] = vif
        except Exception as e:
            logger.error(f"Error calculating VIF for {feature}: {e}")
            vif_data[feature] = float('inf')
            
    return vif_data

def perform_pca(df: pd.DataFrame, features: List[str], n_components: Optional[int] = None) -> Tuple[pd.DataFrame, Any]:
    """
    Perform PCA on the specified features to handle collinearity.
    
    Args:
        df: DataFrame containing the features.
        features: List of column names to perform PCA on.
        n_components: Number of components to keep. If None, keeps all.
        
    Returns:
        Tuple of (transformed DataFrame, PCA object).
    """
    from sklearn.decomposition import PCA
    
    X = df[features].dropna()
    if X.empty:
        logger.warning("No valid data for PCA.")
        return pd.DataFrame(), None
        
    pca = PCA(n_components=n_components)
    X_pca = pca.fit_transform(X)
    
    # Create DataFrame with PCA components
    component_names = [f'PC{i+1}' for i in range(X_pca.shape[1])]
    df_pca = pd.DataFrame(X_pca, columns=component_names, index=X.index)
    
    logger.info(f"PCA explained variance ratio: {pca.explained_variance_ratio_}")
    return df_pca, pca

def multiple_comparison_correction(p_values: List[float], method: str = 'fdr_bh') -> List[float]:
    """
    Apply multiple comparison correction to a list of p-values.
    
    Args:
        p_values: List of raw p-values.
        method: Correction method ('fdr_bh', 'fdr_by', 'bonferroni', etc.).
        
    Returns:
        List of corrected p-values.
    """
    from statsmodels.stats.multitest import multipletests
    
    if not p_values:
        return []
        
    try:
        _, corrected_pvals, _, _ = multipletests(p_values, method=method)
        return corrected_pvals.tolist()
    except Exception as e:
        logger.error(f"Error in multiple comparison correction: {e}")
        return p_values

def detect_tolerance_proxies(merged_data_path: str = None) -> Dict[str, Any]:
    """
    Check for and ingest 'independent tolerance proxies' (e.g., survival rate) if available.
    Required by FR-009.
    
    Args:
        merged_data_path: Path to the merged dataset CSV. If None, uses default path.
        
    Returns:
        Dictionary with detection results and framing text.
    """
    from config import get_config_summary
    
    config = get_config_summary()
    data_dir = Path(config['paths']['data_derived'])
    state_dir = Path(config['paths']['state'])
    
    # Default paths
    if merged_data_path is None:
        merged_data_path = data_dir / "merged_dataset.csv"
        
    merged_data_path = Path(merged_data_path)
    
    # Ensure directories exist
    ensure_directories()
    
    result = {
        'has_proxy': False,
        'proxy_columns': [],
        'proxy_values': {},
        'framing_text': '',
        'report_framing_path': '',
        'proxy_detection_path': ''
    }
    
    # Check if merged data exists
    if not merged_data_path.exists():
        logger.warning(f"Merged dataset not found at {merged_data_path}. "
                     "Cannot detect tolerance proxies. Assuming no proxy available.")
        result['framing_text'] = (
            "No independent tolerance proxy data was found in the merged dataset. "
            "Consequently, the classification model (FR-007/008) and sensitivity analysis (US3) "
            "have been skipped to avoid circular classification. "
            "This project focuses on predicting physiological state (conductance/photosynthesis) "
            "based on root architecture, rather than classifying binary drought tolerance."
        )
        
        # Write framing text
        report_framing_path = data_dir / "report_framing.md"
        with open(report_framing_path, 'w') as f:
            f.write("# Report Framing: Physiological State Prediction\n\n")
            f.write(result['framing_text'] + "\n")
        result['report_framing_path'] = str(report_framing_path)
        
        # Write proxy detection state
        proxy_detection_path = state_dir / "proxy_detection.yaml"
        with open(proxy_detection_path, 'w') as f:
            yaml.dump(result, f, default_flow_style=False)
        result['proxy_detection_path'] = str(proxy_detection_path)
        
        return result
    
    # Load merged data
    try:
        df = pd.read_csv(merged_data_path)
        logger.info(f"Loaded merged dataset with {len(df)} rows and columns: {list(df.columns)}")
    except Exception as e:
        logger.error(f"Failed to load merged dataset: {e}")
        result['framing_text'] = (
            f"Error loading merged dataset: {e}. "
            "Assuming no proxy available."
        )
        
        # Write framing text
        report_framing_path = data_dir / "report_framing.md"
        with open(report_framing_path, 'w') as f:
            f.write("# Report Framing: Physiological State Prediction\n\n")
            f.write(result['framing_text'] + "\n")
        result['report_framing_path'] = str(report_framing_path)
        
        # Write proxy detection state
        proxy_detection_path = state_dir / "proxy_detection.yaml"
        with open(proxy_detection_path, 'w') as f:
            yaml.dump(result, f, default_flow_style=False)
        result['proxy_detection_path'] = str(proxy_detection_path)
        
        return result
    
    # Define potential proxy columns
    # Based on data-model.md and common physiological proxies
    potential_proxies = [
        'survival_rate', 'survival', 'mortality_rate', 'wilting_point',
        'leaf_water_potential', 'stomatal_closure', 'drought_score'
    ]
    
    # Check for presence of proxy columns
    available_proxies = [col for col in potential_proxies if col in df.columns]
    
    if not available_proxies:
        logger.info("No independent tolerance proxy columns found in merged dataset.")
        result['framing_text'] = (
            "No independent tolerance proxy data (e.g., survival_rate) was found in the merged dataset. "
            "Consequently, the classification model (FR-007/008) and sensitivity analysis (US3) "
            "have been skipped to avoid circular classification. "
            "This project focuses on predicting physiological state (conductance/photosynthesis) "
            "based on root architecture, rather than classifying binary drought tolerance."
        )
        
        # Write framing text
        report_framing_path = data_dir / "report_framing.md"
        with open(report_framing_path, 'w') as f:
            f.write("# Report Framing: Physiological State Prediction\n\n")
            f.write(result['framing_text'] + "\n")
        result['report_framing_path'] = str(report_framing_path)
        
        # Write proxy detection state
        proxy_detection_path = state_dir / "proxy_detection.yaml"
        with open(proxy_detection_path, 'w') as f:
            yaml.dump(result, f, default_flow_style=False)
        result['proxy_detection_path'] = str(proxy_detection_path)
        
        return result
    
    # Validate proxy data (non-null, positive where applicable)
    valid_proxies = []
    proxy_stats = {}
    
    for proxy in available_proxies:
        proxy_series = df[proxy].dropna()
        if len(proxy_series) > 0:
            # Check if values are numeric and valid
            try:
                numeric_vals = pd.to_numeric(proxy_series, errors='coerce').dropna()
                if len(numeric_vals) > 0:
                    valid_proxies.append(proxy)
                    proxy_stats[proxy] = {
                        'count': len(numeric_vals),
                        'min': float(numeric_vals.min()),
                        'max': float(numeric_vals.max()),
                        'mean': float(numeric_vals.mean())
                    }
                    logger.info(f"Found valid proxy data for '{proxy}': {len(numeric_vals)} values, range [{numeric_vals.min():.3f}, {numeric_vals.max():.3f}]")
            except Exception as e:
                logger.warning(f"Proxy column '{proxy}' contains non-numeric data: {e}")
    
    if not valid_proxies:
        logger.info("No valid numeric proxy data found after validation.")
        result['framing_text'] = (
            "Potential proxy columns were identified but contained no valid numeric data. "
            "Consequently, the classification model (FR-007/008) and sensitivity analysis (US3) "
            "have been skipped to avoid circular classification. "
            "This project focuses on predicting physiological state (conductance/photosynthesis) "
            "based on root architecture, rather than classifying binary drought tolerance."
        )
        
        # Write framing text
        report_framing_path = data_dir / "report_framing.md"
        with open(report_framing_path, 'w') as f:
            f.write("# Report Framing: Physiological State Prediction\n\n")
            f.write(result['framing_text'] + "\n")
        result['report_framing_path'] = str(report_framing_path)
        
        # Write proxy detection state
        proxy_detection_path = state_dir / "proxy_detection.yaml"
        with open(proxy_detection_path, 'w') as f:
            yaml.dump(result, f, default_flow_style=False)
        result['proxy_detection_path'] = str(proxy_detection_path)
        
        return result
    
    # Proxies found!
    result['has_proxy'] = True
    result['proxy_columns'] = valid_proxies
    result['proxy_values'] = proxy_stats
    
    # Generate framing text
    proxy_names = ', '.join(valid_proxies)
    result['framing_text'] = (
        f"Independent tolerance proxies were detected in the dataset: {proxy_names}. "
        "These proxies will be used to construct a binary drought tolerance classification "
        "(high vs. low tolerance) via median split, enabling the sensitivity analysis (US3). "
        "This approach adheres to FR-009 by using an independent metric rather than "
        "circularly deriving tolerance from the primary physiological predictions."
    )
    
    # Write framing text
    report_framing_path = data_dir / "report_framing.md"
    with open(report_framing_path, 'w') as f:
        f.write("# Report Framing: Drought Tolerance Classification\n\n")
        f.write(result['framing_text'] + "\n\n")
        f.write("## Detected Proxies\n\n")
        for proxy, stats in proxy_stats.items():
            f.write(f"- **{proxy}**: {stats['count']} samples, range [{stats['min']:.3f}, {stats['max']:.3f}], mean {stats['mean']:.3f}\n")
    result['report_framing_path'] = str(report_framing_path)
    
    # Write proxy detection state
    proxy_detection_path = state_dir / "proxy_detection.yaml"
    with open(proxy_detection_path, 'w') as f:
        yaml.dump(result, f, default_flow_style=False)
    result['proxy_detection_path'] = str(proxy_detection_path)
    
    logger.info(f"Proxy detection complete. Found {len(valid_proxies)} valid proxies.")
    return result

def main():
    """Main entry point for the analysis module."""
    logger.info("Starting analysis module...")
    
    # Run proxy detection
    proxy_result = detect_tolerance_proxies()
    
    logger.info(f"Proxy detection result: has_proxy={proxy_result['has_proxy']}")
    logger.info(f"Report framing written to: {proxy_result['report_framing_path']}")
    logger.info(f"Proxy detection state written to: {proxy_result['proxy_detection_path']}")
    
    return proxy_result

if __name__ == "__main__":
    main()
