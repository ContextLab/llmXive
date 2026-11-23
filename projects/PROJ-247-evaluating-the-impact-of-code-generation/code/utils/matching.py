"""
Propensity score matching module for code maintainability study.

Implements 1:1 nearest-neighbor matching based on logistic regression
propensity scores derived from code complexity metrics.
"""
import pandas as pd
import numpy as np
from typing import Tuple, Optional, List, Dict
import logging
from pathlib import Path
import json
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.exceptions import ConvergenceWarning
import warnings

# Suppress convergence warnings for cleaner logs
warnings.filterwarnings("ignore", category=ConvergenceWarning)

class MatchingError(Exception):
    """Custom exception for matching pipeline errors."""
    pass

# Constants
MIN_REPOS_FOR_MATCHING = 1
MIN_BLOCKS_PER_REPO = 5
CONFIDENCE_THRESHOLD = 0.8

logger = logging.getLogger(__name__)

def load_block_metrics(csv_path: str) -> pd.DataFrame:
    """
    Load code block metrics from CSV.
    
    Expected columns: block_id, repo_name, language, label, 
                    cyclomatic_complexity, loc, confidence
    
    Args:
        csv_path: Path to code_blocks.csv
        
    Returns:
        DataFrame with block metrics
        
    Raises:
        MatchingError: If file not found or missing required columns
    """
    path = Path(csv_path)
    if not path.exists():
        raise MatchingError(f"Metrics file not found: {csv_path}")
    
    try:
        df = pd.read_csv(csv_path)
    except Exception as e:
        raise MatchingError(f"Failed to read CSV: {e}")
    
    required_cols = ['block_id', 'repo_name', 'label', 'cyclomatic_complexity', 'loc']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise MatchingError(f"Missing required columns: {missing_cols}")
    
    # Filter by confidence if confidence column exists
    if 'confidence' in df.columns:
        df = df[df['confidence'] >= CONFIDENCE_THRESHOLD]
        logger.info(f"Filtered blocks by confidence >= {CONFIDENCE_THRESHOLD}: {len(df)} remaining")
    
    # Ensure label is string and uppercase
    df['label'] = df['label'].astype(str).str.upper()
    
    return df

def load_repo_metadata(csv_path: str) -> pd.DataFrame:
    """
    Load repository metadata.
    
    Args:
        csv_path: Path to repo_metadata.csv
        
    Returns:
        DataFrame with repo metadata
    """
    path = Path(csv_path)
    if not path.exists():
        logger.warning(f"Repo metadata file not found: {csv_path}. Proceeding without repo-level covariates.")
        return pd.DataFrame()
    
    try:
        return pd.read_csv(csv_path)
    except Exception as e:
        logger.warning(f"Failed to read repo metadata: {e}. Proceeding without repo-level covariates.")
        return pd.DataFrame()

def calculate_propensity_scores(df: pd.DataFrame) -> pd.DataFrame:
    """
    Fit logistic regression model and calculate propensity scores.
    
    The model predicts probability of being LLM-generated based on:
    - cyclomatic_complexity
    - loc (Lines of Code)
    
    Args:
        df: DataFrame with block metrics
        
    Returns:
        DataFrame with added 'propensity_score' column
        
    Raises:
        MatchingError: If matching fails due to insufficient data
    """
    if len(df) < 10:
        raise MatchingError(f"Insufficient data for matching: {len(df)} blocks")
    
    # Prepare features
    feature_cols = ['cyclomatic_complexity', 'loc']
    X = df[feature_cols].values
    y = (df['label'] == 'LLM').astype(int).values
    
    # Check for class imbalance
    llm_count = y.sum()
    human_count = len(y) - llm_count
    
    if llm_count == 0 or human_count == 0:
        raise MatchingError("Cannot perform matching: missing one class (LLM or Human)")
    
    logger.info(f"Class distribution - LLM: {llm_count}, Human: {human_count}")
    
    # Scale features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # Fit logistic regression
    clf = LogisticRegression(max_iter=1000, random_state=42, solver='lbfgs')
    
    try:
        clf.fit(X_scaled, y)
    except Exception as e:
        raise MatchingError(f"Logistic regression fitting failed: {e}")
    
    # Calculate propensity scores
    propensity_scores = clf.predict_proba(X_scaled)[:, 1]
    df = df.copy()
    df['propensity_score'] = propensity_scores
    
    logger.info(f"Propensity scores calculated. Mean: {propensity_scores.mean():.4f}, Std: {propensity_scores.std():.4f}")
    
    return df

