import os
import sys
import logging
import json
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple, Union
import pandas as pd
import numpy as np
from statsmodels.formula.api import ols
from statsmodels.stats.anova import anova_lm
from statsmodels.stats.multitest import multipletests
from statsmodels.regression.mixed_linear_model import MixedLM

class StatsError(Exception):
    """Custom exception for statistics module errors."""
    pass

def load_aggregated_metrics(metrics_path: str) -> pd.DataFrame:
    """
    Load aggregated geometry and fidelity metrics from a JSON/CSV file.
    
    Args:
        metrics_path: Path to the aggregated metrics file.
        
    Returns:
        DataFrame containing the metrics.
        
    Raises:
        StatsError: If the file cannot be loaded or is empty.
    """
    path = Path(metrics_path)
    if not path.exists():
        raise StatsError(f"Aggregated metrics file not found: {metrics_path}")
    
    if path.suffix == '.csv':
        df = pd.read_csv(path)
    elif path.suffix == '.json':
        with open(path, 'r') as f:
            data = json.load(f)
            df = pd.DataFrame(data)
    else:
        raise StatsError(f"Unsupported file format: {path.suffix}")
    
    if df.empty:
        raise StatsError("Aggregated metrics file is empty")
        
    return df

def check_collinearity(df: pd.DataFrame, threshold: float = 5.0) -> bool:
    """
    Check for multicollinearity in the dataset using Variance Inflation Factor (VIF).
    
    Args:
        df: DataFrame containing the features.
        threshold: VIF threshold above which collinearity is considered high.
        
    Returns:
        True if collinearity is detected (VIF >= threshold), False otherwise.
    """
    from statsmodels.stats.outliers_influence import variance_inflation_factor
    
    # Select numeric columns for VIF calculation
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    
    if len(numeric_cols) < 2:
        return False
        
    X = df[numeric_cols].dropna()
    if X.empty:
        return False
        
    # Add constant for intercept
    X_with_const = sm.add_constant(X)
    
    vif_data = []
    for col in X_with_const.columns:
        if col != 'const':
            try:
                vif = variance_inflation_factor(X_with_const.values, X_with_const.columns.get_loc(col))
                vif_data.append(vif)
                if vif >= threshold:
                    return True
            except Exception:
                continue
                
    return False

def fit_fixed_effects_anova(df: pd.DataFrame, formula: str) -> Dict[str, Any]:
    """
    Fit a Fixed-Effects ANOVA model.
    
    Args:
        df: DataFrame containing the data.
        formula: Model formula (e.g., 'fidelity ~ method').
        
    Returns:
        Dictionary containing model results and statistics.
    """
    import statsmodels.api as sm
    
    try:
        model = ols(formula, data=df).fit()
        anova_table = anova_lm(model, typ=2)
        
        return {
            'model_type': 'Fixed-Effects ANOVA',
            'formula': formula,
            'anova_table': anova_table.to_dict(),
            'params': model.params.to_dict(),
            'rsquared': model.rsquared,
            'f_pvalue': model.f_pvalue,
            'success': True
        }
    except Exception as e:
        logging.error(f"Fixed-Effects ANOVA failed: {e}")
        return {
            'model_type': 'Fixed-Effects ANOVA',
            'formula': formula,
            'error': str(e),
            'success': False
        }

