import sys
import logging
import json
import argparse
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.metrics import r2_score, mean_squared_error

# Import seed utilities
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.seed_manager import init_seed, add_seed_argument

def setup_logger_module(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger

logger = setup_logger_module(__name__)

def fit_model(X: np.ndarray, y: np.ndarray, cv: int = 5, seed: Optional[int] = None) -> Dict[str, Any]:
    """Fit linear regression model with cross-validation."""
    init_seed(seed)
    model = LinearRegression()
    scores = cross_val_score(model, X, y, cv=cv, scoring='r2')
    return {
        "mean_r2": float(np.mean(scores)),
        "std_r2": float(np.std(scores)),
        "scores": scores.tolist()
    }

def evaluate_test(X: np.ndarray, y: np.ndarray, seed: Optional[int] = None) -> Dict[str, Any]:
    """Evaluate model on held-out test set."""
    init_seed(seed)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=seed if seed else 42, stratify=None # Stratify if class exists
    )
    
    model = LinearRegression()
    model.fit(X_train, y_train)
    
    y_pred = model.predict(X_test)
    r2 = r2_score(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    
    return {
        "r2": float(r2),
        "rmse": float(rmse),
        "coefficients": model.coef_.tolist(),
        "intercept": float(model.intercept_)
    }

def run_regression_analysis(df: pd.DataFrame, features: List[str], target: str, seed: Optional[int] = None) -> Dict[str, Any]:
    """Run full regression pipeline."""
    init_seed(seed)
    X = df[features].values
    y = df[target].values
    
    cv_results = fit_model(X, y, seed=seed)
    test_results = evaluate_test(X, y, seed=seed)
    
    return {
        "cross_validation": cv_results,
        "test_evaluation": test_results
    }

def save_regression_results(results: Dict, output_path: Path) -> None:
    """Save regression results."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Regression results saved to {output_path}")

def main():
    parser = argparse.ArgumentParser(description="Regression Analysis")
    add_seed_argument(parser)
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    
    init_seed(args.seed)
    
    df = pd.read_csv(args.input)
    features = ["tolerance_factor", "tilting_angle", "bond_length_variance", "unit_cell_volume"]
    target = "thermal_conductivity"
    
    results = run_regression_analysis(df, features, target, seed=args.seed)
    save_regression_results(results, args.output)

if __name__ == "__main__":
    main()
