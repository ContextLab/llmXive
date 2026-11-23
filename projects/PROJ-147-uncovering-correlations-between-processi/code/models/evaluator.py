import os
import json
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
from code.utils.logging import get_logger, log_warning_structured
from code.config import ensure_dirs

logger = get_logger(__name__)

def load_model_predictions(predictions_path: str) -> pd.DataFrame:
    """
    Load model predictions from a CSV file.
    
    Args:
        predictions_path: Path to the predictions CSV file.
        
    Returns:
        DataFrame containing predictions and ground truth data.
    """
    if not os.path.exists(predictions_path):
        raise FileNotFoundError(f"Predictions file not found: {predictions_path}")
    
    df = pd.read_csv(predictions_path)
    logger.info(f"Loaded predictions from {predictions_path} with {len(df)} samples")
    return df

def compute_metrics_per_texture(predictions_df: pd.DataFrame, texture_cols: List[str]) -> Dict[str, Dict[str, float]]:
    """
    Compute R², MAE, and RMSE for each texture coefficient.
    
    Args:
        predictions_df: DataFrame with actual and predicted values.
        texture_cols: List of texture coefficient column names.
        
    Returns:
        Dictionary mapping texture coefficient to metrics.
    """
    metrics = {}
    for col in texture_cols:
        actual = predictions_df[f'actual_{col}'].values
        predicted = predictions_df[f'predicted_{col}'].values
        
        # R² calculation
        ss_res = np.sum((actual - predicted) ** 2)
        ss_tot = np.sum((actual - np.mean(actual)) ** 2)
        r2 = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0.0
        
        # MAE calculation
        mae = np.mean(np.abs(actual - predicted))
        
        # RMSE calculation
        rmse = np.sqrt(np.mean((actual - predicted) ** 2))
        
        metrics[col] = {
            'r2': float(r2),
            'mae': float(mae),
            'rmse': float(rmse)
        }
        
        logger.debug(f"Computed metrics for {col}: R²={r2:.4f}, MAE={mae:.4f}, RMSE={rmse:.4f}")
    
    return metrics

def compute_metrics_per_family(predictions_df: pd.DataFrame, texture_cols: List[str], family_col: str = 'alloy_family') -> Dict[str, Dict[str, Dict[str, float]]]:
    """
    Compute R², MAE, and RMSE for each texture coefficient per alloy family.
    
    Args:
        predictions_df: DataFrame with actual, predicted, and alloy family data.
        texture_cols: List of texture coefficient column names.
        family_col: Column name for alloy family.
        
    Returns:
        Nested dictionary: {family: {texture_col: {metric: value}}}
    """
    families = predictions_df[family_col].unique()
    family_metrics = {}
    
    for family in families:
        family_df = predictions_df[predictions_df[family_col] == family]
        family_metrics[family] = compute_metrics_per_texture(family_df, texture_cols)
        logger.info(f"Computed metrics for family {family} with {len(family_df)} samples")
    
    return family_metrics

def validate_sc002(importance_report: Dict[str, Any], threshold: float = 0.10) -> Tuple[bool, Dict[str, Any]]:
    """
    Validate Success Criterion 002 (SC-002): At least one variable importance >= 0.10 for EVERY AlloyFamily.
    
    This function checks the permutation importance report and verifies that for each alloy family,
    there exists at least one feature with importance >= 0.10.
    
    Args:
        importance_report: Dictionary containing feature importances per alloy family.
        threshold: Minimum importance threshold (default 0.10).
        
    Returns:
        Tuple of (is_valid, validation_details).
        is_valid: True if SC-002 is met for all families, False otherwise.
        validation_details: Dictionary with detailed results per family.
    """
    logger.info(f"Validating SC-002: checking for importance >= {threshold} in all alloy families")
    
    validation_details = {
        'threshold': threshold,
        'families_checked': [],
        'families_passed': [],
        'families_failed': [],
        'failed_families_details': {},
        'overall_passed': True
    }
    
    # Expected structure: importance_report = {family_name: {feature_name: importance_value, ...}, ...}
    # If the report uses a different structure (e.g., list of dicts), we adapt.
    
    if not isinstance(importance_report, dict):
        logger.error("Importance report is not a dictionary. SC-002 validation cannot proceed.")
        validation_details['overall_passed'] = False
        validation_details['error'] = "Invalid importance report structure"
        return False, validation_details
    
    for family_name, features in importance_report.items():
        family_result = {
            'family': family_name,
            'passed': False,
            'max_importance': 0.0,
            'top_features': []
        }
        
        if not isinstance(features, dict):
            # Try to handle list of feature dicts if structure is different
            if isinstance(features, list) and len(features) > 0:
                max_imp = max(f.get('importance', 0) for f in features)
                top_features = sorted(features, key=lambda x: x.get('importance', 0), reverse=True)[:5]
                family_result['max_importance'] = float(max_imp)
                family_result['top_features'] = top_features
            else:
                logger.warning(f"Unexpected structure for family {family_name} in importance report")
                max_imp = 0.0
                top_features = []
                family_result['max_importance'] = float(max_imp)
                family_result['top_features'] = []
        else:
            # Standard dict structure: {feature_name: importance_value}
            if not features:
                max_imp = 0.0
                top_features = []
            else:
                max_imp = max(features.values())
                sorted_features = sorted(features.items(), key=lambda x: x[1], reverse=True)[:5]
                top_features = [{'feature': k, 'importance': float(v)} for k, v in sorted_features]
            
            family_result['max_importance'] = float(max_imp)
            family_result['top_features'] = top_features
        
        validation_details['families_checked'].append(family_name)
        
        if family_result['max_importance'] >= threshold:
            family_result['passed'] = True
            validation_details['families_passed'].append(family_name)
            logger.info(f"SC-002 PASSED for family {family_name}: max importance = {family_result['max_importance']:.4f}")
        else:
            family_result['passed'] = False
            validation_details['families_failed'].append(family_name)
            validation_details['failed_families_details'][family_name] = {
                'max_importance': family_result['max_importance'],
                'threshold': threshold,
                'top_features': family_result['top_features']
            }
            validation_details['overall_passed'] = False
            logger.warning(f"SC-002 FAILED for family {family_name}: max importance = {family_result['max_importance']:.4f} < {threshold}")
    
    log_warning_structured(
        logger,
        "SC-002 Validation",
        f"Overall SC-002 status: {'PASSED' if validation_details['overall_passed'] else 'FAILED'}. "
        f"Checked {len(validation_details['families_checked'])} families, "
        f"{len(validation_details['families_passed'])} passed, "
        f"{len(validation_details['families_failed'])} failed.",
        data=validation_details
    )
    
    return validation_details['overall_passed'], validation_details

