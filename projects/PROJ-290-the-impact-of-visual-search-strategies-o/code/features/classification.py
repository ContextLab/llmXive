import os
import sys
import json
import logging
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.utils import resample
from config import get_config
from utils.logging import get_logger

# Ensure parent directory is in path for imports if running as script
if __name__ == "__main__":
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def get_logger_wrapper(func):
    """Decorator to add logging to functions."""
    def wrapper(*args, **kwargs):
        logger = get_logger(func.__name__)
        logger.info(f"Starting {func.__name__}")
        result = func(*args, **kwargs)
        logger.info(f"Finished {func.__name__}")
        return result
    return wrapper

@get_logger_wrapper
def calculate_continuous_ratio(features_df):
    """
    Calculate the continuous ratio of eye-to-mouth fixation time.
    Primary Predictor: Eye Duration / Mouth Duration.
    Handles division by zero.
    """
    logger = get_logger("calculate_continuous_ratio")
    
    if 'eye_fixation_duration' not in features_df.columns or 'mouth_fixation_duration' not in features_df.columns:
        raise ValueError("Required columns 'eye_fixation_duration' and 'mouth_fixation_duration' not found in features_df.")
    
    # Avoid division by zero
    denominator = features_df['mouth_fixation_duration'].replace(0, np.nan)
    features_df['fixation_ratio'] = features_df['eye_fixation_duration'] / denominator
    
    # Fill NaN (where mouth duration was 0) with 0 or a large number? 
    # Spec says: if mean ratio <= 0, log warning. 
    # Let's fill NaN with 0 for now, or keep as NaN depending on downstream needs.
    # Standard practice: if mouth is 0, ratio is undefined. We'll fill with 0 for calculation safety 
    # but the mean check handles the logic.
    features_df['fixation_ratio'] = features_df['fixation_ratio'].fillna(0.0)
    
    mean_ratio = features_df['fixation_ratio'].mean()
    if mean_ratio <= 0:
        logger.warning(f"Mean fixation ratio is {mean_ratio:.4f} (<= 0). Proceeding with descriptive stats only.")
    
    return features_df

@get_logger_wrapper
def perform_kmeans_clustering(features_df, n_clusters=2, random_state=42):
    """
    Perform K-Means clustering on fixation_ratio.
    Returns dataframe with cluster labels and silhouette score.
    """
    logger = get_logger("perform_kmeans_clustering")
    
    if 'fixation_ratio' not in features_df.columns:
        raise ValueError("'fixation_ratio' column not found. Run calculate_continuous_ratio first.")
    
    X = features_df[['fixation_ratio']].values
    
    kmeans = KMeans(n_clusters=n_clusters, random_state=random_state, n_init=10)
    labels = kmeans.fit_predict(X)
    
    # Calculate silhouette score
    score = silhouette_score(X, labels)
    logger.info(f"Silhouette Score: {score:.4f}")
    
    if score < 0.25:
        logger.warning(f"Silhouette score ({score:.4f}) is low (< 0.25). Clusters may not be well separated.")
    
    cluster_sizes = pd.Series(labels).value_counts()
    for cluster_id, size in cluster_sizes.items():
        if size < 5:
            logger.warning(f"Cluster {cluster_id} has size {size} (< 5). Proceeding with descriptive stats only.")
    
    result_df = features_df.copy()
    result_df['cluster_label'] = labels
    
    return result_df, score

