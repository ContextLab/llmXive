import os
import json
import logging
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from code.config import get_data_path, get_processed_path, get_results_path, setup_logging
from code.monitoring import get_ram_usage_mb, get_cpu_utilization

logger = logging.getLogger(__name__)

def load_static_baseline() -> pd.DataFrame:
    """Load the static baseline CSV."""
    path = os.path.join(get_data_path(), "static_baseline.csv")
    if not os.path.exists(path):
        raise FileNotFoundError(f"Static baseline not found at {path}")
    df = pd.read_csv(path)
    logger.info(f"Loaded static baseline with {len(df)} rows")
    return df

def load_semantic_results() -> pd.DataFrame:
    """Load the semantic results JSON and convert to DataFrame."""
    path = os.path.join(get_processed_path(), "semantic_results.json")
    if not os.path.exists(path):
        raise FileNotFoundError(f"Semantic results not found at {path}")
    
    with open(path, 'r') as f:
        data = json.load(f)
    
    # Ensure it's a list of dicts
    if isinstance(data, dict) and 'results' in data:
        data = data['results']
    
    df = pd.DataFrame(data)
    logger.info(f"Loaded semantic results with {len(df)} rows")
    return df

def merge_datasets(static_df: pd.DataFrame, semantic_df: pd.DataFrame) -> pd.DataFrame:
    """Merge static and semantic datasets on function index."""
    # Ensure both have a common index or id column
    if 'id' in static_df.columns and 'id' in semantic_df.columns:
        merged = pd.merge(static_df, semantic_df, on='id', how='inner')
    elif 'index' in static_df.columns and 'index' in semantic_df.columns:
        merged = pd.merge(static_df, semantic_df, on='index', how='inner')
    else:
        # Fallback: assume same order and add index
        static_df = static_df.reset_index(drop=True)
        semantic_df = semantic_df.reset_index(drop=True)
        static_df['index'] = static_df.index
        semantic_df['index'] = semantic_df.index
        merged = pd.merge(static_df, semantic_df, on='index', how='inner')
    
    logger.info(f"Merged dataset has {len(merged)} rows")
    return merged

def validate_merged_dataset(merged_df: pd.DataFrame, threshold: float = 0.95) -> Tuple[bool, Dict[str, Any]]:
    """
    Validate that >= 95% of rows have all required fields.
    Required fields: code, loc, cyclomatic_complexity, static_smell_labels, 
                     semantic_vectors, llm_labels
    """
    required_fields = [
        'code', 
        'loc', 
        'cyclomatic_complexity', 
        'static_smell_labels', 
        'semantic_vectors', 
        'llm_labels'
    ]
    
    total_rows = len(merged_df)
    if total_rows == 0:
        logger.error("Merged dataset is empty")
        return False, {"valid": False, "reason": "Empty dataset"}
    
    # Check for required columns
    missing_cols = [col for col in required_fields if col not in merged_df.columns]
    if missing_cols:
        logger.error(f"Missing required columns: {missing_cols}")
        return False, {"valid": False, "reason": f"Missing columns: {missing_cols}"}
    
    # Count rows with all required fields populated (not null/empty)
    valid_count = 0
    for idx, row in merged_df.iterrows():
        is_valid = True
        for field in required_fields:
            val = row[field]
            if pd.isna(val) or (isinstance(val, str) and val.strip() == ""):
                is_valid = False
                break
            # For list-like fields (semantic_vectors, smell_labels), ensure they aren't empty
            if isinstance(val, str):
                try:
                    # Try to parse if it's a JSON string representation
                    parsed = json.loads(val)
                    if isinstance(parsed, (list, dict)) and len(parsed) == 0:
                        is_valid = False
                        break
                except (json.JSONDecodeError, TypeError):
                    # If it's a plain string, it's valid as long as not empty
                    pass
            elif isinstance(val, (list, dict)) and len(val) == 0:
                is_valid = False
                break
        
        if is_valid:
            valid_count += 1
    
    completeness_ratio = valid_count / total_rows
    is_valid = completeness_ratio >= threshold
    
    result = {
        "valid": is_valid,
        "total_rows": total_rows,
        "valid_rows": valid_count,
        "completeness_ratio": completeness_ratio,
        "threshold": threshold,
        "required_fields": required_fields
    }
    
    if is_valid:
        logger.info(f"Dataset validation PASSED: {completeness_ratio:.2%} rows valid (>= {threshold:.0%})")
    else:
        logger.error(f"Dataset validation FAILED: {completeness_ratio:.2%} rows valid (< {threshold:.0%})")
    
    return is_valid, result

