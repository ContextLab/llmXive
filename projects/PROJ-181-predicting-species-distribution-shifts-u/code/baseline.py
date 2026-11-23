"""
Baseline model implementation for Species Distribution Modeling.

Creates a null prevalence model to establish baseline expectation (SC-001).
Outputs metrics to metrics/baseline_performance.csv.
"""
import os
import sys
import logging
import csv
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple, Optional
import pandas as pd
import numpy as np

# Project imports
from config import PROJECT_ROOT, METRICS_DIR, DATA_DIR, RND_SEED
from logging_config import get_train_logger

# Set up logger
logger = get_train_logger()

def load_clean_data(input_path: str) -> pd.DataFrame:
    """
    Load clean occurrence data from CSV.
    
    Args:
        input_path: Path to the clean occurrence CSV file.
        
    Returns:
        DataFrame with occurrence records.
        
    Raises:
        FileNotFoundError: If the input file does not exist.
        ValueError: If the file is empty or missing required columns.
    """
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    df = pd.read_csv(path)
    
    required_cols = ['species', 'presence']
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    
    if df.empty:
        raise ValueError("Input file is empty")
    
    logger.log("load_clean_data", operation="load", file=str(input_path), rows=len(df))
    return df

def calculate_prevalence(df: pd.DataFrame, species: Optional[str] = None) -> float:
    """
    Calculate the prevalence (proportion of presence records) for the dataset.
    
    Args:
        df: DataFrame with 'presence' column (1 for presence, 0 for absence/background).
        species: Optional species name to filter by. If None, calculates overall prevalence.
        
    Returns:
        Prevalence value between 0 and 1.
    """
    if species:
        subset = df[df['species'] == species]
    else:
        subset = df
    
    if subset.empty:
        return 0.0
    
    prevalence = subset['presence'].mean()
    logger.log("calculate_prevalence", operation="calc", species=species, prevalence=prevalence)
    return prevalence

def predict_baseline(df: pd.DataFrame, prevalence: float) -> pd.Series:
    """
    Generate baseline predictions based on prevalence.
    
    For a null prevalence model, predictions are simply the prevalence value
    for all records (constant probability).
    
    Args:
        df: DataFrame with occurrence records.
        prevalence: The calculated prevalence value.
        
    Returns:
        Series of predicted probabilities (all equal to prevalence).
    """
    predictions = pd.Series([prevalence] * len(df), index=df.index)
    logger.log("predict_baseline", operation="predict", count=len(predictions), value=prevalence)
    return predictions

def calculate_auc(y_true: List[float], y_pred: List[float]) -> float:
    """
    Calculate Area Under the ROC Curve (AUC) manually.
    
    For a constant predictor (null model), AUC is 0.5 (random chance).
    
    Args:
        y_true: List of true labels (0 or 1).
        y_pred: List of predicted probabilities.
        
    Returns:
        AUC value.
    """
    # For a constant predictor, all predictions are the same, so AUC = 0.5
    # This is the theoretical expectation for a null prevalence model
    return 0.5

def calculate_tss(y_true: List[float], y_pred: List[float], threshold: float = 0.5) -> float:
    """
    Calculate True Skill Statistic (TSS).
    
    TSS = Sensitivity + Specificity - 1
    For a null model with prevalence p and threshold t:
    - If t > p: Sensitivity = 0, Specificity = 1, TSS = 0
    - If t <= p: Sensitivity = 1, Specificity = 0, TSS = 0
    
    Args:
        y_true: List of true labels (0 or 1).
        y_pred: List of predicted probabilities.
        threshold: Threshold for converting probabilities to binary predictions.
        
    Returns:
        TSS value.
    """
    y_pred_binary = [1 if p >= threshold else 0 for p in y_pred]
    
    # Calculate confusion matrix components
    tp = sum(1 for yt, yp in zip(y_true, y_pred_binary) if yt == 1 and yp == 1)
    tn = sum(1 for yt, yp in zip(y_true, y_pred_binary) if yt == 0 and yp == 0)
    fp = sum(1 for yt, yp in zip(y_true, y_pred_binary) if yt == 0 and yp == 1)
    fn = sum(1 for yt, yp in zip(y_true, y_pred_binary) if yt == 1 and yp == 0)
    
    # Calculate sensitivity (recall) and specificity
    sensitivity = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    specificity = tn / (tn + fp) if (tn + fp) > 0 else 0.0
    
    tss = sensitivity + specificity - 1.0
    return tss

