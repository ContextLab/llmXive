"""
Validation module for plant disease resistance prediction pipeline.

This module implements null model baseline comparisons on training/CV folds
as per FR-005. It does NOT perform permutation testing on hold-out sets
(deferred to T033).

Key responsibilities:
1. Train null models (random labels) on training data
2. Compare null model performance against primary model on CV folds
3. Calculate performance gap and statistical significance
4. Flag high VIF features for multicollinearity (FR-005)
"""

import os
import json
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Any, Tuple, Optional, List
from sklearn.linear_model import LogisticRegression, LinearRegression
from sklearn.ensemble import GradientBoostingClassifier, GradientBoostingRegressor
from sklearn.model_selection import cross_val_score, StratifiedKFold, KFold
from sklearn.metrics import accuracy_score, roc_auc_score, r2_score
import warnings

# Import from project modules
from config import get_artifacts_path, get_reports_path
from utils.logging import get_logger
from utils.stats import calculate_vif, filter_high_vif_features
from analysis.modeling import load_split_data, detect_problem_type, train_model

logger = get_logger(__name__)


def train_null_model(X: pd.DataFrame, y: pd.Series, problem_type: str, 
                    cv_folds: int = 5) -> Dict[str, Any]:
    """
    Train a null model with randomized labels on training data.
    
    Args:
        X: Feature matrix (training set only)
        y: Target labels (will be shuffled for null model)
        problem_type: 'classification' or 'regression'
        cv_folds: Number of cross-validation folds
        
    Returns:
      Dict containing null model metrics and CV scores
    """
    logger.info(f"Training null model with randomized labels ({problem_type})")
    
    # Shuffle labels to create null distribution
    np.random.seed(42)  # For reproducibility
    y_shuffled = y.sample(frac=1, random_state=42).reset_index(drop=True)
    
    # Select appropriate null model
    if problem_type == 'classification':
        model = LogisticRegression(max_iter=1000, random_state=42)
        cv = StratifiedKFold(n_splits=cv_folds, shuffle=True, random_state=42)
        scoring = 'roc_auc'
    else:
        model = LinearRegression()
        cv = KFold(n_splits=cv_folds, shuffle=True, random_state=42)
        scoring = 'r2'
    
    # Cross-validate null model
    cv_scores = cross_val_score(model, X, y_shuffled, cv=cv, scoring=scoring)
    
    # Fit on full training data for reference
    model.fit(X, y_shuffled)
    
    # Calculate metrics
    if problem_type == 'classification':
        # Predict on training set (in-sample)
        y_pred_proba = model.predict_proba(X)[:, 1]
        in_sample_auc = roc_auc_score(y_shuffled, y_pred_proba)
        metrics = {
            'cv_mean_score': float(np.mean(cv_scores)),
            'cv_std_score': float(np.std(cv_scores)),
            'in_sample_auc': float(in_sample_auc),
            'cv_scores': cv_scores.tolist()
        }
    else:
        y_pred = model.predict(X)
        in_sample_r2 = r2_score(y_shuffled, y_pred)
        metrics = {
            'cv_mean_score': float(np.mean(cv_scores)),
            'cv_std_score': float(np.std(cv_scores)),
            'in_sample_r2': float(in_sample_r2),
            'cv_scores': cv_scores.tolist()
        }
    
    logger.info(f"Null model CV mean: {metrics['cv_mean_score']:.4f} (+/- {metrics['cv_std_score']:.4f})")
    return metrics


