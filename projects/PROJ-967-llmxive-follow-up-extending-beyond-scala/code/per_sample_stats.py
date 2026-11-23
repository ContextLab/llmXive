"""
Task T025a: Compute Per-Sample Stats and Global Dominant Eigenvalue.

Reads aligned data (raw and cleaned), computes per-sample statistical descriptors
(variance, entropy, skewness, kurtosis), conditionally adds Mahalanobis distance
if Random Forest is selected, and outputs a JSON record containing all features
plus the global dominant eigenvalue.
"""
import argparse
import json
import logging
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

# Import shared utilities from existing project modules
from entanglement_scores import calculate_entropy
from mahalanobis_distance import load_model_selection, load_covariance_matrix, load_global_mean, calculate_mahalanobis_distance as calc_mahalanobis

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)

def setup_directories(base_path):
    """Ensure output directories exist."""
    processed_dir = base_path / 'data' / 'processed'
    results_dir = base_path / 'results'
    processed_dir.mkdir(parents=True, exist_ok=True)
    results_dir.mkdir(parents=True, exist_ok=True)
    return processed_dir, results_dir

def load_raw_dataset(logger, base_path):
    """Load the full aligned dataset from T012."""
    raw_path = base_path / 'data' / 'processed' / 'raw_data.parquet'
    if not raw_path.exists():
        raise FileNotFoundError(f"Raw data file not found at {raw_path}. Run T012 first.")
    logger.info(f"Loading raw data from {raw_path}")
    return pd.read_parquet(raw_path)

def load_cleaned_data(logger, base_path):
    """Load the filtered dataset from T024."""
    cleaned_path = base_path / 'data' / 'processed' / 'cleaned_data.parquet'
    if not cleaned_path.exists():
        raise FileNotFoundError(f"Cleaned data file not found at {cleaned_path}. Run T024 first.")
    logger.info(f"Loading cleaned data from {cleaned_path}")
    return pd.read_parquet(cleaned_path)

def load_dominant_eigenvalue(logger, base_path):
    """Load the dominant eigenvalue computed in T022b-eigen."""
    eigen_path = base_path / 'results' / 'dominant_eigenvalue.json'
    if not eigen_path.exists():
        raise FileNotFoundError(f"Dominant eigenvalue file not found at {eigen_path}. Run T022b-eigen first.")
    with open(eigen_path, 'r') as f:
        data = json.load(f)
    return data.get('dominant_eigenvalue')

def compute_per_sample_stats(df, logger):
    """
    Compute per-sample variance, entropy, skewness, kurtosis for teacher scores.
    
    Teacher scores are expected in columns: 'Alignment', 'Realism', 'Aesthetics', 'Plausibility'.
    """
    dimensions = ['Alignment', 'Realism', 'Aesthetics', 'Plausibility']
    
    # Ensure all dimension columns exist
    missing_dims = [d for d in dimensions if d not in df.columns]
    if missing_dims:
        raise ValueError(f"Missing teacher score dimensions in dataset: {missing_dims}")
    
    results = []
    
    for idx, row in df.iterrows():
        scores = np.array([row[d] for d in dimensions], dtype=float)
        
        # Variance
        var = np.var(scores, ddof=0) # Population variance for consistency with entanglement logic
        
        # Entropy (Shannon)
        # Normalize to probability distribution
        # Handle zero values by adding small epsilon if necessary, but per spec: 
        # "Handle zero-variance cases (set variance = 0, entropy = 0)"
        if var == 0 or np.all(scores == scores[0]):
            entropy = 0.0
        else:
            # Normalize to sum to 1.0. Ensure non-negative for log.
            # If scores can be negative, we might need to shift, but typically 
            # scores are in a range. Assuming positive or shifted to positive.
            # If scores are raw logits, they might be negative. 
            # For entropy of a distribution, we need p_i >= 0 and sum(p_i)=1.
            # If scores are not probabilities, we treat them as weights.
            weights = np.abs(scores) # Absolute value to ensure non-negative for entropy calc
            if np.sum(weights) == 0:
                entropy = 0.0
            else:
                probs = weights / np.sum(weights)
                entropy = calculate_entropy(probs)
        
        # Skewness and Kurtosis
        # Use scipy.stats for robust calculation
        # Handle constant arrays (variance 0)
        if var == 0:
            skewness = 0.0
            kurtosis = 0.0 # Excess kurtosis for constant is undefined, set to 0
        else:
            skewness = stats.skew(scores, bias=False)
            kurtosis = stats.kurtosis(scores, bias=False) # Fisher's definition (excess)
        
        results.append({
            'sample_id': row.get('sample_id', idx),
            'variance': float(var),
            'entropy': float(entropy),
            'skewness': float(skewness),
            'kurtosis': float(kurtosis)
        })
    
    return pd.DataFrame(results)

