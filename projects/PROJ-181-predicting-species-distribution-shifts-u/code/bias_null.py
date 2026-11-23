"""
bias_null.py

Implements a bias-only null model using random background sampling.
This replaces any KDE-based bias layer with a purely random sampling approach
to serve as a null hypothesis baseline for model performance evaluation.

Output: metrics/bias_null_metrics.csv with columns: species, algorithm, auc, tss
"""
import os
import sys
import logging
import csv
import json
import random
from pathlib import Path
from datetime import datetime

import pandas as pd
import numpy as np
from sklearn.metrics import roc_auc_score, confusion_matrix

# Import project configuration and utilities
import config
from logging_config import get_train_logger
from utils.data_utils import validate_coordinates

def get_bias_null_logger():
    """Get a logger specifically for bias null model tasks."""
    return get_train_logger("bias_null")

def load_clean_data(input_path):
    """
    Load cleaned occurrence data from CSV.
    
    Args:
        input_path: Path to the cleaned occurrence CSV file
        
    Returns:
        DataFrame with occurrence records
    """
    logger = get_bias_null_logger()
    if not os.path.exists(input_path):
        logger.error(f"Clean data file not found: {input_path}")
        raise FileNotFoundError(f"Clean data file not found: {input_path}")
    
    df = pd.read_csv(input_path)
    logger.info(f"Loaded {len(df)} records from {input_path}")
    return df

def generate_random_background(df, n_samples=10000, seed=None):
    """
    Generate random background points within the bounding box of the occurrence data.
    
    This implements the bias-only null model by sampling uniformly from the
    geographic extent of the data, ignoring any environmental or sampling bias.
    
    Args:
        df: DataFrame with occurrence records (must have decimalLatitude, decimalLongitude)
        n_samples: Number of background points to generate
        seed: Random seed for reproducibility
        
    Returns:
        DataFrame with random background points
    """
    logger = get_bias_null_logger()
    
    if seed is not None:
        random.seed(seed)
        np.random.seed(seed)
    
    # Get bounding box from occurrence data
    lat_min = df['decimalLatitude'].min()
    lat_max = df['decimalLatitude'].max()
    lon_min = df['decimalLongitude'].min()
    lon_max = df['decimalLongitude'].max()
    
    logger.info(f"Generating {n_samples} random background points within "
               f"lat [{lat_min:.2f}, {lat_max:.2f}], lon [{lon_min:.2f}, {lon_max:.2f}]")
    
    # Generate random coordinates
    background_lats = np.random.uniform(lat_min, lat_max, n_samples)
    background_lons = np.random.uniform(lon_min, lon_max, n_samples)
    
    background_df = pd.DataFrame({
        'decimalLatitude': background_lats,
        'decimalLongitude': background_lons
    })
    
    return background_df

def train_bias_null_model(presence_df, background_df, seed=None):
    """
    Train a simple bias-only null model.
    
    The null model assumes that presence and background are indistinguishable
    beyond their spatial distribution. We use a simple logistic regression
    with no features (intercept only) to establish the baseline prevalence.
    
    Args:
        presence_df: DataFrame with presence records
        background_df: DataFrame with background records
        seed: Random seed for reproducibility
        
    Returns:
        dict: Model parameters (prevalence)
    """
    logger = get_bias_null_logger()
    
    # Calculate prevalence (proportion of presence in combined dataset)
    n_presence = len(presence_df)
    n_background = len(background_df)
    n_total = n_presence + n_background
    
    prevalence = n_presence / n_total
    
    logger.info(f"Null model prevalence: {prevalence:.4f} "
               f"({n_presence} presence, {n_background} background)")
    
    return {'prevalence': prevalence, 'n_presence': n_presence, 'n_background': n_background}

def predict_bias_null(model_params, n_samples):
    """
    Predict using the bias-only null model.
    
    The null model predicts the same probability (prevalence) for all points.
    
    Args:
        model_params: Dictionary with model parameters
        n_samples: Number of samples to predict
        
    Returns:
        numpy array of predicted probabilities
    """
    prevalence = model_params['prevalence']
    return np.full(n_samples, prevalence)