def parse_smell_labels(label_str: str) -> List[str]:
    """Parse a string of smell labels into a list."""
    if pd.isna(label_str) or not isinstance(label_str, str):
        return []
    try:
        # Try JSON parse first
        parsed = json.loads(label_str)
        if isinstance(parsed, list):
            return parsed
        elif isinstance(parsed, str):
            # Handle comma-separated string
            return [s.strip() for s in parsed.split(',') if s.strip()]
    except (json.JSONDecodeError, TypeError):
        # Handle comma-separated string directly
        return [s.strip() for s in label_str.split(',') if s.strip()]
    return []

def create_detection_matrix(merged_df: pd.DataFrame) -> pd.DataFrame:
    """Create a binary detection matrix for each smell category."""
    all_smells = set()
    
    # Collect all unique smells from both static and LLM labels
    for labels_col in ['static_smell_labels', 'llm_labels']:
        if labels_col in merged_df.columns:
            for labels in merged_df[labels_col]:
                parsed = parse_smell_labels(labels)
                all_smells.update(parsed)
    
    # Create binary columns
    detection_matrix = pd.DataFrame(index=merged_df.index)
    detection_matrix['id'] = merged_df['id'] if 'id' in merged_df.columns else merged_df.index
    
    for smell in sorted(all_smells):
        detection_matrix[f'static_{smell}'] = merged_df['static_smell_labels'].apply(
            lambda x: 1 if smell in parse_smell_labels(x) else 0
        )
        detection_matrix[f'llm_{smell}'] = merged_df['llm_labels'].apply(
            lambda x: 1 if smell in parse_smell_labels(x) else 0
        )
    
    return detection_matrix

def run_mcnemar_test(static_col: str, llm_col: str, df: pd.DataFrame) -> Dict[str, Any]:
    """
    Perform McNemar's test for paired nominal data.
    Returns p-value and test statistic.
    """
    try:
        from statsmodels.stats.contingency_tables import mcnemar
        
        # Create contingency table
        table = pd.crosstab(df[static_col], df[llm_col])
        
        # Ensure we have the right structure
        if 0 not in table.index or 1 not in table.index:
            return {"p_value": None, "statistic": None, "error": "Missing categories"}
        if 0 not in table.columns or 1 not in table.columns:
            return {"p_value": None, "statistic": None, "error": "Missing categories"}
        
        result = mcnemar(table, exact=True)
        return {
            "p_value": float(result.pvalue),
            "statistic": float(result.statistic),
            "table": table.to_dict()
        }
    except Exception as e:
        logger.warning(f"McNemar test failed: {e}")
        return {"p_value": None, "statistic": None, "error": str(e)}

def calculate_vif(df: pd.DataFrame, feature_cols: List[str]) -> pd.Series:
    """Calculate Variance Inflation Factor for each feature."""
    from statsmodels.stats.outliers_influence import variance_inflation_factor
    
    vif_data = pd.Series(index=feature_cols, dtype=float)
    
    # Add constant for intercept
    X = df[feature_cols].dropna()
    if len(X) < 2:
        return vif_data.fillna(np.nan)
    
    X = sm.add_constant(X)
    
    for i, col in enumerate(feature_cols):
        try:
            vif = variance_inflation_factor(X.values, i + 1)  # +1 because of constant
            vif_data[col] = vif
        except Exception as e:
            logger.warning(f"VIF calculation failed for {col}: {e}")
            vif_data[col] = np.nan
    
    return vif_data

