"""
Sparsity Generation Module (US2)

Implements K-Means clustering on elemental fingerprints to generate
multiple stratified subsets of the Representative Stratified Sample (RSS)
pool, preserving chemical space as per FR-003.

Outputs:
    - data/processed/sparsity_<level>_<seed>.csv for each subset
    - data/metadata/sparsity_<level>_<seed>.json for each subset
"""
import os
import sys
import json
import hashlib
import argparse
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from scipy.stats import entropy

# Project imports
from utils.logging import get_logger
from utils.data_models import SparsitySubset
from utils.cpu_constraints import enforce_memory_limit
from utils.checksum_utils import generate_and_save_checksum

logger = get_logger(__name__)

# Configuration constants
RSS_SIZE = 30000  # Baseline size for RSS as per T031
SPARSITY_LEVELS = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7]  # Percentages of RSS
NUM_CLUSTERS = 100  # Number of K-Means clusters for stratification
SEEDS = [42, 123, 456, 789, 1011]  # Multiple seeds for robustness
INPUT_FILE = "data/processed/filtered_pool.csv"
OUTPUT_DIR = "data/processed"
METADATA_DIR = "data/metadata"

def load_rss_pool(input_path: str) -> pd.DataFrame:
    """
    Load the RSS pool from the filtered dataset.
    Assumes T031 has already capped the pool to RSS_SIZE.
    """
    logger.info(f"Loading RSS pool from {input_path}")
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    df = pd.read_csv(input_path)
    logger.info(f"Loaded {len(df)} rows. Expected ~{RSS_SIZE} rows.")
    
    if len(df) > RSS_SIZE:
        logger.warning(f"Pool size ({len(df)}) exceeds RSS_SIZE ({RSS_SIZE}). Truncating.")
        df = df.head(RSS_SIZE)
    
    return df

def compute_elemental_fingerprints(df: pd.DataFrame) -> np.ndarray:
    """
    Compute elemental fingerprints for K-Means clustering.
    Uses elemental composition to generate a feature vector.
    
    Note: This is a simplified approach assuming 'composition' column exists.
    In a full implementation, matminer's ElementPropertyFeatureExtractor would be used,
    but for sparsity generation, we focus on the compositional distribution.
    """
    logger.info("Computing elemental fingerprints...")
    
    # Extract unique elements and compute presence/abundance
    # Simple approach: one-hot encode elements present in each composition
    # More robust: use atomic fractions of top N elements
    
    all_elements = set()
    for comp in df['composition']:
        # Parse composition string (e.g., "Fe2O3" -> {"Fe": 2, "O": 3})
        # Simplified parsing for demo - assumes standard format
        import re
        elements = re.findall(r'([A-Z][a-z]?)(\d*)', comp)
        for elem, count in elements:
            all_elements.add(elem)
    
    element_list = sorted(list(all_elements))
    logger.info(f"Found {len(element_list)} unique elements")
    
    # Create fingerprint matrix
    fingerprints = []
    for comp in df['composition']:
        fingerprint = np.zeros(len(element_list))
        import re
        elements = re.findall(r'([A-Z][a-z]?)(\d*)', comp)
        for elem, count in elements:
            idx = element_list.index(elem)
            count = int(count) if count else 1
            fingerprint[idx] = count
        fingerprints.append(fingerprint)
    
    fingerprints = np.array(fingerprints)
    logger.info(f"Fingerprint matrix shape: {fingerprints.shape}")
    return fingerprints

def generate_stratified_subsets(
    df: pd.DataFrame,
    fingerprints: np.ndarray,
    levels: List[float],
    seeds: List[int],
    num_clusters: int = NUM_CLUSTERS
) -> List[Tuple[pd.DataFrame, SparsitySubset]]:
    """
    Generate stratified subsets using K-Means clustering on fingerprints.
    
    For each sparsity level and seed:
    1. Run K-Means clustering on fingerprints
    2. Sample proportionally from each cluster
    3. Return subset with metadata
    """
    logger.info(f"Generating subsets for {len(levels)} levels x {len(seeds)} seeds")
    
    # Scale fingerprints for better clustering
    scaler = StandardScaler()
    scaled_fingerprints = scaler.fit_transform(fingerprints)
    
    # Run K-Means once (clusters are data-driven, not level-dependent)
    logger.info(f"Running K-Means with {num_clusters} clusters...")
    kmeans = KMeans(n_clusters=num_clusters, random_state=SEEDS[0], n_init=10)
    cluster_labels = kmeans.fit_predict(scaled_fingerprints)
    
    subsets = []
    
    for level in levels:
        for seed in seeds:
            logger.info(f"Processing level={level}, seed={seed}")
            np.random.seed(seed)
            
            # Calculate target size
            target_size = int(len(df) * level)
            
            # Stratified sampling by cluster
            subset_indices = []
            for cluster_id in range(num_clusters):
                cluster_indices = np.where(cluster_labels == cluster_id)[0]
                cluster_size = len(cluster_indices)
                
                # Sample proportionally from this cluster
                sample_size = max(1, int(cluster_size * level))
                sampled_indices = np.random.choice(cluster_indices, size=sample_size, replace=False)
                subset_indices.extend(sampled_indices)
            
            # Ensure we have exactly target_size (adjust if needed)
            if len(subset_indices) > target_size:
                subset_indices = np.random.choice(subset_indices, size=target_size, replace=False)
            elif len(subset_indices) < target_size:
                # Fill with random samples if undersampled
                remaining = target_size - len(subset_indices)
                all_indices = set(range(len(df))) - set(subset_indices)
                if remaining <= len(all_indices):
                    fill_indices = np.random.choice(list(all_indices), size=remaining, replace=False)
                    subset_indices.extend(fill_indices)
            
            subset_df = df.iloc[subset_indices].reset_index(drop=True)
            
            # Create metadata
            metadata = SparsitySubset(
                level=level,
                seed=seed,
                percentage=level * 100,
                checksum=""  # Will be filled after saving
            )
            
            subsets.append((subset_df, metadata))
    
    logger.info(f"Generated {len(subsets)} subsets")
    return subsets

