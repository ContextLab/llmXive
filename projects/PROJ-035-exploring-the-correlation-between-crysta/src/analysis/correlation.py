import sys
import logging
import json
import argparse
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union
import pandas as pd
import numpy as np
from scipy import stats

# Import from project utilities
from src.utils.validation import setup_logger
from src.utils.seed_manager import init_seed, get_seed

# Import from project analysis modules
from src.analysis.stratify import stratify_dataframe, classify_chemistry

def setup_logger_module(name: str) -> logging.Logger:
    """
    Setup a module-level logger.
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        logger.addHandler(handler)
    return logger

logger = setup_logger_module(__name__)

def compute_correlation_matrix(
    df: pd.DataFrame,
    predictors: List[str],
    target: str,
    method: str = 'pearson'
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Compute correlation matrix between predictors and target.
    
    Args:
        df: Input dataframe
        predictors: List of predictor column names
        target: Target column name
        method: 'pearson' or 'spearman'
        
    Returns:
        Tuple of (correlation coefficients dataframe, p-values dataframe)
    """
    if method not in ['pearson', 'spearman']:
        raise ValueError(f"Method must be 'pearson' or 'spearman', got {method}")
    
    # Select relevant columns
    cols = predictors + [target]
    data = df[cols].dropna()
    
    if len(data) < 3:
        raise ValueError("Insufficient data points for correlation analysis")
    
    coeffs = []
    pvals = []
    
    for pred in predictors:
        if method == 'pearson':
            corr, pval = stats.pearsonr(data[pred], data[target])
        else:
            corr, pval = stats.spearmanr(data[pred], data[target])
        
        coeffs.append(corr)
        pvals.append(pval)
    
    coeffs_df = pd.DataFrame({
        'predictor': predictors,
        'correlation': coeffs
    })
    pvals_df = pd.DataFrame({
        'predictor': predictors,
        'p_value': pvals
    })
    
    return coeffs_df, pvals_df

def apply_multiple_comparison_correction(
    p_values: List[float],
    method: str = 'bonferroni'
) -> List[float]:
    """
    Apply multiple comparison correction to p-values.
    
    Args:
        p_values: List of raw p-values
        method: 'bonferroni' or 'fdr' (Benjamini-Hochberg)
        
    Returns:
        List of corrected p-values
    """
    p_values = np.array(p_values)
    n_tests = len(p_values)
    
    if method == 'bonferroni':
        corrected = p_values * n_tests
        corrected = np.minimum(corrected, 1.0)
    elif method == 'fdr':
        # Benjamini-Hochberg procedure
        sorted_indices = np.argsort(p_values)
        sorted_pvals = p_values[sorted_indices]
        
        corrected_sorted = np.zeros(n_tests)
        for i in range(n_tests):
            rank = i + 1
            corrected_sorted[i] = sorted_pvals[i] * n_tests / rank
        
        # Ensure monotonicity (cumulative min from the end)
        for i in range(n_tests - 2, -1, -1):
            corrected_sorted[i] = min(corrected_sorted[i], corrected_sorted[i + 1])
        
        # Unsort back to original order
        corrected = np.zeros(n_tests)
        corrected[sorted_indices] = corrected_sorted
        corrected = np.minimum(corrected, 1.0)
    else:
        raise ValueError(f"Unknown correction method: {method}")
    
    return corrected.tolist()

