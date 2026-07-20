"""
validation.py

Implements statistical validation logic and mock ground truth generation
for the llmXive drift detection pipeline.
"""
import json
import os
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
import pandas as pd
from scipy import stats

from config import get_path, get_output_path, get_config
from utils import load_csv_file, save_csv_file


def calculate_cohen_d(group1: pd.Series, group2: pd.Series) -> float:
    """
    Calculate Cohen's d effect size between two groups.
    
    Args:
        group1: First group of values (e.g., benign drift scores)
        group2: Second group of values (e.g., novel drift scores)
        
    Returns:
        Cohen's d effect size
    """
    mean1, std1, n1 = group1.mean(), group1.std(ddof=1), len(group1)
    mean2, std2, n2 = group2.mean(), group2.std(ddof=1), len(group2)
    
    # Pooled standard deviation
    pooled_std = np.sqrt(((n1 - 1) * std1**2 + (n2 - 1) * std2**2) / (n1 + n2 - 2))
    
    if pooled_std == 0:
        return 0.0
        
    return (mean1 - mean2) / pooled_std


def perform_statistical_tests(
    benign_scores: pd.Series,
    novel_scores: pd.Series
) -> Dict[str, Any]:
    """
    Perform statistical tests to compare benign vs novel drift scores.
    
    Args:
        benign_scores: Drift scores for benign logs
        novel_scores: Drift scores for novel logs
        
    Returns:
        Dictionary containing p-value, effect size (Cohen's d), and test results
    """
    # Mann-Whitney U test (non-parametric)
    u_stat, p_value = stats.mannwhitneyu(
        benign_scores, novel_scores, 
        alternative='two-sided'
    )
    
    # Calculate effect size
    cohens_d = calculate_cohen_d(benign_scores, novel_scores)
    
    return {
        "test": "Mann-Whitney U",
        "statistic": float(u_stat),
        "p_value": float(p_value),
        "p_significant": bool(p_value < 0.05),
        "effect_size_cohen_d": float(cohens_d),
        "effect_size_threshold_met": bool(abs(cohens_d) >= 0.5),
        "benign_count": len(benign_scores),
        "novel_count": len(novel_scores),
        "benign_mean": float(benign_scores.mean()),
        "novel_mean": float(novel_scores.mean()),
        "benign_std": float(benign_scores.std()),
        "novel_std": float(novel_scores.std())
    }


def load_test_static_logs() -> pd.DataFrame:
    """
    Load the static test logs fixture.
    
    Returns:
        DataFrame containing test logs
    """
    path = get_path("data/test_static_logs.json")
    with open(path, 'r') as f:
        data = json.load(f)
    return pd.DataFrame(data)


def generate_mock_ground_truth(
    drift_scores_path: Optional[str] = None,
    output_path: Optional[str] = None,
    novel_ratio: float = 0.3,
    seed: int = 42
) -> pd.DataFrame:
    """
    Generate a synthetic but statistically valid ground truth dataset
    with known benign/novel labels for MVP testing of US-01.
    
    This function creates a mock ground truth by:
    1. Loading the drift scores from the pipeline output
    2. Stratifying the logs based on drift scores (high scores = novel, low = benign)
    3. Assigning labels according to a specified ratio
    4. Ensuring the distribution is statistically distinguishable
    
    Args:
        drift_scores_path: Path to the drift_scores.csv file (default: from config)
        output_path: Path to save the mock ground truth (default: from config)
        novel_ratio: Proportion of logs to label as novel (default: 0.3)
        seed: Random seed for reproducibility
        
    Returns:
        DataFrame with log_id, drift_score, and label columns
    """
    # Set seed for reproducibility
    np.random.seed(seed)
    
    # Load drift scores
    if drift_scores_path is None:
        drift_scores_path = get_path("data/processed/drift_scores.csv")
    
    if not os.path.exists(drift_scores_path):
        raise FileNotFoundError(
            f"Drift scores file not found at {drift_scores_path}. "
            "Please run the drift scoring pipeline first (T016)."
        )
    
    df = load_csv_file(drift_scores_path)
    
    # Validate required columns
    required_cols = ['log_id', 'drift_score']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")
    
    # Sort by drift score descending (higher = more novel)
    df_sorted = df.sort_values('drift_score', ascending=False).reset_index(drop=True)
    
    # Calculate split point for novel/benign
    novel_count = int(len(df_sorted) * novel_ratio)
    benign_count = len(df_sorted) - novel_count
    
    if novel_count == 0 or benign_count == 0:
        raise ValueError(
            f"Novel ratio {novel_ratio} results in zero samples in one class. "
            f"Total samples: {len(df_sorted)}"
        )
    
    # Assign labels: top N by drift score = novel, rest = benign
    df_sorted['label'] = ['novel'] * novel_count + ['benign'] * benign_count
    
    # Shuffle to make it look more realistic (but keep distribution)
    df_shuffled = df_sorted.sample(frac=1, random_state=seed).reset_index(drop=True)
    
    # Ensure output path exists
    if output_path is None:
        output_path = get_path("data/processed/mock_ground_truth.csv")
    
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save to CSV
    save_csv_file(df_shuffled, output_path)
    
    # Log statistics
    novel_scores = df_shuffled[df_shuffled['label'] == 'novel']['drift_score']
    benign_scores = df_shuffled[df_shuffled['label'] == 'benign']['drift_score']
    
    stats_result = perform_statistical_tests(benign_scores, novel_scores)
    
    print(f"Mock ground truth generated: {output_path}")
    print(f"  Total samples: {len(df_shuffled)}")
    print(f"  Novel samples: {novel_count} ({novel_ratio*100:.1f}%)")
    print(f"  Benign samples: {benign_count} ({(1-novel_ratio)*100:.1f}%)")
    print(f"  Novel mean drift score: {novel_scores.mean():.4f}")
    print(f"  Benign mean drift score: {benign_scores.mean():.4f}")
    print(f"  Cohen's d: {stats_result['effect_size_cohen_d']:.4f}")
    print(f"  P-value: {stats_result['p_value']:.6f}")
    print(f"  Statistically significant: {stats_result['p_significant']}")
    
    return df_shuffled


def main():
    """
    Main entry point for generating mock ground truth.
    """
    config = get_config()
    seed = config.get('random_seed', 42)
    novel_ratio = config.get('mock_novel_ratio', 0.3)
    
    print("Generating mock ground truth for US-01 MVP testing...")
    
    df = generate_mock_ground_truth(
        drift_scores_path=get_path("data/processed/drift_scores.csv"),
        output_path=get_path("data/processed/mock_ground_truth.csv"),
        novel_ratio=novel_ratio,
        seed=seed
    )
    
    print("Done.")


if __name__ == "__main__":
    main()