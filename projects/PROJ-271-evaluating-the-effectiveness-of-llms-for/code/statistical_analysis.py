import os
import json
import logging
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
import statsmodels.api as sm
from scipy import stats
from sklearn.linear_model import LogisticRegression
from statsmodels.stats.outliers_influence import variance_inflation_factor

from config import get_path, get_data_path, get_processed_path, get_results_path, setup_logging
from helpers import (
    calculate_statistics, parse_smell_labels, create_detection_matrix,
    validate_dataset_completeness, safe_divide
)

logger = setup_logging(__name__)

def load_static_baseline(filepath: Optional[str] = None) -> pd.DataFrame:
    """Loads the static baseline CSV file."""
    if filepath is None:
        filepath = str(get_data_path("static_baseline.csv"))
    
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Static baseline file not found: {filepath}")
    
    df = pd.read_csv(filepath)
    logger.info(f"Loaded static baseline with {len(df)} rows")
    return df

def load_semantic_results(filepath: Optional[str] = None) -> List[Dict[str, Any]]:
    """Loads the semantic results JSON file."""
    if filepath is None:
        filepath = str(get_processed_path("semantic_results.json"))
    
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Semantic results file not found: {filepath}")
    
    with open(filepath, 'r') as f:
        data = json.load(f)
    
    logger.info(f"Loaded semantic results with {len(data)} entries")
    return data

def merge_datasets(static_df: pd.DataFrame, semantic_data: List[Dict[str, Any]]) -> pd.DataFrame:
    """Merges static baseline and semantic results into a unified dataset."""
    # Convert semantic data to DataFrame
    semantic_rows = []
    for item in semantic_data:
        row = {
            'code': item.get('code'),
            'static_labels': item.get('static_labels', []),
            'llm_labels': item.get('llm_labels', []),
            'embedding': item.get('embedding'),
            'static_only': len(set(item.get('static_labels', [])) - set(item.get('llm_labels', []))),
            'llm_only': len(set(item.get('llm_labels', [])) - set(item.get('static_labels', []))),
            'both': len(set(item.get('static_labels', [])) & set(item.get('llm_labels', [])))
        }
        
        # Calculate mean semantic embedding
        embedding = item.get('embedding')
        if embedding and isinstance(embedding, list):
            row['semantic_mean'] = float(np.mean(embedding))
        else:
            row['semantic_mean'] = 0.0
        
        semantic_rows.append(row)
    
    semantic_df = pd.DataFrame(semantic_rows)
    
    # Merge on code (assuming code is unique or we use index)
    # For simplicity, we'll assume the order matches or we merge by index
    if len(static_df) == len(semantic_df):
        merged = pd.concat([static_df.reset_index(drop=True), semantic_df.reset_index(drop=True)], axis=1)
    else:
        # Fallback: try to merge by code if available in both
        if 'code' in static_df.columns and 'code' in semantic_df.columns:
            merged = pd.merge(static_df, semantic_df, on='code', how='inner')
        else:
            logger.warning("Cannot merge datasets: mismatched lengths and no common key")
            merged = pd.concat([static_df, semantic_df], axis=1)
    
    logger.info(f"Merged dataset has {len(merged)} rows")
    return merged

def validate_merged_dataset(df: pd.DataFrame, threshold: float = 0.95) -> bool:
    """Validates the merged dataset has required fields and completeness."""
    required_cols = ['code', 'loc', 'cyclomatic_complexity', 'nesting_depth', 
                   'static_labels', 'llm_labels', 'semantic_mean']
    
    return validate_dataset_completeness(df, required_cols, threshold)

def run_mcnemar_test(static_labels: List[str], llm_labels: List[str]) -> Dict[str, float]:
    """
    Runs McNemar's test for paired nominal data.
    
    Compares detection outcomes between static and LLM analysis.
    
    Args:
        static_labels: List of labels from static analysis.
        llm_labels: List of labels from LLM analysis.
    
    Returns:
        Dictionary with 'chi2' statistic and 'pvalue'.
    """
    # Create contingency table
    # a = both detected, b = static only, c = llm only, d = neither
    a = len(set(static_labels) & set(llm_labels))
    b = len(set(static_labels) - set(llm_labels))
    c = len(set(llm_labels) - set(static_labels))
    d = 0 # Neither is context dependent, usually not counted in McNemar for this use case
    
    # McNemar's test requires b and c
    if b + c == 0:
        return {'chi2': 0.0, 'pvalue': 1.0}
    
    chi2, pvalue = stats.binom_test(min(b, c), n=b+c, p=0.5, alternative='two-sided')
    
    return {'chi2': float(chi2), 'pvalue': float(pvalue)}