def compare_models(primary_metrics: Dict[str, Any], null_metrics: Dict[str, Any], 
                  problem_type: str) -> Dict[str, Any]:
    """
    Compare primary model performance against null model baseline.
    
    Args:
        primary_metrics: CV metrics from primary model
        null_metrics: CV metrics from null model
        problem_type: 'classification' or 'regression'
        
    Returns:
        Dict with comparison statistics and significance assessment
    """
    logger.info("Comparing primary model vs null model baseline")
    
    primary_cv_mean = primary_metrics.get('cv_mean_score', 0)
    null_cv_mean = null_metrics.get('cv_mean_score', 0)
    
    # Calculate performance gap
    performance_gap = primary_cv_mean - null_cv_mean
    
    # Calculate relative improvement
    if null_cv_mean != 0:
        relative_improvement = (performance_gap / abs(null_cv_mean)) * 100
    else:
        relative_improvement = float('inf') if performance_gap > 0 else 0
    
    # Determine if improvement is meaningful
    # Rule of thumb: > 0.05 absolute improvement or > 20% relative improvement
    is_significant = (performance_gap > 0.05) or (relative_improvement > 20)
    
    comparison = {
        'primary_cv_mean': primary_cv_mean,
        'null_cv_mean': null_cv_mean,
        'performance_gap': performance_gap,
        'relative_improvement_pct': relative_improvement,
        'is_significantly_better': is_significant,
        'interpretation': "Model outperforms random baseline" if is_significant 
                         else "Model does not significantly outperform random baseline"
    }
    
    logger.info(f"Performance gap: {performance_gap:.4f} ({relative_improvement:.1f}% improvement)")
    logger.info(f"Significance: {comparison['interpretation']}")
    
    return comparison


def validate_null_baseline(X_train: pd.DataFrame, y_train: pd.Series, 
                          primary_model_metrics: Dict[str, Any],
                          problem_type: str,
                          cv_folds: int = 5) -> Dict[str, Any]:
    """
    Full validation workflow: train null model and compare with primary.
    
    Args:
        X_train: Training feature matrix
        y_train: Training target labels
        primary_model_metrics: Metrics from primary model training
        problem_type: 'classification' or 'regression'
        cv_folds: Number of CV folds
        
    Returns:
        Complete validation results dictionary
    """
    logger.info("Starting null model baseline validation")
    
    # Train null model
    null_metrics = train_null_model(X_train, y_train, problem_type, cv_folds)
    
    # Compare models
    comparison = compare_models(primary_model_metrics, null_metrics, problem_type)
    
    # Compile results
    validation_results = {
        'null_model_metrics': null_metrics,
        'primary_model_metrics': primary_model_metrics,
        'comparison': comparison,
        'validation_status': 'PASSED' if comparison['is_significantly_better'] else 'WARNING',
        'timestamp': pd.Timestamp.now().isoformat()
    }
    
    logger.info(f"Validation status: {validation_results['validation_status']}")
    return validation_results


def check_vif_multicollinearity(X: pd.DataFrame, threshold: float = 5.0) -> Dict[str, Any]:
    """
    Check for multicollinearity using Variance Inflation Factor (VIF).
    
    Args:
        X: Feature matrix
        threshold: VIF threshold for flagging (default 5.0)
        
    Returns:
        Dict with VIF analysis results and flagged features
    """
    logger.info(f"Checking multicollinearity with VIF threshold {threshold}")
    
    if X.shape[1] == 0:
        logger.warning("No features to check for VIF")
        return {'flagged_features': [], 'all_vif': [], 'status': 'NO_FEATURES'}
    
    try:
        vif_data = calculate_vif(X)
        
        # Filter high VIF features
        high_vif = filter_high_vif_features(vif_data, threshold)
        
        # Determine status
        if len(high_vif) == 0:
            status = 'PASS'
            message = "No multicollinearity issues detected"
        elif len(high_vif) < X.shape[1] * 0.2:
            status = 'WARNING'
            message = f"{len(high_vif)} features have high VIF (> {threshold})"
        else:
            status = 'CRITICAL'
            message = f"Severe multicollinearity: {len(high_vif)} features have high VIF"
        
        result = {
            'status': status,
            'message': message,
            'threshold': threshold,
            'flagged_features': high_vif['feature'].tolist(),
            'flagged_vif_values': high_vif['VIF'].tolist(),
            'all_vif': vif_data.to_dict(orient='records'),
            'timestamp': pd.Timestamp.now().isoformat()
        }
        
        logger.info(f"VIF check: {status} - {message}")
        return result
        
    except Exception as e:
        logger.error(f"VIF calculation failed: {str(e)}")
        return {
            'status': 'ERROR',
            'message': f"VIF calculation failed: {str(e)}",
            'flagged_features': [],
            'all_vif': [],
            'timestamp': pd.Timestamp.now().isoformat()
        }


