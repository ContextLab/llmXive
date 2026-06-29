import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
import pandas as pd
import numpy as np

from utils.logger import get_logger, log_error_to_file

logger = get_logger(__name__)

def calculate_vif_for_column(df: pd.DataFrame, target_col: str) -> float:
    """
    Calculate Variance Inflation Factor (VIF) for a specific column.
    
    VIF = 1 / (1 - R^2) where R^2 is from regressing target_col against all other columns.
    
    Args:
        df: DataFrame containing the variables
        target_col: Name of the column to calculate VIF for
        
    Returns:
        float: VIF value. Returns np.inf if perfect collinearity is detected.
    """
    if target_col not in df.columns:
        raise ValueError(f"Column '{target_col}' not found in DataFrame")
        
    # Remove rows with NaN in the target column or any other column
    clean_df = df.dropna(subset=[target_col] + [c for c in df.columns if c != target_col])
    
    if len(clean_df) < 2:
        logger.warning("Insufficient data to calculate VIF")
        return np.nan
        
    # Prepare features (all columns except target)
    X = clean_df[[c for c in df.columns if c != target_col]]
    y = clean_df[target_col]
    
    # Handle case where X has only one column
    if X.shape[1] == 0:
        return 1.0
        
    # Add intercept
    X_with_intercept = X.copy()
    X_with_intercept['intercept'] = 1.0
    
    # Calculate R^2 using linear regression
    try:
        # Using numpy for simple OLS
        # y = X * beta + epsilon
        # beta = (X^T X)^-1 X^T y
        
        X_mat = X_with_intercept.values
        y_vec = y.values
        
        # Check for singularity
        if np.linalg.cond(X_mat) > 1e10:
            logger.warning("Matrix is nearly singular, VIF calculation may be unreliable")
            return np.inf
        
        # Solve for coefficients
        coeffs, residuals, rank, s = np.linalg.lstsq(X_mat, y_vec, rcond=None)
        
        # Calculate predictions
        y_pred = X_mat @ coeffs
        
        # Calculate R^2
        ss_res = np.sum((y_vec - y_pred) ** 2)
        ss_tot = np.sum((y_vec - np.mean(y_vec)) ** 2)
        
        if ss_tot == 0:
            return 1.0
            
        r_squared = 1 - (ss_res / ss_tot)
        
        # Calculate VIF
        if r_squared >= 1.0:
            return np.inf
        vif = 1.0 / (1.0 - r_squared)
        
        return vif
        
    except np.linalg.LinAlgError as e:
        logger.error(f"Linear algebra error in VIF calculation: {e}")
        return np.inf

def calculate_vif_matrix(df: pd.DataFrame) -> pd.Series:
    """
    Calculate VIF for all numeric columns in the DataFrame.
    
    Args:
        df: DataFrame containing numeric variables
        
    Returns:
        pd.Series: VIF values indexed by column name
    """
    # Select only numeric columns
    numeric_df = df.select_dtypes(include=[np.number])
    
    if numeric_df.empty:
        logger.warning("No numeric columns found in DataFrame")
        return pd.Series(dtype=float)
        
    vif_values = {}
    
    for col in numeric_df.columns:
        vif = calculate_vif_for_column(numeric_df, col)
        vif_values[col] = vif
        
    return pd.Series(vif_values)

