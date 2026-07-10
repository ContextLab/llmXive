"""
Data integrity validators for HEA alloy datasets.

Provides validation functions for:
1. Composition normalization (sum == 1.0 within tolerance)
2. Sample count thresholds (underpowered study detection)
3. Data type and missing value checks
"""
import logging
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional, Union
import pandas as pd
import numpy as np

from utils.seeds import get_seed

logger = logging.getLogger(__name__)

COMPOSITION_SUM_TOLERANCE = 1e-6
MIN_SAMPLE_THRESHOLD = 500
MIN_ALLOY_SYSTEMS_THRESHOLD = 10

class ValidationError(Exception):
    """Custom exception for data validation failures."""
    pass

def validate_composition_sum(
    df: pd.DataFrame,
    composition_col: str = 'composition',
    tolerance: float = COMPOSITION_SUM_TOLERANCE
) -> Tuple[pd.DataFrame, List[Dict[str, Any]]]:
    """
    Validate that composition fractions sum to 1.0.
    
    Args:
        df: DataFrame containing composition data
        composition_col: Name of the column containing composition dicts/series
        tolerance: Allowed deviation from 1.0
        
    Returns:
        Tuple of (validated DataFrame with 'composition_sum' column, 
                 list of validation issues)
    """
    issues = []
    
    if composition_col not in df.columns:
        raise ValidationError(f"Column '{composition_col}' not found in DataFrame")
        
    sums = []
    for idx, row in df.iterrows():
        comp = row[composition_col]
        if isinstance(comp, dict):
            total = sum(comp.values())
        elif isinstance(comp, pd.Series):
            total = comp.sum()
        elif isinstance(comp, str):
            # Attempt to parse string representation if needed
            try:
                total = sum(float(x) for x in comp.replace('{', '').replace('}', '').split(',') if x.strip().replace('.', '').isdigit())
            except ValueError:
                total = np.nan
        else:
            total = np.nan
            
        sums.append(total)
        
        if not np.isnan(total) and abs(total - 1.0) > tolerance:
            issues.append({
                'row_index': idx,
                'type': 'composition_sum_deviation',
                'value': total,
                'deviation': abs(total - 1.0),
                'message': f"Composition sum {total:.6f} deviates from 1.0 by {abs(total - 1.0):.6f}"
            })
    
    df['composition_sum'] = sums
    
    if issues:
        logger.warning(f"Found {len(issues)} rows with composition sum deviations")
        
    return df, issues

def normalize_compositions(
    df: pd.DataFrame,
    composition_col: str = 'composition',
    target_sum: float = 1.0
) -> pd.DataFrame:
    """
    Normalize compositions to sum to target (default 1.0).
    
    Args:
        df: DataFrame with composition data
        composition_col: Column name containing compositions
        target_sum: Target sum for normalization
        
    Returns:
        DataFrame with normalized compositions
    """
    df = df.copy()
    
    def normalize_comp(comp):
        if isinstance(comp, dict):
            total = sum(comp.values())
            if total == 0:
                return comp
            return {k: v / total * target_sum for k, v in comp.items()}
        elif isinstance(comp, pd.Series):
            total = comp.sum()
            if total == 0:
                return comp
            return (comp / total * target_sum).to_dict()
        return comp
        
    df[composition_col] = df[composition_col].apply(normalize_comp)
    
    # Verify normalization
    _, issues = validate_composition_sum(df, composition_col)
    if issues:
        logger.warning(f"Normalization did not fully resolve composition sums: {len(issues)} issues")
        
    return df