def fit_mixed_effects_model(df: pd.DataFrame, formula: str, group_col: str) -> Dict[str, Any]:
    """
    Fit a Mixed-Effects Linear Model.
    
    Args:
        df: DataFrame containing the data.
        formula: Model formula (e.g., 'fidelity ~ method').
        group_col: Column name for the random effect grouping variable.
        
    Returns:
        Dictionary containing model results and statistics.
    """
    try:
        # Ensure group_col is categorical
        df[group_col] = df[group_col].astype('category')
        
        # Fit the mixed model
        # Formula format: dependent ~ independent + (1|group)
        # We construct the formula dynamically
        mixed_formula = f"{formula} + (1|{group_col})"
        
        # statsmodels MixedLM requires a specific formula syntax
        # We use the simpler approach: specify groups explicitly
        if group_col not in df.columns:
            raise StatsError(f"Group column '{group_col}' not found in data")
            
        # Prepare data for MixedLM
        # Extract fixed effects and random effects groups
        # Using a simpler approach: fit OLS with group as fixed effect first to check
        # Then try MixedLM if needed
        
        # Direct MixedLM implementation
        # We need to parse the formula to extract dependent and independent variables
        # For simplicity, we assume the formula is 'fidelity ~ method'
        
        dependent_var = formula.split('~')[0].strip()
        if dependent_var not in df.columns:
            raise StatsError(f"Dependent variable '{dependent_var}' not found in data")
            
        # Create design matrix for fixed effects
        # Using patsy for formula parsing
        import patsy
        
        # Parse the fixed effects part of the formula
        fixed_part = formula.split('+')[0].strip() # Take the part before the random effect
        if '+' in formula:
            fixed_part = formula.split('+')[0].strip()
            # Remove the random effect part for fixed effects design
            # The random effect is usually in the format (1|group)
            
        y, X = patsy.dmatrices(formula, df, return_type='dataframe')
        
        # Handle the random effect part
        # MixedLM expects groups to be passed separately
        groups = df[group_col]
        
        # Fit the model
        # Note: MixedLM formula syntax in statsmodels is slightly different
        # We use the direct matrix approach for clarity
        model = MixedLM(y, X, groups=groups)
        result = model.fit()
        
        return {
            'model_type': 'Mixed-Effects Model',
            'formula': formula,
            'groups': group_col,
            'params': result.params.to_dict() if hasattr(result.params, 'to_dict') else dict(result.params),
            'random_effects_params': result.random_effects.to_dict() if hasattr(result.random_effects, 'to_dict') else {},
            'f_pvalue': result.f_pvalue,
            'loglike': result.llf,
            'success': True
        }
    except Exception as e:
        logging.error(f"Mixed-Effects Model failed: {e}")
        return {
            'model_type': 'Mixed-Effects Model',
            'formula': formula,
            'groups': group_col,
            'error': str(e),
            'success': False
        }

def fit_simplified_model(df: pd.DataFrame, formula: str) -> Dict[str, Any]:
    """
    Fit a simplified model (e.g., t-test or simple ANOVA) when the full model fails.
    
    Args:
        df: DataFrame containing the data.
        formula: Model formula.
        
    Returns:
        Dictionary containing simplified model results.
    """
    import scipy.stats as stats
    
    try:
        dependent_var = formula.split('~')[0].strip()
        independent_var = formula.split('~')[1].strip().split('+')[0].strip()
        
        if dependent_var not in df.columns or independent_var not in df.columns:
            raise StatsError("Variables not found in data")
            
        # Group by independent variable
        groups = [group[dependent_var].values for name, group in df.groupby(independent_var)]
        
        if len(groups) == 2:
            # T-test for two groups
            stat, p_value = stats.ttest_ind(groups[0], groups[1])
            return {
                'model_type': 'T-Test (Simplified)',
                'statistic': stat,
                'p_value': p_value,
                'success': True
            }
        elif len(groups) > 2:
            # One-way ANOVA for multiple groups
            stat, p_value = stats.f_oneway(*groups)
            return {
                'model_type': 'One-way ANOVA (Simplified)',
                'statistic': stat,
                'p_value': p_value,
                'success': True
            }
        else:
            raise StatsError("Insufficient groups for statistical test")
            
    except Exception as e:
        logging.error(f"Simplified model failed: {e}")
        return {
            'model_type': 'Simplified Model',
            'error': str(e),
            'success': False
        }

def run_interaction_test(df: pd.DataFrame, formula: str, alpha: float = 0.05) -> Dict[str, Any]:
    """
    Run ANOVA F-tests for interaction terms.
    
    Args:
        df: DataFrame containing the data.
        formula: Model formula.
        alpha: Significance level.
        
    Returns:
        Dictionary containing interaction test results.
    """
    try:
        model = ols(formula, data=df).fit()
        anova_table = anova_lm(model, typ=2)
        
        # Extract p-values for interaction terms
        interaction_terms = [row for row in anova_table.index if ':' in row]
        
        results = {
            'interaction_terms': interaction_terms,
            'p_values': {},
            'significant': {}
        }
        
        for term in interaction_terms:
            if term in anova_table.index:
                p_val = anova_table.loc[term, 'PR(>F)']
                results['p_values'][term] = p_val
                results['significant'][term] = p_val < alpha
                
        return results
    except Exception as e:
        logging.error(f"Interaction test failed: {e}")
        return {'error': str(e), 'success': False}

def apply_benjamini_hochberg(p_values: List[float], alpha: float = 0.05) -> Tuple[List[float], List[bool]]:
    """
    Apply Benjamini-Hochberg correction to a list of p-values.
    
    Args:
        p_values: List of p-values to correct.
        alpha: Significance level.
        
    Returns:
        Tuple of (adjusted p-values, boolean list indicating significance).
    """
    try:
        # Use statsmodels for BH correction
        reject, pvals_corrected, _, _ = multipletests(p_values, alpha=alpha, method='fdr_bh')
        return pvals_corrected.tolist(), reject.tolist()
    except Exception as e:
        logging.error(f"Benjamini-Hochberg correction failed: {e}")
        return p_values, [p < alpha for p in p_values]