def run_vif_analysis(df: pd.DataFrame, threshold: float = 5.0, 
                    columns_to_check: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Run VIF analysis on the provided DataFrame.
    
    Args:
        df: DataFrame to analyze
        threshold: VIF threshold above which collinearity is flagged
        columns_to_check: Optional list of specific columns to check. 
                         If None, checks all numeric columns.
                         
    Returns:
        Dict containing:
            - 'vif_scores': pd.Series of VIF values
            - 'high_collinearity': List of columns with VIF > threshold
            - 'summary': Dict with summary statistics
    """
    if columns_to_check is not None:
        # Filter DataFrame to only include specified columns
        check_df = df[columns_to_check].copy()
    else:
        check_df = df.copy()
        
    vif_scores = calculate_vif_matrix(check_df)
    
    if vif_scores.empty:
        return {
            'vif_scores': pd.Series(dtype=float),
            'high_collinearity': [],
            'summary': {'message': 'No numeric columns to analyze'}
        }
    
    high_collinearity = vif_scores[vif_scores > threshold].index.tolist()
    
    summary = {
        'total_columns_analyzed': len(vif_scores),
        'columns_with_high_collinearity': len(high_collinearity),
        'threshold_used': threshold,
        'max_vif': float(vif_scores.max()) if not np.isnan(vif_scores.max()) else None,
        'mean_vif': float(vif_scores.mean()) if not np.isnan(vif_scores.mean()) else None
    }
    
    # Log results
    logger.info(f"VIF Analysis Complete: {len(high_collinearity)} columns exceed threshold {threshold}")
    for col in high_collinearity:
        logger.warning(f"High collinearity detected for '{col}': VIF = {vif_scores[col]:.2f}")
    
    return {
        'vif_scores': vif_scores,
        'high_collinearity': high_collinearity,
        'summary': summary
    }

def audit_blame_definition(df: pd.DataFrame, target_col: str = 'choice') -> Dict[str, Any]:
    """
    Audit the target variable to verify it represents a behavioral outcome (choice)
    and not a self-reported moral judgment.
    
    This implements the "Blame Definition" audit requested by the Socratic critique,
    ensuring that the target variable is strictly a behavioral outcome.
    
    Args:
        df: DataFrame containing the data
        target_col: Name of the target column (default: 'choice')
        
    Returns:
        Dict containing:
            - 'is_behavioral': bool indicating if target is behavioral
            - 'modality': str describing the detected modality
            - 'warnings': List of warning messages
            - 'details': Dict with additional details about the audit
    """
    warnings = []
    modality = "unknown"
    is_behavioral = False
    
    if target_col not in df.columns:
        msg = f"Target column '{target_col}' not found in DataFrame"
        warnings.append(msg)
        logger.warning(msg)
        return {
            'is_behavioral': False,
            'modality': 'missing',
            'warnings': warnings,
            'details': {'target_col': target_col, 'available_columns': list(df.columns)}
        }
    
    target_data = df[target_col]
    
    # Check for common behavioral choice indicators
    # Behavioral choices are typically:
    # - Binary (0/1, True/False, 'left'/'right')
    # - Categorical with discrete options
    # - Numeric with limited distinct values (e.g., 0, 1, 2)
    
    # Check if it's binary
    unique_vals = target_data.dropna().unique()
    unique_count = len(unique_vals)
    
    # Check for binary behavioral patterns
    is_binary = unique_count == 2
    is_01 = set(unique_vals) == {0, 1} or set(unique_vals) == {0.0, 1.0}
    is_bool = target_data.dtype == bool or set(unique_vals) == {True, False}
    
    # Check for categorical behavioral patterns
    categorical_behavioral = {'left', 'right', 'A', 'B', 'option1', 'option2', 
                             'save_left', 'save_right', 'blame_A', 'blame_B'}
    is_categorical_behavioral = set(str(v).lower() for v in unique_vals if pd.notna(v)) <= categorical_behavioral
    
    # Check for self-reported judgment indicators
    # These might include Likert scales, continuous ratings, or explicit "judgment" labels
    likely_judgment_indicators = [
        'judgment', 'rating', 'score', 'moral', 'good', 'bad', 'right', 'wrong',
        'approve', 'disapprove', 'percent', 'likelihood'
    ]
    
    # Check column name for judgment indicators
    name_lower = target_col.lower()
    has_judgment_name = any(ind in name_lower for ind in ['judgment', 'moral', 'rating', 'score'])
    
    # Check if values look like Likert scales (e.g., 1-5, 1-7) or continuous ratings
    is_likert = unique_count > 2 and unique_count <= 10 and all(isinstance(v, (int, float)) for v in unique_vals if pd.notna(v))
    is_continuous = target_data.dtype == float and unique_count > 10
    
    # Determine modality
    if is_01 or is_bool or is_binary or is_categorical_behavioral:
        modality = "behavioral_choice"
        is_behavioral = True
        logger.info(f"Target '{target_col}' identified as behavioral choice (binary/categorical)")
        
    elif has_judgment_name or is_likert or is_continuous:
        modality = "self_reported_judgment"
        is_behavioral = False
        warning_msg = f"Target '{target_col}' appears to be self-reported moral judgment, not behavioral choice. " \
                     f"This may confound the analysis of attentional bias."
        warnings.append(warning_msg)
        logger.warning(warning_msg)
        
    else:
        modality = "mixed_or_unknown"
        is_behavioral = False
        warning_msg = f"Target '{target_col}' has {unique_count} unique values: {list(unique_vals[:10])}. " \
                     f"Unable to definitively classify as behavioral choice. Manual review recommended."
        warnings.append(warning_msg)
        logger.warning(warning_msg)
    
    # Check for mixed modalities (e.g., if the dataset contains multiple target-like columns)
    potential_targets = [col for col in df.columns if any(ind in col.lower() for ind in 
                         ['choice', 'decision', 'blame', 'judgment', 'select', 'pick'])]
    
    if len(potential_targets) > 1 and target_col in potential_targets:
        other_targets = [col for col in potential_targets if col != target_col]
        logger.info(f"Multiple potential target variables found: {potential_targets}")
        
        # Check if any other target looks like a judgment
        for other in other_targets:
            other_unique = df[other].dropna().unique()
            if len(other_unique) > 2 and len(other_unique) <= 10:
                warning_msg = f"Found potential self-reported judgment column '{other}' alongside behavioral target. " \
                             f"Mixed modalities detected in dataset."
                warnings.append(warning_msg)
                logger.warning(warning_msg)
                break
    
    details = {
        'target_column': target_col,
        'unique_values_count': unique_count,
        'unique_values_sample': list(unique_vals[:10]),
        'is_binary': is_binary,
        'is_01': is_01,
        'is_categorical_behavioral': is_categorical_behavioral,
        'has_judgment_name': has_judgment_name,
        'potential_other_targets': potential_targets
    }
    
    return {
        'is_behavioral': is_behavioral,
        'modality': modality,
        'warnings': warnings,
        'details': details
    }

def main():
    """
    Main function to run VIF analysis and Blame Definition audit.
    
    This script:
    1. Loads preprocessed data
    2. Runs VIF analysis on salience and control variables
    3. Audits the target variable for behavioral vs. judgment modalities
    4. Outputs reports to data/processed/
    """
    logger.info("Starting Diagnostics: VIF Analysis and Blame Definition Audit")
    
    # Paths
    project_root = Path(__file__).resolve().parent.parent.parent
    data_dir = project_root / "data" / "processed"
    output_dir = project_root / "data" / "processed"
    
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Load preprocessed data
    input_file = data_dir / "preprocessed_moral_machine.csv"
    
    if not input_file.exists():
        error_msg = f"Input file not found: {input_file}"
        logger.error(error_msg)
        log_error_to_file(error_msg, "diagnostics_errors.log")
        return
    
    logger.info(f"Loading data from {input_file}")
    df = pd.read_csv(input_file)
    
    logger.info(f"Loaded {len(df)} rows, {len(df.columns)} columns")
    
    # Define columns to check for VIF
    # Based on FR-008: salience_score, visual_salience, text_salience, and proxy controls
    vif_columns = ['salience_score']
    for col in ['visual_salience', 'text_salience', 'lives_lost', 'lives_saved', 
               'species', 'age', 'gender', 'social_status']:
        if col in df.columns:
            vif_columns.append(col)
    
    # Remove non-numeric columns for VIF calculation
    numeric_vif_columns = [col for col in vif_columns if col in df.select_dtypes(include=[np.number]).columns]
    
    # Run VIF analysis
    logger.info("Running VIF analysis...")
    vif_results = run_vif_analysis(df, threshold=5.0, columns_to_check=numeric_vif_columns)
    
    # Save VIF results
    vif_report_file = output_dir / "vif_analysis_report.json"
    serializable_vif = {
        'vif_scores': vif_results['vif_scores'].to_dict() if not vif_results['vif_scores'].empty else {},
        'high_collinearity': vif_results['high_collinearity'],
        'summary': vif_results['summary']
    }
    
    import json
    with open(vif_report_file, 'w') as f:
        json.dump(serializable_vif, f, indent=2)
    
    logger.info(f"VIF report saved to {vif_report_file}")
    
    # Run Blame Definition Audit
    logger.info("Running Blame Definition Audit...")
    audit_results = audit_blame_definition(df, target_col='choice')
    
    # Save audit results
    audit_report_file = output_dir / "blame_definition_audit.json"
    serializable_audit = {
        'is_behavioral': audit_results['is_behavioral'],
        'modality': audit_results['modality'],
        'warnings': audit_results['warnings'],
        'details': audit_results['details']
    }
    
    with open(audit_report_file, 'w') as f:
        json.dump(serializable_audit, f, indent=2)
    
    logger.info(f"Blame Definition Audit saved to {audit_report_file}")
    
    # Print summary
    print("\n" + "="*60)
    print("DIAGNOSTICS SUMMARY")
    print("="*60)
    print(f"VIF Analysis: {len(vif_results['high_collinearity'])} columns exceed threshold 5.0")
    if vif_results['high_collinearity']:
        print(f"  High collinearity columns: {vif_results['high_collinearity']}")
    
    print(f"\nBlame Definition Audit:")
    print(f"  Target modality: {audit_results['modality']}")
    print(f"  Is behavioral choice: {audit_results['is_behavioral']}")
    if audit_results['warnings']:
        print(f"  Warnings ({len(audit_results['warnings'])}):")
        for w in audit_results['warnings']:
            print(f"    - {w}")
    
    print("="*60)
    
    # If warnings were generated, log them to a dedicated file
    if audit_results['warnings']:
        warning_log = output_dir / "blame_definition_warnings.log"
        with open(warning_log, 'w') as f:
            f.write("Blame Definition Audit Warnings\n")
            f.write("="*40 + "\n")
            for w in audit_results['warnings']:
                f.write(f"WARNING: {w}\n")
        logger.info(f"Warnings logged to {warning_log}")
    
    logger.info("Diagnostics completed successfully")

if __name__ == "__main__":
    main()