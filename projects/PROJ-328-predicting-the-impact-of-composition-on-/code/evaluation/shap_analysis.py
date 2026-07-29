"""
SHAP analysis module for solder hardness prediction models.

This module implements SHAP value calculation and top-3 feature ranking
for the XGBoost and Linear Regression models trained in the pipeline.

It loads the validated dataset, applies the CLR transform, loads the trained
XGBoost model, computes SHAP values, and saves the top-3 feature rankings
and summary plots to the outputs directory.
"""

import os
import sys
import logging
import json
import pickle
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

import numpy as np
import pandas as pd
import shap
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for server environments
import matplotlib.pyplot as plt

# Project imports
from seed import init_reproducibility
from config import (
    get_data_processed_dir,
    get_data_outputs_dir,
    get_models_dir,
    get_log_level,
    get_log_format
)
from features.transformer import CLRTransformer
from utils.logging_config import get_logger
from utils.error_handlers import ModelTrainingError, ConfigurationError

logger = get_logger(__name__)


class SHAPAnalyzer:
    """
    Analyzes trained models using SHAP (SHapley Additive exPlanations).

    This class handles loading models, computing SHAP values, and generating
    feature importance rankings and visualizations.
    """

    def __init__(self, model_type: str = "xgboost"):
        """
        Initialize the SHAP analyzer.

        Args:
            model_type: Type of model to analyze ('xgboost' or 'linear')
        """
        self.model_type = model_type
        self.shap_values = None
        self.expected_value = None
        self.feature_names = None
        self.model = None
        self.transformer = None

    def load_data(self, data_path: Optional[Path] = None) -> pd.DataFrame:
        """
        Load the validated dataset.

        Args:
            data_path: Optional path to the validated dataset. If None, uses config.

        Returns:
            DataFrame containing the validated solder composition data.
        """
        if data_path is None:
            data_dir = get_data_processed_dir()
            data_path = Path(data_dir) / "solder_hardness_validated.csv"

        if not os.path.exists(data_path):
            raise ConfigurationError(f"Validated dataset not found at {data_path}")

        logger.info(f"Loading validated dataset from {data_path}")
        df = pd.read_csv(data_path)
        return df

    def load_model(self, model_path: Optional[Path] = None):
        """
        Load the trained model.

        Args:
            model_path: Optional path to the model file. If None, uses config.

        Raises:
            ConfigurationError: If model file not found.
            ModelTrainingError: If model loading fails.
        """
        if model_path is None:
            models_dir = get_models_dir()
            if self.model_type == "xgboost":
                model_path = Path(models_dir) / "xgboost_model.pkl"
            else:
                model_path = Path(models_dir) / "linear_model.pkl"

        if not os.path.exists(model_path):
            raise ConfigurationError(f"Model file not found at {model_path}")

        logger.info(f"Loading model from {model_path}")
        try:
            with open(model_path, 'rb') as f:
                self.model = pickle.load(f)
            logger.info(f"Successfully loaded {self.model_type} model")
        except Exception as e:
            raise ModelTrainingError(f"Failed to load model: {str(e)}")

    def prepare_features(self, df: pd.DataFrame) -> Tuple[np.ndarray, List[str]]:
        """
        Prepare feature matrix by applying CLR transform.

        Args:
            df: DataFrame with composition columns.

        Returns:
            Tuple of (transformed feature matrix, feature names).
        """
        # Identify composition columns (all columns except target and metadata)
        composition_cols = [col for col in df.columns if col not in ['vickers_hardness', 'alloy_id', 'source']]

        if not composition_cols:
            raise ConfigurationError("No composition columns found in dataset")

        logger.info(f"Using {len(composition_cols)} composition columns for CLR transform")

        # Initialize and fit CLR transformer
        self.transformer = CLRTransformer()
        X_raw = df[composition_cols].values

        # Apply CLR transform
        X_transformed = self.transformer.fit_transform(X_raw)

        # Generate feature names for CLR components
        self.feature_names = [f"CLR_{col}" for col in composition_cols]

        logger.info(f"CLR transform completed. Shape: {X_transformed.shape}")
        return X_transformed, self.feature_names

    def compute_shap_values(self, X: np.ndarray, sample_size: int = 100):
        """
        Compute SHAP values for the model.

        Args:
            X: Feature matrix (already transformed).
            sample_size: Number of samples to use for background dataset.
        """
        if self.model is None:
            raise ConfigurationError("Model not loaded. Call load_model() first.")

        logger.info("Computing SHAP values...")

        # Create background dataset for SHAP explainer
        if X.shape[0] > sample_size:
            # Sample a subset for background
            np.random.seed(42)  # Use fixed seed for reproducibility
            indices = np.random.choice(X.shape[0], sample_size, replace=False)
            background = X[indices]
        else:
            background = X

        # Initialize SHAP explainer based on model type
        if self.model_type == "xgboost":
            explainer = shap.TreeExplainer(self.model)
        else:
            # For linear models, use LinearExplainer
            explainer = shap.LinearExplainer(self.model, background)

        # Compute SHAP values
        self.shap_values = explainer.shap_values(X)
        self.expected_value = explainer.expected_value

        logger.info(f"SHAP values computed. Shape: {self.shap_values.shape}")

        # Handle case where SHAP returns list for some model types
        if isinstance(self.shap_values, list):
            self.shap_values = self.shap_values[0]

    def get_top_features(self, n: int = 3) -> List[Tuple[str, float]]:
        """
        Get the top N most important features based on SHAP values.

        Args:
            n: Number of top features to return.

        Returns:
            List of (feature_name, mean_abs_shap_value) tuples.
        """
        if self.shap_values is None:
            raise ConfigurationError("SHAP values not computed. Call compute_shap_values() first.")

        # Calculate mean absolute SHAP values for each feature
        mean_abs_shap = np.mean(np.abs(self.shap_values), axis=0)

        # Get indices of top features
        top_indices = np.argsort(mean_abs_shap)[::-1][:n]

        # Create list of (feature_name, importance) tuples
        top_features = [
            (self.feature_names[i], float(mean_abs_shap[i]))
            for i in top_indices
        ]

        logger.info(f"Top {n} features identified: {[name for name, _ in top_features]}")
        return top_features

    def save_results(self, output_dir: Optional[Path] = None, filename: str = "shap_results.json"):
        """
        Save SHAP analysis results to a JSON file.

        Args:
            output_dir: Optional output directory. If None, uses config.
            filename: Name of the output file.
        """
        if output_dir is None:
            output_dir = get_data_outputs_dir()
        else:
            output_dir = Path(output_dir)

        output_path = Path(output_dir) / filename
        output_dir.mkdir(parents=True, exist_ok=True)

        # Get top features
        top_features = self.get_top_features(n=3)

        # Prepare results dictionary
        results = {
            "model_type": self.model_type,
            "top_3_features": [
                {"feature": name, "importance": float(importance)}
                for name, importance in top_features
            ],
            "all_features_importance": [
                {"feature": name, "importance": float(imp)}
                for name, imp in zip(self.feature_names, np.mean(np.abs(self.shap_values), axis=0))
            ],
            "shap_stats": {
                "mean_shap": float(np.mean(self.shap_values)),
                "std_shap": float(np.std(self.shap_values)),
                "max_abs_shap": float(np.max(np.abs(self.shap_values)))
            }
        }

        # Save to JSON
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)

        logger.info(f"SHAP results saved to {output_path}")
        return results

    def plot_summary(self, output_dir: Optional[Path] = None, filename: str = "shap_summary.png"):
        """
        Generate and save a SHAP summary plot.

        Args:
            output_dir: Optional output directory. If None, uses config.
            filename: Name of the output file.
        """
        if self.shap_values is None:
            raise ConfigurationError("SHAP values not computed. Call compute_shap_values() first.")

        if output_dir is None:
            output_dir = get_data_outputs_dir()
        else:
            output_dir = Path(output_dir)

        output_path = Path(output_dir) / filename
        output_dir.mkdir(parents=True, exist_ok=True)

        # Create summary plot
        plt.figure(figsize=(10, 8))
        shap.summary_plot(
            self.shap_values,
            self.transformer.transformer_output if hasattr(self.transformer, 'transformer_output') else None,
            features=self.transformer.transformer_output if hasattr(self.transformer, 'transformer_output') else None,
            feature_names=self.feature_names,
            show=False,
            plot_type="dot"
        )

        plt.title("SHAP Summary Plot - Solder Hardness Prediction")
        plt.tight_layout()
        plt.savefig(output_path, dpi=150)
        plt.close()

        logger.info(f"SHAP summary plot saved to {output_path}")

    def run_full_analysis(self, data_path: Optional[Path] = None, model_path: Optional[Path] = None, output_dir: Optional[Path] = None):
        """
        Run the complete SHAP analysis pipeline.

        Args:
            data_path: Path to validated dataset.
            model_path: Path to trained model.
            output_dir: Path to output directory.

        Returns:
            Dictionary containing analysis results.
        """
        # Initialize reproducibility
        init_reproducibility()

        # Load data
        df = self.load_data(data_path)

        # Load model
        self.load_model(model_path)

        # Prepare features
        X, feature_names = self.prepare_features(df)

        # Compute SHAP values
        self.compute_shap_values(X)

        # Get top features
        top_features = self.get_top_features(n=3)

        # Save results
        results = self.save_results(output_dir)

        # Generate plot
        self.plot_summary(output_dir)

        return results


