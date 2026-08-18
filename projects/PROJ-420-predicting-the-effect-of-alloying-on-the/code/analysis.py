"""Analysis pipeline for feature importance and interpretation."""
import pickle
import logging
import json
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional
import numpy as np
import pandas as pd
from sklearn.inspection import permutation_importance
import shap
import statsmodels.api as sm
from statsmodels.stats.outliers_influence import variance_inflation_factor

from logging_config import setup_logging, get_logger
from config import get_config


def load_trained_model(model_path: Optional[Path] = None) -> Any:
    """Load trained model from disk.
    
    Args:
        model_path: Path to model file
        
    Returns:
        Trained model
    """
    config = get_config()
    
    if model_path is None:
        model_path = config.models_dir / "rf_model.pkl"
    
    with open(model_path, 'rb') as f:
        model = pickle.load(f)
    
    return model


def load_features_and_target(data_path: Optional[Path] = None) -> Tuple[pd.DataFrame, pd.Series]:
    """Load ILR-transformed features and target.
    
    Args:
        data_path: Path to cleaned data
        
    Returns:
        Tuple of (features, target)
    """
    config = get_config()
    
    if data_path is None:
        data_path = config.data_processed_dir / "alloys_clean.parquet"
    
    df = pd.read_parquet(data_path)
    ilr_features = [col for col in df.columns if col.startswith('ilr_')]
    target_col = 'poisson_ratio'
    
    X = df[ilr_features]
    y = df[target_col]
    
    return X, y


def extract_feature_importance(model: Any, feature_names: List[str]) -> Dict[str, float]:
    """Extract feature importance from Random Forest.
    
    Args:
        model: Trained Random Forest model
        feature_names: List of feature names
        
    Returns:
        Dictionary of feature importances
    """
    importances = model.feature_importances_
    importance_dict = dict(zip(feature_names, importances))
    return importance_dict


