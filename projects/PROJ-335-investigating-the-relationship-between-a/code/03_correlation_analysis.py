"""
Correlation Analysis Module for Alpha Oscillations and Working Memory Capacity.

Implements:
- VIF calculation and collinearity detection
- Partial correlation and PCA fallback
- FDR correction
- LOSO cross-validation
- Split-half reliability analysis (T033)
"""
import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import numpy as np
import pandas as pd
from scipy import stats
from sklearn.linear_model import LinearRegression
from statsmodels.stats.multitest import multipletests

# Import local utilities
try:
    from utils.validation import load_and_validate_csv
except ImportError:
    # Fallback for direct execution or different import context
    import sys
    sys.path.append(str(Path(__file__).parent / 'utils'))
    from validation import load_and_validate_csv

# Setup logger
logger = logging.getLogger(__name__)

def load_config() -> Dict[str, Any]:
    """Load configuration from code/config.yaml."""
    config_path = Path(__file__).parent / 'config.yaml'
    if not config_path.exists():
        # Fallback if config.yaml is in root
        config_path = Path(__file__).parent.parent / 'config.yaml'
    
    import yaml
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def load_metric_data(filepath: str) -> pd.DataFrame:
    """Load metric data from CSV file."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Metric file not found: {filepath}")
    
    df = pd.read_csv(filepath)
    if df.empty:
        raise ValueError(f"Metric file is empty: {filepath}")
    return df

def merge_metrics(alpha_power_path: str, plv_path: str, wm_path: str) -> pd.DataFrame:
    """Merge alpha power, PLV, and WM capacity metrics by subject."""
    alpha_df = load_metric_data(alpha_power_path)
    plv_df = load_metric_data(plv_path)
    wm_df = load_metric_data(wm_path)
    
    # Ensure subject column exists and is consistent
    for df in [alpha_df, plv_df, wm_df]:
        if 'subject' not in df.columns:
            # Try to infer from filename or use index
            if 'subject_id' in df.columns:
                df.rename(columns={'subject_id': 'subject'}, inplace=True)
            else:
                raise ValueError("Missing 'subject' or 'subject_id' column in metric data")
    
    # Merge on subject
    merged = alpha_df.merge(plv_df, on='subject', how='inner')
    merged = merged.merge(wm_df, on='subject', how='inner')
    
    logger.info(f"Merged {len(merged)} subjects from all metric sources")
    return merged

def calculate_vif(df: pd.DataFrame, features: List[str]) -> Dict[str, float]:
    """Calculate Variance Inflation Factor for given features."""
    if len(features) < 2:
        return {}
    
    X = df[features].values
    vif_data = {}
    
    for i, feature in enumerate(features):
        # Regress feature against all other features
        X_other = np.delete(X, i, axis=1)
        model = LinearRegression()
        model.fit(X_other, X[:, i])
        r_squared = model.score(X_other, X[:, i])
        vif = 1.0 / (1.0 - r_squared) if r_squared < 1.0 else np.inf
        vif_data[feature] = vif
    
    return vif_data

def detect_collinearity(vif_data: Dict[str, float], threshold: float = 5.0) -> List[str]:
    """Detect features with VIF above threshold."""
    return [feat for feat, vif in vif_data.items() if vif > threshold]

def prepare_pca_components(df: pd.DataFrame, features: List[str], n_components: int = 1):
    """Prepare PCA components for collinear features."""
    from sklearn.decomposition import PCA
    
    X = df[features].values
    pca = PCA(n_components=n_components)
    components = pca.fit_transform(X)
    
    logger.info(f"PCA components explained variance: {pca.explained_variance_ratio_}")
    return components, pca

def calculate_partial_correlation(df: pd.DataFrame, x: str, y: str, controls: List[str]) -> Tuple[float, float]:
    """Calculate partial correlation between x and y, controlling for controls."""
    if not controls:
        return stats.pearsonr(df[x], df[y])
    
    # Residualize x and y against controls
    X_controls = df[controls].values
    x_vals = df[x].values
    y_vals = df[y].values
    
    # Regress x on controls
    model_x = LinearRegression()
    model_x.fit(X_controls, x_vals)
    residuals_x = x_vals - model_x.predict(X_controls)
    
    # Regress y on controls
    model_y = LinearRegression()
    model_y.fit(X_controls, y_vals)
    residuals_y = y_vals - model_y.predict(X_controls)
    
    # Correlation of residuals
    r, p = stats.pearsonr(residuals_x, residuals_y)
    return r, p

def apply_fdr_correction(p_values: List[float]) -> Tuple[List[bool], List[float]]:
    """Apply Benjamini-Hochberg FDR correction."""
    if not p_values:
        return [], []
    
    reject, p_corrected, _, _ = multipletests(p_values, method='fdr_bh')
    return list(reject), list(p_corrected)

def run_loso_cross_validation(df: pd.DataFrame, x_col: str, y_col: str, 
                              control_cols: List[str] = None) -> Dict[str, Any]:
    """
    Run Leave-One-Subject-Out cross-validation for correlation model.
    
    Returns:
      Dictionary with mean correlation, std, and per-fold results
    """
    subjects = df['subject'].unique()
    correlations = []
    
    for test_subject in subjects:
        train_df = df[df['subject'] != test_subject]
        test_df = df[df['subject'] == test_subject]
        
        if len(train_df) < 3:
            continue
        
        if control_cols:
            r, _ = calculate_partial_correlation(train_df, x_col, y_col, control_cols)
        else:
            r, _ = stats.pearsonr(train_df[x_col], train_df[y_col])
        
        correlations.append(r)
    
    if not correlations:
        return {
            'mean_r': 0.0,
            'std_r': 0.0,
            'n_folds': 0,
            'status': 'INSUFFICIENT_DATA'
        }
    
    return {
        'mean_r': float(np.mean(correlations)),
        'std_r': float(np.std(correlations)),
        'n_folds': len(correlations),
        'per_fold_r': correlations,
        'status': 'SUCCESS'
    }

def run_split_half_reliability(df: pd.DataFrame, x_col: str, y_col: str, 
                               control_cols: List[str] = None, 
                               n_iterations: int = 100, 
                               random_seed: int = 42) -> Dict[str, Any]:
    """
    Implement split-half reliability analysis.
    
    Splits subjects into two random halves, computes correlation in each half,
    then calculates the correlation between the two halves (Spearman-Brown corrected).
    Repeats multiple times to get a robust estimate.
    
    Args:
        df: DataFrame with subject data
        x_col: Independent variable column name
        y_col: Dependent variable column name
        control_cols: Optional list of control variables for partial correlation
        n_iterations: Number of random splits to perform
        random_seed: Random seed for reproducibility
    
    Returns:
        Dictionary with reliability metrics including Spearman-Brown corrected coefficient
    """
    np.random.seed(random_seed)
    subjects = df['subject'].unique()
    n_subjects = len(subjects)
    
    if n_subjects < 4:
        logger.warning(f"Insufficient subjects ({n_subjects}) for split-half reliability")
        return {
            'reliability_coeff': 0.0,
            'std_reliability': 0.0,
            'n_iterations': 0,
            'status': 'INSUFFICIENT_SUBJECTS',
            'message': f'Need at least 4 subjects for split-half reliability, got {n_subjects}'
        }
    
    correlations_half1 = []
    correlations_half2 = []
    
    for i in range(n_iterations):
        # Shuffle and split subjects
        np.random.shuffle(subjects)
        mid = len(subjects) // 2
        half1_subjects = subjects[:mid]
        half2_subjects = subjects[mid:]
        
        df_half1 = df[df['subject'].isin(half1_subjects)]
        df_half2 = df[df['subject'].isin(half2_subjects)]
        
        # Ensure both halves have enough data
        if len(df_half1) < 3 or len(df_half2) < 3:
            continue
        
        # Calculate correlation for each half
        if control_cols:
            r1, _ = calculate_partial_correlation(df_half1, x_col, y_col, control_cols)
            r2, _ = calculate_partial_correlation(df_half2, x_col, y_col, control_cols)
        else:
            r1, _ = stats.pearsonr(df_half1[x_col], df_half1[y_col])
            r2, _ = stats.pearsonr(df_half2[x_col], df_half2[y_col])
        
        # Handle NaN correlations
        if np.isnan(r1) or np.isnan(r2):
            continue
        
        correlations_half1.append(r1)
        correlations_half2.append(r2)
    
    if len(correlations_half1) < 5:
        logger.warning(f"Could not complete enough iterations for split-half reliability")
        return {
            'reliability_coeff': 0.0,
            'std_reliability': 0.0,
            'n_iterations': len(correlations_half1),
            'status': 'LOW_ITERATIONS',
            'message': f'Only completed {len(correlations_half1)} valid iterations'
        }
    
    # Calculate correlation between the two halves
    r_split_half, p_value = stats.pearsonr(correlations_half1, correlations_half2)
    
    # Apply Spearman-Brown prophecy formula to correct for half-length
    # r_sb = (2 * r_split) / (1 + r_split)
    if r_split_half < -1.0:
        r_split_half = -1.0
    if r_split_half > 1.0:
        r_split_half = 1.0
        
    reliability_coeff = (2 * r_split_half) / (1 + r_split_half) if (1 + r_split_half) != 0 else 0.0
    
    # Calculate standard deviation of reliability estimates across iterations
    # (using bootstrapped reliability from the split correlations)
    reliability_estimates = [(2 * r) / (1 + r) if (1 + r) != 0 else 0.0 
                             for r in correlations_half1]
    std_reliability = float(np.std(reliability_estimates))
    
    logger.info(f"Split-half reliability: {reliability_coeff:.4f} (SD: {std_reliability:.4f})")
    
    return {
        'reliability_coeff': float(reliability_coeff),
        'std_reliability': std_reliability,
        'n_iterations': len(correlations_half1),
        'correlation_half1_mean': float(np.mean(correlations_half1)),
        'correlation_half2_mean': float(np.mean(correlations_half2)),
        'split_half_correlation': float(r_split_half),
        'p_value': float(p_value),
        'status': 'SUCCESS'
    }

def main():
    """Main entry point for correlation analysis with split-half reliability."""
    # Setup logging
    log_dir = Path(__file__).parent.parent / 'data' / 'results'
    log_dir.mkdir(parents=True, exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / 'correlation_analysis.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    logger.info("Starting correlation analysis with split-half reliability")
    
    try:
        config = load_config()
        
        # Paths to metric files (adjust based on actual output from previous steps)
        base_path = Path(__file__).parent.parent / 'data'
        alpha_power_path = base_path / 'metrics' / 'alpha_power.csv'
        plv_path = base_path / 'metrics' / 'plv.csv'
        wm_path = base_path / 'metrics' / 'wm_capacity.csv'
        
        # Verify files exist
        for path in [alpha_power_path, plv_path, wm_path]:
            if not path.exists():
                logger.error(f"Required metric file not found: {path}")
                sys.exit(1)
        
        # Merge metrics
        merged_df = merge_metrics(
            str(alpha_power_path), 
            str(plv_path), 
            str(wm_path)
        )
        
        if merged_df.empty:
            logger.error("No data after merging metrics")
            sys.exit(1)
        
        logger.info(f"Loaded {len(merged_df)} subjects for analysis")
        
        # Select variables for analysis
        # Assuming 'alpha_power' and 'wm_k' are the main variables
        # Adjust column names based on actual data structure
        x_col = 'alpha_power'
        y_col = 'wm_k'
        control_cols = ['plv']  # Example control variable
        
        # Check if columns exist
        if x_col not in merged_df.columns:
            # Try to find similar column
            possible_x = [c for c in merged_df.columns if 'alpha' in c.lower()]
            if possible_x:
                x_col = possible_x[0]
                logger.info(f"Using {x_col} as x variable")
            else:
                raise ValueError(f"Could not find alpha power column. Available: {merged_df.columns.tolist()}")
        
        if y_col not in merged_df.columns:
            possible_y = [c for c in merged_df.columns if 'wm' in c.lower() or 'capacity' in c.lower()]
            if possible_y:
                y_col = possible_y[0]
                logger.info(f"Using {y_col} as y variable")
            else:
                raise ValueError(f"Could not find WM capacity column. Available: {merged_df.columns.tolist()}")
        
        # Run split-half reliability analysis
        logger.info(f"Running split-half reliability for {x_col} vs {y_col}")
        
        reliability_results = run_split_half_reliability(
            merged_df, 
            x_col, 
            y_col, 
            control_cols=control_cols,
            n_iterations=100,
            random_seed=config.get('random_seed', 42)
        )
        
        # Save results
        results_path = log_dir / 'split_half_reliability.json'
        with open(results_path, 'w') as f:
            json.dump(reliability_results, f, indent=2)
        
        logger.info(f"Split-half reliability results saved to {results_path}")
        
        # Print summary
        print("\n" + "="*50)
        print("SPLIT-HALF RELIABILITY ANALYSIS RESULTS")
        print("="*50)
        print(f"Reliability Coefficient (Spearman-Brown): {reliability_results['reliability_coeff']:.4f}")
        print(f"Standard Deviation: {reliability_results['std_reliability']:.4f}")
        print(f"Number of Valid Iterations: {reliability_results['n_iterations']}")
        print(f"Status: {reliability_results['status']}")
        
        if reliability_results['status'] == 'SUCCESS':
            if reliability_results['reliability_coeff'] >= 0.7:
                print("Status: PASS - Reliability meets threshold (≥0.7)")
            else:
                print("Status: LOW - Reliability below threshold (<0.7)")
        print("="*50)
        
    except Exception as e:
        logger.error(f"Analysis failed: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == '__main__':
    main()