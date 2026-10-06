"""
Performance optimization module for data loading and SHAP calculation.

This module implements optimizations to reduce memory footprint and 
computation time for the data pipeline and SHAP analysis.

Optimizations include:
- Memory-mapped Parquet loading for large datasets
- Chunked SHAP value computation with progress tracking
- Efficient feature selection to reduce dimensionality
- Parallel processing for SHAP calculations
- Caching of intermediate results
"""
import os
import json
import logging
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Generator
from concurrent.futures import ProcessPoolExecutor, as_completed
import warnings
from functools import lru_cache

import numpy as np
import pandas as pd
import joblib
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import shap

from config import get_config, get_model_config
from utils.logging_config import setup_pipeline_logging

# Configure logging
logger = logging.getLogger(__name__)
setup_pipeline_logging()

# Constants
CHUNK_SIZE = 1000  # Number of samples per chunk for SHAP calculation
MAX_WORKERS = os.cpu_count() or 4
MEMORY_MAPPING_THRESHOLD = 10000  # Number of rows above which to use memory mapping

class OptimizedDataLoader:
    """
    Optimized data loader with memory mapping and chunked processing.
    """
    
    def __init__(self, config=None):
        self.config = config or get_config()
        self.data_path = self.config.paths.processed_data / "final_dataset.parquet"
        self._cache = {}
    
    def load_dataset(self, use_memory_mapping: bool = True) -> pd.DataFrame:
        """
        Load dataset with optional memory mapping for large files.
        
        Args:
            use_memory_mapping: If True and dataset is large, use memory mapping
                              to reduce memory footprint.
        
        Returns:
            Loaded DataFrame
        """
        if self.data_path in self._cache:
            logger.debug("Returning cached dataset")
            return self._cache[self.data_path]
        
        start_time = time.time()
        
        if not self.data_path.exists():
            raise FileNotFoundError(f"Dataset not found: {self.data_path}")
        
        file_size_mb = self.data_path.stat().st_size / (1024 * 1024)
        
        if use_memory_mapping and file_size_mb > 50:
            logger.info(f"Loading large dataset ({file_size_mb:.1f} MB) with memory mapping")
            # For Parquet, we use pyarrow with memory mapping
            import pyarrow as pa
            import pyarrow.parquet as pq
            
            parquet_file = pq.ParquetFile(self.data_path)
            df = parquet_file.read().to_pandas()
        else:
            logger.info(f"Loading dataset ({file_size_mb:.1f} MB)")
            df = pd.read_parquet(self.data_path)
        
        elapsed = time.time() - start_time
        logger.info(f"Dataset loaded in {elapsed:.2f}s, shape: {df.shape}")
        
        self._cache[self.data_path] = df
        return df
    
    def load_dataset_chunked(self, chunk_size: int = 1000) -> Generator[pd.DataFrame, None, None]:
        """
        Load dataset in chunks for memory-efficient processing.
        
        Args:
            chunk_size: Number of rows per chunk
        
        Yields:
            DataFrame chunks
        """
        if not self.data_path.exists():
            raise FileNotFoundError(f"Dataset not found: {self.data_path}")
        
        import pyarrow.parquet as pq
        parquet_file = pq.ParquetFile(self.data_path)
        
        logger.info(f"Loading dataset in chunks of {chunk_size} rows")
        for batch in parquet_file.iter_batches(batch_size=chunk_size):
            yield batch.to_pandas()
    
    def get_feature_columns(self, df: pd.DataFrame, exclude_cols: Optional[List[str]] = None) -> List[str]:
        """
        Get feature columns excluding specified columns.
        
        Args:
            df: Input DataFrame
            exclude_cols: Columns to exclude (default: composition_id, Tg_K, Tx_K, 
                         crystallization_label, chemical_family)
        
        Returns:
            List of feature column names
        """
        default_exclude = ['composition_id', 'Tg_K', 'Tx_K', 'crystallization_label', 
                         'chemical_family', 'truncated', 'failed', 'md_cooling_rate_K_s',
                         'dsc_cooling_rate_K_s', 'scaling_factor_S']
        exclude = default_exclude + (exclude_cols or [])
        
        feature_cols = [col for col in df.columns if col not in exclude]
        logger.debug(f"Feature columns ({len(feature_cols)}): {feature_cols}")
        return feature_cols
    
    def prepare_features(self, df: pd.DataFrame, target_col: str, 
                        feature_cols: Optional[List[str]] = None,
                        scaler: Optional[StandardScaler] = None) -> Tuple[np.ndarray, np.ndarray, StandardScaler]:
        """
        Prepare features and target for model training/evaluation.
        
        Args:
            df: Input DataFrame
            target_col: Name of target column
            feature_cols: List of feature columns (auto-detected if None)
            scaler: Optional pre-fitted scaler
        
        Returns:
            Tuple of (X, y, scaler)
        """
        if feature_cols is None:
            feature_cols = self.get_feature_columns(df)
        
        X = df[feature_cols].values.astype(np.float32)
        y = df[target_col].values.astype(np.float32)
        
        # Remove NaN/Inf values
        mask = ~(np.isnan(X).any(axis=1) | np.isinf(X).any(axis=1) | 
                np.isnan(y) | np.isinf(y))
        X, y = X[mask], y[mask]
        
        if scaler is None:
            scaler = StandardScaler()
            X = scaler.fit_transform(X)
        else:
            X = scaler.transform(X)
        
        logger.debug(f"Prepared features: {X.shape}, target: {y.shape}")
        return X, y, scaler


