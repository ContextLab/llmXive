import os
import sys
import json
import argparse
from typing import Dict, List, Optional, Tuple, Any, Union
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler

# Project relative imports based on API surface
# Note: When running as a script, we need to ensure utils is on path
import_code_dir = os.path.dirname(os.path.abspath(__file__))
if os.path.basename(import_code_dir) == 'code':
    sys.path.insert(0, os.path.dirname(import_code_dir))

from utils.config import get_clustering_params, get_config
from utils.kinematics import extract_kinematic_features, normalize_joint_angles
from utils.seeds import set_global_seed

def load_and_prepare_data(data_path: str) -> pd.DataFrame:
    """
    Load pre-ingested data from parquet/CSV.
    Expects a DataFrame with 'text_instruction' and 'action' columns.
    """
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Data file not found: {data_path}")
    
    if data_path.endswith('.parquet'):
        df = pd.read_parquet(data_path)
    elif data_path.endswith('.csv'):
        df = pd.read_csv(data_path)
    else:
        raise ValueError(f"Unsupported file format: {data_path}")
    
    return df

def extract_kinematic_features_from_df(df: pd.DataFrame) -> pd.DataFrame:
    """
    Extract kinematic features (velocity, acceleration, joint angles) from action sequences.
    Adds columns: 'velocity', 'acceleration', 'joint_angle_stats' (flattened).
    """
    # Placeholder for actual kinematic extraction logic
    # In a real implementation, this would iterate over action sequences
    # and compute derivatives and statistics.
    # For now, we assume the data has 'action' as a list or string representation.
    
    # Mock extraction for structure demonstration if columns missing
    if 'velocity' not in df.columns:
        # Simulate extraction if not present (in real run, this computes from actions)
        # Assuming action is a list of joints or a string representation
        def calc_velocity(action):
            if isinstance(action, str):
                return 0.0
            elif isinstance(action, (list, np.ndarray)):
                if len(action) < 2: return 0.0
                return float(np.mean(np.diff(action)))
            return 0.0

        def calc_acceleration(action):
            if isinstance(action, str):
                return 0.0
            elif isinstance(action, (list, np.ndarray)):
                if len(action) < 3: return 0.0
                vel = np.diff(action)
                return float(np.mean(np.diff(vel)))
            return 0.0

        def calc_joint_stats(action):
            if isinstance(action, str):
                return 0.0
            elif isinstance(action, (list, np.ndarray)):
                return float(np.std(action))
            return 0.0

        df['velocity'] = df['action'].apply(calc_velocity)
        df['acceleration'] = df['action'].apply(calc_acceleration)
        df['joint_std'] = df['action'].apply(calc_joint_stats)
    else:
        # Ensure numeric
        df['velocity'] = pd.to_numeric(df['velocity'], errors='coerce').fillna(0)
        df['acceleration'] = pd.to_numeric(df['acceleration'], errors='coerce').fillna(0)
        if 'joint_std' not in df.columns:
            df['joint_std'] = 0.0

    return df