def stratified_correlation_analysis(
    df: pd.DataFrame,
    predictors: List[str],
    target: str,
    method: str = 'pearson',
    correction_method: str = 'bonferroni',
    stratify_col: str = 'chemistry_class'
) -> Dict[str, Any]:
    """
    Perform correlation analysis stratified by a categorical column.
    
    Args:
        df: Input dataframe
        predictors: List of predictor column names
        target: Target column name
        method: Correlation method ('pearson' or 'spearman')
        correction_method: Multiple comparison correction method
        stratify_col: Column to stratify by
        
    Returns:
        Dictionary with stratified results and corrected p-values
    """
    # Ensure stratify_col exists
    if stratify_col not in df.columns:
        # Try to classify if not present
        if 'chemistry' in str(stratify_col).lower():
            df[stratify_col] = df.apply(lambda row: classify_chemistry(row), axis=1)
        else:
            raise ValueError(f"Stratify column '{stratify_col}' not found in dataframe")
    
    results = {}
    
    # Get unique strata
    strata = df[stratify_col].dropna().unique()
    
    for stratum in strata:
        stratum_df = df[df[stratify_col] == stratum]
        
        if len(stratum_df) < 3:
            logger.warning(f"Insufficient samples for stratum {stratum} (n={len(stratum_df)})")
            continue
        
        coeffs_df, pvals_df = compute_correlation_matrix(
            stratum_df, predictors, target, method
        )
        
        # Apply correction
        corrected_pvals = apply_multiple_comparison_correction(
            pvals_df['p_value'].tolist(), correction_method
        )
        
        # Combine results
        result_dict = coeffs_df.to_dict('records')
        for i, entry in enumerate(result_dict):
            entry['corrected_p_value'] = corrected_pvals[i]
            entry['raw_p_value'] = pvals_df.iloc[i]['p_value']
        
        results[stratum] = {
            'sample_size': len(stratum_df),
            'correlations': result_dict
        }
    
    return results

def save_correlation_results(
    results: Dict[str, Any],
    output_path: Path
) -> None:
    """
    Save correlation analysis results to JSON file.
    
    Args:
        results: Results dictionary from stratified_correlation_analysis
        output_path: Path to output JSON file
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    logger.info(f"Results saved to {output_path}")

def main():
    """
    Main entry point for correlation analysis.
    """
    parser = argparse.ArgumentParser(
        description='Perform stratified correlation analysis with multiple comparison correction'
    )
    parser.add_argument(
        '--input',
        type=str,
        required=True,
        help='Path to input CSV file (stratified data)'
    )
    parser.add_argument(
        '--output',
        type=str,
        required=True,
        help='Path to output JSON file'
    )
    parser.add_argument(
        '--target',
        type=str,
        default='thermal_conductivity',
        help='Target variable column name'
    )
    parser.add_argument(
        '--method',
        type=str,
        choices=['pearson', 'spearman'],
        default='pearson',
        help='Correlation method'
    )
    parser.add_argument(
        '--correction-method',
        type=str,
        choices=['bonferroni', 'fdr'],
        default='bonferroni',
        help='Multiple comparison correction method'
    )
    parser.add_argument(
        '--stratify-col',
        type=str,
        default='chemistry_class',
        help='Column to stratify by'
    )
    parser.add_argument(
        '--seed',
        type=int,
        default=42,
        help='Random seed for reproducibility'
    )
    
    args = parser.parse_args()
    
    # Initialize seed
    init_seed(args.seed)
    logger.info(f"Initialized seed: {get_seed()}")
    
    # Load input data
    input_path = Path(args.input)
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        sys.exit(1)
    
    df = pd.read_csv(input_path)
    logger.info(f"Loaded {len(df)} rows from {input_path}")
    
    # Define predictors (exclude non-predictor columns)
    exclude_cols = ['structure_id', 'source_reference', 'chemistry_class', args.target]
    predictors = [col for col in df.columns if col not in exclude_cols]
    
    if not predictors:
        logger.error("No predictor columns found in dataframe")
        sys.exit(1)
    
    logger.info(f"Using predictors: {predictors}")
    
    # Perform stratified analysis
    results = stratified_correlation_analysis(
        df=df,
        predictors=predictors,
        target=args.target,
        method=args.method,
        correction_method=args.correction_method,
        stratify_col=args.stratify_col
    )
    
    # Save results
    output_path = Path(args.output)
    save_correlation_results(results, output_path)
    
    # Also save sensitivity analysis reference (as required by task)
    # The task requires reading sensitivity_analysis.json, so we verify it exists
    sensitivity_path = Path('data/results/sensitivity_analysis.json')
    if sensitivity_path.exists():
        logger.info(f"Sensitivity analysis file found: {sensitivity_path}")
        # Load and log a summary
        with open(sensitivity_path, 'r') as f:
            sens_data = json.load(f)
            logger.info(f"Sensitivity analysis keys: {list(sens_data.keys())}")
    else:
        logger.warning(f"Sensitivity analysis file not found: {sensitivity_path}")
    
    logger.info("Correlation analysis completed successfully")

if __name__ == '__main__':
    main()