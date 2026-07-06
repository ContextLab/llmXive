import pickle
import logging
import json
from pathlib import Path
from typing import Dict, List, Any, Tuple
import numpy as np
from sklearn.inspection import permutation_importance

from config import get_config
from logging_config import get_logger

logger = get_logger(__name__)


def load_trained_model(model_path: Path) -> Any:
    """Load the trained Random Forest model from disk."""
    logger.info(f"Loading model from {model_path}")
    with open(model_path, "rb") as f:
        model = pickle.load(f)
    return model


def extract_feature_importance(model: Any, feature_names: List[str]) -> Dict[str, float]:
    """Extract feature importance scores from the trained model."""
    importances = model.feature_importances_
    importance_dict = {name: float(imp) for name, imp in zip(feature_names, importances)}
    logger.info(f"Extracted importance for {len(importance_dict)} features")
    return importance_dict


def save_importance_results(importance_dict: Dict[str, float], output_path: Path) -> None:
    """Save feature importance results to a JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(importance_dict, f, indent=2)
    logger.info(f"Saved importance results to {output_path}")


def run_permutation_importance(model: Any, X: np.ndarray, y: np.ndarray, feature_names: List[str], n_repeats: int = 10, random_state: int = 42) -> Dict[str, float]:
    """Run permutation importance to validate feature importance."""
    logger.info("Running permutation importance")
    result = permutation_importance(model, X, y, n_repeats=n_repeats, random_state=random_state, scoring='neg_mean_absolute_error')
    perm_importance = result.importances_mean
    perm_dict = {name: float(imp) for name, imp in zip(feature_names, perm_importance)}
    logger.info(f"Permutation importance calculated for {len(perm_dict)} features")
    return perm_dict


def run_importance_analysis(model: Any, X: np.ndarray, y: np.ndarray, feature_names: List[str], output_dir: Path) -> Dict[str, Any]:
    """Run full importance analysis including extraction and permutation."""
    model_importance = extract_feature_importance(model, feature_names)
    perm_importance = run_permutation_importance(model, X, y, feature_names)

    save_importance_results(model_importance, output_dir / "model_importance.json")
    save_importance_results(perm_importance, output_dir / "permutation_importance.json")

    return {
        "model_importance": model_importance,
        "permutation_importance": perm_importance
    }


def calculate_vif(X: np.ndarray, feature_names: List[str]) -> Dict[str, float]:
    """Calculate Variance Inflation Factor for each feature."""
    from statsmodels.stats.outliers_influence import variance_inflation_factor
    logger.info("Calculating VIF for raw predictors")
    vif_data = {}
    for i, name in enumerate(feature_names):
        vif = variance_inflation_factor(X, i)
        vif_data[name] = float(vif)
        if vif > 5:
            logger.warning(f"High VIF detected for {name}: {vif:.2f}")
    return vif_data


def save_vif_results(vif_dict: Dict[str, float], output_path: Path) -> None:
    """Save VIF results to a JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(vif_dict, f, indent=2)
    logger.info(f"Saved VIF results to {output_path}")


def rank_and_compare_importance(importance_dict: Dict[str, float]) -> List[Tuple[str, float]]:
    """Rank features by importance and return sorted list."""
    ranked = sorted(importance_dict.items(), key=lambda x: x[1], reverse=True)
    logger.info(f"Ranked {len(ranked)} features by importance")
    return ranked


def save_ranking_results(ranked_list: List[Tuple[str, float]], output_path: Path) -> None:
    """Save ranked importance results to a JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump([{"feature": name, "importance": imp} for name, imp in ranked_list], f, indent=2)
    logger.info(f"Saved ranking results to {output_path}")


def main():
    """Main entry point for importance analysis."""
    config = get_config()
    model_path = config.models_dir / "rf_model.pkl"
    output_dir = config.output_dir

    logger.info("Starting feature importance analysis")

    try:
        model = load_trained_model(model_path)
        # Assuming features and target are loaded from processed data
        # This would typically be passed in or loaded from a file
        # For now, we assume the caller handles data loading
        logger.warning("Data loading for importance analysis not implemented in this module. Ensure X and y are provided.")
    except FileNotFoundError:
        logger.error(f"Model not found at {model_path}")
        raise


if __name__ == "__main__":
    main()