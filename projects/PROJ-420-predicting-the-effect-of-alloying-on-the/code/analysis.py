"""
Analysis module for feature importance, ranking, and comparison logic.
Implements SHAP-based importance aggregation and result ranking.
"""
import pickle
import logging
import json
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional
import numpy as np

# Import logging infrastructure (tolerant implementation)
try:
    from logging_config import get_logger, log_operation
except ImportError:
    # Fallback for standalone execution if logging_config is not yet available
    logging.basicConfig(level=logging.INFO)
    def get_logger(name=None):
        return logging.getLogger(name)
    def log_operation(*args, **kwargs):
        return None

# Constants for the analysis
ELEMENTS = ['Cu', 'Mg', 'Si', 'Zn', 'Mn']
ILR_FEATURES = ['ilr_0', 'ilr_1', 'ilr_2', 'ilr_3', 'ilr_4']

logger = get_logger(__name__)

def load_trained_model(model_path: str = "models/rf_model.pkl") -> Any:
    """Load the trained Random Forest model from disk."""
    path = Path(model_path)
    if not path.exists():
        raise FileNotFoundError(f"Model file not found: {model_path}")
    with open(path, 'rb') as f:
        return pickle.load(f)

def load_features_and_target(data_path: str = "data/processed/alloys_ilr.parquet") -> Tuple[np.ndarray, np.ndarray]:
    """Load ILR-transformed features and target variable."""
    import pandas as pd
    path = Path(data_path)
    if not path.exists():
        raise FileNotFoundError(f"Data file not found: {data_path}")
    
    df = pd.read_parquet(path)
    
    # Identify feature columns (those starting with 'ilr_')
    feature_cols = [col for col in df.columns if col.startswith('ilr_')]
    if not feature_cols:
        raise ValueError("No ILR features found in the dataset. Expected columns like 'ilr_0', 'ilr_1', etc.")
    
    # Sort to ensure consistent order
    feature_cols.sort()
    
    X = df[feature_cols].values
    y = df['poisson_ratio'].values
    
    return X, y

def run_shap_importance(model: Any, X: np.ndarray, feature_names: List[str]) -> Dict[str, float]:
    """
    Calculate SHAP feature importance for the model.
    Returns a dictionary mapping feature names to mean absolute SHAP values.
    """
    try:
        import shap
        explainer = shap.TreeExplainer(model)
        shap_values = explainer.shap_values(X)
        
        # For regression, shap_values is a 2D array (samples, features)
        if len(shap_values.shape) == 2:
            mean_abs_shap = np.mean(np.abs(shap_values), axis=0)
        else:
            # Handle case where shap_values might be a list (e.g., for classification)
            # But for regression, it should be 2D
            mean_abs_shap = np.mean(np.abs(shap_values), axis=0)
        
        importance = {name: float(val) for name, val in zip(feature_names, mean_abs_shap)}
        return importance
    except ImportError:
        logger.warning("SHAP not installed. Using feature_importances_ from model as fallback.")
        importance = {name: float(val) for name, val in zip(feature_names, model.feature_importances_)}
        return importance

def aggregate_ilr_to_element(ilr_importance: Dict[str, float], ilr_mapping: Dict[str, List[str]] = None) -> Dict[str, float]:
    """
    Aggregate ILR coordinate importances to element-level importances.
    
    The ILR transformation creates coordinates based on a Sequential Binary Partition (SBP).
    We map each ILR coordinate back to the elements that contribute to it.
    
    For a 5-element composition (Cu, Mg, Si, Zn, Mn), the ILR coordinates are:
    ilr_0: log( (Cu) / (Mg*Si*Zn*Mn)^(1/4) ) -> Cu vs rest
    ilr_1: log( (Mg) / (Si*Zn*Mn)^(1/3) ) -> Mg vs rest (excluding Cu)
    ilr_2: log( (Si) / (Zn*Mn)^(1/2) ) -> Si vs rest (excluding Cu, Mg)
    ilr_3: log( (Zn) / (Mn) ) -> Zn vs Mn
    ilr_4: log( (Mn) / 1 ) -> Mn (this is not standard, usually there are 4 ILR coords for 5 parts)
    
    Actually, for D parts, there are D-1 ILR coordinates. So for 5 elements, we have 4 coordinates.
    The mapping depends on the specific SBP used.
    
    Assuming a standard sequential partition:
    ilr_0: Cu vs (Mg, Si, Zn, Mn)
    ilr_1: Mg vs (Si, Zn, Mn)
    ilr_2: Si vs (Zn, Mn)
    ilr_3: Zn vs Mn
    
    We'll assign importance to the "positive" side of the balance (numerator) and 
    distribute the "negative" side importance proportionally or to the main element.
    
    For simplicity in this implementation, we'll use a heuristic:
    - ilr_0: Cu gets full weight, others get 0
    - ilr_1: Mg gets full weight, others get 0
    - ilr_2: Si gets full weight, others get 0
    - ilr_3: Zn gets full weight, Mn gets 0 (or we could split)
    
    However, a more accurate approach is to consider the balance:
    The importance of an element is the sum of absolute SHAP values of coordinates
    where it appears in the numerator, weighted by the coordinate's position.
    
    Let's implement a simple mapping based on the SBP order:
    """
    
    # Define the mapping from ILR coordinates to elements (numerator side)
    # This assumes a specific SBP: Cu, Mg, Si, Zn, Mn
    ilr_to_element = {
        'ilr_0': 'Cu',
        'ilr_1': 'Mg',
        'ilr_2': 'Si',
        'ilr_3': 'Zn',
        'ilr_4': 'Mn'  # If there are 5 coords, the last one is for the last element
    }
    
    element_importance = {elem: 0.0 for elem in ELEMENTS}
    
    for ilr_coord, importance in ilr_importance.items():
        if ilr_coord in ilr_to_element:
            elem = ilr_to_element[ilr_coord]
            element_importance[elem] += importance
        else:
            # If there's an ILR coordinate not in our mapping, distribute its importance
            # This shouldn't happen with a proper 5-element composition
            logger.warning(f"ILR coordinate {ilr_coord} not in mapping. Distributing importance.")
            for elem in ELEMENTS:
                element_importance[elem] += importance / len(ELEMENTS)
    
    return element_importance

