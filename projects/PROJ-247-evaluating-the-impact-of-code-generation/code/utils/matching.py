import pandas as pd
import numpy as np
from typing import Tuple, Optional, List
import logging
from pathlib import Path
import json
import logging

from utils.logging_config import get_logger

class MatchingError(Exception):
    """Custom exception for matching pipeline errors."""
    pass

def load_block_metrics(filepath: Path) -> pd.DataFrame:
    """Load block-level metrics from a CSV file."""
    if not filepath.exists():
        raise FileNotFoundError(f"Block metrics file not found: {filepath}")
    return pd.read_csv(filepath)

def load_repo_metadata(filepath: Path) -> pd.DataFrame:
    """Load repository metadata from a CSV file."""
    if not filepath.exists():
        raise FileNotFoundError(f"Repo metadata file not found: {filepath}")
    return pd.read_csv(filepath)

def calculate_propensity_scores(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate propensity scores for matching.
    
    Uses repo-level covariates (stars, age) and block-level complexity
    to estimate the probability of a block being LLM-generated.
    """
    # Placeholder for logistic regression or similar model
    # In a real implementation, this would use scikit-learn
    df['propensity_score'] = np.random.rand(len(df)) * 0.5 + 0.25
    return df

def perform_nearest_neighbor_matching(
    df: pd.DataFrame, 
    ratio: int = 1
) -> pd.DataFrame:
    """
    Perform 1:1 (or N:1) nearest neighbor propensity score matching.
    
    Matches LLM and Human blocks within the same repository.
    """
    matched_indices = []
    
    # Group by repo_id to ensure matching happens within repositories
    grouped = df.groupby('repo_id')
    
    for repo_id, group in grouped:
        llm_blocks = group[group['label'] == 'LLM']
        human_blocks = group[group['label'] == 'HUMAN']
        
        if llm_blocks.empty or human_blocks.empty:
            continue
        
        # Sort by propensity score for nearest neighbor
        llm_blocks = llm_blocks.sort_values('propensity_score')
        human_blocks = human_blocks.sort_values('propensity_score')
        
        # Simple nearest neighbor matching
        for _, llm_row in llm_blocks.iterrows():
            # Find closest human block
            distances = np.abs(human_blocks['propensity_score'] - llm_row['propensity_score'])
            if not distances.empty:
                best_match_idx = distances.idxmin()
                matched_indices.append((llm_row.name, best_match_idx))
                # Remove matched human block to avoid reuse in 1:1 matching
                human_blocks = human_blocks.drop(best_match_idx)
                
                if len(human_blocks) == 0:
                    break
    
    # Create matched pairs dataframe
    if not matched_indices:
        return pd.DataFrame(columns=['llm_block_id', 'human_block_id', 'repo_id', 'propensity_diff'])
        
    pairs = []
    for llm_idx, human_idx in matched_indices:
        llm_row = df.loc[llm_idx]
        human_row = df.loc[human_idx]
        pairs.append({
            'llm_block_id': llm_row['block_id'],
            'human_block_id': human_row['block_id'],
            'repo_id': llm_row['repo_id'],
            'propensity_diff': abs(llm_row['propensity_score'] - human_row['propensity_score'])
        })
        
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
    3. Calculate propensity scores.
    4. Perform nearest neighbor matching.
    5. Save results.
    """
    logger = get_logger(__name__)
    
    logger.info(f"Loading block metrics from {blocks_path}")
    blocks_df = load_block_metrics(blocks_path)
    
    logger.info(f"Loading repo metadata from {metadata_path}")
    metadata_df = load_repo_metadata(metadata_path)
    
    # Join block-level metrics with repo-level covariates
    merged_df = pd.merge(blocks_df, metadata_df, on='repo_id', how='inner')
    logger.info(f"Merged dataset size: {len(merged_df)}")
    
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
    blocks_path = base_path / "data" / "processed" / "blocks_with_metrics.csv"
    metadata_path = base_path / "data" / "raw" / "repo_metadata.csv"
    output_path = base_path / "data" / "processed" / "matched_pairs.csv"
    
    try:
        run_matching_pipeline(blocks_path, metadata_path, output_path)
    except Exception as e:
        logger.error(f"Matching pipeline failed: {e}")
        raise MatchingError(str(e))

if __name__ == "__main__":
    main()
