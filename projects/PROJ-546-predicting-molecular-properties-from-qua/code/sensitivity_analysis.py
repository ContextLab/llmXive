import argparse
import csv
import json
import logging
import os
import sys
from pathlib import Path

import joblib
import pandas as pd

# ---------------------------------------------------------------------------
# Logging Setup
# ---------------------------------------------------------------------------

def setup_logger(name: str, log_file: str, level=logging.INFO) -> logging.Logger:
    """
    Configure a logger that writes to both console and file.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # File handler
    fh = logging.FileHandler(log_file)
    fh.setLevel(level)

    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(level)

    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)

    logger.addHandler(fh)
    logger.addHandler(ch)

    return logger

# ---------------------------------------------------------------------------
# Core Logic
# ---------------------------------------------------------------------------

def load_model(model_path: str) -> object:
    """
    Load a trained Random Forest model from a .pkl file.
    """
    if not os.path.exists(model_path):
        raise FileNotFoundError(
            f"Model file not found: {model_path}. "
            "Ensure T021 (train_models) has completed successfully."
        )
    try:
        model = joblib.load(model_path)
        return model
    except Exception as e:
        raise RuntimeError(f"Failed to load model from {model_path}: {e}")

def load_data(data_path: str) -> pd.DataFrame:
    """
    Load descriptor data from a CSV file.
    """
    if not os.path.exists(data_path):
        raise FileNotFoundError(
            f"Data file not found: {data_path}. "
            "Ensure T013e (descriptor_pipeline) has completed successfully."
        )
    return pd.read_csv(data_path)

def prepare_features_target(df: pd.DataFrame, target_col: str = 'experimental_barrier') -> tuple:
    """
    Separate features and target from the DataFrame.
    """
    if target_col not in df.columns:
        raise ValueError(f"Target column '{target_col}' not found in data.")

    X = df.drop(columns=[target_col])
    y = df[target_col]
    return X, y

def extract_feature_importance(model: object, feature_names: list) -> list:
    """
    Extract feature importances from a Random Forest model and map to names.
    """
    if not hasattr(model, 'feature_importances_'):
        raise AttributeError(
            "Model does not have 'feature_importances_' attribute. "
            "Ensure a Random Forest (or similar) model was trained."
        )

    importances = model.feature_importances_

    # Create a list of (name, importance) tuples
    importance_list = []
    for name, imp in zip(feature_names, importances):
        importance_list.append({'descriptor': name, 'importance': float(imp)})

    # Sort by descending importance
    importance_list.sort(key=lambda x: x['importance'], reverse=True)

    # Calculate cumulative importance
    cumulative = 0.0
    for i, item in enumerate(importance_list):
        cumulative += item['importance']
        item['rank'] = i + 1
        item['cumulative_importance'] = float(cumulative)

    return importance_list

def write_sensitivity_csv(data: list, output_path: str) -> None:
    """
    Write the sensitivity analysis results to a CSV file.
    """
    if not data:
        raise ValueError("No data to write to sensitivity CSV.")

    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    fieldnames = ['rank', 'descriptor', 'importance', 'cumulative_importance']

    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)

def main():
    """
    Main entry point for Feature Importance Extraction (T029).
    """
    # Configuration
    project_root = Path(__file__).resolve().parent.parent
    model_path = project_root / 'state' / 'model_semi.pkl'
    # We need the feature names. The task spec defines them explicitly.
    # We assume the model was trained on exactly these three features.
    feature_names = ['HOMO_energy', 'LUMO_energy', 'mayer_bond_order']
    output_path = project_root / 'reports' / 'sensitivity.csv'
    log_path = project_root / 'logs' / 'sensitivity_analysis.log'

    # Ensure directories exist
    log_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    logger = setup_logger('sensitivity_analysis', str(log_path))

    logger.info("Starting Feature Importance Extraction (T029).")

    try:
        # 1. Load Model
        logger.info(f"Loading model from {model_path}...")
        model = load_model(str(model_path))
        logger.info("Model loaded successfully.")

        # 2. Extract Feature Importances
        logger.info("Extracting feature importances...")
        sensitivity_data = extract_feature_importance(model, feature_names)
        logger.info(f"Extracted importances for {len(sensitivity_data)} features.")

        # 3. Write Output
        logger.info(f"Writing results to {output_path}...")
        write_sensitivity_csv(sensitivity_data, str(output_path))
        logger.info("Sensitivity analysis complete.")

        # Log summary
        logger.info("Top 3 Descriptors:")
        for item in sensitivity_data[:3]:
            logger.info(f"  {item['rank']}. {item['descriptor']}: {item['importance']:.4f} (Cum: {item['cumulative_importance']:.4f})")

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()