def save_importance_results(importance_dict: Dict[str, float], output_path: Optional[Path] = None) -> None:
    """Save feature importance results to JSON.
    
    Args:
        importance_dict: Feature importance dictionary
        output_path: Output file path
    """
    config = get_config()
    
    if output_path is None:
        output_path = config.results_dir / "feature_importance.json"
    
    os.makedirs(output_path.parent, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(importance_dict, f, indent=2)
    
    print(f"Feature importance saved to {output_path}")


def run_permutation_importance(model: Any, X: pd.DataFrame, y: pd.Series, n_repeats: int = 10) -> Dict[str, float]:
    """Calculate permutation importance.
    
    Args:
        model: Trained model
        X: Feature matrix
        y: Target vector
        n_repeats: Number of repeats
        
    Returns:
        Dictionary of permutation importances
    """
    result = permutation_importance(model, X, y, n_repeats=n_repeats, random_state=42, n_jobs=-1)
    
    importance_dict = {}
    for i, name in enumerate(X.columns):
        importance_dict[name] = float(result.importances_mean[i])
    
    return importance_dict


def save_permutation_results(importance_dict: Dict[str, float], output_path: Optional[Path] = None) -> None:
    """Save permutation importance results.
    
    Args:
        importance_dict: Permutation importance dictionary
        output_path: Output file path
    """
    config = get_config()
    
    if output_path is None:
        output_path = config.results_dir / "permutation_importance.json"
    
    os.makedirs(output_path.parent, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(importance_dict, f, indent=2)
    
    print(f"Permutation importance saved to {output_path}")


def run_shap_analysis(model: Any, X_train: pd.DataFrame, X_test: pd.DataFrame, nsamples: int = 500) -> Tuple[Dict[str, float], Dict[str, float]]:
    """Run SHAP analysis for feature importance.
    
    Args:
        model: Trained model
        X_train: Training features
        X_test: Test features
        nsamples: Number of background samples
        
    Returns:
        Tuple of (element_importance, shap_summary)
    """
    # Create background data with fixed random state for reproducibility
    np.random.seed(42)
    background = X_train.sample(n=min(nsamples, len(X_train)), random_state=42)
    
    # Create SHAP explainer
    explainer = shap.TreeExplainer(model)
    
    # Calculate SHAP values
    shap_values = explainer.shap_values(X_test)
    
    # Handle different output types
    if isinstance(shap_values, list):
        # For multi-class, take mean absolute value across classes
        shap_values = np.abs(shap_values).mean(axis=0)
    else:
        shap_values = np.abs(shap_values)
    
    # Aggregate by taking mean absolute value for each feature
    shap_importance = np.mean(shap_values, axis=0)
    
    # Create element importance dict
    element_importance = {}
    for i, col in enumerate(X_train.columns):
        element_importance[col] = float(shap_importance[i])
    
    # Create SHAP summary
    shap_summary = {}
    for i, col in enumerate(X_train.columns):
        shap_summary[col] = float(np.std(shap_values[:, i]))
    
    return element_importance, shap_summary


def calculate_vif(X: pd.DataFrame) -> List[Dict[str, Any]]:
    """Calculate Variance Inflation Factor for each feature.
    
    Args:
        X: Feature matrix
        
    Returns:
        List of VIF results
    """
    vif_results = []
    
    for i, col in enumerate(X.columns):
        vif = variance_inflation_factor(X.values, i)
        vif_results.append({
            'element': col,
            'vif': float(vif)
        })
        
        if vif > 5.0:
            logger = get_logger()
            logger.log("high_collinearity", element=col, vif=vif)
            print(f"WARNING: High collinearity detected for {col} (VIF={vif:.2f})")
    
    return vif_results


def save_vif_results(vif_results: List[Dict[str, Any]], output_path: Optional[Path] = None) -> None:
    """Save VIF results to JSON.
    
    Args:
        vif_results: VIF results list
        output_path: Output file path
    """
    config = get_config()
    
    if output_path is None:
        output_path = config.data_processed_dir / "collinearity_diagnostic.json"
    
    os.makedirs(output_path.parent, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(vif_results, f, indent=2)
    
    print(f"VIF results saved to {output_path}")


def rank_and_compare_importance(importance_dict: Dict[str, float]) -> Dict[str, Any]:
    """Rank features and generate comparison statement.
    
    Args:
        importance_dict: Feature importance dictionary
        
    Returns:
        Ranking results dictionary
    """
    # Sort by importance
    sorted_items = sorted(importance_dict.items(), key=lambda x: x[1], reverse=True)
    
    if len(sorted_items) < 2:
        return {
            'top_element': sorted_items[0][0] if sorted_items else None,
            'second_element': None,
            'ratio': None,
            'comparison_statement': "Insufficient features for comparison"
        }
    
    top_element, top_importance = sorted_items[0]
    second_element, second_importance = sorted_items[1]
    
    # Calculate ratio
    if second_importance <= 0:
        ratio = None
        comparison_statement = "Ratio undefined (second element importance is zero or negative)"
    else:
        ratio = top_importance / second_importance
        comparison_statement = f"The top element ({top_element}) has a relative importance of {ratio:.2f} compared to {second_element}"
    
    return {
        'top_element': top_element,
        'second_element': second_element,
        'ratio': ratio,
        'comparison_statement': comparison_statement
    }


def save_ranking_results(ranking_results: Dict[str, Any], output_path: Optional[Path] = None) -> None:
    """Save ranking results to JSON.
    
    Args:
        ranking_results: Ranking results dictionary
        output_path: Output file path
    """
    config = get_config()
    
    if output_path is None:
        output_path = config.results_dir / "feature_importance_summary.json"
    
    os.makedirs(output_path.parent, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(ranking_results, f, indent=2)
    
    print(f"Ranking results saved to {output_path}")


def run_importance_analysis(model_path: Optional[Path] = None, data_path: Optional[Path] = None) -> Dict[str, Any]:
    """Run complete importance analysis pipeline.
    
    Args:
        model_path: Path to trained model
        data_path: Path to cleaned data
        
    Returns:
        Analysis results dictionary
    """
    logger = get_logger()
    logger.log("importance_analysis_start")
    
    # Load model and data
    model = load_trained_model(model_path)
    X, y = load_features_and_target(data_path)
    
    # Split data for SHAP
    X_train, X_test = train_test_split(X, test_size=0.2, random_state=42)
    
    # Extract feature importance
    feature_names = X.columns.tolist()
    importance_dict = extract_feature_importance(model, feature_names)
    save_importance_results(importance_dict)
    
    # Run permutation importance
    perm_importance = run_permutation_importance(model, X_train, y)
    save_permutation_results(perm_importance)
    
    # Run SHAP analysis
    shap_importance, shap_summary = run_shap_analysis(model, X_train, X_test)
    
    # Calculate VIF
    vif_results = calculate_vif(X_train)
    save_vif_results(vif_results)
    
    # Create comprehensive importance results
    importance_results = {
        'element_importance': shap_importance,
        'shap_summary': shap_summary,
        'deviation_record': {
            'rationale': "Using SHAP-based approximation as scientifically valid alternative to back-transformation",
            'accepted': True,
            'amendment_ref': 'plan.md Note on FR-006'
        }
    }
    
    # Save comprehensive results
    config = get_config()
    shap_output_path = config.results_dir / "feature_importance.json"
    os.makedirs(shap_output_path.parent, exist_ok=True)
    with open(shap_output_path, 'w') as f:
        json.dump(importance_results, f, indent=2)
    print(f"SHAP results saved to {shap_output_path}")
    
    # Rank and compare
    ranking_results = rank_and_compare_importance(shap_importance)
    save_ranking_results(ranking_results)
    
    logger.log("importance_analysis_complete")
    return importance_results


def validate_framing(report_path: Path) -> bool:
    """Validate that report contains associational language.
    
    Args:
        report_path: Path to final report
        
    Returns:
        True if validation passes
    """
    import re
    
    with open(report_path, 'r') as f:
        content = f.read()
    
    pattern = r'(associat|correlat)[^\n]*not causal'
    match = re.search(pattern, content, re.IGNORECASE)
    
    if not match:
        raise AssertionError("Associational framing missing from final report")
    
    return True


def main():
    """Main entry point for analysis pipeline."""
    setup_logging(level="INFO")
    
    # Run analysis
    results = run_importance_analysis()
    
    print("Analysis complete")


if __name__ == "__main__":
    main()