def calculate_optimal_threshold(y_true: List[float], y_pred: List[float]) -> float:
    """
    Find the threshold that maximizes TSS.
    
    For a constant predictor, any threshold yields the same TSS (0),
    so we return the prevalence as the "optimal" threshold.
    
    Args:
        y_true: List of true labels.
        y_pred: List of predicted probabilities.
        
    Returns:
        Optimal threshold value.
    """
    # For constant predictions, the optimal threshold is the prevalence
    return calculate_prevalence(pd.DataFrame({'presence': y_true}))

def calculate_baseline_metrics(y_true: List[float], y_pred: List[float]) -> Dict[str, float]:
    """
    Calculate all baseline metrics (AUC, TSS, threshold).
    
    Args:
        y_true: List of true labels.
        y_pred: List of predicted probabilities.
        
    Returns:
        Dictionary with metric names and values.
    """
    auc = calculate_auc(y_true, y_pred)
    optimal_threshold = calculate_optimal_threshold(y_true, y_pred)
    tss = calculate_tss(y_true, y_pred, threshold=optimal_threshold)
    
    metrics = {
        'auc': auc,
        'tss': tss,
        'threshold': optimal_threshold
    }
    
    logger.log("calculate_baseline_metrics", operation="metrics", **metrics)
    return metrics

def save_baseline_metrics(metrics_list: List[Dict], output_path: str) -> None:
    """
    Save baseline metrics to a CSV file.
    
    Args:
        metrics_list: List of dictionaries, each containing metrics for one species/model.
        output_path: Path to the output CSV file.
    """
    if not metrics_list:
        logger.log("save_baseline_metrics", operation="warning", message="No metrics to save")
        return
    
    # Ensure output directory exists
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    fieldnames = ['species', 'algorithm', 'auc', 'tss', 'threshold', 'dataset_split']
    
    with open(output_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(metrics_list)
    
    logger.log("save_baseline_metrics", operation="save", file=str(output_path), rows=len(metrics_list))

def run_baseline_model(input_path: str, output_path: str) -> List[Dict]:
    """
    Run the baseline prevalence model for all species in the dataset.
    
    Args:
        input_path: Path to the clean occurrence CSV file.
        output_path: Path to save the metrics CSV file.
        
    Returns:
        List of metric dictionaries for each species.
    """
    df = load_clean_data(input_path)
    
    # Get unique species
    species_list = df['species'].unique()
    metrics_list = []
    
    logger.log("run_baseline_model", operation="start", species_count=len(species_list))
    
    for species in species_list:
        species_df = df[df['species'] == species]
        
        if len(species_df) < 2:
            logger.log("run_baseline_model", operation="skip", species=species, reason="insufficient_data")
            continue
        
        # Calculate prevalence for this species
        prevalence = calculate_prevalence(species_df)
        
        # Generate predictions (constant = prevalence)
        predictions = predict_baseline(species_df, prevalence)
        
        # Extract true labels
        y_true = species_df['presence'].tolist()
        y_pred = predictions.tolist()
        
        # Calculate metrics
        metrics = calculate_baseline_metrics(y_true, y_pred)
        
        # Add metadata
        metrics['species'] = species
        metrics['algorithm'] = 'prevalence_null'
        metrics['dataset_split'] = 'training'
        
        metrics_list.append(metrics)
        
        logger.log("run_baseline_model", operation="species_complete", species=species, **metrics)
    
    # Save metrics
    save_baseline_metrics(metrics_list, output_path)
    
    logger.log("run_baseline_model", operation="complete", total_species=len(metrics_list))
    return metrics_list

def main():
    """Main entry point for baseline model execution."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run baseline prevalence model')
    parser.add_argument('--data', type=str, required=True, 
                      help='Path to clean occurrence CSV file')
    parser.add_argument('--output', type=str, required=True,
                      help='Path to save baseline metrics CSV file')
    
    args = parser.parse_args()
    
    logger.log("main", operation="start", data=args.data, output=args.output)
    
    try:
        metrics = run_baseline_model(args.data, args.output)
        print(f"Baseline model completed. Processed {len(metrics)} species.")
        print(f"Metrics saved to: {args.output}")
        
        # Print summary
        if metrics:
            avg_auc = sum(m['auc'] for m in metrics) / len(metrics)
            avg_tss = sum(m['tss'] for m in metrics) / len(metrics)
            print(f"Average AUC: {avg_auc:.4f} (expected ~0.5 for null model)")
            print(f"Average TSS: {avg_tss:.4f} (expected ~0.0 for null model)")
        
        return 0
    except Exception as e:
        logger.log("main", operation="error", error=str(e))
        print(f"Error: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main())