def calculate_metrics(y_true, y_pred_proba):
    """
    Calculate AUC and TSS metrics for the null model.
    
    Args:
        y_true: Binary labels (1 for presence, 0 for background)
        y_pred_proba: Predicted probabilities
        
    Returns:
        dict: AUC and TSS scores
    """
    logger = get_bias_null_logger()
    
    # Calculate AUC
    try:
        auc = roc_auc_score(y_true, y_pred_proba)
    except ValueError as e:
        logger.warning(f"Could not calculate AUC: {e}")
        auc = 0.5  # Random baseline
    
    # Calculate TSS (True Skill Statistic)
    # Find optimal threshold (for null model, this is typically the prevalence)
    threshold = 0.5
    y_pred = (y_pred_proba >= threshold).astype(int)
    
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred).ravel()
    
    sensitivity = tp / (tp + fn) if (tp + fn) > 0 else 0
    specificity = tn / (tn + fp) if (tn + fp) > 0 else 0
    
    tss = sensitivity + specificity - 1
    
    logger.info(f"AUC: {auc:.4f}, TSS: {tss:.4f}")
    
    return {'auc': auc, 'tss': tss, 'threshold': threshold}

def run_bias_null_model(species_name, data_path, n_background=10000, seed=None):
    """
    Run the bias-only null model for a specific species.
    
    Args:
        species_name: Name of the species to model
        data_path: Path to the cleaned occurrence data
        n_background: Number of background points to generate
        seed: Random seed for reproducibility
        
    Returns:
        dict: Model results including metrics
    """
    logger = get_bias_null_logger()
    logger.info(f"Running bias-only null model for species: {species_name}")
    
    # Load data
    df = load_clean_data(data_path)
    species_df = df[df['species'] == species_name].copy()
    
    if len(species_df) == 0:
        logger.warning(f"No data found for species: {species_name}")
        return None
    
    if len(species_df) < 10:
        logger.warning(f"Insufficient data for species: {species_name} ({len(species_df)} records)")
        return None
    
    # Generate random background
    background_df = generate_random_background(species_df, n_samples=n_background, seed=seed)
    
    # Create combined dataset with labels
    species_df['presence'] = 1
    background_df['presence'] = 0
    
    combined_df = pd.concat([species_df, background_df], ignore_index=True)
    
    # Shuffle
    if seed is not None:
        combined_df = combined_df.sample(frac=1, random_state=seed).reset_index(drop=True)
    
    y_true = combined_df['presence'].values
    n_samples = len(y_true)
    
    # Train null model
    model_params = train_bias_null_model(species_df, background_df, seed=seed)
    
    # Predict
    y_pred_proba = predict_bias_null(model_params, n_samples)
    
    # Calculate metrics
    metrics = calculate_metrics(y_true, y_pred_proba)
    
    result = {
        'species': species_name,
        'algorithm': 'bias_null_random',
        'auc': metrics['auc'],
        'tss': metrics['tss'],
        'threshold': metrics['threshold'],
        'prevalence': model_params['prevalence'],
        'n_presence': model_params['n_presence'],
        'n_background': model_params['n_background'],
        'timestamp': datetime.now().isoformat()
    }
    
    logger.info(f"Completed bias-only null model for {species_name}: AUC={result['auc']:.4f}, TSS={result['tss']:.4f}")
    
    return result

def save_metrics(results, output_path):
    """
    Save model metrics to CSV.
    
    Args:
        results: List of result dictionaries
        output_path: Path to output CSV file
    """
    logger = get_bias_null_logger()
    
    if not results:
        logger.warning("No results to save")
        return
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Write to CSV
    with open(output_path, 'w', newline='') as f:
        fieldnames = ['species', 'algorithm', 'auc', 'tss']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for result in results:
            writer.writerow({
                'species': result['species'],
                'algorithm': result['algorithm'],
                'auc': result['auc'],
                'tss': result['tss']
            })
    
    logger.info(f"Saved metrics to {output_path}")

def main():
    """Main function to run bias-only null model for all species."""
    logger = get_bias_null_logger()
    logger.info("Starting bias-only null model training")
    
    # Configuration
    data_path = os.path.join(config.DATA_DIR, 'processed', 'occurrence_clean.csv')
    output_path = os.path.join(config.METRICS_DIR, 'bias_null_metrics.csv')
    n_background = 10000
    seed = config.RND_SEED
    
    # Load all data
    try:
        df = load_clean_data(data_path)
    except FileNotFoundError as e:
        logger.error(f"Cannot proceed: {e}")
        sys.exit(1)
    
    # Get unique species
    species_list = df['species'].unique()
    logger.info(f"Found {len(species_list)} species to process")
    
    results = []
    
    for species in species_list:
        result = run_bias_null_model(species, data_path, n_background=n_background, seed=seed)
        if result:
            results.append(result)
    
    # Save results
    if results:
        save_metrics(results, output_path)
        logger.info(f"Successfully processed {len(results)} species")
    else:
        logger.warning("No species were successfully processed")
        sys.exit(1)
    
    logger.info("Bias-only null model training completed")

if __name__ == "__main__":
    main()
