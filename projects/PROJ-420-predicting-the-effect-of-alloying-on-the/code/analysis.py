"""
Analysis module for feature importance, VIF, and sensitivity analysis.
"""
import pickle
import logging
import json
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional
import numpy as np
import pandas as pd
from statsmodels.stats.outliers_influence import variance_inflation_factor
from sklearn.inspection import permutation_importance
from sklearn.ensemble import RandomForestRegressor
from config import get_config

# Configure logger
logger = logging.getLogger(__name__)

def load_trained_model(model_path: Optional[str] = None) -> RandomForestRegressor:
    """Load the trained Random Forest model."""
    config = get_config()
    if model_path is None:
        model_path = str(config.models_dir / "rf_model.pkl")
    
    if not Path(model_path).exists():
        raise FileNotFoundError(f"Model file not found: {model_path}")
    
    with open(model_path, 'rb') as f:
        return pickle.load(f)

def load_features_and_target() -> Tuple[pd.DataFrame, pd.Series]:
    """Load the cleaned dataset and split features/target."""
    config = get_config()
    data_path = config.data_processed_dir / "alloys_clean.parquet"
    
    if not data_path.exists():
        raise FileNotFoundError(f"Cleaned data not found: {data_path}")
    
    df = pd.read_parquet(data_path)
    
    # ILR transformed features
    feature_cols = [col for col in df.columns if col.startswith('ilr_')]
    target_col = 'poisson_ratio'
    
    if not feature_cols:
        raise ValueError("No ILR transformed features found in the dataset")
    
    return df[feature_cols], df[target_col]

def extract_feature_importance(model: RandomForestRegressor, feature_names: List[str]) -> Dict[str, float]:
    """Extract feature importances from the trained model."""
    importances = model.feature_importances_
    return {name: float(imp) for name, imp in zip(feature_names, importances)}

def save_importance_results(results: Dict[str, Any], output_path: Optional[str] = None) -> None:
    """Save feature importance results to JSON."""
    config = get_config()
    if output_path is None:
        output_path = str(config.results_dir / "feature_importance.json")
    
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

def run_permutation_importance(model: RandomForestRegressor, X: pd.DataFrame, y: pd.Series, 
                               n_repeats: int = 10, random_state: int = 42) -> Dict[str, float]:
    """Run permutation importance on ILR features."""
    result = permutation_importance(model, X, y, n_repeats=n_repeats, random_state=random_state, n_jobs=2)
    importance_dict = {col: float(mean_imp) for col, mean_imp in zip(X.columns, result.importances_mean)}
    return importance_dict

def save_permutation_results(results: Dict[str, Any], output_path: Optional[str] = None) -> None:
    """Save permutation importance results to JSON."""
    config = get_config()
    if output_path is None:
        output_path = str(config.results_dir / "permutation_importance.json")
    
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

def calculate_vif(X: pd.DataFrame) -> List[Dict[str, Any]]:
    """Calculate Variance Inflation Factor for each feature."""
    vif_data = []
    for i, col in enumerate(X.columns):
        vif = variance_inflation_factor(X.values, i)
        vif_data.append({
            'element': col,
            'vif': float(vif)
        })
        if vif > 5.0:
            logger.warning(f"High collinearity detected for {col} (VIF={vif:.2f})")
    return vif_data

def save_vif_results(results: List[Dict[str, Any]], output_path: Optional[str] = None) -> None:
    """Save VIF results to JSON."""
    config = get_config()
    if output_path is None:
        output_path = str(config.data_processed_dir / "collinearity_diagnostic.json")
    
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

def rank_and_compare_importance(importance_dict: Dict[str, float]) -> Dict[str, Any]:
    """Rank features by importance and generate comparison statement."""
    sorted_importance = sorted(importance_dict.items(), key=lambda x: x[1], reverse=True)
    
    if len(sorted_importance) < 2:
        return {
            'top_element': sorted_importance[0][0] if sorted_importance else None,
            'second_element': None,
            'ratio': None,
            'comparison_statement': "Insufficient features for comparison"
        }
    
    top_element, top_imp = sorted_importance[0]
    second_element, second_imp = sorted_importance[1]
    
    ratio = top_imp / second_imp if second_imp > 0 else float('inf')
    
    comparison_statement = f"The top element ({top_element}) has a relative importance of {ratio:.2f} compared to {second_element}"
    
    return {
        'top_element': top_element,
        'second_element': second_element,
        'ratio': float(ratio),
        'comparison_statement': comparison_statement
    }

def save_ranking_results(results: Dict[str, Any], output_path: Optional[str] = None) -> None:
    """Save ranking results to JSON."""
    config = get_config()
    if output_path is None:
        output_path = str(config.results_dir / "feature_importance_summary.json")
    
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

def run_perturbation_sensitivity_analysis(model: RandomForestRegressor, X_train: pd.DataFrame, 
                                          output_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Perform perturbation-based sensitivity analysis.
    
    Calculates sigma as a small fraction (1%) of the range of each element's 
    training set values, then measures the model's sensitivity to perturbations.
    """
    config = get_config()
    if output_path is None:
        output_path = str(config.results_dir / "sensitivity_analysis.json")
    
    # Calculate sigma for each feature (1% of the range)
    sigma_values = {}
    perturbation_results = {}
    
    for col in X_train.columns:
        col_range = X_train[col].max() - X_train[col].min()
        sigma = 0.01 * col_range  # 1% of the range
        sigma_values[col] = float(sigma)
        
        # Create perturbed data
        X_perturbed = X_train.copy()
        noise = np.random.normal(0, sigma, size=X_perturbed[col].shape)
        X_perturbed[col] = X_perturbed[col] + noise
        
        # Measure sensitivity (change in predictions)
        original_pred = model.predict(X_train)
        perturbed_pred = model.predict(X_perturbed)
        
        sensitivity = np.mean(np.abs(perturbed_pred - original_pred))
        perturbation_results[col] = {
            'sigma': float(sigma),
            'sensitivity': float(sensitivity)
        }
        
        if sensitivity > 0.01:  # Arbitrary threshold for "high sensitivity"
            logger.warning(f"High sensitivity detected for {col}: {sensitivity:.4f}")
    
    results = {
        'sigma_values': sigma_values,
        'perturbation_results': perturbation_results,
        'methodology': 'Perturbation-based sensitivity analysis using 1% of feature range as sigma',
        'threshold_high_sensitivity': 0.01
    }
    
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Sensitivity analysis results saved to {output_path}")
    return results

def validate_framing(results: Dict[str, Any]) -> bool:
    """Validate that results use associational (not causal) language."""
    # This is a placeholder - actual validation happens in main.py
    return True

def run_importance_analysis() -> None:
    """Run the full importance analysis pipeline."""
    logger.info("Starting feature importance analysis")
    
    # Load model and data
    model = load_trained_model()
    X, y = load_features_and_target()
    
    # Extract feature importance
    feature_importance = extract_feature_importance(model, X.columns.tolist())
    
    # Run permutation importance
    perm_importance = run_permutation_importance(model, X, y)
    
    # Calculate VIF
    vif_results = calculate_vif(X)
    save_vif_results(vif_results)
    
    # Rank and compare
    ranking = rank_and_compare_importance(feature_importance)
    save_ranking_results(ranking)
    
    # Run perturbation sensitivity analysis
    run_perturbation_sensitivity_analysis(model, X)
    
    logger.info("Feature importance analysis completed")

def main():
    """Main entry point for analysis."""
    logging.basicConfig(level=logging.INFO)
    run_importance_analysis()

if __name__ == "__main__":
    main()
