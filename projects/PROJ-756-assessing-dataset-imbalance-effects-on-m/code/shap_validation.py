import os
import sys
import json
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from scipy import stats

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_ground_truth(filepath: str) -> pd.DataFrame:
    """
    Load the synthetic ground truth dataset containing known_weights.
    
    Args:
        filepath: Path to the ground truth parquet file.
        
    Returns:
        DataFrame with 'known_weights' column.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Ground truth file not found: {filepath}")
    
    logger.info(f"Loading ground truth from {filepath}")
    df = pd.read_parquet(filepath)
    
    if 'known_weights' not in df.columns:
        raise ValueError(f"Ground truth file missing 'known_weights' column. Columns: {df.columns.tolist()}")
    
    return df

def load_rank_shift(filepath: str) -> pd.DataFrame:
    """
    Load the rank shift analysis results.
    
    Args:
        filepath: Path to the rank shift CSV file.
        
    Returns:
        DataFrame with feature ranking data.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Rank shift file not found: {filepath}")
    
    logger.info(f"Loading rank shift data from {filepath}")
    df = pd.read_csv(filepath)
    
    required_cols = ['feature', 'rank_skewed', 'rank_balanced', 'rank_shift']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Rank shift file missing columns: {missing_cols}")
    
    return df

def compute_rank_weight_correlation(rank_shift_df: pd.DataFrame, known_weights: np.ndarray) -> dict:
    """
    Compute the correlation between rank shift magnitude and the absolute known weight.
    
    The hypothesis is that features with higher known weights (more important in ground truth)
    should have smaller rank shifts (more stable rankings) between skewed and balanced models.
    
    Args:
        rank_shift_df: DataFrame with rank shift data.
        known_weights: Array of known weights corresponding to features.
        
    Returns:
        Dictionary with correlation statistics.
    """
    # Ensure alignment: rank_shift_df features should match known_weights order
    # We assume the order in rank_shift_df matches the order of features in known_weights
    # If feature names are available, we should match by name, but here we assume positional alignment
    
    if len(rank_shift_df) != len(known_weights):
        logger.warning(f"Feature count mismatch: rank_shift has {len(rank_shift_df)}, known_weights has {len(known_weights)}. Attempting to match by index.")
        # Truncate to the minimum length
        min_len = min(len(rank_shift_df), len(known_weights))
        rank_shift_df = rank_shift_df.iloc[:min_len]
        known_weights = known_weights[:min_len]
    
    # Use absolute values of known weights for correlation
    abs_weights = np.abs(known_weights)
    rank_shift_magnitudes = np.abs(rank_shift_df['rank_shift'].values)
    
    # Pearson correlation
    correlation, p_value = stats.pearsonr(abs_weights, rank_shift_magnitudes)
    
    # Spearman correlation (rank-based, more robust to outliers)
    spearman_corr, spearman_p = stats.spearmanr(abs_weights, rank_shift_magnitudes)
    
    return {
        'pearson_correlation': float(correlation),
        'pearson_p_value': float(p_value),
        'spearman_correlation': float(spearman_corr),
        'spearman_p_value': float(spearman_p),
        'interpretation': 'Negative correlation expected: higher weights -> lower rank shift'
    }

def compute_top_k_overlap(rank_shift_df: pd.DataFrame, k: int = 10) -> dict:
    """
    Compute the overlap of top-K features by known weight vs top-K by rank stability (lowest shift).
    
    Args:
        rank_shift_df: DataFrame with rank shift data.
        k: Number of top features to consider.
        
    Returns:
        Dictionary with overlap statistics.
    """
    # Top K by known weight (assuming known_weights are passed in order)
    # We need to reconstruct known_weights from the ground truth
    # This function assumes the order in rank_shift_df matches the order of known_weights
    # We'll return a placeholder for known_weights to be passed from main
    
    # Sort by rank_shift (ascending, most stable first)
    top_k_stable = rank_shift_df.nsmallest(k, 'rank_shift')['feature'].tolist()
    
    # We cannot compute top_k_weight here without known_weights
    # This will be handled in main
    return {
        'top_k_stable_features': top_k_stable,
        'k': k,
        'note': 'Top K by weight requires known_weights array'
    }

