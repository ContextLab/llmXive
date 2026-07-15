import os
import sys
import json
import yaml
import pandas as pd
import numpy as np
from statsmodels.stats.outliers_influence import variance_inflation_factor
from pathlib import Path

# Import shared config loader from analysis.py to ensure consistency
# Note: We assume analysis.py is importable from the same directory
try:
    from analysis import load_config as analysis_load_config
except ImportError:
    def analysis_load_config(config_path='code/config.yaml'):
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)

def load_analysis_results(results_path='data/analysis/correlation_results.json'):
    """
    Load the results from the correlation analysis.
    Expects a JSON file containing the correlation matrix or summary statistics.
    """
    if not os.path.exists(results_path):
        raise FileNotFoundError(f"Analysis results not found at {results_path}. "
                                "Run analysis.py first.")
    
    with open(results_path, 'r') as f:
        return json.load(f)

def calculate_vif(df: pd.DataFrame, feature_columns: list) -> pd.DataFrame:
    """
    Calculate Variance Inflation Factor (VIF) for a set of features.
    
    Args:
        df: DataFrame containing the features.
        feature_columns: List of column names to calculate VIF for.
        
    Returns:
        DataFrame with columns 'feature' and 'vif'.
    """
    # Select only the specified columns
    X = df[feature_columns].copy()
    
    # Handle constant columns (VIF is undefined for constant variables)
    # Replace constant columns with NaN or drop them before calculation
    # For VIF calculation, we need to add a constant for the intercept if using OLS,
    # but statsmodels' vif function expects the design matrix without the intercept
    # if we are calculating VIF for each predictor in the context of a model with intercept.
    # However, the standard formula VIF = 1 / (1 - R^2) where R^2 is from regressing
    # one predictor against all others.
    
    # Check for constant columns
    constant_cols = []
    for col in X.columns:
        if X[col].std() == 0:
            constant_cols.append(col)
    
    if constant_cols:
        print(f"Warning: The following columns are constant and will be excluded from VIF calculation: {constant_cols}")
        X = X.drop(columns=constant_cols)
    
    if X.shape[1] < 2:
        # VIF requires at least 2 variables to calculate correlation between them
        print("Warning: Less than 2 non-constant features provided. VIF cannot be calculated.")
        return pd.DataFrame(columns=['feature', 'vif'])

    vif_data = []
    for i, col in enumerate(X.columns):
        # Regress col against all other columns
        y = X[col]
        # Create a design matrix for the regression of y on other X columns
        # We do NOT add a constant here because the VIF formula inherently accounts for the intercept
        # by looking at R^2 of the auxiliary regression.
        # However, statsmodels vif function implementation usually expects the design matrix
        # that includes the constant if we were fitting a model, but for VIF calculation
        # specifically, we regress one predictor on the others.
        
        # The standard approach for VIF calculation using statsmodels:
        # VIF for feature j = 1 / (1 - R_j^2)
        # where R_j^2 is from regressing feature j on all other features.
        
        # We need to construct the design matrix for the auxiliary regression
        # excluding the target column 'col'
        other_cols = [c for c in X.columns if c != col]
        X_aux = X[other_cols]
        
        # Add constant for the auxiliary regression
        X_aux_with_const = sm.add_constant(X_aux)
        
        # Fit OLS
        try:
            model = sm.OLS(y, X_aux_with_const).fit()
            r_squared = model.rsquared
            vif = 1.0 / (1.0 - r_squared)
        except Exception as e:
            # If regression fails (e.g., perfect multicollinearity), VIF is infinite
            vif = np.inf
        
        vif_data.append({'feature': col, 'vif': vif})
    
    return pd.DataFrame(vif_data)

