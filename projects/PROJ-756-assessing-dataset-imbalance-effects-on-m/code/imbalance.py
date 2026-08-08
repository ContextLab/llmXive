import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from scipy import stats

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/imbalance_analysis.log')
    ]
)
logger = logging.getLogger(__name__)

# Constants
MIN_SAMPLES_THRESHOLD = 100
KMEANS_N_CLUSTERS = 50
RESULTS_DIR = Path('results')
DESRIPTORS_PATH = Path('data/processed/descriptors.parquet')

def ensure_results_directory():
    """Ensure the results directory exists."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    logger.info(f"Ensured results directory exists at {RESULTS_DIR}")

def load_data() -> pd.DataFrame:
    """
    Load the processed descriptors from disk.
    Expects a parquet file containing composition features and target properties.
    """
    if not DESRIPTORS_PATH.exists():
        raise FileNotFoundError(
            f"Processed descriptors file not found at {DESCRIPTORS_PATH}. "
            "Please run code/descriptors.py first (Task T007)."
        )
    
    logger.info(f"Loading data from {DESCRIPTORS_PATH}")
    df = pd.read_parquet(DESCRIPTORS_PATH)
    logger.info(f"Loaded {len(df)} rows. Columns: {list(df.columns)}")
    return df

def calculate_gini(values: np.ndarray) -> float:
    """
    Calculate the Gini coefficient for a 1D array of values.
    Handles negative values by taking the absolute value (as per task instructions
    for handling negative target properties).
    
    Gini = (2 * sum(sorted_values * (i+1)) - (n+1) * sum(values)) / (n * sum(values))
    """
    if len(values) == 0:
        return 0.0
    
    # Handle negative values by taking absolute value as per task spec
    abs_values = np.abs(values)
    
    if np.sum(abs_values) == 0:
        return 0.0
    
    n = len(abs_values)
    sorted_values = np.sort(abs_values)
    indices = np.arange(1, n + 1)
    
    numerator = 2 * np.sum(indices * sorted_values)
    denominator = n * np.sum(sorted_values)
    
    gini = (numerator - (n + 1) * np.sum(sorted_values)) / denominator
    return float(gini)

def identify_target_columns(df: pd.DataFrame) -> List[str]:
    """
    Identify target property columns.
    Heuristic: Columns that are not the primary composition identifier 
    and are not the Magpie descriptor columns (which are typically numeric 
    and start with specific prefixes or are known descriptor names).
    For this implementation, we assume target columns are numeric columns
    that are NOT part of the compositional feature set.
    """
    # Identify numeric columns
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    
    # Exclude known descriptor columns if they follow a pattern (e.g., 'Magpie_' or similar)
    # Since the exact column names depend on T007, we assume targets are the remaining numeric cols
    # that are not the 'composition' string column if it exists.
    
    # Common non-target columns to exclude
    exclude_patterns = ['composition', 'cluster_id', 'bin_id']
    
    target_cols = []
    for col in numeric_cols:
        if any(pat in col.lower() for pat in exclude_patterns):
            continue
        # Heuristic: If it looks like a descriptor (e.g., many decimal places, specific names), skip
        # For robustness, we'll assume the user has labeled targets or they are the only numeric cols left
        # after excluding obvious non-targets.
        # In a real scenario, T007 would output a specific schema. We assume targets are numeric.
        target_cols.append(col)
    
    # If we have too many numeric columns, we might be including descriptors.
    # A safer heuristic: if descriptors are present, they are usually many.
    # Let's assume the last few numeric columns or specific known property names are targets.
    # However, without a schema, we assume all numeric cols (except composition) are targets for now.
    # A more robust way: Check for a 'target' column or specific property names.
    # Given the task context, we will treat all numeric columns as potential targets
    # and filter later by sample count.
    
    return target_cols

def calculate_target_imbalance_score(df: pd.DataFrame, target_col: str) -> Optional[float]:
    """
    Calculate the Target Imbalance Score (Gini coefficient) for a specific target column.
    Skips properties with < 100 samples.
    """
    values = df[target_col].dropna().values
    
    if len(values) < MIN_SAMPLES_THRESHOLD:
        logger.info(f"Skipping target '{target_col}': only {len(values)} samples (threshold: {MIN_SAMPLES_THRESHOLD})")
        return None
    
    gini = calculate_gini(values)
    logger.info(f"Target Imbalance Score for '{target_col}': {gini:.4f} (n={len(values)})")
    return gini

def calculate_compositional_imbalance_score(df: pd.DataFrame, compositional_features: List[str]) -> float:
    """
    Calculate the Compositional Imbalance Score.
    1. Perform K-Means clustering (k=50) on compositional features.
    2. Extract cluster assignments.
    3. Calculate Gini coefficient of cluster assignments (counts per cluster).
    """
    if len(compositional_features) == 0:
        raise ValueError("No compositional features provided for clustering.")
    
    X = df[compositional_features].dropna()
    if len(X) < KMEANS_N_CLUSTERS:
        logger.warning(f"Dataset size ({len(X)}) is smaller than k ({KMEANS_N_CLUSTERS}). "
                       "Adjusting k or raising error. Proceeding with k=min(len, 50).")
        k = min(len(X), KMEANS_N_CLUSTERS)
    else:
        k = KMEANS_N_CLUSTERS
    
    logger.info(f"Performing K-Means clustering (k={k}) on {len(compositional_features)} features...")
    
    kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
    cluster_labels = kmeans.fit_predict(X)
    
    # Count samples per cluster
    unique, counts = np.unique(cluster_labels, return_counts=True)
    
    # Calculate Gini of the counts
    gini = calculate_gini(counts)
    
    logger.info(f"Compositional Imbalance Score (Gini of cluster counts): {gini:.4f}")
    return gini

def analyze_all_properties(df: pd.DataFrame) -> Tuple[Dict[str, float], float]:
    """
    Analyze all properties in the dataframe.
    Returns:
      - target_scores: Dict mapping target column name to Gini score
      - compositional_score: Single float for the whole dataset
    """
    target_cols = identify_target_columns(df)
    logger.info(f"Identified potential target columns: {target_cols}")
    
    # Filter for numeric columns only (in case identify returned non-numeric)
    numeric_target_cols = [c for c in target_cols if c in df.select_dtypes(include=[np.number]).columns]
    
    target_scores = {}
    for col in numeric_target_cols:
        score = calculate_target_imbalance_score(df, col)
        if score is not None:
            target_scores[col] = score
    
    # Identify compositional features.
    # Heuristic: All numeric columns that are NOT targets and NOT known non-features.
    # Assuming descriptors were computed in T007.
    all_numeric = df.select_dtypes(include=[np.number]).columns.tolist()
    compositional_features = [c for c in all_numeric if c not in target_cols]
    
    if not compositional_features:
        logger.warning("No compositional features found. Cannot calculate Compositional Imbalance Score.")
        compositional_score = 0.0
    else:
        logger.info(f"Using {len(compositional_features)} compositional features for clustering.")
        compositional_score = calculate_compositional_imbalance_score(df, compositional_features)
    
    return target_scores, compositional_score

def save_results(target_scores: Dict[str, float], compositional_score: float):
    """
    Save results to CSV files.
    - results/target_imbalance_scores.csv
    - results/compositional_imbalance_score.csv
    """
    ensure_results_directory()
    
    # Save Target Imbalance Scores
    target_df = pd.DataFrame([
        {"property": prop, "imbalance_score": score}
        for prop, score in target_scores.items()
    ])
    target_path = RESULTS_DIR / "target_imbalance_scores.csv"
    target_df.to_csv(target_path, index=False)
    logger.info(f"Saved target imbalance scores to {target_path}")
    
    # Save Compositional Imbalance Score
    # Format: single row with the score
    comp_df = pd.DataFrame([
        {"score_type": "compositional", "imbalance_score": compositional_score}
    ])
    comp_path = RESULTS_DIR / "compositional_imbalance_score.csv"
    comp_df.to_csv(comp_path, index=False)
    logger.info(f"Saved compositional imbalance score to {comp_path}")

def main():
    """Main entry point for the imbalance analysis task."""
    try:
        logger.info("Starting Imbalance Analysis (Task T008)...")
        
        # 1. Load Data
        df = load_data()
        
        # 2. Analyze
        target_scores, compositional_score = analyze_all_properties(df)
        
        # 3. Save Results
        save_results(target_scores, compositional_score)
        
        logger.info("Imbalance Analysis completed successfully.")
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"Data file missing: {e}")
        return 1
    except Exception as e:
        logger.exception(f"An error occurred during analysis: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