def save_subset(
    subset_df: pd.DataFrame,
    metadata: SparsitySubset,
    output_dir: str,
    metadata_dir: str
) -> str:
    """
    Save subset to CSV and metadata to JSON.
    Returns the path to the saved CSV.
    """
    # Generate filenames
    level_str = f"{int(metadata.percentage)}"
    filename = f"sparsity_{level_str}_{metadata.seed}.csv"
    csv_path = Path(output_dir) / filename
    json_filename = f"sparsity_{level_str}_{metadata.seed}.json"
    json_path = Path(metadata_dir) / json_filename
    
    # Ensure directories exist
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save CSV
    subset_df.to_csv(csv_path, index=False)
    logger.info(f"Saved subset to {csv_path}")
    
    # Generate checksum
    checksum = generate_and_save_checksum(str(csv_path))
    metadata.checksum = checksum
    
    # Save metadata
    metadata_dict = {
        "level": metadata.level,
        "seed": metadata.seed,
        "percentage": metadata.percentage,
        "criteria": "K-Means stratified sampling on elemental fingerprints",
        "checksum": metadata.checksum,
        "row_count": len(subset_df),
        "source_file": str(csv_path)
    }
    
    with open(json_path, 'w') as f:
        json.dump(metadata_dict, f, indent=2)
    logger.info(f"Saved metadata to {json_path}")
    
    return str(csv_path)

def validate_stratification(
    original_df: pd.DataFrame,
    subset_df: pd.DataFrame,
    feature_col: str = "formation_energy"
) -> Dict[str, Any]:
    """
    Validate that the subset preserves the distribution of the original data.
    Uses Kolmogorov-Smirnov test and Jensen-Shannon divergence.
    """
    from scipy.stats import ks_2samp
    
    original_values = original_df[feature_col].dropna().values
    subset_values = subset_df[feature_col].dropna().values
    
    # KS-test
    ks_stat, ks_p = ks_2samp(original_values, subset_values)
    
    # Jensen-Shannon divergence (requires binning)
    hist_orig, bin_edges = np.histogram(original_values, bins=50, density=True)
    hist_sub, _ = np.histogram(subset_values, bins=bin_edges, density=True)
    
    # Normalize
    hist_orig = hist_orig / hist_orig.sum()
    hist_sub = hist_sub / hist_sub.sum()
    
    # Avoid log(0)
    hist_orig = np.clip(hist_orig, 1e-10, 1)
    hist_sub = np.clip(hist_sub, 1e-10, 1)
    
    js_divergence = 0.5 * (entropy(hist_orig, (hist_orig + hist_sub) / 2) + 
                           entropy(hist_sub, (hist_orig + hist_sub) / 2))
    
    return {
        "ks_statistic": float(ks_stat),
        "ks_p_value": float(ks_p),
        "js_divergence": float(js_divergence),
        "distribution_preserved": ks_p > 0.05 and js_divergence < 0.05
    }

def main():
    """
    Main entry point for sparsity generation.
    """
    logger.info("Starting sparsity generation pipeline")
    
    # Enforce memory constraints
    enforce_memory_limit(limit_mb=8000)
    
    # Load RSS pool
    try:
        df = load_rss_pool(INPUT_FILE)
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)
    
    # Compute fingerprints
    fingerprints = compute_elemental_fingerprints(df)
    
    # Generate subsets
    subsets = generate_stratified_subsets(
        df, fingerprints, SPARSITY_LEVELS, SEEDS
    )
    
    # Save and validate
    results = []
    for subset_df, metadata in subsets:
        csv_path = save_subset(subset_df, metadata, OUTPUT_DIR, METADATA_DIR)
        
        # Validate stratification
        validation = validate_stratification(df, subset_df)
        results.append({
            "file": csv_path,
            "metadata": metadata.__dict__,
            "validation": validation
        })
        
        logger.info(f"Subset {metadata.percentage}% (seed {metadata.seed}): "
                   f"KS p={validation['ks_p_value']:.3f}, JS={validation['js_divergence']:.4f}, "
                   f"preserved={validation['distribution_preserved']}")
    
    # Summary
    preserved_count = sum(1 for r in results if r['validation']['distribution_preserved'])
    logger.info(f"Stratification validation: {preserved_count}/{len(results)} subsets passed")
    
    if preserved_count < len(results):
        logger.warning("Some subsets did not pass stratification validation. "
                     "Consider adjusting clustering parameters.")
    
    logger.info("Sparsity generation completed successfully")
    return 0

if __name__ == "__main__":
    sys.exit(main())
