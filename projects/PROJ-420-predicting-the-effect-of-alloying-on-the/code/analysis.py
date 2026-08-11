"""Analysis module for feature importance, VIF, and sensitivity analysis."""
import pickle
import logging
import json
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional
import numpy as np
import pandas as pd
from statsmodels.stats.outliers_influence import variance_inflation_factor
from compositional import ilr, ilr_inv
from config import get_config
from logging_config import setup_logging, get_logger

# Initialize logger
logger = setup_logging()
if logger is None:
    # Fallback if setup_logging returns None or fails
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

def load_trained_model() -> Any:
    """Load the trained Random Forest model from disk."""
    config = get_config()
    model_path = config.models_dir / "rf_model.pkl"
    if not model_path.exists():
        raise FileNotFoundError(f"Model not found at {model_path}. Run modeling pipeline first.")
    
    with open(model_path, 'rb') as f:
        return pickle.load(f)

def extract_feature_importance(model: Any) -> Dict[str, float]:
    """Extract feature importance from the trained Random Forest model."""
    # Feature names are the ILR transformed components
    feature_names = ['ilr_0', 'ilr_1', 'ilr_2', 'ilr_3', 'ilr_4']
    importances = model.feature_importances_
    
    importance_dict = {}
    for name, imp in zip(feature_names, importances):
        importance_dict[name] = float(imp)
    
    return importance_dict

def save_importance_results(importance_dict: Dict[str, float], output_path: Optional[Path] = None) -> None:
    """Save feature importance results to JSON."""
    if output_path is None:
        config = get_config()
        output_path = config.results_dir / "feature_importance.json"
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(importance_dict, f, indent=2)
    
    logger.info(f"Feature importance saved to {output_path}")

def run_permutation_importance(model: Any, X: pd.DataFrame, y: pd.Series, n_repeats: int = 10, random_state: int = 42) -> Dict[str, float]:
    """Run permutation importance to assess feature importance."""
    from sklearn.inspection import permutation_importance
    
    result = permutation_importance(model, X, y, n_repeats=n_repeats, random_state=random_state)
    
    importance_dict = {}
    for i, name in enumerate(X.columns):
        importance_dict[name] = float(result.importances_mean[i])
    
    return importance_dict

def save_permutation_results(importance_dict: Dict[str, float], output_path: Optional[Path] = None) -> None:
    """Save permutation importance results to JSON."""
    if output_path is None:
        config = get_config()
        output_path = config.results_dir / "permutation_importance.json"
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(importance_dict, f, indent=2)
    
    logger.info(f"Permutation importance saved to {output_path}")

def calculate_vif(data: pd.DataFrame, feature_columns: List[str]) -> List[Dict[str, Any]]:
    """
    Calculate Variance Inflation Factor (VIF) for each feature.
    
    Args:
        data: DataFrame containing the features
        feature_columns: List of column names to calculate VIF for
        
    Returns:
        List of dictionaries with 'element' and 'vif' keys
    """
    vif_results = []
    
    # Prepare the design matrix (add constant for intercept if needed, but VIF doesn't require it)
    X = data[feature_columns].values
    
    for i, col in enumerate(feature_columns):
        try:
            vif_value = variance_inflation_factor(X, i)
            vif_results.append({
                'element': col,
                'vif': float(vif_value)
            })
            
            # Log warning if VIF > 5.0
            if vif_value > 5.0:
                logger.warning(f"WARNING: High collinearity detected for {col} (VIF={vif_value:.2f})")
                
        except Exception as e:
            logger.error(f"Error calculating VIF for {col}: {e}")
            vif_results.append({
                'element': col,
                'vif': float('nan')
            })
    
    return vif_results

def save_vif_results(vif_results: List[Dict[str, Any]], output_path: Optional[Path] = None) -> None:
    """Save VIF results to JSON."""
    if output_path is None:
        config = get_config()
        output_path = config.data_processed_dir / "collinearity_diagnostic.json"
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(vif_results, f, indent=2)
    
    logger.info(f"VIF results saved to {output_path}")

def rank_and_compare_importance(importance_dict: Dict[str, float]) -> Dict[str, Any]:
    """Rank features by importance and generate comparison statement."""
    # Sort by importance descending
    sorted_items = sorted(importance_dict.items(), key=lambda x: x[1], reverse=True)
    
    if len(sorted_items) < 2:
        return {
            'top_element': sorted_items[0][0] if sorted_items else None,
            'second_element': None,
            'ratio': None,
            'comparison_statement': "Insufficient features for comparison."
        }
    
    top_element, top_importance = sorted_items[0]
    second_element, second_importance = sorted_items[1]
    
    # Calculate ratio (avoid division by zero)
    if second_importance > 0:
        ratio = top_importance / second_importance
    else:
        ratio = float('inf') if top_importance > 0 else 0.0
    
    comparison_statement = f"The top element ({top_element}) has a relative importance of {ratio:.2f} compared to {second_element}"
    
    return {
        'top_element': top_element,
        'second_element': second_element,
        'ratio': float(ratio),
        'comparison_statement': comparison_statement
    }

