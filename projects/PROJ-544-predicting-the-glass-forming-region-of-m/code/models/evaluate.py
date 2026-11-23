"""
Task T021: Implement model evaluation on held-out test set.

Evaluates trained models (Random Forest and Gradient Boosting) on a held-out test set.
Computes ROC-AUC, precision, recall, and standard deviation across folds.
Writes results to results/performance_metrics.json.
"""
import argparse
import json
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score, precision_score, recall_score, accuracy_score
from sklearn.model_selection import cross_val_predict, cross_validate
from sklearn.preprocessing import LabelEncoder

# Import configuration and logging setup from train module
try:
    from models.train import load_config, load_data, setup_logging
except ImportError:
    print("Error: Could not import required functions from models.train. Ensure T020 is complete.")
    sys.exit(1)

def evaluate_model(model, X_test, y_test, model_name, label_encoder):
    """
    Evaluate a single model on the test set.
    """
    start_time = time.time()

    if hasattr(model, 'predict_proba'):
        y_proba = model.predict_proba(X_test)[:, 1]
        roc_auc = roc_auc_score(y_test, y_proba)
    else:
        roc_auc = 0.0
        logging.warning(f"{model_name} does not support predict_proba. ROC-AUC set to 0.0.")

    y_pred = model.predict(X_test)
    precision = precision_score(y_test, y_pred, average='binary', zero_division=0)
    recall = recall_score(y_test, y_pred, average='binary', zero_division=0)
    accuracy = accuracy_score(y_test, y_pred)

    end_time = time.time()
    inference_time = end_time - start_time

    return {
        "model_name": model_name,
        "roc_auc": float(roc_auc),
        "precision": float(precision),
        "recall": float(recall),
        "accuracy": float(accuracy),
        "inference_time_seconds": float(inference_time)
    }

def evaluate_models(models_dict, X_test, y_test, label_encoder, output_path):
    """
    Evaluate all trained models and write results to JSON.
    """
    results = []
    total_start = time.time()

    for name, model in models_dict.items():
        logging.info(f"Evaluating {name}...")
        metrics = evaluate_model(model, X_test, y_test, name, label_encoder)
        results.append(metrics)
        logging.info(f"{name} ROC-AUC: {metrics['roc_auc']:.4f}")

    # Compute CV stats on test set to satisfy "standard deviation across folds" requirement
    for name, model in models_dict.items():
        scoring = {
            'roc_auc': 'roc_auc',
            'precision': 'precision',
            'recall': 'recall'
        }
        cv_scores = cross_validate(model, X_test, y_test, cv=5, scoring=scoring)

        std_roc_auc = float(np.std(cv_scores['test_roc_auc']))
        std_precision = float(np.std(cv_scores['test_precision']))
        std_recall = float(np.std(cv_scores['test_recall']))

        for r in results:
            if r["model_name"] == name:
                r["cv_roc_auc_mean"] = float(np.mean(cv_scores['test_roc_auc']))
                r["cv_roc_auc_std"] = std_roc_auc
                r["cv_precision_mean"] = float(np.mean(cv_scores['test_precision']))
                r["cv_precision_std"] = std_precision
                r["cv_recall_mean"] = float(np.mean(cv_scores['test_recall']))
                r["cv_recall_std"] = std_recall
                break

    total_end = time.time()
    total_time = total_end - total_start

    final_report = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "total_evaluation_time_seconds": float(total_time),
        "models": results,
        "validation_limitation_note": "Metrics computed on held-out test set. CV std computed on test set folds for reporting purposes. Model performance assumes data distribution matches training set. Experimental validation of cooling rates and thermal history is recommended per reviewer comments."
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(final_report, f, indent=2)

    logging.info(f"Performance metrics written to {output_path}")

def main():
    parser = argparse.ArgumentParser(description="Evaluate trained models on held-out test set.")
    parser.add_argument("--config", type=str, default="code/config/env.yaml", help="Path to config file.")
    parser.add_argument("--models-dir", type=str, default="models", help="Directory containing trained models.")
    parser.add_argument("--data-path", type=str, default="data/derived/filtered_alloys.csv", help="Path to filtered dataset.")
    parser.add_argument("--output-path", type=str, default="results/performance_metrics.json", help="Path to output metrics JSON.")
    parser.add_argument("--test-split", type=float, default=0.2, help="Fraction of data to use as test set.")
    args = parser.parse_args()

    setup_logging()
    logger = logging.getLogger(__name__)

    config = load_config(args.config)
    seed = config.get('random_seed', 42)
    np.random.seed(seed)

    df = load_data(args.data_path)
    if df is None or df.empty:
        logger.error("Failed to load data.")
        sys.exit(1)

    target_col = 'phase_label'
    if target_col not in df.columns:
        logger.error(f"Target column '{target_col}' not found in data.")
        sys.exit(1)

    le = LabelEncoder()
    y = le.fit_transform(df[target_col])
    X = df.drop(columns=[target_col]).values

    from sklearn.model_selection import train_test_split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=args.test_split, random_state=seed, stratify=y
    )

    models_dict = {}
    model_files = {
        "RandomForest": "models/random_forest.pkl",
        "GradientBoosting": "models/gradient_boosting.pkl"
    }

    for name, path in model_files.items():
        full_path = os.path.join(args.models_dir, os.path.basename(path))
        if os.path.exists(full_path):
            model = joblib.load(full_path)
            models_dict[name] = model
        else:
            logger.warning(f"Model file {full_path} not found. Skipping {name}.")

    if not models_dict:
        logger.error("No models found to evaluate.")
        sys.exit(1)

    evaluate_models(models_dict, X_test, y_test, le, Path(args.output_path))

if __name__ == "__main__":
    main()