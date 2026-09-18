"""
Script to implement the performance optimization for T037.
Ensures PCA is applied before PGLS if feature count > N (number of samples).
"""
import os
import sys
import json
import logging
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.logging import setup_logging, get_logger
from config import get_config
from modeling.train import load_pca_features, apply_pca
from modeling.phylo import train_pgls
from data.align import align_data
import pandas as pd
import numpy as np

def load_aligned_matrix() -> pd.DataFrame:
    """Load the aligned matrix from data/processed."""
    config = get_config()
    # Assuming the aligned matrix is saved at the standard location
    # based on T018 implementation
    aligned_path = Path("data/processed/aligned_matrix.csv")
    
    if not aligned_path.exists():
        raise FileNotFoundError(
            f"Aligned matrix not found at {aligned_path}. "
            "Please run the data alignment pipeline first."
        )
    
    return pd.read_csv(aligned_path)

def determine_optimization_needed(df: pd.DataFrame, threshold: float = 1.0) -> bool:
    """
    Determine if PCA optimization is needed.
    
    Args:
        df: The aligned dataframe containing features and target
        threshold: Ratio of features to samples (default 1.0, meaning features > samples)
    
    Returns:
        True if PCA should be applied before PGLS, False otherwise
    """
    # Identify feature columns (exclude non-feature columns like 'species', 'clade', etc.)
    # Assuming target column is something like 'metabolite_abundance' or similar
    # and species info is in 'species' or 'name' column
    exclude_cols = {'species', 'name', 'clade', 'metabolite_abundance', 'target', 'class', 'metabolite_class'}
    
    feature_cols = [col for col in df.columns if col.lower() not in exclude_cols]
    n_features = len(feature_cols)
    n_samples = len(df)
    
    logger = get_logger()
    logger.info(f"Dataset statistics: {n_samples} samples, {n_features} features")
    logger.info(f"Feature-to-sample ratio: {n_features / max(n_samples, 1):.2f}")
    
    # Apply optimization if features > samples (or ratio exceeds threshold)
    needs_pca = n_features > (n_samples * threshold)
    
    if needs_pca:
        logger.warning(f"High dimensionality detected: {n_features} features > {n_samples} samples. "
                     f"PCA optimization will be applied.")
    else:
        logger.info("Dimensionality is acceptable. PCA optimization not required.")
    
    return needs_pca

def run_optimized_pipeline() -> dict:
    """
    Run the PGLS pipeline with conditional PCA application.
    
    Returns:
        Dictionary containing optimization results and metrics
    """
    logger = get_logger()
    logger.info("Starting optimized PGLS pipeline (T037)")
    
    # Load aligned data
    logger.info("Loading aligned data...")
    df = load_aligned_matrix()
    
    # Determine if PCA is needed
    needs_pca = determine_optimization_needed(df)
    
    results = {
        "optimization_applied": needs_pca,
        "n_samples": len(df),
        "n_features": len([col for col in df.columns if col.lower() not in {'species', 'name', 'clade', 'metabolite_abundance', 'target', 'class', 'metabolite_class'}]),
        "message": ""
    }
    
    if needs_pca:
        # Apply PCA
        logger.info("Applying PCA for dimensionality reduction...")
        try:
            # Load or apply PCA features
            # Note: T023a_pca should have already created pca_features.csv
            # We verify it exists or apply PCA fresh if needed
            pca_features_path = Path("data/interim/pca_features.csv")
            
            if not pca_features_path.exists():
                logger.info("PCA features not found, applying PCA fresh...")
                # Apply PCA using the train module
                pca_df = apply_pca(df)
                pca_df.to_csv(pca_features_path, index=False)
                logger.info(f"PCA features saved to {pca_features_path}")
            else:
                logger.info(f"Loading existing PCA features from {pca_features_path}")
            
            # Load PCA features for PGLS
            pca_features = load_pca_features()
            logger.info(f"PCA reduced to {pca_features.shape[1]} components")
            
            results["pca_components"] = pca_features.shape[1]
            results["message"] = "PCA successfully applied before PGLS"
            
            # Train PGLS with PCA features
            logger.info("Training PGLS model with PCA-reduced features...")
            pgls_results = train_pgls(pca_features)
            
            results["pgls_r2"] = pgls_results.get('r2', 0.0)
            results["pgls_model"] = "PCA-PGLS"
            
        except Exception as e:
            logger.error(f"PCA optimization failed: {str(e)}")
            results["optimization_applied"] = False
            results["message"] = f"PCA optimization failed: {str(e)}"
            raise
    else:
        # Direct PGLS without PCA
        logger.info("Training PGLS model without PCA...")
        # Prepare features directly from aligned data
        exclude_cols = {'species', 'name', 'clade', 'metabolite_abundance', 'target', 'class', 'metabolite_class'}
        feature_cols = [col for col in df.columns if col.lower() not in exclude_cols]
        X = df[feature_cols]
        
        pgls_results = train_pgls(X)
        
        results["pgls_r2"] = pgls_results.get('r2', 0.0)
        results["pgls_model"] = "Direct-PGLS"
        results["message"] = "PCA optimization not needed, using direct PGLS"
    
    # Save results
    results_path = Path("data/processed/optimization_results.json")
    results_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(results_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Optimization results saved to {results_path}")
    logger.info(f"Final PGLS R²: {results['pgls_r2']:.4f}")
    
    return results

def main():
    """Main entry point for the optimization script."""
    # Setup logging
    log_config = get_config()
    logger = setup_logging(
        log_level="INFO",
        log_file="data/logs/optimization.log"
    )
    
    logger.info("=" * 60)
    logger.info("T037: Performance Optimization - PCA before PGLS")
    logger.info("=" * 60)
    
    try:
        results = run_optimized_pipeline()
        
        logger.info("=" * 60)
        logger.info("OPTIMIZATION SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Optimization Applied: {results['optimization_applied']}")
        logger.info(f"Samples: {results['n_samples']}")
        logger.info(f"Features: {results['n_features']}")
        if results.get('pca_components'):
            logger.info(f"PCA Components: {results['pca_components']}")
        logger.info(f"Model Type: {results['pgls_model']}")
        logger.info(f"PGLS R²: {results['pgls_r2']:.4f}")
        logger.info(f"Message: {results['message']}")
        logger.info("=" * 60)
        
        return 0
        
    except Exception as e:
        logger.error(f"Pipeline execution failed: {str(e)}")
        logger.exception("Full traceback:")
        return 1

if __name__ == "__main__":
    sys.exit(main())