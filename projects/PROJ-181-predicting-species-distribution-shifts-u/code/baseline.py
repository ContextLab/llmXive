"""
Baseline model implementation for Species Distribution Modeling.

This module implements a null prevalence model (SC-001) that predicts
species occurrence based solely on the overall prevalence rate in the
training data. This serves as a baseline expectation for model comparison.
"""

import os
import sys
import logging
import csv
import json
from pathlib import Path
from datetime import datetime

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config import DATA_DIR, METRICS_DIR, RND_SEED
from logging_config import get_train_logger

# Initialize logger
logger = get_train_logger(__name__)

def load_clean_data():
    """
    Load the cleaned occurrence data from the processed CSV.
    
    Returns:
        list: List of dictionaries containing occurrence records with climate variables.
    """
    input_path = DATA_DIR / "processed" / "occurrence_clean.csv"
    
    if not input_path.exists():
        logger.error(f"Clean data file not found: {input_path}")
        raise FileNotFoundError(f"Clean data file not found: {input_path}")
    
    records = []
    with open(input_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Convert numeric fields
            try:
                row['presence'] = 1  # All records in occurrence data are presences
                records.append(row)
            except (ValueError, KeyError) as e:
                logger.warning(f"Skipping malformed record: {e}")
                continue
    
    logger.info(f"Loaded {len(records)} records from {input_path}")
    return records

def calculate_prevalence(records):
    """
    Calculate the prevalence rate (proportion of presences) in the dataset.
    
    Args:
        records (list): List of occurrence records.
        
    Returns:
        float: Prevalence rate (0.0 to 1.0).
    """
    if not records:
        return 0.0
    
    # In occurrence-only data, all records are presences
    # Prevalence is calculated relative to the total area sampled
    # For baseline, we use the observed prevalence in the dataset
    total_records = len(records)
    presence_count = sum(1 for r in records if r.get('presence', 0) == 1)
    
    prevalence = presence_count / total_records if total_records > 0 else 0.0
    logger.info(f"Calculated prevalence: {prevalence:.4f} ({presence_count}/{total_records})")
    
    return prevalence

def predict_baseline(records, prevalence):
    """
    Generate baseline predictions using the prevalence rate.
    
    The null model predicts the same probability (prevalence) for all locations.
    
    Args:
        records (list): List of occurrence records.
        prevalence (float): The calculated prevalence rate.
        
    Returns:
        list: List of dictionaries with species, predicted probability, and actual label.
    """
    predictions = []
    for record in records:
        predictions.append({
            'species': record.get('species', 'unknown'),
            'predicted_probability': prevalence,
            'actual_presence': record.get('presence', 1)
        })
    
    return predictions

def calculate_baseline_metrics(predictions):
    """
    Calculate performance metrics for the baseline model.
    
    Args:
        predictions (list): List of prediction dictionaries.
        
    Returns:
        dict: Metrics including AUC, TSS, and threshold.
    """
    if not predictions:
        return {
            'species': 'unknown',
            'algorithm': 'null_prevalence',
            'auc': 0.5,
            'tss': 0.0,
            'threshold': 0.5
        }
    
    # Extract actual and predicted values
    actuals = [p['actual_presence'] for p in predictions]
    predicted_probs = [p['predicted_probability'] for p in predictions]
    
    # For baseline model:
    # - AUC is typically around 0.5 (random performance)
    # - TSS is 0.0 (no improvement over random)
    # - Threshold is set to the prevalence rate
    
    # Calculate AUC using trapezoidal rule
    # Since all predictions are the same, AUC = 0.5
    auc = 0.5
    
    # Calculate TSS
    # TSS = Sensitivity + Specificity - 1
    # For baseline: Sensitivity = 1.0 (all presences predicted as positive if threshold <= prevalence)
    #               Specificity = 0.0 (all absences predicted as positive)
    #               TSS = 1.0 + 0.0 - 1.0 = 0.0
    tss = 0.0
    
    # Threshold is set to prevalence
    threshold = predictions[0]['predicted_probability'] if predictions else 0.5
    
    metrics = {
        'species': predictions[0]['species'] if predictions else 'unknown',
        'algorithm': 'null_prevalence',
        'auc': auc,
        'tss': tss,
        'threshold': threshold
    }
    
    logger.info(f"Baseline metrics: AUC={auc:.4f}, TSS={tss:.4f}, Threshold={threshold:.4f}")
    
    return metrics

def save_baseline_metrics(metrics, output_path):
    """
    Save baseline model metrics to a CSV file.
    
    Args:
        metrics (dict): Dictionary containing model metrics.
        output_path (Path): Path to the output CSV file.
    """
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Check if file exists to determine if we need headers
    file_exists = output_path.exists()
    
    with open(output_path, 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['species', 'algorithm', 'auc', 'tss', 'threshold'])
        
        if not file_exists:
            writer.writeheader()
        
        writer.writerow(metrics)
    
    logger.info(f"Saved baseline metrics to {output_path}")

def run_baseline_model():
    """
    Main function to run the baseline prevalence model.
    
    Returns:
        dict: Final metrics dictionary.
    """
    logger.info("Starting baseline model implementation")
    
    # Load clean data
    records = load_clean_data()
    
    if not records:
        logger.error("No records found in clean data")
        return None
    
    # Calculate prevalence
    prevalence = calculate_prevalence(records)
    
    # Generate predictions
    predictions = predict_baseline(records, prevalence)
    
    # Calculate metrics
    metrics = calculate_baseline_metrics(predictions)
    
    # Save metrics
    output_path = METRICS_DIR / "baseline_performance.csv"
    save_baseline_metrics(metrics, output_path)
    
    logger.info("Baseline model completed successfully")
    
    return metrics

def main():
    """Entry point for the baseline model script."""
    try:
        metrics = run_baseline_model()
        if metrics:
            print(json.dumps(metrics, indent=2))
            return 0
        else:
            logger.error("Failed to compute baseline metrics")
            return 1
    except Exception as e:
        logger.exception(f"Error in baseline model: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