def calculate_vif(features: pd.DataFrame) -> Dict[str, float]:
    """
    Calculates Variance Inflation Factor (VIF) for each feature.
    
    Args:
        features: DataFrame with numeric features.
    
    Returns:
        Dictionary mapping feature names to VIF scores.
    """
    if features.empty:
        return {}
    
    # Add constant for intercept
    X = sm.add_constant(features)
    
    vif_data = {}
    for i, col in enumerate(features.columns):
        vif = variance_inflation_factor(X.values, i + 1) # +1 because of constant
        vif_data[col] = float(vif)
    
    return vif_data

def run_logistic_regression_with_vif_filter(
    features: pd.DataFrame, 
    target: pd.Series, 
    vif_threshold: float = 5.0
) -> Dict[str, Any]:
    """
    Runs logistic regression with VIF-based feature filtering.
    
    Excludes predictors with VIF >= threshold, prioritizing exclusion of highest VIF.
    
    Args:
        features: DataFrame of features.
        target: Target variable series.
        vif_threshold: Maximum allowed VIF.
    
    Returns:
        Dictionary with coefficients, excluded features, and model metrics.
    """
    excluded_features = []
    current_features = features.copy()
    
    while True:
        vif_scores = calculate_vif(current_features)
        if not vif_scores:
            break
        
        max_vif_feature = max(vif_scores, key=vif_scores.get)
        max_vif = vif_scores[max_vif_feature]
        
        if max_vif >= vif_threshold:
            logger.warning(f"Excluding '{max_vif_feature}' with VIF={max_vif:.2f} >= {vif_threshold}")
            excluded_features.append({
                'feature': max_vif_feature,
                'vif': max_vif,
                'reason': f"VIF >= {vif_threshold}"
            })
            current_features = current_features.drop(columns=[max_vif_feature])
        else:
            break
    
    if current_features.empty:
        logger.error("All features excluded due to high VIF")
        return {
            'coefficients': {},
            'excluded_features': excluded_features,
            'model': None,
            'warning': "No features remaining for regression"
        }
    
    # Fit logistic regression
    X = sm.add_constant(current_features)
    model = sm.Logit(target, X).fit(disp=0)
    
    coefficients = {}
    for param in model.params.index:
        if param != 'const':
            coefficients[param] = float(model.params[param])
    
    return {
        'coefficients': coefficients,
        'excluded_features': excluded_features,
        'model': model,
        'vif_scores': calculate_vif(current_features),
        'pvalues': {param: float(model.pvalues[param]) for param in model.pvalues.index if param != 'const'}
    }

def generate_vif_report(excluded_features: List[Dict], vif_scores: Dict[str, float], output_path: str):
    """Generates a markdown report for VIF analysis."""
    report_lines = [
        "# VIF Analysis Report\n",
        "## Excluded Features\n",
        "| Feature | VIF Score | Reason |\n",
        "|---------|-----------|--------|\n"
    ]
    
    for item in excluded_features:
        report_lines.append(f"| {item['feature']} | {item['vif']:.2f} | {item['reason']} |\n")
    
    report_lines.append("\n## Remaining Feature VIF Scores\n")
    for feat, vif in vif_scores.items():
        report_lines.append(f"- {feat}: {vif:.2f}\n")
    
    with open(output_path, 'w') as f:
        f.writelines(report_lines)
    
    logger.info(f"VIF report saved to {output_path}")

def run_sensitivity_analysis(
    df: pd.DataFrame, 
    loc_thresholds: List[int],
    target_col: str = 'llm_only'
) -> List[Dict[str, Any]]:
    """
    Runs sensitivity analysis across different LOC thresholds.
    
    Calculates false-positive and false-negative rates for static-only detection.
    
    Args:
        df: Merged dataset.
        loc_thresholds: List of LOC thresholds to test.
        target_col: Column name for LLM-only detection flag.
    
    Returns:
        List of dictionaries with threshold, fp_rate, and fn_rate.
    """
    results = []
    
    for threshold in loc_thresholds:
        # Static detected: loc >= threshold
        static_detected = df['loc'] >= threshold
        # LLM detected: llm_only > 0 or both > 0 (simplified)
        llm_detected = (df['llm_only'] > 0) | (df['both'] > 0)
        
        # True positives: both detected
        tp = (static_detected & llm_detected).sum()
        # False positives: static detected but not LLM
        fp = (static_detected & ~llm_detected).sum()
        # False negatives: LLM detected but not static
        fn = (~static_detected & llm_detected).sum()
        # Total static detected
        total_static = static_detected.sum()
        # Total LLM detected
        total_llm = llm_detected.sum()
        
        fp_rate = safe_divide(fp, total_static)
        fn_rate = safe_divide(fn, total_llm)
        
        results.append({
            'threshold': threshold,
            'fp_rate': fp_rate,
            'fn_rate': fn_rate,
            'tp': int(tp),
            'fp': int(fp),
            'fn': int(fn)
        })
    
    return results