def perform_nearest_neighbor_matching(df: pd.DataFrame) -> pd.DataFrame:
    """
    Perform 1:1 nearest-neighbor matching within repositories.
    
    For each LLM block, find the closest Human block in the same repository
    based on propensity score difference.
    
    Args:
        df: DataFrame with propensity scores
        
    Returns:
        DataFrame with matched pairs (block_id_llm, block_id_human, propensity_diff)
        
    Raises:
        MatchingError: If matching fails
    """
    if len(df) < 4:
        raise MatchingError(f"Insufficient data for matching: {len(df)} blocks")
    
    # Group by repository
    matched_pairs = []
    repos_processed = 0
    repos_skipped = 0
    
    for repo_name, group in df.groupby('repo_name'):
        llm_blocks = group[group['label'] == 'LLM']
        human_blocks = group[group['label'] == 'HUMAN']
        
        # Skip repos with insufficient blocks
        if len(llm_blocks) < 1 or len(human_blocks) < 1:
            repos_skipped += 1
            continue
        
        repos_processed += 1
        
        # Sort by propensity score for efficient matching
        llm_blocks = llm_blocks.sort_values('propensity_score')
        human_blocks = human_blocks.sort_values('propensity_score')
        
        used_human_indices = set()
        
        # Match each LLM block to nearest available Human block
        for _, llm_row in llm_blocks.iterrows():
            # Calculate distances to all unused human blocks
            human_scores = human_blocks['propensity_score'].values
            llm_score = llm_row['propensity_score']
            
            distances = np.abs(human_scores - llm_score)
            
            # Find nearest unused human block
            best_idx = None
            best_dist = np.inf
            
            for idx, dist in enumerate(distances):
                if idx not in used_human_indices and dist < best_dist:
                    best_idx = idx
                    best_dist = dist
            
            if best_idx is not None:
                used_human_indices.add(best_idx)
                human_row = human_blocks.iloc[best_idx]
                
                matched_pairs.append({
                    'block_id_llm': llm_row['block_id'],
                    'block_id_human': human_row['block_id'],
                    'repo_name': repo_name,
                    'propensity_score_llm': llm_row['propensity_score'],
                    'propensity_score_human': human_row['propensity_score'],
                    'propensity_diff': best_dist,
                    'cyclomatic_complexity_llm': llm_row['cyclomatic_complexity'],
                    'cyclomatic_complexity_human': human_row['cyclomatic_complexity'],
                    'loc_llm': llm_row['loc'],
                    'loc_human': human_row['loc']
                })
    
    logger.info(f"Matching completed. Repos processed: {repos_processed}, skipped: {repos_skipped}")
    logger.info(f"Total matched pairs: {len(matched_pairs)}")
    
    if len(matched_pairs) == 0:
        raise MatchingError("No matched pairs found. Check data distribution.")
    
    return pd.DataFrame(matched_pairs)

def run_matching_pipeline(input_csv: str, output_csv: str, repo_metadata_csv: Optional[str] = None):
    """
    Run the complete matching pipeline.
    
    1. Load block metrics
    2. Calculate propensity scores
    3. Perform nearest-neighbor matching
    4. Save results
    
    Args:
        input_csv: Path to code_blocks.csv
        output_csv: Path to save matched_pairs.csv
        repo_metadata_csv: Optional path to repo_metadata.csv
    """
    logger.info("Starting matching pipeline")
    
    # Load data
    df = load_block_metrics(input_csv)
    logger.info(f"Loaded {len(df)} blocks from {input_csv}")
    
    # Optionally merge repo metadata (for future extensions)
    if repo_metadata_csv:
        repo_meta = load_repo_metadata(repo_metadata_csv)
        if not repo_meta.empty:
            df = df.merge(repo_meta, on='repo_name', how='left')
            logger.info(f"Merged with repo metadata: {len(repo_meta)} repos")
    
    # Calculate propensity scores
    df = calculate_propensity_scores(df)
    
    # Perform matching
    matched_df = perform_nearest_neighbor_matching(df)
    
    # Save results
    output_path = Path(output_csv)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    matched_df.to_csv(output_csv, index=False)
    
    logger.info(f"Saved {len(matched_df)} matched pairs to {output_csv}")
    
    # Save matching statistics
    stats = {
        'total_blocks_input': len(df),
        'matched_pairs': len(matched_df),
        'repos_processed': matched_df['repo_name'].nunique(),
        'propensity_score_stats': {
            'llm_mean': float(matched_df['propensity_score_llm'].mean()),
            'llm_std': float(matched_df['propensity_score_llm'].std()),
            'human_mean': float(matched_df['propensity_score_human'].mean()),
            'human_std': float(matched_df['propensity_score_human'].std()),
            'mean_diff': float(matched_df['propensity_diff'].mean())
        }
    }
    
    stats_path = output_path.parent / 'matching_stats.json'
    with open(stats_path, 'w') as f:
        json.dump(stats, f, indent=2)
    
    logger.info(f"Saved matching statistics to {stats_path}")
    
    return matched_df

def main():
    """Main entry point for matching pipeline."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Propensity score matching for code blocks')
    parser.add_argument('--input', type=str, default='data/raw/code_blocks.csv',
                      help='Input CSV with block metrics')
    parser.add_argument('--output', type=str, default='data/processed/matched_pairs.csv',
                      help='Output CSV with matched pairs')
    parser.add_argument('--repo-metadata', type=str, default='data/raw/repo_metadata.csv',
                      help='Optional repo metadata CSV')
    parser.add_argument('--log-level', type=str, default='INFO',
                      choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'])
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('data/logs/matching_pipeline.log')
        ]
    )
    
    try:
        run_matching_pipeline(
            input_csv=args.input,
            output_csv=args.output,
            repo_metadata_csv=args.repo_metadata if Path(args.repo_metadata).exists() else None
        )
        logger.info("Matching pipeline completed successfully")
    except MatchingError as e:
        logger.error(f"Matching pipeline failed: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise

if __name__ == '__main__':
    main()