def integrate_features(base_path, logger):
    """
    Main orchestration for T025a.
    1. Load raw and cleaned data.
    2. Compute per-sample stats.
    3. Conditionally compute Mahalanobis distance.
    4. Load dominant eigenvalue.
    5. Output JSON record.
    """
    processed_dir, results_dir = setup_directories(base_path)
    
    # Load Data
    df_raw = load_raw_dataset(logger, base_path)
    df_cleaned = load_cleaned_data(logger, base_path)
    
    # Compute Per-Sample Stats on the cleaned data (as per T025a description: "Read ... filtered dataset")
    # Note: T022a ran on raw, but T025a specifically says "Read ... filtered dataset" and "Compute per-sample stats".
    # We will compute stats on the cleaned data to ensure we only have valid samples.
    stats_df = compute_per_sample_stats(df_cleaned, logger)
    
    # Check Model Selection for Mahalanobis
    model_type = "unknown"
    model_selection_path = base_path / 'data' / 'processed' / 'model_selection.json'
    if model_selection_path.exists():
        with open(model_selection_path, 'r') as f:
            model_data = json.load(f)
            model_type = model_data.get('model_type', 'unknown')
    
    mahalanobis_values = None
    if model_type == 'rf':
        logger.info("Model type is Random Forest. Computing Mahalanobis Distance.")
        # Load required global stats
        cov_matrix = load_covariance_matrix(logger, base_path)
        global_mean = load_global_mean(logger, base_path)
        
        # Calculate Mahalanobis for the cleaned data
        # We need to extract the teacher scores matrix from the cleaned data
        dimensions = ['Alignment', 'Realism', 'Aesthetics', 'Plausibility']
        X = df_cleaned[dimensions].values
        
        mahalanobis_values = []
        for i in range(len(X)):
            md = calculate_mahalanobis(X[i], global_mean, cov_matrix)
            mahalanobis_values.append(md)
        
        stats_df['mahalanobis_distance'] = mahalanobis_values
    else:
        logger.info(f"Model type is {model_type}. Skipping Mahalanobis Distance.")
        # Add null or skip column? T025a says "Ensure no null values for required keys".
        # If Mahalanobis is conditional, we might not include it or include a sentinel.
        # The spec says: "Output a JSON record containing all per-sample features plus the global dominant_eigenvalue."
        # If Mahalanobis is skipped, we don't include it in the per-sample features for this run.
        pass
    
    # Load Global Dominant Eigenvalue
    dominant_eigenvalue = load_dominant_eigenvalue(logger, base_path)
    
    # Prepare Output
    # Create a list of records
    output_records = []
    for _, row in stats_df.iterrows():
        record = {
            'sample_id': row['sample_id'],
            'variance': row['variance'],
            'entropy': row['entropy'],
            'skewness': row['skewness'],
            'kurtosis': row['kurtosis'],
            'dominant_eigenvalue': dominant_eigenvalue
        }
        if 'mahalanobis_distance' in row:
            record['mahalanobis_distance'] = row['mahalanobis_distance']
        
        # Ensure no nulls for required keys
        for key in ['sample_id', 'variance', 'entropy', 'skewness', 'kurtosis', 'dominant_eigenvalue']:
            if record[key] is None:
                logger.warning(f"Null value found for {key} in sample {record['sample_id']}. Setting to 0.0.")
                record[key] = 0.0
        
        output_records.append(record)
    
    # Write Output
    output_path = processed_dir / 'per_sample_stats.json'
    with open(output_path, 'w') as f:
        json.dump(output_records, f, indent=2)
    
    logger.info(f"Successfully wrote per-sample stats to {output_path}")
    return output_path

def parse_args():
    parser = argparse.ArgumentParser(description="Task T025a: Compute Per-Sample Stats")
    parser.add_argument('--base-path', type=str, default='projects/PROJ-967-llmxive-follow-up-extending-beyond-scala',
                        help='Base path of the project')
    return parser.parse_args()

def main():
    args = parse_args()
    logger = setup_logging()
    base_path = Path(args.base_path)
    
    try:
        integrate_features(base_path, logger)
        logger.info("T025a completed successfully.")
    except Exception as e:
        logger.error(f"Task T025a failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