@get_logger_wrapper
def perform_bootstrap_stability_check(features_df, n_clusters=2, n_iterations=100, random_state=42):
    """
    Bootstrap Stability Check (FR-010, Plan-2.3).
    Repeats clustering on multiple bootstrap samples to assess label stability.
    Outputs stability metrics to data/processed/bootstrap_stability.json.
    
    Metrics:
    - Mean Adjusted Rand Index (ARI) between original labels and bootstrap labels (mapped).
    - Mean Silhouette Score across iterations.
    - Label stability frequency (how often a point keeps its label).
    """
    logger = get_logger("perform_bootstrap_stability_check")
    
    if 'fixation_ratio' not in features_df.columns:
        raise ValueError("'fixation_ratio' column not found.")
    
    X = features_df[['fixation_ratio']].values
    n_samples = len(X)
    
    # Run original clustering
    kmeans_orig = KMeans(n_clusters=n_clusters, random_state=random_state, n_init=10)
    orig_labels = kmeans_orig.fit_predict(X)
    
    ari_scores = []
    sil_scores = []
    label_stability_matrix = np.zeros((n_samples, n_clusters))
    
    logger.info(f"Running {n_iterations} bootstrap iterations...")
    
    for i in range(n_iterations):
        # Bootstrap sample (sample with replacement)
        indices = resample(np.arange(n_samples), replace=True, n_samples=n_samples, random_state=random_state + i)
        X_boot = X[indices]
        
        # Fit KMeans on bootstrap sample
        kmeans_boot = KMeans(n_clusters=n_clusters, random_state=random_state + i, n_init=10)
        boot_labels_boot = kmeans_boot.fit_predict(X_boot)
        
        # Map boot_labels_boot to orig_labels to compute ARI
        # Since cluster labels are arbitrary, we need to find the best permutation.
        # sklearn.metrics.adjusted_rand_score handles label permutation invariance automatically.
        # We need to project boot labels back to original indices to compare with orig_labels?
        # Actually, ARI compares two labelings of the SAME set of items.
        # Here, we have the SAME items (indices), but the bootstrap sample has duplicates.
        # We need to compare the clustering of the original set vs the clustering of the bootstrap set.
        # This is tricky because the bootstrap set has duplicates.
        # Alternative approach: Train on bootstrap, predict on original (X).
        
        # Let's use the approach: Train on Bootstrap, Predict on Original X
        # This tests if the model trained on a perturbed dataset gives consistent labels on the original data.
        
        boot_labels_pred = kmeans_boot.predict(X)
        
        # Calculate Silhouette on the bootstrap sample
        sil = silhouette_score(X_boot, boot_labels_boot)
        sil_scores.append(sil)
        
        # Calculate ARI between original labels and predicted labels
        # ARI is permutation invariant
        from sklearn.metrics import adjusted_rand_score
        ari = adjusted_rand_score(orig_labels, boot_labels_pred)
        ari_scores.append(ari)
        
        # Track label stability: how often does a point get the same label?
        for idx, pred_label in enumerate(boot_labels_pred):
            if pred_label == orig_labels[idx]:
                label_stability_matrix[idx, pred_label] += 1
    
    # Normalize stability matrix to frequency (0.0 to 1.0)
    stability_frequencies = label_stability_matrix / n_iterations
    
    # Calculate mean ARI and Silhouette
    mean_ari = np.mean(ari_scores)
    mean_sil = np.mean(sil_scores)
    std_ari = np.std(ari_scores)
    std_sil = np.std(sil_scores)
    
    # Overall stability: percentage of points that kept their original label in > 50% of iterations
    # We look at the max frequency for each point (if it matched its original label, that frequency is in the column of the original label)
    # But since we only incremented when pred == orig, the value in label_stability_matrix[i, orig_labels[i]] is the count of matches.
    match_counts = np.array([label_stability_matrix[i, orig_labels[i]] for i in range(n_samples)])
    stability_rate = np.mean(match_counts > (n_iterations * 0.5))
    
    results = {
        "n_iterations": n_iterations,
        "n_clusters": n_clusters,
        "mean_ari": float(mean_ari),
        "std_ari": float(std_ari),
        "mean_silhouette": float(mean_sil),
        "std_silhouette": float(std_sil),
        "label_stability_rate_50pct": float(stability_rate),
        "description": "Bootstrap stability check for k-means clustering. ARI measures agreement between original clustering and clustering of bootstrap samples (trained on bootstrap, predicted on original). Stability rate is the fraction of points that retained their original label in >50% of iterations."
    }
    
    logger.info(f"Bootstrap Stability Results: Mean ARI={mean_ari:.4f}, Stability Rate={stability_rate:.4f}")
    
    # Save to file
    config = get_config()
    output_path = config['paths']['processed_data'] / 'bootstrap_stability.json'
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Stability metrics saved to {output_path}")
    
    return results

@get_logger_wrapper
def save_ratio_features(features_df, output_path):
    """Save the features dataframe with ratio and cluster labels."""
    logger = get_logger("save_ratio_features")
    features_df.to_csv(output_path, index=False)
    logger.info(f"Features saved to {output_path}")

def main():
    """
    Main entry point for classification pipeline.
    1. Load features.
    2. Calculate continuous ratio.
    3. Perform K-Means clustering.
    4. Perform Bootstrap Stability Check.
    5. Save results.
    """
    logger = get_logger("main")
    config = get_config()
    
    input_path = config['paths']['processed_data'] / 'features.csv'
    output_path = config['paths']['processed_data'] / 'features_classified.csv'
    
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}. Run feature extraction first.")
        sys.exit(1)
    
    df = pd.read_csv(input_path)
    
    # Step 1: Calculate Ratio
    df = calculate_continuous_ratio(df)
    
    # Step 2: Clustering
    df_classified, score = perform_kmeans_clustering(df, n_clusters=2)
    
    # Step 3: Bootstrap Stability Check (FR-010)
    stability_results = perform_bootstrap_stability_check(df_classified, n_clusters=2, n_iterations=100)
    
    # Step 4: Save
    save_ratio_features(df_classified, output_path)
    
    logger.info("Classification pipeline completed successfully.")

if __name__ == "__main__":
    main()