def run_statistical_analysis(
    static_baseline_path: Optional[str] = None,
    semantic_results_path: Optional[str] = None,
    output_dir: Optional[str] = None
) -> Dict[str, Any]:
    """
    Runs the full statistical analysis pipeline.
    
    Args:
        static_baseline_path: Path to static baseline CSV.
        semantic_results_path: Path to semantic results JSON.
        output_dir: Directory for output files.
    
    Returns:
        Dictionary with analysis results.
    """
    if output_dir is None:
        output_dir = str(get_results_path())
    
    # Load data
    static_df = load_static_baseline(static_baseline_path)
    semantic_data = load_semantic_results(semantic_results_path)
    
    # Merge datasets
    merged_df = merge_datasets(static_df, semantic_data)
    
    # Validate
    is_valid = validate_merged_dataset(merged_df)
    if not is_valid:
        logger.error("Merged dataset validation failed")
        return {'error': 'Dataset validation failed'}
    
    # Prepare features for regression
    feature_cols = ['loc', 'cyclomatic_complexity', 'nesting_depth', 'semantic_mean']
    available_cols = [col for col in feature_cols if col in merged_df.columns]
    
    if len(available_cols) < len(feature_cols):
        logger.warning(f"Missing feature columns: {set(feature_cols) - set(available_cols)}")
    
    X = merged_df[available_cols].fillna(0)
    # Create target: 1 if LLM detected any smell, 0 otherwise
    y = ((merged_df['llm_only'] > 0) | (merged_df['both'] > 0)).astype(int)
    
    # Run VIF and regression
    regression_results = run_logistic_regression_with_vif_filter(X, y)
    
    # Generate VIF report
    vif_report_path = os.path.join(output_dir, "vif_report.md")
    if regression_results.get('excluded_features'):
        generate_vif_report(
            regression_results['excluded_features'],
            regression_results.get('vif_scores', {}),
            vif_report_path
        )
    
    # Run McNemar's test
    mcnemar_results = run_mcnemar_test(
        merged_df['static_labels'].iloc[0] if isinstance(merged_df['static_labels'].iloc[0], list) else [],
        merged_df['llm_labels'].iloc[0] if isinstance(merged_df['llm_labels'].iloc[0], list) else []
    )
    
    # Sensitivity analysis
    loc_thresholds = [50, 100, 200, 500]
    sensitivity_results = run_sensitivity_analysis(merged_df, loc_thresholds)
    
    # Prepare final output
    return {
        'merged_dataset_info': {
            'rows': len(merged_df),
            'columns': list(merged_df.columns),
            'valid': is_valid
        },
        'regression': {
            'coefficients': regression_results['coefficients'],
            'excluded_features': regression_results['excluded_features'],
            'vif_scores': regression_results.get('vif_scores', {})
        },
        'mcnemar': mcnemar_results,
        'sensitivity': sensitivity_results,
        'vif_report_path': vif_report_path if regression_results.get('excluded_features') else None
    }

def main():
    """Main entry point for statistical analysis."""
    logger.info("Starting statistical analysis")
    
    try:
        results = run_statistical_analysis()
        
        # Save results
        results_path = get_results_path("statistical_significance.json")
        with open(results_path, 'w') as f:
            # Convert non-serializable objects
            serializable_results = {
                k: v for k, v in results.items() if k != 'regression' or k != 'model'
            }
            if 'regression' in serializable_results:
                serializable_results['regression'] = {
                    k: v for k, v in serializable_results['regression'].items() if k != 'model'
                }
            json.dump(serializable_results, f, indent=2, default=str)
        
        logger.info(f"Analysis complete. Results saved to {results_path}")
        
    except Exception as e:
        logger.error(f"Statistical analysis failed: {e}")
        raise

if __name__ == "__main__":
    main()
