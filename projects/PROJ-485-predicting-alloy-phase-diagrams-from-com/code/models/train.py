import os
import sys
import json
import pickle
import argparse
import time
from typing import Dict, Any, List, Optional
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import LeaveOneOut
from statsmodels.stats.power import TTestIndPower
from utils.logging import get_logger, log_info, log_warning, log_error
from utils.error_codes import ErrorCode

def load_processed_data(data_path: str) -> tuple[List[float], List[float]]:
    """Loads processed data from a CSV file."""
    try:
        with open(data_path, 'r') as f:
            lines = f.readlines()
        features = []
        targets = []
        for line in lines[1:]:
            feature, target = line.strip().split(',')
            features.append(float(feature))
            targets.append(float(target))
        return features, targets
    except FileNotFoundError:
        log_error(f"Data file not found: {data_path}")
        raise FileNotFoundError(f"Data file not found: {data_path}")
    except Exception as e:
        log_error(f"Error loading data: {e}")
        raise

def apply_property_range_extrapolation_check(training_features: List[float], test_feature: float) -> bool:
    """Checks if a test feature falls within the convex hull of the training features."""
    if not training_features:
        return True  # If no training data, allow interpolation
    min_val = min(training_features)
    max_val = max(training_features)
    return min_val <= test_feature <= max_val

def train_random_forest(X_train: List[float], y_train: List[float]) -> RandomForestRegressor:
    """Trains a Random Forest Regressor."""
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    return model

def run_loso_cv(X: List[float], y: List[float]) -> List[float]:
    """Runs Leave-One-Out Cross-Validation."""
    loso = LeaveOneOut()
    predictions = []
    for train_index, test_index in loso.split(X):
        X_train, X_test = X[train_index], X[test_index]
        y_train, y_test = y[train_index], y[test_index]
        model = train_random_forest(X_train, y_train)
        prediction = model.predict(X_test)[0]
        predictions.append(prediction)
    return predictions

def perform_power_analysis(effect_size: float, alpha: float = 0.05, power: float = 0.8) -> TTestIndPower:
    """Performs power analysis."""
    analysis = TTestIndPower()
    sample_size = analysis.solve_power(effect_size, power=power, alpha=alpha)
    return analysis

def save_model(model: RandomForestRegressor, model_path: str):
    """Saves the trained model."""
    with open(model_path, 'wb') as f:
        pickle.dump(model, f)

def save_report(loso_results: List[float], report_path: str):
    """Saves the LOSO results to a JSON file."""
    with open(report_path, 'w') as f:
        json.dump(loso_results, f)

def main(data_path: str, model_path: str, report_path: str):
    """Main function to train the model and run LOSO CV."""
    try:
        X, y = load_processed_data(data_path)
        loso_results = run_loso_cv(X, y)
        save_report(loso_results, report_path)
        save_model(train_random_forest(X, y), model_path)
        log_info("Model trained and saved successfully.")
    except Exception as e:
        log_error(f"Error during training: {e}")
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data_path", default="data/processed/descriptors.csv", help="Path to the processed data CSV file.")
    parser.add_argument("--model_path", default="data/artifacts/model.pkl", help="Path to save the trained model.")
    parser.add_argument("--report_path", default="data/artifacts/loso_report.json", help="Path to save the LOSO report.")
    args = parser.parse_args()
    main(args.data_path, args.model_path, args.report_path)