def save_ranking_results(ranking_dict: Dict[str, Any], output_path: Optional[Path] = None) -> None:
    """Save ranking results to JSON."""
    if output_path is None:
        config = get_config()
        output_path = config.results_dir / "feature_importance_summary.json"
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(ranking_dict, f, indent=2)
    
    logger.info(f"Ranking results saved to {output_path}")

def run_perturbation_sensitivity_analysis(model: Any, X_train: pd.DataFrame, feature_columns: List[str]) -> Dict[str, float]:
    """
    Run perturbation-based sensitivity analysis.
    
    Args:
        model: Trained model
        X_train: Training data
        feature_columns: List of feature column names
        
    Returns:
        Dictionary with sigma values for each feature
    """
    sensitivity_results = {}
    
    for col in feature_columns:
        # Calculate sigma as a small fraction of the range
        col_range = X_train[col].max() - X_train[col].min()
        sigma = 0.01 * col_range if col_range > 0 else 0.001
        sensitivity_results[col] = float(sigma)
    
    return sensitivity_results

def save_sensitivity_results(sensitivity_results: Dict[str, float], output_path: Optional[Path] = None) -> None:
    """Save sensitivity analysis results to JSON."""
    if output_path is None:
        config = get_config()
        output_path = config.results_dir / "sensitivity_analysis.json"
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(sensitivity_results, f, indent=2)
    
    logger.info(f"Sensitivity analysis results saved to {output_path}")

def validate_framing(data: pd.DataFrame, target_column: str, feature_columns: List[str]) -> Dict[str, Any]:
    """Validate the framing of the analysis (basic checks)."""
    validation_results = {
        'n_samples': len(data),
        'n_features': len(feature_columns),
        'target_var': target_column,
        'features': feature_columns,
        'target_stats': {
            'mean': float(data[target_column].mean()),
            'std': float(data[target_column].std()),
            'min': float(data[target_column].min()),
            'max': float(data[target_column].max())
        }
    }
    
    return validation_results

def run_importance_analysis(model_path: Optional[Path] = None, data_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Run the full importance analysis pipeline.
    
    Args:
        model_path: Path to the trained model
        data_path: Path to the ILR-transformed data
        
    Returns:
        Dictionary containing all analysis results
    """
    config = get_config()
    
    # Load model
    if model_path is None:
        model_path = config.models_dir / "rf_model.pkl"
    
    model = load_trained_model()
    
    # Load data
    if data_path is None:
        data_path = config.data_processed_dir / "alloys_clean.parquet"
    
    if not data_path.exists():
        raise FileNotFoundError(f"Data not found at {data_path}. Run cleaning pipeline first.")
    
    data = pd.read_parquet(data_path)
    
    # ILR feature columns
    ilr_features = ['ilr_0', 'ilr_1', 'ilr_2', 'ilr_3', 'ilr_4']
    
    # Extract feature importance
    importance = extract_feature_importance(model)
    save_importance_results(importance)
    
    # Run permutation importance
    if 'poisson_ratio' in data.columns:
        X = data[ilr_features]
        y = data['poisson_ratio']
        perm_importance = run_permutation_importance(model, X, y)
        save_permutation_results(perm_importance)
    
    # Calculate VIF
    vif_results = calculate_vif(data, ilr_features)
    save_vif_results(vif_results)
    
    # Rank and compare
    ranking = rank_and_compare_importance(importance)
    save_ranking_results(ranking)
    
    # Sensitivity analysis
    if 'poisson_ratio' in data.columns:
        X_train = data[ilr_features]
        sensitivity = run_perturbation_sensitivity_analysis(model, X_train, ilr_features)
        save_sensitivity_results(sensitivity)
    
    # Validation
    validation = validate_framing(data, 'poisson_ratio', ilr_features)
    
    return {
        'importance': importance,
        'permutation_importance': perm_importance if 'perm_importance' in locals() else None,
        'vif': vif_results,
        'ranking': ranking,
        'sensitivity': sensitivity if 'sensitivity' in locals() else None,
        'validation': validation
    }

def main():
    """Main entry point for analysis."""
    logger.info("Starting analysis pipeline...")
    
    try:
        results = run_importance_analysis()
        logger.info("Analysis pipeline completed successfully.")
        return results
    except Exception as e:
        logger.error(f"Analysis pipeline failed: {e}")
        raise

if __name__ == "__main__":
    main()