def save_importance_results(importance_scores: Dict[str, float], output_path: str = "results/feature_importance.json") -> None:
    """Save feature importance results to a JSON file."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    result = {
        "importance_scores": importance_scores,
        "elements": ELEMENTS
    }
    
    with open(path, 'w') as f:
        json.dump(result, f, indent=2)
    
    logger.info(f"Feature importance results saved to {output_path}")

def rank_feature_importance(importance_scores: Dict[str, float]) -> Dict[str, Any]:
    """
    Rank elements by feature importance and generate comparison statements.
    
    Returns a dictionary with:
    - top_element: The element with highest importance
    - second_element: The element with second highest importance
    - ratio: The ratio of top to second importance
    - comparison_statement: A human-readable comparison statement
    """
    # Sort elements by importance (descending)
    sorted_elements = sorted(importance_scores.items(), key=lambda x: x[1], reverse=True)
    
    if len(sorted_elements) < 2:
        raise ValueError("Need at least 2 elements to rank and compare.")
    
    top_element, top_score = sorted_elements[0]
    second_element, second_score = sorted_elements[1]
    
    # Calculate ratio (avoid division by zero)
    if second_score > 0:
        ratio = top_score / second_score
    else:
        ratio = float('inf') if top_score > 0 else 1.0
    
    # Generate comparison statement
    if ratio > 2.0:
        comparison_statement = f"{top_element} is the dominant factor influencing Poisson's ratio, with an importance {ratio:.2f}x greater than {second_element}."
    elif ratio > 1.5:
        comparison_statement = f"{top_element} has a significantly higher importance than {second_element} (ratio: {ratio:.2f})."
    else:
        comparison_statement = f"{top_element} and {second_element} have comparable importance levels (ratio: {ratio:.2f})."
    
    return {
        "top_element": top_element,
        "second_element": second_element,
        "ratio": ratio,
        "comparison_statement": comparison_statement,
        "all_rankings": [elem for elem, _ in sorted_elements],
        "all_scores": {elem: score for elem, score in sorted_elements}
    }

def run_importance_analysis(
    model_path: str = "models/rf_model.pkl",
    data_path: str = "data/processed/alloys_ilr.parquet",
    output_path: str = "results/feature_importance.json",
    summary_path: str = "results/feature_importance_summary.json"
) -> Dict[str, Any]:
    """
    Run the full feature importance analysis pipeline:
    1. Load model and data
    2. Calculate SHAP importance
    3. Aggregate to element level
    4. Save detailed results
    5. Generate ranking summary
    
    Returns the summary dictionary.
    """
    logger.info("Starting feature importance analysis...")
    
    # Step 1: Load model and data
    logger.info("Loading model and data...")
    model = load_trained_model(model_path)
    X, y = load_features_and_target(data_path)
    feature_names = [f"ilr_{i}" for i in range(X.shape[1])]
    
    # Step 2: Calculate SHAP importance
    logger.info("Calculating SHAP importance...")
    ilr_importance = run_shap_importance(model, X, feature_names)
    
    # Step 3: Aggregate to element level
    logger.info("Aggregating ILR importance to element level...")
    element_importance = aggregate_ilr_to_element(ilr_importance)
    
    # Step 4: Save detailed results
    logger.info("Saving detailed feature importance results...")
    save_importance_results(element_importance, output_path)
    
    # Step 5: Generate ranking summary
    logger.info("Generating feature importance ranking summary...")
    summary = rank_feature_importance(element_importance)
    
    # Save summary
    summary_path_obj = Path(summary_path)
    summary_path_obj.parent.mkdir(parents=True, exist_ok=True)
    with open(summary_path_obj, 'w') as f:
        json.dump(summary, f, indent=2)
    
    logger.info(f"Feature importance summary saved to {summary_path}")
    logger.info(f"Top element: {summary['top_element']}, Second: {summary['second_element']}, Ratio: {summary['ratio']:.2f}")
    
    return summary

def main():
    """Main entry point for the analysis script."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run feature importance analysis for alloy Poisson's ratio model.")
    parser.add_argument("--model", type=str, default="models/rf_model.pkl", help="Path to the trained model file.")
    parser.add_argument("--data", type=str, default="data/processed/alloys_ilr.parquet", help="Path to the ILR-transformed data file.")
    parser.add_argument("--output", type=str, default="results/feature_importance.json", help="Path for detailed feature importance output.")
    parser.add_argument("--summary", type=str, default="results/feature_importance_summary.json", help="Path for feature importance summary output.")
    
    args = parser.parse_args()
    
    try:
        summary = run_importance_analysis(
            model_path=args.model,
            data_path=args.data,
            output_path=args.output,
            summary_path=args.summary
        )
        print("Analysis completed successfully.")
        print(f"Top element: {summary['top_element']}")
        print(f"Comparison: {summary['comparison_statement']}")
    except Exception as e:
        logger.error(f"Analysis failed: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()