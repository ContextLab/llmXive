"""
Virtual Cohort Matching and Distributional Comparison Fallback.

Implements Path A (Nearest-Neighbor Matching) with fallback to Propensity Score
matching. If both fail to produce >=10 pairs, switches to Path B (Distributional
Comparison) by splitting data into High/Low abundance groups.
"""
import os
import sys
import logging
import warnings
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
import pandas as pd
from sklearn.neighbors import NearestNeighbors
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from scipy.stats import median_abs_deviation

# Local imports matching existing API surface
from config import get_project_root, load_config
from logging_config import get_logger, log_structured_event, flush_yaml_logs
from seed_manager import get_seed, set_seed

# Suppress specific warnings for cleaner logs
warnings.filterwarnings('ignore', category=FutureWarning)
warnings.filterwarnings('ignore', category=UserWarning)

def load_processed_data() -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Load preprocessed microbiome and EEG feature DataFrames.
    Returns:
        Tuple of (microbiome_df, eeg_df)
    """
    root = get_project_root()
    microbiome_path = root / "data" / "processed" / "microbiome_features.csv"
    eeg_path = root / "data" / "processed" / "eeg_features.csv"

    if not microbiome_path.exists():
        raise FileNotFoundError(f"Microbiome features not found at {microbiome_path}. Run preprocess_microbiome.py first.")
    if not eeg_path.exists():
        raise FileNotFoundError(f"EEG features not found at {eeg_path}. Run preprocess_eeg.py first.")

    logger = get_logger("match_cohorts")
    logger.info(f"Loading microbiome data from {microbiome_path}")
    logger.info(f"Loading EEG data from {eeg_path}")

    df_micro = pd.read_csv(microbiome_path)
    df_eeg = pd.read_csv(eeg_path)

    # Ensure metadata columns exist
    required_cols = ['subject_id', 'age', 'sex', 'bmi']
    for col in required_cols:
        if col not in df_micro.columns:
            # Try to infer from common naming variations if needed, but strict check first
            raise ValueError(f"Microbiome data missing required column: {col}")
        if col not in df_eeg.columns:
            raise ValueError(f"EEG data missing required column: {col}")

    logger.info(f"Loaded {len(df_micro)} microbiome subjects and {len(df_eeg)} EEG subjects")
    return df_micro, df_eeg

def prepare_features(df_micro: pd.DataFrame, df_eeg: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Prepare feature matrices for matching.
    Standardizes Age, BMI, and one-hot encodes Sex.
    Returns:
        X_micro, X_eeg, idx_micro, idx_eeg
    """
    logger = get_logger("match_cohorts")
    
    # One-hot encode Sex
    df_micro['sex_encoded'] = df_micro['sex'].apply(lambda x: 1 if x in ['M', 'Male', '1'] else 0)
    df_eeg['sex_encoded'] = df_eeg['sex'].apply(lambda x: 1 if x in ['M', 'Male', '1'] else 0)

    feature_cols = ['age', 'bmi', 'sex_encoded']
    
    X_micro = df_micro[feature_cols].values.astype(float)
    X_eeg = df_eeg[feature_cols].values.astype(float)
    
    # Handle potential NaNs by dropping rows (should be rare after preprocessing)
    mask_micro = ~np.isnan(X_micro).any(axis=1)
    mask_eeg = ~np.isnan(X_eeg).any(axis=1)
    
    X_micro_clean = X_micro[mask_micro]
    X_eeg_clean = X_eeg[mask_eeg]
    idx_micro = df_micro[mask_micro]['subject_id'].values
    idx_eeg = df_eeg[mask_eeg]['subject_id'].values

    # Standardize features
    scaler = StandardScaler()
    X_micro_scaled = scaler.fit_transform(X_micro_clean)
    X_eeg_scaled = scaler.transform(X_eeg_clean)

    logger.info(f"Prepared features: Microbiome ({X_micro_scaled.shape[0]}), EEG ({X_eeg_scaled.shape[0]})")
    return X_micro_scaled, X_eeg_scaled, idx_micro, idx_eeg