def fit_logistic_regression(merged_df: pd.DataFrame, target_col: str, feature_cols: List[str]) -> Dict[str, Any]:
    """Fit logistic regression with VIF filtering."""
    import statsmodels.api as sm
    
    # Filter out high VIF features
    vif_scores = calculate_vif(merged_df, feature_cols)
    low_vif_features = [f for f in feature_cols if vif_scores.get(f, np.inf) < 5]
    
    if len(low_vif_features) == 0:
        return {"error": "All features have VIF >= 5", "coefficients": {}, "vif_scores": vif_scores.to_dict()}
    
    X = merged_df[low_vif_features].dropna()
    y = merged_df.loc[X.index, target_col]
    
    if len(X) < 2 or len(y) < 2:
        return {"error": "Insufficient data after filtering", "coefficients": {}, "vif_scores": vif_scores.to_dict()}
    
    X = sm.add_constant(X)
    model = sm.Logit(y, X).fit(disp=False)
    
    return {
        "coefficients": model.params.to_dict(),
        "p_values": model.pvalues.to_dict(),
        "vif_scores": vif_scores.to_dict(),
        "excluded_features": [f for f in feature_cols if vif_scores.get(f, np.inf) >= 5]
    }

def run_sensitivity_analysis(merged_df: pd.DataFrame, loc_thresholds: List[int] = [50, 100, 150]) -> Dict[str, Any]:
    """Run sensitivity analysis across different LOC thresholds."""
    results = {}
    
    for threshold in loc_thresholds:
        high_loc = merged_df[merged_df['loc'] >= threshold]
        low_loc = merged_df[merged_df['loc'] < threshold]
        
        # Calculate detection rates
        def calc_rate(df, smell_col):
            if len(df) == 0:
                return 0.0
            return df[smell_col].apply(lambda x: len(parse_smell_labels(x)) > 0).mean()
        
        results[threshold] = {
            "high_loc_rate": calc_rate(high_loc, 'static_smell_labels'),
            "low_loc_rate": calc_rate(low_loc, 'static_smell_labels'),
            "high_loc_llm_rate": calc_rate(high_loc, 'llm_labels'),
            "low_loc_llm_rate": calc_rate(low_loc, 'llm_labels'),
            "sample_size_high": len(high_loc),
            "sample_size_low": len(low_loc)
        }
    
    return results

def generate_sensitivity_report(sensitivity_results: Dict[str, Any], merged_df: pd.DataFrame) -> str:
    """Generate a markdown report for sensitivity analysis."""
    report = "# Sensitivity Analysis Report\n\n"
    report += "## Overview\n\n"
    report += f"Total samples: {len(merged_df)}\n\n"
    
    report += "## Results by LOC Threshold\n\n"
    for threshold, data in sensitivity_results.items():
        report += f"### LOC >= {threshold}\n\n"
        report += f"- Static detection rate: {data['high_loc_rate']:.2%}\n"
        report += f"- LLM detection rate: {data['high_loc_llm_rate']:.2%}\n"
        report += f"- Sample size: {data['sample_size_high']}\n\n"
        
        report += f"### LOC < {threshold}\n\n"
        report += f"- Static detection rate: {data['low_loc_rate']:.2%}\n"
        report += f"- LLM detection rate: {data['low_loc_llm_rate']:.2%}\n"
        report += f"- Sample size: {data['sample_size_low']}\n\n"
    
    return report

def run_statistical_analysis():
    """Main function to run the full statistical analysis pipeline."""
    setup_logging()
    
    try:
        # Load data
        logger.info("Loading static baseline...")
        static_df = load_static_baseline()
        
        logger.info("Loading semantic results...")
        semantic_df = load_semantic_results()
        
        # Merge datasets
        logger.info("Merging datasets...")
        merged_df = merge_datasets(static_df, semantic_df)
        
        # Validate merged dataset (T021a)
        logger.info("Validating merged dataset...")
        is_valid, validation_result = validate_merged_dataset(merged_df, threshold=0.95)
        
        if not is_valid:
            logger.error(f"Validation failed: {validation_result}")
            # Save validation result for inspection
            with open(os.path.join(get_results_path(), "validation_result.json"), 'w') as f:
                json.dump(validation_result, f, indent=2)
            raise ValueError("Merged dataset validation failed")
        
        # Save validation result
        with open(os.path.join(get_results_path(), "validation_result.json"), 'w') as f:
            json.dump(validation_result, f, indent=2)
        
        logger.info("Validation passed. Proceeding with analysis...")
        
        # Continue with other analyses (T022-T025)
        # ... (implementation of other tasks)
        
        return merged_df, validation_result
        
    except Exception as e:
        logger.error(f"Statistical analysis failed: {e}")
        raise

def main():
    """Entry point for the script."""
    run_statistical_analysis()

if __name__ == "__main__":
    main()