def main():
    """
    Main entry point for SHAP analysis.

    This function orchestrates the complete SHAP analysis workflow:
    1. Load validated dataset
    2. Load trained XGBoost model
    3. Apply CLR transform
    4. Compute SHAP values
    5. Identify top 3 features
    6. Save results and generate visualization
    """
    # Initialize logging
    logging.basicConfig(
        level=get_log_level(),
        format=get_log_format()
    )

    logger.info("Starting SHAP analysis for solder hardness prediction")

    try:
        # Initialize analyzer
        analyzer = SHAPAnalyzer(model_type="xgboost")

        # Run full analysis
        results = analyzer.run_full_analysis()

        logger.info("SHAP analysis completed successfully")
        logger.info(f"Top 3 features: {results['top_3_features']}")

        # Print summary to stdout
        print("\n" + "="*50)
        print("SHAP ANALYSIS RESULTS")
        print("="*50)
        print(f"Model Type: {results['model_type']}")
        print("\nTop 3 Most Important Features:")
        for i, feature in enumerate(results['top_3_features'], 1):
            print(f"  {i}. {feature['feature']}: {feature['importance']:.4f}")
        print("="*50 + "\n")

        return 0

    except Exception as e:
        logger.error(f"SHAP analysis failed: {str(e)}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())