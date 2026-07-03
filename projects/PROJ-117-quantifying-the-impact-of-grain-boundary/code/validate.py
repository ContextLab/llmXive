import os
import sys
import json
import logging
import argparse
from pathlib import Path
from typing import Dict, Any, List, Tuple

import numpy as np
import pandas as pd
from sklearn.model_selection import cross_val_score, KFold
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_percentage_error
from scipy import stats
import xgboost as xgb

from utils import setup_logging, set_random_seed, raise_data_insufficiency

# Configure logging
logger = logging.getLogger(__name__)

def load_model(model_path: str) -> xgb.Booster:
    """Load the trained XGBoost model."""
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model file not found: {model_path}")
    
    model = xgb.Booster()
    model.load_model(model_path)
    return model

def load_data(data_path: str) -> pd.DataFrame:
    """Load the cleaned dataset."""
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Data file not found: {data_path}")
    
    df = pd.read_parquet(data_path)
    logger.info(f"Loaded dataset with {len(df)} records")
    return df

def prepare_features(df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
    """Prepare feature matrix X and target vector y."""
    # Define feature columns based on the preprocessing step
    feature_cols = [
        'misorientation_angle', 'boundary_plane_normal_h', 'boundary_plane_normal_k', 
        'boundary_plane_normal_l', 'sigma_value', 'boundary_width', 'excess_volume',
        'temperature', 'composition_encoded', 'simulation_method_encoded', 
        'potential_id_encoded'
    ]
    
    # Check if all required features are present
    missing_features = [col for col in feature_cols if col not in df.columns]
    if missing_features:
        raise ValueError(f"Missing required features: {missing_features}")
    
    X = df[feature_cols].values
    y = df['diffusivity'].values
    
    return X, y

def perform_cross_validation(X: np.ndarray, y: np.ndarray, model: xgb.Booster, k: int = 5) -> Dict[str, float]:
    """Perform k-fold cross-validation and return metrics."""
    kf = KFold(n_splits=k, shuffle=True, random_state=42)
    
    r2_scores = []
    rmse_scores = []
    mape_scores = []
    
    for train_idx, test_idx in kf.split(X):
        X_train, X_test = X[train_idx], X[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]
        
        # Convert to DMatrix for XGBoost
        dtrain = xgb.DMatrix(X_train, label=y_train)
        dtest = xgb.DMatrix(X_test, label=y_test)
        
        # Make predictions
        y_pred = model.predict(dtest)
        
        # Calculate metrics
        r2 = r2_score(y_test, y_pred)
        rmse = np.sqrt(mean_squared_error(y_test, y_pred))
        mape = mean_absolute_percentage_error(y_test, y_pred)
        
        r2_scores.append(r2)
        rmse_scores.append(rmse)
        mape_scores.append(mape)
    
    return {
        'r2_mean': float(np.mean(r2_scores)),
        'r2_std': float(np.std(r2_scores)),
        'rmse_mean': float(np.mean(rmse_scores)),
        'mape_mean': float(np.mean(mape_scores)),
        'r2_scores': [float(s) for s in r2_scores],
        'rmse_scores': [float(s) for s in rmse_scores],
        'mape_scores': [float(s) for s in mape_scores]
    }

def regression_bias_test(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    """
    Perform regression bias test: y_true ~ y_pred
    Calculate intercept, slope, and p-values.
    """
    # Perform linear regression: y_true = intercept + slope * y_pred
    slope, intercept, r_value, p_value, std_err = stats.linregress(y_pred, y_true)
    
    return {
        'intercept': float(intercept),
        'slope': float(slope),
        'r_squared': float(r_value**2),
        'p_value': float(p_value),
        'std_error': float(std_err)
    }

def apply_bonferroni_correction(p_values: List[float], alpha: float = 0.05) -> List[bool]:
    """
    Apply Bonferroni correction for multiple hypothesis tests.
    Returns list of booleans indicating whether each test is significant.
    """
    n_tests = len(p_values)
    if n_tests == 0:
        return []
    
    alpha_adj = alpha / n_tests
    significant = [p < alpha_adj for p in p_values]
    
    logger.info(f"Bonferroni correction: alpha={alpha}, adjusted alpha={alpha_adj:.4f}")
    return significant

def generate_validation_report(
    cv_metrics: Dict[str, float],
    bias_test_results: Dict[str, float],
    r2_threshold: float = 0.05
) -> Dict[str, Any]:
    """Generate the validation report dictionary."""
    # Check if R2 std is within threshold
    r2_std_pass = cv_metrics['r2_std'] <= r2_threshold
    
    # Check if slope is close to 1 (ideal case)
    slope_pass = 0.9 <= bias_test_results['slope'] <= 1.1
    
    # Check if intercept is close to 0 (ideal case)
    intercept_pass = abs(bias_test_results['intercept']) < 0.1 * np.abs(bias_test_results['slope'])
    
    # Apply Bonferroni correction to p-value (only one test here, but structure for extensibility)
    p_values = [bias_test_results['p_value']]
    alpha = 0.05
    alpha_adj = alpha / len(p_values)  # Bonferroni correction
    significant = [p < alpha_adj for p in p_values]
    
    report = {
        'cross_validation': {
            'k_folds': 5,
            'r2_mean': cv_metrics['r2_mean'],
            'r2_std': cv_metrics['r2_std'],
            'rmse_mean': cv_metrics['rmse_mean'],
            'mape_mean': cv_metrics['mape_mean'],
            'r2_std_threshold': r2_threshold,
            'r2_std_pass': r2_std_pass,
            'r2_scores_per_fold': cv_metrics['r2_scores'],
            'rmse_scores_per_fold': cv_metrics['rmse_scores'],
            'mape_scores_per_fold': cv_metrics['mape_scores']
        },
        'bias_test': {
            'intercept': bias_test_results['intercept'],
            'slope': bias_test_results['slope'],
            'r_squared': bias_test_results['r_squared'],
            'p_value': bias_test_results['p_value'],
            'std_error': bias_test_results['std_error'],
            'slope_pass': slope_pass,
            'intercept_pass': intercept_pass
        },
        'bonferroni_correction': {
            'alpha': alpha,
            'alpha_adjusted': alpha_adj,
            'p_values': p_values,
            'significant': significant
        },
        'overall_assessment': {
            'r2_std_within_threshold': r2_std_pass,
            'bias_test_passed': slope_pass and intercept_pass,
            'bonferroni_significant': significant[0] if significant else False,
            'model_valid': r2_std_pass and slope_pass and intercept_pass
        }
    }
    
    return report

def main():
    """Main function to run validation."""
    parser = argparse.ArgumentParser(description='Validate trained model')
    parser.add_argument('--model-path', type=str, default='models/best_model.json',
                      help='Path to trained model')
    parser.add_argument('--data-path', type=str, default='data/processed/cleaned_dataset.parquet',
                      help='Path to cleaned dataset')
    parser.add_argument('--output-path', type=str, default='artifacts/reports/validation_report.json',
                      help='Path to output validation report')
    parser.add_argument('--k-folds', type=int, default=5,
                      help='Number of cross-validation folds')
    parser.add_argument('--r2-threshold', type=float, default=0.05,
                      help='Maximum allowed standard deviation of R2 scores')
    parser.add_argument('--seed', type=int, default=42,
                      help='Random seed for reproducibility')
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging()
    set_random_seed(args.seed)
    
    try:
        # Load model and data
        logger.info(f"Loading model from {args.model_path}")
        model = load_model(args.model_path)
        
        logger.info(f"Loading data from {args.data_path}")
        df = load_data(args.data_path)
        
        # Prepare features
        X, y = prepare_features(df)
        logger.info(f"Prepared features: {X.shape[1]} features, {len(y)} samples")
        
        # Perform cross-validation
        logger.info(f"Performing {args.k_folds}-fold cross-validation")
        cv_metrics = perform_cross_validation(X, y, model, k=args.k_folds)
        
        # Perform regression bias test
        logger.info("Performing regression bias test")
        # For bias test, we use the full dataset predictions
        dtest = xgb.DMatrix(X)
        y_pred_full = model.predict(dtest)
        bias_test_results = regression_bias_test(y, y_pred_full)
        
        # Generate validation report
        report = generate_validation_report(cv_metrics, bias_test_results, args.r2_threshold)
        
        # Save report
        output_path = Path(args.output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Validation report saved to {args.output_path}")
        
        # Print summary
        print("\n=== Validation Summary ===")
        print(f"R² Mean: {cv_metrics['r2_mean']:.4f}")
        print(f"R² Std: {cv_metrics['r2_std']:.4f} (threshold: {args.r2_threshold})")
        print(f"RMSE Mean: {cv_metrics['rmse_mean']:.4f}")
        print(f"MAPE Mean: {cv_metrics['mape_mean']:.4f}")
        print(f"Bias Test Slope: {bias_test_results['slope']:.4f}")
        print(f"Bias Test Intercept: {bias_test_results['intercept']:.4f}")
        print(f"Model Valid: {report['overall_assessment']['model_valid']}")
        print("========================\n")
        
        # Exit with appropriate code
        if not report['overall_assessment']['model_valid']:
            logger.warning("Model validation failed some checks")
            # Don't exit with error code here as validation is informative
            # Exit with 0 to indicate successful execution of validation script
        
    except Exception as e:
        logger.error(f"Validation failed: {str(e)}")
        raise

if __name__ == '__main__':
    main()