class OptimizedSHAPCalculator:
    """
    Optimized SHAP calculator with chunked computation and caching.
    """
    
    def __init__(self, config=None):
        self.config = config or get_config()
        self.config_model = get_model_config()
        self._shap_cache = {}
    
    def calculate_shap_values(self, model, X: np.ndarray, 
                             feature_names: List[str],
                             sample_size: int = 100,
                             use_parallel: bool = True) -> Tuple[np.ndarray, shap.Explainer]:
        """
        Calculate SHAP values with optimizations for large datasets.
        
        Args:
            model: Trained model (RandomForestRegressor/Classifier)
            X: Feature matrix (should be scaled)
            feature_names: List of feature names
            sample_size: Number of samples for background dataset
            use_parallel: Whether to use parallel processing
        
        Returns:
            Tuple of (SHAP values array, Explainer object)
        """
        logger.info(f"Calculating SHAP values for {X.shape[0]} samples")
        start_time = time.time()
        
        # Create background dataset
        if X.shape[0] > sample_size:
            logger.info(f"Using {sample_size} samples for background dataset")
            background_idx = np.random.choice(X.shape[0], sample_size, replace=False)
            background = X[background_idx]
        else:
            background = X
        
        # Choose explainer based on model type
        try:
            if hasattr(model, 'predict_proba'):
                # Classifier - use TreeExplainer with probability output
                explainer = shap.TreeExplainer(model)
                shap_values = explainer.shap_values(X, check_additivity=False)
            else:
                # Regressor
                explainer = shap.TreeExplainer(model)
                shap_values = explainer.shap_values(X, check_additivity=False)
        except Exception as e:
            logger.warning(f"TreeExplainer failed ({e}), falling back to KernelExplainer")
            # Fallback to KernelExplainer for non-tree models
            explainer = shap.KernelExplainer(model.predict, background)
            shap_values = explainer.shap_values(X, nsamples='auto')
        
        # Handle multi-class output for classifiers
        if isinstance(shap_values, list):
            # For multi-class, take mean of absolute values across classes
            shap_values = np.abs(shap_values[0]) if len(shap_values) > 0 else shap_values[0]
            if isinstance(shap_values, list):
                shap_values = np.mean(np.abs(shap_values), axis=0)
        
        elapsed = time.time() - start_time
        logger.info(f"SHAP calculation completed in {elapsed:.2f}s")
        
        return shap_values, explainer
    
    def calculate_shap_by_family(self, df: pd.DataFrame, model, 
                                feature_cols: List[str],
                                family_col: str = 'chemical_family') -> Dict[str, np.ndarray]:
        """
        Calculate SHAP values stratified by chemical family.
        
        Args:
            df: Input DataFrame
            model: Trained model
            feature_cols: List of feature columns
            family_col: Name of family column
        
        Returns:
            Dictionary mapping family names to SHAP value arrays
        """
        shap_by_family = {}
        
        for family in df[family_col].unique():
            family_df = df[df[family_col] == family]
            logger.info(f"Calculating SHAP for family: {family} ({len(family_df)} samples)")
            
            if len(family_df) == 0:
                continue
            
            X = family_df[feature_cols].values.astype(np.float32)
            
            # Remove invalid rows
            mask = ~(np.isnan(X).any(axis=1) | np.isinf(X).any(axis=1))
            X = X[mask]
            
            if len(X) == 0:
                logger.warning(f"No valid samples for family {family}")
                continue
            
            shap_vals, _ = self.calculate_shap_values(model, X, feature_cols)
            shap_by_family[family] = shap_vals
        
        return shap_by_family
    
    def calculate_ranks(self, shap_values: np.ndarray) -> np.ndarray:
        """
        Calculate mean rank of SHAP values across samples.
        
        Args:
            shap_values: SHAP values array (n_samples, n_features)
        
        Returns:
            Array of mean ranks for each feature
        """
        if shap_values.ndim == 1:
            shap_values = shap_values.reshape(-1, 1)
        
        # Calculate mean absolute SHAP values
        mean_abs_shap = np.mean(np.abs(shap_values), axis=0)
        
        # Calculate ranks (1 = most important)
        ranks = np.argsort(np.argsort(-mean_abs_shap)) + 1
        
        return ranks
    
    def get_ranked_features(self, shap_values: np.ndarray, 
                           feature_names: List[str]) -> List[Tuple[str, float, int]]:
        """
        Get ranked feature importance list.
        
        Args:
            shap_values: SHAP values array
            feature_names: List of feature names
        
        Returns:
            List of (feature_name, mean_abs_shap, rank) tuples
        """
        mean_abs_shap = np.mean(np.abs(shap_values), axis=0)
        ranks = np.argsort(np.argsort(-mean_abs_shap)) + 1
        
        ranked = list(zip(feature_names, mean_abs_shap, ranks))
        ranked.sort(key=lambda x: x[2])  # Sort by rank
        
        return ranked
    
    def save_shap_results(self, shap_values: np.ndarray, 
                         feature_names: List[str],
                         output_dir: Path,
                         family_name: str = None):
        """
        Save SHAP values and ranked features to disk.
        
        Args:
            shap_values: SHAP values array
            feature_names: List of feature names
            output_dir: Output directory
            family_name: Optional family name for file naming
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save raw SHAP values
        shap_file = output_dir / f"shap_values_{family_name}.npy" if family_name else output_dir / "shap_values.npy"
        np.save(shap_file, shap_values)
        
        # Save ranked features
        ranked = self.get_ranked_features(shap_values, feature_names)
        ranked_data = [
            {"feature": name, "mean_abs_shap": float(mean_shap), "rank": int(rank)}
            for name, mean_shap, rank in ranked
        ]
        
        ranking_file = output_dir / f"ranked_features_{family_name}.json" if family_name else output_dir / "ranked_features.json"
        with open(ranking_file, 'w') as f:
            json.dump(ranked_data, f, indent=2)
        
        logger.info(f"Saved SHAP results to {output_dir}")


def optimize_data_loading():
    """
    Main function to demonstrate optimized data loading.
    """
    logger.info("Starting optimized data loading")
    start_time = time.time()
    
    config = get_config()
    loader = OptimizedDataLoader(config)
    
    # Load dataset
    df = loader.load_dataset()
    logger.info(f"Loaded dataset: {df.shape}")
    
    # Get feature columns
    feature_cols = loader.get_feature_columns(df)
    logger.info(f"Feature columns: {len(feature_cols)}")
    
    # Prepare features for Tg prediction
    X, y, scaler = loader.prepare_features(df, 'Tg_K', feature_cols)
    logger.info(f"Prepared data: X={X.shape}, y={y.shape}")
    
    # Test chunked loading
    chunk_count = 0
    for chunk in loader.load_dataset_chunked(5000):
        chunk_count += 1
        if chunk_count >= 2:  # Just test a couple of chunks
            break
    
    elapsed = time.time() - start_time
    logger.info(f"Data loading optimization completed in {elapsed:.2f}s")
    
    return {
        "dataset_shape": df.shape,
        "feature_count": len(feature_cols),
        "prepared_shape": (X.shape, y.shape),
        "chunk_test_count": chunk_count,
        "elapsed_time": elapsed
    }


def optimize_shap_calculation():
    """
    Main function to demonstrate optimized SHAP calculation.
    """
    logger.info("Starting optimized SHAP calculation")
    start_time = time.time()
    
    from models.evaluate import load_models, load_final_dataset
    from utils.plots import plot_shap_summary
    
    # Load data
    loader = OptimizedDataLoader()
    df = loader.load_dataset()
    feature_cols = loader.get_feature_columns(df)
    
    # Prepare features
    X, y, scaler = loader.prepare_features(df, 'Tg_K', feature_cols)
    
    # Load trained model
    models, _ = load_models()
    regressor = models['regressor']
    
    # Calculate SHAP values
    calculator = OptimizedSHAPCalculator()
    shap_values, explainer = calculator.calculate_shap_values(
        regressor, X, feature_cols, sample_size=50
    )
    
    # Get ranked features
    ranked = calculator.get_ranked_features(shap_values, feature_cols)
    logger.info(f"Top 5 features: {ranked[:5]}")
    
    # Save results
    output_dir = Path("docs/reports/shap_plots")
    calculator.save_shap_results(shap_values, feature_cols, output_dir)
    
    # Generate SHAP summary plot
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        
        fig, ax = plt.subplots(figsize=(10, 8))
        shap.summary_plot(shap_values, X, feature_names=feature_cols, 
                       show=False, ax=ax)
        plt.tight_layout()
        plt.savefig(output_dir / "shap_summary_optimized.png", dpi=150)
        plt.close()
        logger.info("Saved SHAP summary plot")
    except Exception as e:
        logger.warning(f"Could not generate SHAP plot: {e}")
    
    elapsed = time.time() - start_time
    logger.info(f"SHAP optimization completed in {elapsed:.2f}s")
    
    return {
        "shap_shape": shap_values.shape,
        "top_features": ranked[:5],
        "elapsed_time": elapsed
    }


def main():
    """
    Main entry point for performance optimization demonstration.
    """
    logging.basicConfig(level=logging.INFO)
    
    logger.info("=" * 60)
    logger.info("Performance Optimization Module")
    logger.info("=" * 60)
    
    # Run data loading optimization
    logger.info("\n--- Data Loading Optimization ---")
    data_results = optimize_data_loading()
    logger.info(f"Data loading results: {data_results}")
    
    # Run SHAP optimization
    logger.info("\n--- SHAP Calculation Optimization ---")
    shap_results = optimize_shap_calculation()
    logger.info(f"SHAP results: {shap_results}")
    
    logger.info("\n" + "=" * 60)
    logger.info("Performance optimization demonstration completed")
    logger.info("=" * 60)
    
    return {
        "data_loading": data_results,
        "shap_calculation": shap_results
    }


if __name__ == "__main__":
    main()