def nearest_neighbor_matching(X_source: np.ndarray, X_target: np.ndarray, 
                              idx_source: np.ndarray, idx_target: np.ndarray,
                              n_neighbors: int = 1) -> Optional[pd.DataFrame]:
    """
    Perform Nearest-Neighbor matching from Source (Microbiome) to Target (EEG).
    Returns a DataFrame of matched pairs if >= 10 pairs found, else None.
    """
    logger = get_logger("match_cohorts")
    logger.info(f"Running Nearest-Neighbor matching (k={n_neighbors})")

    if len(X_target) < n_neighbors:
        logger.warning("Target dataset too small for requested neighbors.")
        return None

    try:
        nn = NearestNeighbors(n_neighbors=n_neighbors, algorithm='auto', metric='euclidean')
        nn.fit(X_target)
        distances, indices = nn.kneighbors(X_source)
    except Exception as e:
        logger.error(f"Nearest-Neighbor matching failed: {e}")
        return None

    # Extract pairs
    pairs = []
    for i, target_idx_list in enumerate(indices):
        source_id = idx_source[i]
        target_id = idx_target[target_idx_list[0]] # 1:1 matching
        dist = distances[i][0]
        pairs.append({
            'microbiome_subject_id': source_id,
            'eeg_subject_id': target_id,
            'distance': dist
        })

    df_pairs = pd.DataFrame(pairs)
    
    # Filter based on distance threshold (optional, but good practice)
    # Using a heuristic: if distance > 3.0, it's a poor match
    threshold = 3.0 * np.std(df_pairs['distance'])
    valid_pairs = df_pairs[df_pairs['distance'] < threshold]
    
    logger.info(f"Found {len(valid_pairs)} valid pairs (threshold={threshold:.2f})")
    
    if len(valid_pairs) >= 10:
        return valid_pairs
    else:
        return None

def propensity_score_matching(df_micro: pd.DataFrame, df_eeg: pd.DataFrame,
                              idx_micro: np.ndarray, idx_eeg: np.ndarray) -> Optional[pd.DataFrame]:
    """
    Fallback: Propensity Score Matching.
    Estimates probability of being in the 'Microbiome' group based on demographics,
    then matches based on propensity scores.
    """
    logger = get_logger("match_cohorts")
    logger.info("Running Propensity Score matching (fallback)")

    # Combine data with labels
    df_micro['group'] = 1
    df_eeg['group'] = 0
    df_micro['subject_id'] = idx_micro
    df_eeg['subject_id'] = idx_eeg
    
    # Ensure consistent columns
    common_cols = ['age', 'bmi', 'sex_encoded', 'group', 'subject_id']
    df_combined = pd.concat([df_micro[common_cols], df_eeg[common_cols]], ignore_index=True)
    
    # Handle NaNs
    df_combined = df_combined.dropna()
    
    if len(df_combined) < 20:
        logger.warning("Insufficient data for propensity score matching.")
        return None

    X = df_combined[['age', 'bmi', 'sex_encoded']].values
    y = df_combined['group'].values

    try:
        clf = LogisticRegression(random_state=get_seed(), max_iter=1000)
        clf.fit(X, y)
        probs = clf.predict_proba(X)[:, 1]
        df_combined['propensity'] = probs
    except Exception as e:
        logger.error(f"Propensity Score model training failed: {e}")
        return None

    # Match: For each Microbiome subject, find nearest EEG subject in propensity space
    df_micro_matched = df_combined[df_combined['group'] == 1].sort_values('propensity')
    df_eeg_matched = df_combined[df_combined['group'] == 0].sort_values('propensity')

    pairs = []
    matched_eeg_ids = set()
    
    # Simple greedy matching
    for _, row_m in df_micro_matched.iterrows():
        # Find closest unmatched EEG subject
        diffs = np.abs(df_eeg_matched['propensity'] - row_m['propensity'])
        best_idx = diffs.idxmin()
        if best_idx not in matched_eeg_ids:
            pairs.append({
                'microbiome_subject_id': row_m['subject_id'],
                'eeg_subject_id': df_eeg_matched.loc[best_idx, 'subject_id'],
                'distance': diffs[best_idx]
            })
            matched_eeg_ids.add(best_idx)
    
    df_pairs = pd.DataFrame(pairs)
    logger.info(f"Propensity Score matching found {len(df_pairs)} pairs")

    if len(df_pairs) >= 10:
        return df_pairs
    return None