def generate_validation_summary(
    ground_truth_df: pd.DataFrame,
    rank_shift_df: pd.DataFrame,
    output_path: str
) -> dict:
    """
    Generate the complete validation summary comparing SHAP rankings to ground truth.
    
    Args:
        ground_truth_df: DataFrame with known_weights.
        rank_shift_df: DataFrame with rank shift analysis.
        output_path: Path to save the JSON summary.
        
    Returns:
        Dictionary containing the validation summary.
    """
    known_weights = ground_truth_df['known_weights'].values
    
    # Correlation analysis
    correlation_stats = compute_rank_weight_correlation(rank_shift_df, known_weights)
    
    # Top K overlap analysis
    top_k_analysis = compute_top_k_overlap(rank_shift_df, k=10)
    # Manually compute top K by weight for the summary
    top_k_weight_features = rank_shift_df.nlargest(10, 'feature').index.tolist() if False else []
    # Since we don't have a direct mapping of feature name to weight index in rank_shift_df
    # (it just has 'feature' as string), we assume the order in rank_shift_df matches known_weights
    # We'll create a temporary dataframe with weights
    temp_df = rank_shift_df.copy()
    temp_df['known_weight'] = known_weights
    top_k_weight_features = temp_df.nlargest(10, 'known_weight')['feature'].tolist()
    top_k_stable_features = temp_df.nsmallest(10, 'rank_shift')['feature'].tolist()
    
    overlap = len(set(top_k_weight_features) & set(top_k_stable_features))
    overlap_pct = (overlap / 10) * 100
    
    # Summary statistics
    summary = {
        'validation_status': 'completed',
        'total_features_analyzed': len(rank_shift_df),
        'correlation_analysis': correlation_stats,
        'top_k_overlap_analysis': {
            'k': 10,
            'top_k_by_weight': top_k_weight_features,
            'top_k_by_stability': top_k_stable_features,
            'overlap_count': overlap,
            'overlap_percentage': overlap_pct,
            'interpretation': f'{overlap_pct:.1f}% of top-10 important features (by weight) are also the most stable (lowest rank shift).'
        },
        'rank_shift_statistics': {
            'mean_rank_shift': float(rank_shift_df['rank_shift'].mean()),
            'median_rank_shift': float(rank_shift_df['rank_shift'].median()),
            'std_rank_shift': float(rank_shift_df['rank_shift'].std()),
            'max_rank_shift': float(rank_shift_df['rank_shift'].max()),
            'min_rank_shift': float(rank_shift_df['rank_shift'].min())
        },
        'conclusion': (
            f"Validation complete. Features with higher ground-truth weights show "
            f"{'stronger' if correlation_stats['pearson_correlation'] < -0.3 else 'weaker'} "
            f"stability (correlation: {correlation_stats['pearson_correlation']:.3f}). "
            f"Top-10 overlap: {overlap_pct:.1f}%."
        )
    }
    
    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    # Save to JSON
    with open(output_path, 'w') as f:
        json.dump(summary, f, indent=2)
    
    logger.info(f"Validation summary saved to {output_path}")
    return summary

def main():
    """Main entry point for T039: SHAP validation against synthetic ground truth."""
    # Define paths relative to project root
    project_root = Path(__file__).resolve().parent.parent
    ground_truth_path = project_root / 'data' / 'synthetic' / 'ground_truth.parquet'
    rank_shift_path = project_root / 'results' / 'shap_analysis' / 'rank_shift.csv'
    output_path = project_root / 'results' / 'shap_analysis' / 'shap_validation.json'
    
    logger.info("Starting T039: SHAP validation against synthetic ground truth")
    
    try:
        # Load data
        ground_truth_df = load_ground_truth(str(ground_truth_path))
        rank_shift_df = load_rank_shift(str(rank_shift_path))
        
        # Generate validation summary
        summary = generate_validation_summary(
            ground_truth_df,
            rank_shift_df,
            str(output_path)
        )
        
        logger.info("T039 completed successfully")
        print(json.dumps(summary, indent=2))
        
    except FileNotFoundError as e:
        logger.error(f"Data file not found: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Data validation error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during validation: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()