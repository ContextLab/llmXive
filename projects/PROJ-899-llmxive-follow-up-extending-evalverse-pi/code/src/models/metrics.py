"""
Metrics module for llmXive: Correlation, Bootstrap, and Permutation tests.

Implements FR-004 (Point Estimates) and FR-007 (Bootstrapping for CIs).
"""
import os
import sys
import json
import logging
import traceback
from typing import List, Tuple, Dict, Any, Optional
import numpy as np
import pandas as pd
from scipy.stats import pearsonr, spearmanr, bootstrap
from src.config import get_processed_data_dir, get_project_root
from src.utils import write_csv, read_json

logger = logging.getLogger(__name__)

def load_feature_vectors() -> Tuple[Dict[str, np.ndarray], Dict[str, np.ndarray], Dict[str, np.ndarray]]:
    """
    Load optical and audio feature vectors from JSON files.
    
    Returns:
        optical_data: Dict[clip_id, {"dimension": str, "feature_vector": list, "missing_data_flag": bool}]
        audio_data: Dict[clip_id, {"dimension": str, "feature_vector": list, "missing_data_flag": bool}]
        scores: Dict[clip_id, {"dimension": str, "human_score": float, "vlm_proxy_score": float}]
    """
    data_dir = get_processed_data_dir()
    
    # Load Optical
    optical_path = os.path.join(data_dir, "features_optical.json")
    if not os.path.exists(optical_path):
        raise FileNotFoundError(f"Optical features not found at {optical_path}. Run T012a first.")
    optical_data = read_json(optical_path)
    
    # Load Audio
    audio_path = os.path.join(data_dir, "features_audio.json")
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Audio features not found at {audio_path}. Run T013a first.")
    audio_data = read_json(audio_path)
    
    # Load Scores
    scores_path = os.path.join(data_dir, "scores.csv")
    if not os.path.exists(scores_path):
        raise FileNotFoundError(f"Scores not found at {scores_path}. Run T042 first.")
    scores_df = pd.read_csv(scores_path)
    scores = {}
    for _, row in scores_df.iterrows():
        scores[row['clip_id']] = {
            'dimension': row['dimension'],
            'human_score': row['human_score'],
            'vlm_proxy_score': row['vlm_proxy_score']
        }
        
    return optical_data, audio_data, scores

def load_human_scores() -> pd.DataFrame:
    """Load human scores from processed CSV."""
    scores_path = os.path.join(get_processed_data_dir(), "scores.csv")
    return pd.read_csv(scores_path)

def calculate_correlation_for_dimension(
    features: np.ndarray, 
    scores: np.ndarray
) -> Tuple[float, float]:
    """
    Calculate Pearson and Spearman correlation for a single dimension.
    
    Args:
        features: 1D array of feature values (or flattened composite).
        scores: 1D array of human scores.
        
    Returns:
        Tuple of (pearson_r, spearman_r)
    """
    # Remove NaNs/Infs
    mask = np.isfinite(features) & np.isfinite(scores)
    f_clean = features[mask]
    s_clean = scores[mask]
    
    if len(f_clean) < 3:
        return np.nan, np.nan
        
    p_r, _ = pearsonr(f_clean, s_clean)
    s_r, _ = spearmanr(f_clean, s_clean)
    
    return float(p_r), float(s_r)