def save_results(results: Dict[str, Any], output_path: str) -> None:
    """
    Save statistical analysis results to a JSON file.
    
    Args:
        results: Dictionary containing analysis results.
        output_path: Path to save the results.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    # Convert numpy types to Python native types for JSON serialization
    def convert_numpy_types(obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, dict):
            return {k: convert_numpy_types(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_numpy_types(i) for i in obj]
        return obj
        
    clean_results = convert_numpy_types(results)
    
    with open(path, 'w') as f:
        json.dump(clean_results, f, indent=2)
        
    logging.info(f"Results saved to {output_path}")

def run_analysis_with_error_handling(df: pd.DataFrame, model_type: str, formula: str, group_col: Optional[str] = None) -> Dict[str, Any]:
    """
    Run statistical analysis with comprehensive error handling.
    
    Args:
        df: DataFrame containing the data.
        model_type: Type of model to fit ('fixed', 'mixed', 'simplified').
        formula: Model formula.
        group_col: Group column for mixed-effects model.
        
    Returns:
        Dictionary containing the analysis results.
    """
    results = {
        'model_type': model_type,
        'formula': formula,
        'group_col': group_col,
        'success': False,
        'error': None
    }
    
    try:
        if model_type == 'mixed' and group_col:
            # Check VIF for collinearity
            if check_collinearity(df):
                logging.warning("High collinearity detected (VIF >= 5). Attempting simplified model.")
                results['collinearity_warning'] = True
                return run_analysis_with_error_handling(df, 'simplified', formula, group_col)
                
            model_result = fit_mixed_effects_model(df, formula, group_col)
        elif model_type == 'fixed':
            model_result = fit_fixed_effects_anova(df, formula)
        elif model_type == 'simplified':
            model_result = fit_simplified_model(df, formula)
        else:
            raise StatsError(f"Unknown model type: {model_type}")
            
        results.update(model_result)
        results['success'] = model_result.get('success', False)
        
    except Exception as e:
        results['error'] = str(e)
        logging.error(f"Analysis failed: {e}")
        
    return results

def main():
    """
    Main entry point for the statistics module.
    Loads aggregated metrics, runs statistical analysis, and saves results.
    """
    logging.basicConfig(level=logging.INFO)
    
    # Default paths (can be overridden by command line arguments)
    metrics_path = "data/processed/aggregated_metrics.csv"
    output_path = "results/statistical_analysis.json"
    
    # Parse command line arguments
    if len(sys.argv) > 1:
        metrics_path = sys.argv[1]
    if len(sys.argv) > 2:
        output_path = sys.argv[2]
        
    try:
        # Load data
        logging.info(f"Loading aggregated metrics from {metrics_path}")
        df = load_aggregated_metrics(metrics_path)
        
        # Determine number of datasets
        n_datasets = df['dataset_id'].nunique() if 'dataset_id' in df.columns else 1
        
        # Select model based on number of datasets
        if n_datasets == 1:
            model_type = 'fixed'
            logging.info("Single dataset detected. Using Fixed-Effects ANOVA (Case-Study Mode).")
        elif n_datasets <= 3:
            model_type = 'fixed'
            logging.info(f"Detected {n_datasets} datasets. Using Fixed-Effects ANOVA.")
        else:
            model_type = 'mixed'
            logging.info(f"Detected {n_datasets} datasets. Using Mixed-Effects Model.")
            
        # Define formula
        formula = "fidelity_metric ~ method"
        
        # Check if required columns exist
        required_cols = ['fidelity_metric', 'method']
        if not all(col in df.columns for col in required_cols):
            # Try to find similar columns
            if 'fidelity' in df.columns:
                df['fidelity_metric'] = df['fidelity']
            if 'embedding_method' in df.columns:
                df['method'] = df['embedding_method']
                
            if not all(col in df.columns for col in required_cols):
                raise StatsError(f"Required columns {required_cols} not found in data")
                
        # Run analysis
        group_col = 'dataset_id' if model_type == 'mixed' and 'dataset_id' in df.columns else None
        
        results = run_analysis_with_error_handling(df, model_type, formula, group_col)
        
        # Apply Benjamini-Hochberg correction if we have multiple p-values
        if 'anova_table' in results and 'PR(>F)' in results['anova_table']:
            p_values = list(results['anova_table']['PR(>F)'].values())
            if len(p_values) > 1:
                adjusted_p, significant = apply_benjamini_hochberg(p_values)
                results['adjusted_p_values'] = adjusted_p
                results['significant_after_correction'] = significant
                
        # Save results
        save_results(results, output_path)
        
        logging.info("Statistical analysis completed successfully.")
        return 0
        
    except Exception as e:
        logging.error(f"Main analysis failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())