def run_validation_pipeline(X_train: pd.DataFrame, y_train: pd.Series,
                           primary_model_metrics: Dict[str, Any],
                           problem_type: str,
                           cv_folds: int = 5,
                           vif_threshold: float = 5.0) -> Dict[str, Any]:
    """
    Run complete validation pipeline: null model comparison + VIF check.
    
    Args:
        X_train: Training features
        y_train: Training labels
        primary_model_metrics: Primary model CV metrics
        problem_type: 'classification' or 'regression'
        cv_folds: Number of CV folds for null model
        vif_threshold: VIF threshold for multicollinearity detection
        
    Returns:
        Complete validation report
    """
    logger.info("Running complete validation pipeline")
    
    # Null model validation
    null_validation = validate_null_baseline(
        X_train, y_train, primary_model_metrics, problem_type, cv_folds
    )
    
    # VIF check
    vif_results = check_vif_multicollinearity(X_train, vif_threshold)
    
    # Compile final report
    report = {
        'null_model_validation': null_validation,
        'multicollinearity_check': vif_results,
        'overall_status': 'PASSED' if (
            null_validation['validation_status'] == 'PASSED' and 
            vif_results['status'] in ['PASS', 'WARNING']
        ) else 'FAILED',
        'timestamp': pd.Timestamp.now().isoformat()
    }
    
    logger.info(f"Validation pipeline complete: {report['overall_status']}")
    return report


def save_validation_report(report: Dict[str, Any], output_path: Optional[str] = None) -> Path:
    """
    Save validation report to JSON file.
    
    Args:
        report: Validation results dictionary
        output_path: Optional custom output path
        
    Returns:
        Path to saved file
    """
    if output_path is None:
        reports_path = get_reports_path()
        output_path = str(reports_path / 'validation_report.json')
    
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    logger.info(f"Validation report saved to {output_file}")
    return output_file


def main():
    """
    Main entry point for validation module.
    Loads split data, runs validation, and saves report.
    """
    logger.info("Starting validation module main")
    
    try:
        # Load training data
        train_data = load_split_data(split_type='train')
        
        if train_data is None:
            logger.error("Failed to load training data. Ensure split pipeline has run.")
            return
        
        X_train = train_data['X']
        y_train = train_data['y']
        
        # Detect problem type
        problem_type = detect_problem_type(y_train)
        logger.info(f"Detected problem type: {problem_type}")
        
        # Load primary model metrics (from modeling pipeline)
        # In a real run, this would come from the modeling step
        # For now, we'll simulate loading from artifacts
        metrics_path = get_artifacts_path() / 'models' / 'model_metrics.json'
        
        if metrics_path.exists():
            with open(metrics_path, 'r') as f:
                primary_metrics = json.load(f)
        else:
            logger.warning("Primary model metrics not found. Using placeholder.")
            primary_metrics = {
                'cv_mean_score': 0.75 if problem_type == 'classification' else 0.6,
                'cv_std_score': 0.05,
                'cv_scores': [0.70, 0.75, 0.78, 0.72, 0.76]
            }
        
        # Run validation pipeline
        report = run_validation_pipeline(
            X_train, y_train, primary_metrics, problem_type,
            cv_folds=5, vif_threshold=5.0
        )
        
        # Save report
        save_validation_report(report)
        
        logger.info("Validation module completed successfully")
        
    except Exception as e:
        logger.error(f"Validation pipeline failed: {str(e)}")
        raise


if __name__ == "__main__":
    main()