def normalize_features(df: pd.DataFrame) -> np.ndarray:
    """
    Normalize kinematic features to zero mean and unit variance.
    Returns a numpy array of normalized features.
    """
    feature_cols = ['velocity', 'acceleration', 'joint_std']
    missing_cols = [c for c in feature_cols if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required feature columns: {missing_cols}")
    
    X = df[feature_cols].values.astype(float)
    
    # Handle NaNs
    if np.any(np.isnan(X)):
        # Fill NaN with 0 or median? For clustering, 0 is safer if NaNs are sparse
        X = np.nan_to_num(X, nan=0.0)
    
    scaler = StandardScaler()
    X_normalized = scaler.fit_transform(X)
    
    return X_normalized

def run_clustering_pipeline(X: np.ndarray, k: int = 50) -> Tuple[np.ndarray, np.ndarray, Dict[str, Any]]:
    """
    Run K-means clustering on normalized features.
    Returns: labels, centers, stats_dict
    """
    if len(X) < k:
        k = max(1, len(X))
    
    kmeans = KMeans(n_clusters=k, random_state=42, n_init='auto')
    labels = kmeans.fit_predict(X)
    centers = kmeans.cluster_centers_
    
    # Calculate silhouette score
    if k > 1 and len(np.unique(labels)) > 1:
        score = silhouette_score(X, labels)
    else:
        score = -1.0 # Invalid for k=1 or single cluster
    
    stats = {
        "k": k,
        "silhouette_score": float(score),
        "cluster_counts": {int(i): int(np.sum(labels == i)) for i in range(k)}
    }
    
    return labels, centers, stats

def run_clustering_with_validation(df: pd.DataFrame, output_dir: str) -> Dict[str, Any]:
    """
    Main entry point for T016: Clustering with adaptive validation.
    
    Logic:
    1. Extract and normalize features.
    2. Load clustering params from config (k_start, threshold, step, max_attempts).
    3. Iterate:
       - Run K-means.
       - Calculate silhouette score.
       - If score >= threshold, break and save.
       - If score < threshold, reduce k by step.
       - If k <= 1, stop and warn.
    4. Return final stats.
    """
    # 1. Prepare Data
    df_features = extract_kinematic_features_from_df(df)
    X = normalize_features(df_features)
    
    # 2. Load Config
    params = get_clustering_params()
    k_current = params.get("max_k", 50)
    threshold = params.get("silhouette_threshold", 0.25)
    step = params.get("k_decrement_step", 5)
    max_attempts = params.get("max_attempts", 10)
    
    print(f"Starting clustering validation. Max K: {k_current}, Threshold: {threshold}")
    
    best_k = k_current
    best_score = -1.0
    best_labels = None
    best_centers = None
    final_stats = {}
    
    attempts = 0
    while attempts < max_attempts and k_current > 1:
        print(f"Attempt {attempts + 1}: Trying k={k_current}...")
        
        labels, centers, stats = run_clustering_pipeline(X, k_current)
        score = stats["silhouette_score"]
        
        print(f"  Silhouette Score: {score:.4f}")
        
        if score >= threshold:
            print(f"  Success! Score {score:.4f} >= {threshold}")
            best_k = k_current
            best_score = score
            best_labels = labels
            best_centers = centers
            final_stats = stats
            break
        else:
            # Score too low, reduce k
            k_current = max(1, k_current - step)
            attempts += 1
            # Keep best so far if this is better than previous best, even if < threshold
            if score > best_score:
                best_score = score
                best_k = k_current # provisional
                best_labels = labels
                best_centers = centers
                final_stats = stats

    if best_labels is None and len(X) > 0:
        # Fallback to k=1 if nothing else worked
        print("Falling back to k=1 as no valid clustering found.")
        best_k = 1
        best_labels, best_centers, final_stats = run_clustering_pipeline(X, 1)
        best_score = final_stats["silhouette_score"]
        if best_score == -1.0:
            final_stats["silhouette_score"] = 0.0 # Treat k=1 as 0 or specific flag
            print("  Warning: k=1 yields undefined silhouette score.")

    if best_score < threshold:
        print(f"Warning: Final silhouette score {best_score:.4f} is below threshold {threshold}.")
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Save artifacts (T017 responsibility, but we prepare data here)
    # We return the data needed for T017 to write files
    result = {
        "labels": best_labels,
        "centers": best_centers,
        "stats": final_stats,
        "config_used": params
    }
    
    return result

def main():
    parser = argparse.ArgumentParser(description="Run Clustering with Validation (T016)")
    parser.add_argument("--input", type=str, required=True, help="Path to ingested data (parquet/csv)")
    parser.add_argument("--output", type=str, required=True, help="Output directory for artifacts")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    
    args = parser.parse_args()
    
    set_global_seed(args.seed)
    
    if not os.path.exists(args.input):
        raise FileNotFoundError(f"Input file not found: {args.input}")
    
    print(f"Loading data from {args.input}...")
    df = load_and_prepare_data(args.input)
    print(f"Loaded {len(df)} samples.")
    
    print("Running clustering validation pipeline...")
    result = run_clustering_with_validation(df, args.output)
    
    print(f"Clustering complete. Final K: {result['stats']['k']}, Score: {result['stats']['silhouette_score']:.4f}")
    
    # Save temporary intermediate results if needed, 
    # but T017 will handle the final JSON/Parquet serialization.
    # We just ensure the logic is executed.
    
    return result

if __name__ == "__main__":
    main()