def run_collinearity_diagnostics(
    results_path: str = 'data/analysis/correlation_results.json',
    config_path: str = 'code/config.yaml',
    vif_threshold: float = 5.0,
    output_path: str = 'data/analysis/collinearity_report.json'
):
    """
    Run collinearity diagnostics on the combined metrics from the analysis.
    
    This function checks for multicollinearity among the complexity metrics
    (e.g., LZC and PE) if they are combined in a model, ensuring VIF < threshold.
    
    Args:
        results_path: Path to the correlation analysis results JSON.
        config_path: Path to the configuration YAML.
        vif_threshold: Maximum acceptable VIF value.
        output_path: Path to write the collinearity report JSON.
        
    Returns:
        Dictionary containing the diagnostics results.
    """
    config = analysis_load_config(config_path)
    
    # Load analysis results
    # The structure of results depends on how analysis.py outputs data.
    # We assume it contains a list of metrics or a correlation matrix.
    # For VIF, we need the actual data values for the features, not just correlations.
    # However, if only summary statistics are available, we might need to reconstruct
    # or use the correlation matrix to estimate VIF.
    # A more robust approach is to have the analysis script output the feature matrix
    # used in the regression.
    
    # Let's assume the analysis results contain a 'feature_matrix' or we need to
    # load the processed metrics from data/processed/
    # If the analysis.py output is just correlations, we can't calculate VIF directly
    # without the raw data.
    # The task says "if metrics are combined". This implies a regression model.
    # We need the data used in that model.
    
    # Strategy: Try to load the processed metrics from data/processed/
    # which are used in the analysis.
    lzc_path = 'data/processed/lzc_metrics.csv'
    pe_path = 'data/processed/pe_metrics.csv'
    
    combined_data = None
    
    if os.path.exists(lzc_path) and os.path.exists(pe_path):
        df_lzc = pd.read_csv(lzc_path)
        df_pe = pd.read_csv(pe_path)
        
        # Merge on participant_id and segment_id (or similar keys)
        # Assuming common keys: 'participant_id', 'segment_id'
        # Adjust based on actual data model
        common_keys = [col for col in df_lzc.columns if col in df_pe.columns]
        if common_keys:
            combined_data = pd.merge(df_lzc, df_pe, on=common_keys, suffixes=('_lzc', '_pe'))
            print(f"Combined data shape: {combined_data.shape}")
            print(f"Combined columns: {combined_data.columns.tolist()}")
        else:
            print("Warning: No common keys found to merge LZC and PE metrics.")
    else:
        print(f"Warning: Could not find processed metrics files at {lzc_path} or {pe_path}.")
        # Fallback: Try to load from results if it contains a matrix
        results = load_analysis_results(results_path)
        if 'feature_matrix' in results:
            combined_data = pd.DataFrame(results['feature_matrix'])
        else:
            raise ValueError("Could not locate feature data for VIF calculation. "
                             "Ensure processed metrics are available or analysis results contain 'feature_matrix'.")
    
    if combined_data is None or combined_data.empty:
        raise ValueError("No data available for collinearity diagnostics.")
    
    # Identify numeric columns that are likely features (not IDs or targets)
    # Exclude target variables (e.g., fatigue scores) if present
    numeric_cols = combined_data.select_dtypes(include=[np.number]).columns.tolist()
    
    # Heuristic: Exclude columns with 'fatigue' or 'score' in name if they are targets
    feature_cols = [col for col in numeric_cols if 'fatigue' not in col.lower() and 'score' not in col.lower()]
    
    if len(feature_cols) < 2:
        print("Warning: Less than 2 feature columns found for VIF calculation.")
        report = {
            'status': 'incomplete',
            'reason': 'Less than 2 features available.',
            'vif_results': []
        }
    else:
        vif_results_df = calculate_vif(combined_data, feature_cols)
        
        # Check threshold
        max_vif = vif_results_df['vif'].max()
        status = 'passed' if max_vif < vif_threshold else 'failed'
        
        report = {
            'status': status,
            'vif_threshold': vif_threshold,
            'max_vif': float(max_vif),
            'vif_results': vif_results_df.to_dict(orient='records'),
            'message': f"Collinearity check {'passed' if status == 'passed' else 'failed'}. "
                       f"Max VIF: {max_vif:.2f} (Threshold: {vif_threshold})"
        }
    
    # Write report
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"Collinearity report written to {output_path}")
    print(report['message'])
    
    return report

def main():
    """
    Main entry point for collinearity diagnostics.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Run collinearity diagnostics (VIF check).')
    parser.add_argument('--results', type=str, default='data/analysis/correlation_results.json',
                        help='Path to correlation analysis results JSON.')
    parser.add_argument('--config', type=str, default='code/config.yaml',
                        help='Path to configuration YAML.')
    parser.add_argument('--threshold', type=float, default=5.0,
                        help='VIF threshold (default: 5.0).')
    parser.add_argument('--output', type=str, default='data/analysis/collinearity_report.json',
                        help='Output path for collinearity report JSON.')
    
    args = parser.parse_args()
    
    try:
        run_collinearity_diagnostics(
            results_path=args.results,
            config_path=args.config,
            vif_threshold=args.threshold,
            output_path=args.output
        )
        sys.exit(0)
    except Exception as e:
        print(f"Error during collinearity diagnostics: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
