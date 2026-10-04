import pandas as pd
import numpy as np
from typing import Tuple, Optional, List
import logging
from pathlib import Path
import json
import logging
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
import warnings

from utils.logging_config import get_logger

class MatchingError(Exception):
    """Custom exception for matching pipeline errors."""
    pass

def load_block_metrics(filepath: Path) -> pd.DataFrame:
    """Load block-level metrics from a CSV file."""
    if not filepath.exists():
        raise FileNotFoundError(f"Block metrics file not found: {filepath}")
    df = pd.read_csv(filepath)
    # Ensure required columns exist
    required_cols = ['block_id', 'repo_id', 'label', 'cyclomatic_complexity', 'loc']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise MatchingError(f"Block metrics missing required columns: {missing}")
    return df

def load_repo_metadata(filepath: Path) -> pd.DataFrame:
    """Load repository metadata from a CSV file."""
    if not filepath.exists():
        raise FileNotFoundError(f"Repo metadata file not found: {filepath}")
    return pd.read_csv(filepath)

def calculate_propensity_scores(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate propensity scores for matching.
    
    Uses block-level complexity (cyclomatic_complexity, LOC) as covariates
    to estimate the probability of a block being LLM-generated.
    
    Algorithm:
    1. Fit a logistic regression model using cyclomatic_complexity and LOC.
    2. Predict probability (propensity score) for all blocks.
    """
    logger = get_logger(__name__)
    
    # Prepare features
    feature_cols = ['cyclomatic_complexity', 'loc']
    
    # Check for infinite or NaN values in features
    if df[feature_cols].isnull().any().any():
        logger.warning("NaN values detected in features. Dropping rows with NaN in features.")
        df = df.dropna(subset=feature_cols)
    
    if df[feature_cols].isinf().any().any():
        logger.warning("Inf values detected in features. Dropping rows with Inf in features.")
        df = df[~np.isinf(df[feature_cols]).any(axis=1)]
    
    if len(df) == 0:
        raise MatchingError("No valid data remaining after cleaning for propensity score calculation.")
    
    X = df[feature_cols].values
    y = (df['label'] == 'LLM').astype(int).values
    
    # Check if we have both classes
    if len(np.unique(y)) < 2:
        raise MatchingError("Cannot calculate propensity scores: all blocks have the same label.")
    
    # Standardize features for better logistic regression performance
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # Fit logistic regression
    # Using regularization to handle potential separation issues
    clf = LogisticRegression(random_state=42, solver='lbfgs', max_iter=1000)
    
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        clf.fit(X_scaled, y)
    
    # Calculate propensity scores (probability of being LLM)
    propensity_scores = clf.predict_proba(X_scaled)[:, 1]
    
    df = df.copy()
    df['propensity_score'] = propensity_scores
    
    logger.info(f"Propensity scores calculated. Range: [{propensity_scores.min():.4f}, {propensity_scores.max():.4f}]")
    logger.info(f"Mean propensity score: {propensity_scores.mean():.4f}")
    
    return df

def perform_nearest_neighbor_matching(
    df: pd.DataFrame, 
    ratio: int = 1
) -> pd.DataFrame:
    """
    Perform 1:1 (or N:1) nearest neighbor propensity score matching.
    
    Matches LLM and Human blocks within the same repository.
    """
    logger = get_logger(__name__)
    matched_indices = []
    
    # Group by repo_id to ensure matching happens within repositories
    grouped = df.groupby('repo_id')
    total_matches = 0
    
    for repo_id, group in grouped:
        llm_blocks = group[group['label'] == 'LLM'].copy()
        human_blocks = group[group['label'] == 'HUMAN'].copy()
        
        if llm_blocks.empty or human_blocks.empty:
            continue
        
        # Sort by propensity score for nearest neighbor
        llm_blocks = llm_blocks.sort_values('propensity_score')
        human_blocks = human_blocks.sort_values('propensity_score')
        
        # Track used human blocks for this repo
        available_human_indices = set(human_blocks.index)
        
        for llm_idx, llm_row in llm_blocks.iterrows():
            if len(available_human_indices) == 0:
                break
            
            # Calculate distances to available human blocks
            distances = {}
            for h_idx in available_human_indices:
                dist = abs(human_blocks.loc[h_idx, 'propensity_score'] - llm_row['propensity_score'])
                distances[h_idx] = dist
            
            if not distances:
                continue
            
            # Find closest human block
            best_match_idx = min(distances, key=distances.get)
            best_dist = distances[best_match_idx]
            
            # Record the match
            matched_indices.append((llm_idx, best_match_idx, best_dist))
            
            # Remove matched human block to avoid reuse in 1:1 matching
            available_human_indices.remove(best_match_idx)
            total_matches += 1
    
    if not matched_indices:
        logger.warning("No matches found.")
        return pd.DataFrame(columns=['llm_block_id', 'human_block_id', 'repo_id', 'propensity_diff'])
        
    pairs = []
    for llm_idx, human_idx, dist in matched_indices:
        llm_row = df.loc[llm_idx]
        human_row = df.loc[human_idx]
        pairs.append({
            'llm_block_id': llm_row['block_id'],
            'human_block_id': human_row['block_id'],
            'repo_id': llm_row['repo_id'],
            'propensity_diff': dist
        })
        
    logger.info(f"Generated {len(pairs)} matched pairs.")
    return pd.DataFrame(pairs)

def run_matching_pipeline(
    blocks_path: Path, 
    metadata_path: Path, 
    output_path: Path
) -> pd.DataFrame:
    """
    Run the full matching pipeline.
    
    1. Load block metrics and repo metadata.
    2. Join on repo_id.
    3. Calculate propensity scores using logistic regression.
    4. Perform 1:1 nearest neighbor matching within repositories.
    5. Save results.
    """
    logger = get_logger(__name__)
    
    logger.info(f"Loading block metrics from {blocks_path}")
    blocks_df = load_block_metrics(blocks_path)
    
    logger.info(f"Loading repo metadata from {metadata_path}")
    # Metadata is loaded but not strictly needed for propensity calculation 
    # if we only use block-level features, but we merge to satisfy API
    metadata_df = load_repo_metadata(metadata_path)
    
    # Join block-level metrics with repo-level covariates (if needed)
    # For this implementation, we rely on block-level features from T014
    merged_df = pd.merge(blocks_df, metadata_df, on='repo_id', how='inner')
    logger.info(f"Merged dataset size: {len(merged_df)}")
    
    if len(merged_df) == 0:
        raise MatchingError("No data after merging block metrics and repo metadata.")
    
    # Calculate propensity scores
    logger.info("Calculating propensity scores...")
    scored_df = calculate_propensity_scores(merged_df)
    
    # Perform matching
    logger.info("Performing nearest neighbor matching...")
    matched_pairs = perform_nearest_neighbor_matching(scored_df)
    
    # Save results
    output_path.parent.mkdir(parents=True, exist_ok=True)
    matched_pairs.to_csv(output_path, index=False)
    logger.info(f"Saved {len(matched_pairs)} matched pairs to {output_path}")
    
    return matched_pairs

def main():
    """Main entry point for matching pipeline."""
    logger = get_logger(__name__)
    logger.info("Starting Matching Pipeline")
    
    # Example paths (these would be configured or passed as arguments)
    base_path = Path(__file__).parent.parent.parent
    blocks_path = base_path / "data" / "raw" / "code_blocks.csv"
    metadata_path = base_path / "data" / "raw" / "repo_metadata.csv"
    output_path = base_path / "data" / "processed" / "matched_pairs.csv"
    
    try:
        run_matching_pipeline(blocks_path, metadata_path, output_path)
    except Exception as e:
        logger.error(f"Matching pipeline failed: {e}")
        raise MatchingError(str(e))

if __name__ == "__main__":
    main()