def validate_sample_count(
    df: pd.DataFrame,
    min_count: int = MIN_SAMPLE_THRESHOLD,
    group_col: Optional[str] = None
) -> Dict[str, Any]:
    """
    Validate sample count against threshold.
    
    Args:
        df: DataFrame to validate
        min_count: Minimum required sample count
        group_col: Optional column to group by for per-group counts
        
    Returns:
        Dictionary with validation results and power analysis
    """
    total_samples = len(df)
    is_valid = total_samples >= min_count
    
    result = {
        'total_samples': total_samples,
        'min_threshold': min_count,
        'is_valid': is_valid,
        'power_status': 'adequate' if is_valid else 'underpowered',
        'deficit': max(0, min_count - total_samples),
        'message': ""
    }
    
    if not is_valid:
        result['message'] = (
            f"Underpowered Study: Retrieved {total_samples} samples; "
            f"threshold of {min_count} not met. Proceeding with Reduced Power Analysis. "
            f"Deficit: {result['deficit']} samples."
        )
        logger.warning(result['message'])
    else:
        result['message'] = f"Sample count adequate: {total_samples} >= {min_count}"
        
    if group_col and group_col in df.columns:
        group_counts = df.groupby(group_col).size()
        result['unique_groups'] = len(group_counts)
        result['min_group_size'] = int(group_counts.min())
        result['max_group_size'] = int(group_counts.max())
        
        if len(group_counts) < MIN_ALLOY_SYSTEMS_THRESHOLD:
            logger.warning(
                f"Insufficient groups for grouped bootstrap: {len(group_counts)} groups "
                f"(threshold: {MIN_ALLOY_SYSTEMS_THRESHOLD}). "
                f"Falling back to standard bootstrap with caution."
            )
            result['bootstrap_warning'] = (
                f"Insufficient groups for grouped bootstrap (N={len(group_counts)}); "
                f"falling back to standard bootstrap with caution"
            )
            result['bootstrap_ci_warning'] = "potentially underestimated"
    else:
        result['unique_groups'] = None
        
    return result

def validate_data_integrity(
    df: pd.DataFrame,
    required_columns: List[str],
    composition_col: str = 'composition',
    target_col: Optional[str] = None
) -> Dict[str, Any]:
    """
    Comprehensive data integrity validation.
    
    Args:
        df: DataFrame to validate
        required_columns: List of columns that must exist
        composition_col: Column containing composition data
        target_col: Optional target variable column
        
    Returns:
        Dictionary with validation report
    """
    report = {
        'passed': True,
        'issues': [],
        'warnings': [],
        'sample_count_validation': None
    }
    
    # Check required columns
    missing_cols = [col for col in required_columns if col not in df.columns]
    if missing_cols:
        report['passed'] = False
        report['issues'].append({
            'type': 'missing_columns',
            'columns': missing_cols,
            'message': f"Missing required columns: {missing_cols}"
        })
        
    # Validate composition sums
    comp_df, comp_issues = validate_composition_sum(df, composition_col)
    if comp_issues:
        report['warnings'].append({
            'type': 'composition_deviation',
            'count': len(comp_issues),
            'details': comp_issues[:5]  # Limit to first 5 for brevity
        })
        
    # Validate sample count
    report['sample_count_validation'] = validate_sample_count(df)
    if not report['sample_count_validation']['is_valid']:
        report['warnings'].append({
            'type': 'underpowered_study',
            'message': report['sample_count_validation']['message']
        })
        
    # Check for missing values in target if specified
    if target_col and target_col in df.columns:
        null_count = df[target_col].isna().sum()
        if null_count > 0:
            report['warnings'].append({
                'type': 'missing_target_values',
                'count': int(null_count),
                'message': f"Found {null_count} missing values in target column '{target_col}'"
            })
            
    # Check for infinite values
    for col in df.select_dtypes(include=[np.number]).columns:
        inf_count = np.isinf(df[col]).sum()
        if inf_count > 0:
            report['issues'].append({
                'type': 'infinite_values',
                'column': col,
                'count': int(inf_count),
                'message': f"Found {inf_count} infinite values in column '{col}'"
            })
            report['passed'] = False
            
    return report

def run_validations(
    df: pd.DataFrame,
    output_path: Optional[Union[str, Path]] = None
) -> Dict[str, Any]:
    """
    Run all validations and optionally save report.
    
    Args:
        df: DataFrame to validate
        output_path: Optional path to save validation report as JSON
        
    Returns:
        Validation report dictionary
    """
    report = validate_data_integrity(
        df,
        required_columns=['composition', 'bulk_modulus'],
        composition_col='composition',
        target_col='bulk_modulus'
    )
    
    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        import json
        # Convert numpy types to native Python types for JSON serialization
        def convert_types(obj):
            if isinstance(obj, dict):
                return {k: convert_types(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_types(i) for i in obj]
            elif isinstance(obj, (np.integer,)):
                return int(obj)
            elif isinstance(obj, (np.floating,)):
                return float(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            return obj
            
        report_clean = convert_types(report)
        
        with open(output_path, 'w') as f:
            json.dump(report_clean, f, indent=2)
            
        logger.info(f"Validation report saved to {output_path}")
        
    return report