def calculate_dimension_metrics(
    features: np.ndarray,
    scores: np.ndarray,
    n_resamples: int = 1000,
    random_state: int = 42
) -> Dict[str, float]:
    """
    Calculate point estimates and 95% CIs using stratified bootstrapping.
    
    Implements FR-007: Use scipy.stats.bootstrap with method="basic" and stratified sampling.
    
    Args:
        features: 1D array of feature values.
        scores: 1D array of human scores.
        n_resamples: Number of bootstrap resamples.
        random_state: Seed for reproducibility.
        
    Returns:
        Dict with pearson_r, spearman_r, lower_ci, upper_ci.
    """
    mask = np.isfinite(features) & np.isfinite(scores)
    f_clean = features[mask]
    s_clean = scores[mask]
    
    if len(f_clean) < 10:
        logger.warning(f"Insufficient samples ({len(f_clean)}) for bootstrapping. Returning NaNs.")
        return {
            'pearson_r': np.nan,
            'spearman_r': np.nan,
            'lower_ci': np.nan,
            'upper_ci': np.nan
        }

    # Define statistic functions for scipy.stats.bootstrap
    def pearson_stat(data, axis):
        # data is (N, 2) where col 0 is feature, col 1 is score
        x = data[:, 0]
        y = data[:, 1]
        if len(x) < 3:
            return np.nan
        r, _ = pearsonr(x, y)
        return r

    def spearman_stat(data, axis):
        x = data[:, 0]
        y = data[:, 1]
        if len(x) < 3:
            return np.nan
        r, _ = spearmanr(x, y)
        return r

    # Prepare data: stack features and scores
    combined_data = np.column_stack((f_clean, s_clean))
    
    # Stratified Sampling Strategy:
    # To ensure stratification, we resample indices based on score quantiles (bins).
    # We create bins based on the score distribution and ensure each resample
    # maintains the bin proportions.
    # However, scipy.stats.bootstrap does not natively support custom stratification
    # in the 'method' argument directly for arbitrary functions in older versions.
    # We implement a manual stratified bootstrap loop to satisfy the strict requirement.
    
    n = len(f_clean)
    # Create 4 strata based on score quantiles
    quantiles = np.quantile(s_clean, [0.25, 0.5, 0.75])
    strata = np.digitize(s_clean, quantiles)
    
    pearson_ci = []
    spearman_ci = []
    
    # Manual Stratified Bootstrap
    rng = np.random.default_rng(random_state)
    unique_strata = np.unique(strata)
    strata_counts = {s: np.sum(strata == s) for s in unique_strata}
    
    for _ in range(n_resamples):
        # Resample indices within each stratum
        resample_indices = []
        for s in unique_strata:
            count = strata_counts[s]
            strata_indices = np.where(strata == s)[0]
            # Sample with replacement from this stratum
            sampled = rng.choice(strata_indices, size=count, replace=True)
            resample_indices.extend(sampled)
        
        resample_indices = np.array(resample_indices)
        boot_features = f_clean[resample_indices]
        boot_scores = s_clean[resample_indices]
        
        # Calculate stats
        if len(boot_features) < 3:
            continue
            
        p_r, _ = pearsonr(boot_features, boot_scores)
        s_r, _ = spearmanr(boot_features, boot_scores)
        
        if np.isfinite(p_r):
            pearson_ci.append(p_r)
        if np.isfinite(s_r):
            spearman_ci.append(s_r)
    
    pearson_ci = np.array(pearson_ci)
    spearman_ci = np.array(spearman_ci)
    
    # Calculate Basic Bootstrap CI (2.5%, 97.5%)
    # Note: Basic CI = 2*theta_hat - percentile
    # But standard practice often uses percentile method for simplicity in "basic" context
    # unless "basic" strictly implies the bias-corrected inversion. 
    # The prompt asks for "method='basic'". scipy.stats.bootstrap 'basic' method uses:
    # CI = 2*theta - q_{1-alpha/2}, 2*theta - q_{alpha/2}
    # We will compute the percentiles of the bootstrap distribution.
    
    if len(pearson_ci) == 0:
        return {
            'pearson_r': np.nan,
            'spearman_r': np.nan,
            'lower_ci': np.nan,
            'upper_ci': np.nan
        }
        
    # Point estimates
    p_point, _ = pearsonr(f_clean, s_clean)
    s_point, _ = spearmanr(f_clean, s_clean)
    
    # Percentiles for Basic CI calculation
    # Basic CI: [2*theta - q_{1-alpha/2}, 2*theta - q_{alpha/2}]
    # where q is the quantile of the bootstrap distribution
    lower_p = 2 * p_point - np.percentile(pearson_ci, 97.5)
    upper_p = 2 * p_point - np.percentile(pearson_ci, 2.5)
    
    lower_s = 2 * s_point - np.percentile(spearman_ci, 97.5)
    upper_s = 2 * s_point - np.percentile(spearman_ci, 2.5)
    
    return {
        'pearson_r': float(p_point),
        'spearman_r': float(s_point),
        'lower_ci': float(lower_p), # Using Pearson for CI as primary metric
        'upper_ci': float(upper_p)
    }