def run_evaluation(
    predictions_path: str,
    importance_report_path: Optional[str] = None,
    output_dir: str = 'data/processed',
    texture_cols: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Run full evaluation pipeline: load predictions, compute metrics, validate SC-002.
    
    Args:
        predictions_path: Path to predictions CSV.
        importance_report_path: Optional path to feature importance report JSON.
        output_dir: Directory to save evaluation report.
        texture_cols: Optional list of texture columns. If None, inferred from data.
        
    Returns:
        Complete evaluation report dictionary.
    """
    ensure_dirs(output_dir)
    
    # Load predictions
    predictions_df = load_model_predictions(predictions_path)
    
    # Infer texture columns if not provided
    if texture_cols is None:
        texture_cols = [col for col in predictions_df.columns if col.startswith('actual_') and col != 'actual_alloy_family']
        texture_cols = [col.replace('actual_', '') for col in texture_cols]
    
    logger.info(f"Using texture columns: {texture_cols}")
    
    # Compute metrics
    metrics_per_texture = compute_metrics_per_texture(predictions_df, texture_cols)
    metrics_per_family = compute_metrics_per_family(predictions_df, texture_cols)
    
    # Validate SC-002 if importance report is available
    sc002_result = {
        'validated': False,
        'passed': None,
        'details': None
    }
    
    if importance_report_path and os.path.exists(importance_report_path):
        logger.info(f"Loading importance report from {importance_report_path}")
        with open(importance_report_path, 'r') as f:
            importance_report = json.load(f)
        
        passed, details = validate_sc002(importance_report)
        sc002_result = {
            'validated': True,
            'passed': passed,
            'details': details
        }
        
        # Log failure but do NOT halt the pipeline
        if not passed:
            log_warning_structured(
                logger,
                "SC-002 Violation",
                "Success Criterion 002 (SC-002) failed for some alloy families. "
                "Pipeline will continue to sensitivity analysis as per requirements.",
                data={'failed_families': details['families_failed']}
            )
    else:
        logger.warning("No importance report provided or found. SC-002 validation skipped.")
    
    # Compile final report
    evaluation_report = {
        'metrics_per_texture': metrics_per_texture,
        'metrics_per_family': metrics_per_family,
        'sc002_validation': sc002_result,
        'data_source_type': 'Synthetic',  # Will be updated by main.py or caller if real data detected
        'timestamp': pd.Timestamp.now().isoformat()
    }
    
    # Save report
    report_path = os.path.join(output_dir, 'evaluation_report.json')
    with open(report_path, 'w') as f:
        json.dump(evaluation_report, f, indent=2)
    
    logger.info(f"Evaluation report saved to {report_path}")
    return evaluation_report

def evaluate_model(
    predictions_path: str,
    importance_report_path: Optional[str] = None,
    output_dir: str = 'data/processed'
) -> Dict[str, Any]:
    """
    Alias for run_evaluation to maintain API compatibility.
    """
    return run_evaluation(predictions_path, importance_report_path, output_dir)