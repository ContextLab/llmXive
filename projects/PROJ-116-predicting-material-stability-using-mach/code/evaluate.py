import os
import json
import logging
from pathlib import Path
import pandas as pd
import numpy as np
import joblib
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from config import PROCESSED_DATA_DIR, MODELS_DIR, OUTPUTS_DIR
from utils.logging import setup_logger

# Setup logger
logger = setup_logger(__name__)

def main():
    """Evaluate baseline and augmented models."""
    logger.info("Starting model evaluation...")

    # Load test data
    features_path = PROCESSED_DATA_DIR / "baseline_features.parquet"
    if not features_path.exists():
        raise FileNotFoundError(f"Features file not found: {features_path}")

    df = pd.read_parquet(features_path)

    # Prepare features and target
    if 'formation_energy' not in df.columns:
        raise ValueError("formation_energy column not found in features")

    feature_cols = [col for col in df.columns if col != 'formation_energy']
    X = df[feature_cols]
    y = df['formation_energy']

    # Split data (same as training)
    from sklearn.model_selection import train_test_split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    # Load baseline model
    baseline_model_path = MODELS_DIR / "baseline_model.pkl"
    if baseline_model_path.exists():
        baseline_model = joblib.load(baseline_model_path)
        baseline_pred = baseline_model.predict(X_test)
        baseline_mae = mean_absolute_error(y_test, baseline_pred)
        baseline_rmse = np.sqrt(mean_squared_error(y_test, baseline_pred))
        baseline_r2 = r2_score(y_test, baseline_pred)

        logger.info(f"Baseline - MAE: {baseline_mae:.4f}, RMSE: {baseline_rmse:.4f}, R²: {baseline_r2:.4f}")

        # Save baseline results
        baseline_results = pd.DataFrame({
            'material_id': df.iloc[X_test.index]['material_id'].values,
            'actual': y_test.values,
            'predicted': baseline_pred,
            'error': np.abs(y_test.values - baseline_pred)
        })
        baseline_results_path = OUTPUTS_DIR / "baseline_results.csv"
        baseline_results.to_csv(baseline_results_path, index=False)
        logger.info(f"Saved baseline results to {baseline_results_path}")
    else:
        logger.warning("Baseline model not found, skipping baseline evaluation")
        baseline_mae = None

    # Load augmented model
    augmented_model_path = MODELS_DIR / "augmented_model.pkl"
    if augmented_model_path.exists():
        # Load augmented features
        augmented_features_path = PROCESSED_DATA_DIR / "augmented_features.parquet"
        augmented_df = pd.read_parquet(augmented_features_path)

        aug_feature_cols = [col for col in augmented_df.columns if col != 'formation_energy']
        X_aug = augmented_df[aug_feature_cols]
        _, X_aug_test, _, y_aug_test = train_test_split(
            X_aug, augmented_df['formation_energy'], test_size=0.2, random_state=42
        )

        augmented_model = joblib.load(augmented_model_path)
        augmented_pred = augmented_model.predict(X_aug_test)
        augmented_mae = mean_absolute_error(y_aug_test, augmented_pred)
        augmented_rmse = np.sqrt(mean_squared_error(y_aug_test, augmented_pred))
        augmented_r2 = r2_score(y_aug_test, augmented_pred)

        logger.info(f"Augmented - MAE: {augmented_mae:.4f}, RMSE: {augmented_rmse:.4f}, R²: {augmented_r2:.4f}")

        # Calculate deltas
        if baseline_mae is not None:
            mae_delta = baseline_mae - augmented_mae
            r2_delta = augmented_r2 - baseline_r2

            comparison_metrics = {
                'baseline_mae': baseline_mae,
                'augmented_mae': augmented_mae,
                'mae_delta': mae_delta,
                'baseline_r2': baseline_r2,
                'augmented_r2': augmented_r2,
                'r2_delta': r2_delta
            }

            comparison_path = OUTPUTS_DIR / "comparison_metrics.json"
            with open(comparison_path, 'w') as f:
                json.dump(comparison_metrics, f, indent=2)
            logger.info(f"Saved comparison metrics to {comparison_path}")

            # Generate feature importance plot
            generate_feature_importance_plot(augmented_model, aug_feature_cols)
    else:
        logger.warning("Augmented model not found, skipping augmented evaluation")

def generate_feature_importance_plot(model, feature_names):
    """Generate feature importance plot."""
    import matplotlib.pyplot as plt

    # Get feature importances
    importances = model.feature_importances_
    indices = np.argsort(importances)[::-1]

    # Plot top 20 features
    plt.figure(figsize=(10, 8))
    plt.title("Feature Importances")
    plt.bar(range(20), importances[indices][:20], align="center")
    plt.xticks(range(20), [feature_names[i] for i in indices[:20]], rotation=90)
    plt.tight_layout()

    output_path = OUTPUTS_DIR / "figures" / "feature_importance.png"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path)
    logger.info(f"Saved feature importance plot to {output_path}")

if __name__ == "__main__":
    main()