def main():
    """
    Main entry point for T016b: Bootstrapping for 95% CIs.
    
    Loads features from T012a/T013a, calculates correlations with stratified bootstrap,
    and writes data/processed/correlations.csv.
    """
    logging.basicConfig(level=logging.INFO)
    logger.info("Starting T016b: Bootstrapping for 95% CIs")
    
    try:
        # Load Data
        optical_data, audio_data, scores = load_feature_vectors()
        human_scores_df = load_human_scores()
        
        # Get unique dimensions
        dimensions = human_scores_df['dimension'].unique()
        
        results = []
        
        for dim in dimensions:
            logger.info(f"Processing dimension: {dim}")
            
            # Collect features and scores for this dimension
            # We concatenate optical and audio features? 
            # T016a/B usually work on the combined feature set or per-modality.
            # Given the task description "stratified sampling on the raw feature arrays from T012a/T013a",
            # and T015 trains on combined, we assume we are evaluating the final model's input.
            # However, T016a/B specifically mention calculating correlation. 
            # Let's assume we are correlating the *combined* feature vector (or a specific modality if specified).
            # Since T015 trains on combined, let's use the combined feature vector.
            # But T012a/T013a produce separate JSONs. 
            # We need to reconstruct the combined feature vector used in T015.
            # Assumption: T015 concatenated optical and audio.
            # We will do the same here: optical + audio.
            
            dim_features = []
            dim_scores = []
            clip_ids = []
            
            for clip_id in optical_data:
                if optical_data[clip_id]['dimension'] != dim:
                    continue
                if optical_data[clip_id]['missing_data_flag']:
                    continue
                if clip_id not in scores:
                    continue
                
                opt_vec = np.array(optical_data[clip_id]['feature_vector'])
                aud_vec = np.array(audio_data[clip_id]['feature_vector'])
                
                # Concatenate
                combined_vec = np.concatenate([opt_vec, aud_vec])
                # Use mean or first principal component? 
                # T015 likely used the full vector. Correlation with a vector is not defined.
                # We must reduce the vector to a scalar to correlate with a scalar score.
                # Standard approach: Predict the score using a model and correlate PREDICTED vs ACTUAL?
                # OR correlate each feature? No, the task says "correlation calculation".
                # Re-reading T016a: "calculate point estimates".
                # Usually, this means Correlation(Feature, Score). If Feature is a vector, we need a scalar summary.
                # Let's assume we are correlating the *predicted* score from the T015 model vs Human Score.
                # But T015 models are saved as joblib.
                # Alternative: The task might imply correlating the *aggregate* feature (e.g., mean of vector).
                # Given the ambiguity, and the requirement to use "raw feature arrays", 
                # let's assume we are calculating the correlation of the *first* feature (or mean) as a proxy,
                # OR we load the T015 model and predict.
                # Let's look at T015: "targeting human expert scores".
                # The most rigorous interpretation: Correlation(Predicted_Score, Human_Score).
                # But T016a/B are in "metrics", before T017 (Viability).
                # Let's assume the "feature" is the *sum* or *mean* of the vector for this specific task,
                # OR we load the model.
                # Let's try to load the model from T015.
                pass

            # Fallback: If models are not loaded, we cannot correlate a vector to a scalar.
            # We will assume the task implies correlating the *mean* of the feature vector 
            # as a simple baseline, OR we load the Ridge model.
            # Let's implement loading the Ridge model for the dimension.
            
            model_path = os.path.join(get_project_root(), "data", "models", f"{dim}_ridge.joblib")
            if os.path.exists(model_path):
                import joblib
                model = joblib.load(model_path)
                # We need X (features) to predict
                X_list = []
                y_list = []
                for clip_id in scores:
                    if scores[clip_id]['dimension'] != dim:
                        continue
                    if clip_id in optical_data and not optical_data[clip_id]['missing_data_flag']:
                        opt_vec = np.array(optical_data[clip_id]['feature_vector'])
                        aud_vec = np.array(audio_data[clip_id]['feature_vector'])
                        combined = np.concatenate([opt_vec, aud_vec])
                        X_list.append(combined)
                        y_list.append(scores[clip_id]['human_score'])
                
                if len(X_list) == 0:
                    logger.warning(f"No data for dimension {dim}")
                    continue
                    
                X = np.array(X_list)
                y = np.array(y_list)
                
                # Predict
                y_pred = model.predict(X)
                
                # Calculate Correlation between Predicted and Human
                p_r, _ = pearsonr(y_pred, y)
                s_r, _ = spearmanr(y_pred, y)
                
                # Bootstrap on the residuals or the pairs (y_pred, y)?
                # Bootstrap the pairs (y_pred, y) to get CI on correlation.
                combined_pairs = np.column_stack((y_pred, y))
                
                # Stratified Bootstrap on Pairs (stratify by y quantiles)
                n = len(y)
                quantiles = np.quantile(y, [0.25, 0.5, 0.75])
                strata = np.digitize(y, quantiles)
                unique_strata = np.unique(strata)
                strata_counts = {s: np.sum(strata == s) for s in unique_strata}
                
                boot_r = []
                rng = np.random.default_rng(42)
                
                for _ in range(1000):
                    indices = []
                    for s in unique_strata:
                        count = strata_counts[s]
                        idx = np.where(strata == s)[0]
                        sampled = rng.choice(idx, size=count, replace=True)
                        indices.extend(sampled)
                    indices = np.array(indices)
                    boot_pred = combined_pairs[indices, 0]
                    boot_true = combined_pairs[indices, 1]
                    r, _ = pearsonr(boot_pred, boot_true)
                    if np.isfinite(r):
                        boot_r.append(r)
                
                boot_r = np.array(boot_r)
                if len(boot_r) > 0:
                    lower = 2 * p_r - np.percentile(boot_r, 97.5)
                    upper = 2 * p_r - np.percentile(boot_r, 2.5)
                else:
                    lower = upper = np.nan
                
                results.append({
                    'dimension': dim,
                    'pearson_r': p_r,
                    'spearman_r': s_r,
                    'lower_ci': lower,
                    'upper_ci': upper
                })
            else:
                logger.warning(f"Model for {dim} not found, skipping.")

        # Write Output
        output_path = os.path.join(get_processed_data_dir(), "correlations.csv")
        df = pd.DataFrame(results)
        write_csv(output_path, df)
        logger.info(f"Written {output_path}")
        
    except Exception as e:
        logger.error(f"Error in T016b: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()