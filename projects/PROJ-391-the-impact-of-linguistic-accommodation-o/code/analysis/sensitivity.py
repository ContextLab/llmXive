import os
import sys
import json
import logging
import random
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import pandas as pd
import numpy as np

# Import from existing project API
from utils import get_dependency_relations, jaccard_similarity, normalize_text

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
OUTPUTS_REPORTS_DIR = PROJECT_ROOT / "outputs" / "reports"
FINAL_DATASET_PATH = DATA_PROCESSED_DIR / "final_dataset.csv"
SENSITIVITY_RESULTS_PATH = OUTPUTS_REPORTS_DIR / "sensitivity_analysis.json"

SAMPLE_SIZE = 5000
RANDOM_SEED = 42

def load_final_dataset() -> pd.DataFrame:
    """Load the final dataset produced by T031."""
    if not FINAL_DATASET_PATH.exists():
        raise FileNotFoundError(
            f"Final dataset not found at {FINAL_DATASET_PATH}. "
            "Please ensure T031 (emotion_mapping) has completed successfully."
        )
    
    logger.info(f"Loading final dataset from {FINAL_DATASET_PATH}")
    df = pd.read_csv(FINAL_DATASET_PATH)
    logger.info(f"Loaded {len(df)} records")
    return df

def compute_dependency_metrics(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Compute dependency-parse-based metrics (Jaccard similarity of dependency relation sets).
    
    Strategy:
    - If full dataset exceeds memory constraints (heuristic: > 100k rows), sample n=5000.
    - Otherwise, process full dataset.
    
    Returns:
        Tuple of (processed_df, stats_dict)
    """
    full_size = len(df)
    stats = {
        "original_size": full_size,
        "processed_size": 0,
        "sampling_method": None,
        "sampling_seed": None
    }

    # Determine if sampling is needed based on size heuristic
    # Assuming ~100MB+ for full dataset might be heavy on CPU/RAM constrained env
    if full_size > 100000:
        logger.info(f"Dataset size ({full_size}) exceeds memory threshold. Sampling {SAMPLE_SIZE} records.")
        random.seed(RANDOM_SEED)
        np.random.seed(RANDOM_SEED)
        indices = random.sample(range(full_size), SAMPLE_SIZE)
        df_sample = df.iloc[indices].reset_index(drop=True)
        stats["sampling_method"] = "random"
        stats["sampling_seed"] = RANDOM_SEED
        stats["processed_size"] = SAMPLE_SIZE
        df_to_process = df_sample
    else:
        logger.info(f"Processing full dataset ({full_size} records).")
        df_to_process = df
        stats["processed_size"] = full_size
        df_to_process = df_to_process.reset_index(drop=True)

    # Prepare columns for dependency metrics
    # We expect 'speaker_a_turn' and 'speaker_b_turn' (or similar) from final_dataset
    # Check available columns to find the text columns
    text_cols_a = [c for c in df_to_process.columns if 'speaker_a' in c.lower() and 'turn' in c.lower()]
    text_cols_b = [c for c in df_to_process.columns if 'speaker_b' in c.lower() and 'turn' in c.lower()]

    if not text_cols_a or not text_cols_b:
        # Fallback to generic names if specific ones not found, or raise error
        available_cols = list(df_to_process.columns)
        raise ValueError(
            f"Could not find Speaker A/B turn columns. Available: {available_cols}. "
            "Expected columns like 'speaker_a_turn' and 'speaker_b_turn'."
        )

    col_a = text_cols_a[0]
    col_b = text_cols_b[0]

    logger.info(f"Using text columns: {col_a} and {col_b}")

    dependency_scores = []
    processed_count = 0

    for idx, row in df_to_process.iterrows():
        text_a = row[col_a]
        text_b = row[col_b]

        if pd.isna(text_a) or pd.isna(text_b):
            continue

        # Normalize text
        norm_a = normalize_text(str(text_a))
        norm_b = normalize_text(str(text_b))

        if not norm_a or not norm_b:
            continue

        # Get dependency relations
        try:
            deps_a = get_dependency_relations(norm_a)
            deps_b = get_dependency_relations(norm_b)
            
            if deps_a and deps_b:
                # Compute Jaccard similarity on the set of dependency relations
                # get_dependency_relations returns a list of strings like "nsubj:root", etc.
                score = jaccard_similarity(set(deps_a), set(deps_b))
                dependency_scores.append(score)
                processed_count += 1
        except Exception as e:
            # Log error but continue processing
            logger.warning(f"Error processing dependency relations at index {idx}: {e}")
            continue

    # Add dependency similarity column to dataframe
    # If we sampled, we need to map back or just return the sampled dataframe
    if stats["sampling_method"]:
        df_to_process['dependency_similarity'] = dependency_scores
        final_df = df_to_process
    else:
        # Create a new dataframe with the original index to maintain alignment if needed,
        # but for this task, we just need the metrics dataframe to save.
        # We'll create a new dataframe with the results.
        final_df = df_to_process.copy()
        final_df['dependency_similarity'] = dependency_scores

    # Calculate statistics
    if dependency_scores:
        stats['dependency_stats'] = {
            'mean': float(np.mean(dependency_scores)),
            'std': float(np.std(dependency_scores)),
            'min': float(np.min(dependency_scores)),
            'max': float(np.max(dependency_scores)),
            'count': len(dependency_scores)
        }
    else:
        stats['dependency_stats'] = {
            'mean': 0.0,
            'std': 0.0,
            'min': 0.0,
            'max': 0.0,
            'count': 0,
            'error': "No valid dependency relations computed."
        }

    return final_df, stats

def compare_metrics(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Compare POS-based vs Dependency-based metrics.
    
    Assumes 'syntactic_similarity' (POS-based) exists in df from T021/T031.
    Computes correlation between POS-based and Dependency-based metrics.
    """
    if 'syntactic_similarity' not in df.columns or 'dependency_similarity' not in df.columns:
        logger.warning("Cannot compare metrics: required columns missing.")
        return {"error": "Missing columns for comparison"}

    # Filter out NaNs
    valid_df = df[['syntactic_similarity', 'dependency_similarity']].dropna()
    
    if len(valid_df) < 2:
        return {"comparison": "insufficient_data"}

    # Compute Pearson correlation
    corr = valid_df['syntactic_similarity'].corr(valid_df['dependency_similarity'])
    
    # Compute basic stats for each
    pos_stats = {
        'mean': float(valid_df['syntactic_similarity'].mean()),
        'std': float(valid_df['syntactic_similarity'].std())
    }
    dep_stats = {
        'mean': float(valid_df['dependency_similarity'].mean()),
        'std': float(valid_df['dependency_similarity'].std())
    }

    return {
        'correlation': float(corr),
        'pos_based_stats': pos_stats,
        'dependency_based_stats': dep_stats,
        'sample_size': len(valid_df)
    }

def save_results(df: pd.DataFrame, stats: Dict[str, Any], comparison: Dict[str, Any]) -> None:
    """Save the sensitivity analysis results to JSON."""
    OUTPUTS_REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    
    results = {
        "sampling_info": stats,
        "dependency_metric_stats": stats.get('dependency_stats', {}),
        "comparison_with_pos": comparison,
        "data_sample_saved_to": str(DATA_PROCESSED_DIR / "sensitivity_sample.csv") if stats.get('sampling_method') else "full_dataset"
    }

    # Save the processed dataframe (sample or full) to CSV for inspection
    output_csv_path = DATA_PROCESSED_DIR / "sensitivity_sample.csv"
    df.to_csv(output_csv_path, index=False)
    logger.info(f"Saved processed data to {output_csv_path}")

    # Save JSON report
    with open(SENSITIVITY_RESULTS_PATH, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Saved sensitivity analysis report to {SENSITIVITY_RESULTS_PATH}")

def main():
    """Main entry point for sensitivity analysis."""
    try:
        logger.info("Starting Sensitivity Analysis (T038)")
        
        # 1. Load final dataset
        df = load_final_dataset()
        
        # 2. Compute dependency metrics (with sampling if needed)
        processed_df, stats = compute_dependency_metrics(df)
        
        # 3. Compare with POS-based metrics
        comparison = compare_metrics(processed_df)
        
        # 4. Save results
        save_results(processed_df, stats, comparison)
        
        logger.info("Sensitivity Analysis completed successfully.")
        
    except Exception as e:
        logger.error(f"Sensitivity Analysis failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()