def create_distribution_groups(df_micro: pd.DataFrame, df_eeg: pd.DataFrame) -> pd.DataFrame:
    """
    Path B: Create Distributional Comparison groups.
    Splits Microbiome data into High/Low abundance groups based on top taxa.
    Assigns EEG subjects to these groups based on demographic similarity or random.
    """
    logger = get_logger("match_cohorts")
    logger.info("Switching to Path B: Distributional Comparison")

    # Identify top 20 taxa by mean abundance
    # Assuming columns starting with 'taxa_' or similar, or just numeric cols
    # Heuristic: columns that are not metadata
    metadata_cols = ['subject_id', 'age', 'sex', 'bmi', 'sex_encoded']
    taxa_cols = [c for c in df_micro.columns if c not in metadata_cols]
    
    if not taxa_cols:
        logger.error("No taxa columns found in microbiome data.")
        raise ValueError("No taxa columns found.")

    # Compute mean abundance per taxon
    mean_abundances = df_micro[taxa_cols].mean()
    top_20_taxa = mean_abundances.nlargest(20).index.tolist()
    
    # Calculate composite score for each subject (mean of top 20)
    df_micro['microbiome_score'] = df_micro[top_20_taxa].mean(axis=1)
    
    # Median split
    median_score = df_micro['microbiome_score'].median()
    df_micro['group'] = df_micro['microbiome_score'].apply(lambda x: 'High' if x >= median_score else 'Low')
    
    logger.info(f"Split into High (n={len(df_micro[df_micro['group']=='High'])}) and Low (n={len(df_micro[df_micro['group']=='Low'])}) groups")

    # Assign EEG subjects to groups based on demographic similarity
    # We will assign them randomly if no strong link, but try to balance demographics
    # Simple approach: Random assignment to match the ratio of High/Low in Microbiome
    n_high = len(df_micro[df_micro['group'] == 'High'])
    n_low = len(df_micro[df_micro['group'] == 'Low'])
    total_micro = n_high + n_low
    
    if total_micro == 0:
        raise ValueError("No microbiome subjects to define groups.")

    prob_high = n_high / total_micro
    
    rng = np.random.default_rng(get_seed())
    groups = rng.choice(['High', 'Low'], size=len(df_eeg), p=[prob_high, 1-prob_high])
    
    df_eeg['group'] = groups
    
    result = pd.DataFrame({
        'subject_id': df_eeg['subject_id'],
        'group': df_eeg['group'],
        'source': 'eeg'
    })
    
    # Also include microbiome subjects for completeness in the group file
    micro_result = pd.DataFrame({
        'subject_id': df_micro['subject_id'],
        'group': df_micro['group'],
        'source': 'microbiome'
    })
    
    full_groups = pd.concat([result, micro_result], ignore_index=True)
    return full_groups

def main():
    """
    Main execution flow for T014.
    1. Load data.
    2. Try Nearest-Neighbor Matching (Path A).
    3. If <10 pairs, try Propensity Score Matching.
    4. If still <10 pairs, switch to Distributional Comparison (Path B).
    5. Write output files.
    """
    seed = get_seed()
    set_seed(seed)
    logger = get_logger("match_cohorts")
    
    log_structured_event(
        event="match_cohorts_start",
        seed=seed,
        path="code/match_cohorts.py"
    )

    try:
        # Load Data
        df_micro, df_eeg = load_processed_data()
        
        # Prepare Features
        X_micro, X_eeg, idx_micro, idx_eeg = prepare_features(df_micro, df_eeg)

        # Path A: Nearest-Neighbor
        matched_pairs = nearest_neighbor_matching(X_micro, X_eeg, idx_micro, idx_eeg)
        
        if matched_pairs is not None and len(matched_pairs) >= 10:
            # Success Path A
            root = get_project_root()
            out_path = root / "data" / "processed" / "matched_pairs.csv"
            matched_pairs.to_csv(out_path, index=False)
            
            log_structured_event(
                event="path_a_selected",
                method="nearest_neighbor",
                n_pairs=len(matched_pairs),
                output_file=str(out_path)
            )
            logger.info(f"Path A Selected: Virtual Cohort Matching successful (N={len(matched_pairs)})")
            print(f"Success: {len(matched_pairs)} matched pairs written to {out_path}")
            sys.exit(0)

        # Fallback: Propensity Score
        logger.info("Nearest-Neighbor failed to find sufficient pairs. Attempting Propensity Score.")
        matched_pairs = propensity_score_matching(df_micro, df_eeg, idx_micro, idx_eeg)
        
        if matched_pairs is not None and len(matched_pairs) >= 10:
            root = get_project_root()
            out_path = root / "data" / "processed" / "matched_pairs.csv"
            matched_pairs.to_csv(out_path, index=False)
            
            log_structured_event(
                event="path_a_selected",
                method="propensity_score",
                n_pairs=len(matched_pairs),
                output_file=str(out_path)
            )
            logger.info(f"Path A Selected: Virtual Cohort Matching successful (N={len(matched_pairs)}) via Propensity Score")
            print(f"Success: {len(matched_pairs)} matched pairs written to {out_path}")
            sys.exit(0)

        # Path B: Distributional Comparison
        logger.info("Both matching methods failed (<10 pairs). Switching to Path B.")
        distribution_groups = create_distribution_groups(df_micro, df_eeg)
        
        root = get_project_root()
        out_path = root / "data" / "processed" / "distribution_groups.csv"
        distribution_groups.to_csv(out_path, index=False)
        
        log_structured_event(
            event="path_b_selected",
            n_microbiome=len(df_micro),
            n_eeg=len(df_eeg),
            output_file=str(out_path)
        )
        logger.info(f"Path B Selected: Insufficient matches. Switching to Distributional Comparison. Output: {out_path}")
        print(f"Success: Distribution groups written to {out_path}")
        sys.exit(0)

    except Exception as e:
        logger.error(f"Critical error in match_cohorts: {e}", exc_info=True)
        log_structured_event(
            event="match_cohorts_failed",
            error=str(e)
        )
        sys.exit(1)
    finally:
        flush_yaml_logs()

if __name__ == "__main__":
    main()
