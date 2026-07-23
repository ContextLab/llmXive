import numpy as np
import pandas as pd
import logging
import os
import json
from pathlib import Path
from typing import List, Tuple, Dict, Optional
from rdkit import DataStructs
from rdkit.Chem import AllChem, MACCSkeys
from rdkit import Chem

# Import constants from project constants
try:
    from constants import TANIMOTO_THRESHOLD, MORGAN_RADIUS, MORGAN_BITS, MACCS_BITS, N_FOLDS
except ImportError:
    # Fallback if constants not imported (should be handled by task T006)
    TANIMOTO_THRESHOLD = 0.85
    MORGAN_RADIUS = 2
    MORGAN_BITS = 2048
    MACCS_BITS = 166
    N_FOLDS = 5

# Import utils for logging
try:
    from utils import setup_logging, get_logger, init_random_seed
except ImportError:
    # Fallback if utils not available
    def setup_logging():
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    def get_logger(name):
        return logging.getLogger(name)

    def init_random_seed(seed=42):
        import random
        random.seed(seed)
        np.random.seed(seed)

def load_fingerprints(input_path: str, fingerprint_type: str = 'morgan') -> Tuple[pd.DataFrame, List]:
    """
    Load fingerprints from a processed CSV file.
    Expects columns: 'smiles', 'morgan_fp' (or 'maccs_fp'), and toxicity labels.
    Returns DataFrame and list of RDKit fingerprint objects.
    """
    logger = get_logger(__name__)
    df = pd.read_csv(input_path)
    
    fp_col = 'morgan_fp' if fingerprint_type == 'morgan' else 'maccs_fp'
    
    if fp_col not in df.columns:
        raise ValueError(f"Column '{fp_col}' not found in {input_path}. Available: {df.columns.tolist()}")
    
    fps = []
    for i, row in df.iterrows():
        # Assuming fingerprints are stored as numpy arrays or lists in the CSV
        # If stored as strings, we need to convert them back
        fp_data = row[fp_col]
        if isinstance(fp_data, str):
            # Convert string representation back to numpy array
            fp_arr = np.fromstring(fp_data.strip('[]'), sep=',')
        else:
            fp_arr = np.array(fp_data)
        
        # Reconstruct RDKit fingerprint
        if fingerprint_type == 'morgan':
            fp = DataStructs.ExplicitBitVect(MORGAN_BITS)
            for bit in np.where(fp_arr > 0)[0]:
                fp.SetBit(int(bit))
        else:
            fp = DataStructs.ExplicitBitVect(MACCS_BITS)
            for bit in np.where(fp_arr > 0)[0]:
                fp.SetBit(int(bit))
        
        fps.append(fp)
    
    logger.info(f"Loaded {len(fps)} fingerprints from {input_path}")
    return df, fps

def greedy_maximal_dissimilarity_split(
    fingerprints: List, 
    n_folds: int = 5, 
    threshold: float = TANIMOTO_THRESHOLD,
    min_test_size: int = 20
) -> Dict[int, Dict[str, List[int]]]:
    """
    Execute Greedy Maximal Dissimilarity Split for each of n_folds.
    
    Algorithm:
    1. Initialize test set with the compound furthest from the mean.
    2. Iterate through remaining compounds, selecting the one with max min-distance 
       to current test set.
    3. Add to test set if distance > threshold (Tanimoto < 1 - threshold).
       Note: Tanimoto similarity < threshold implies distance > 1 - threshold.
       However, the task specifies "Add to test set if distance > threshold".
       In Tanimoto terms, distance = 1 - similarity. So we want 1 - sim > threshold?
       Actually, the task says "Tanimoto < 0.85". So we select points where 
       Tanimoto similarity to ALL current test set members is < 0.85.
       This is equivalent to min_similarity < threshold.
    
    Returns: Dict mapping fold_id -> {'train': [...], 'test': [...]}
    """
    logger = get_logger(__name__)
    n_samples = len(fingerprints)
    all_indices = list(range(n_samples))
    
    # Precompute Tanimoto similarities for efficiency (symmetric matrix)
    # Since N might be large, we compute on demand or in chunks if needed.
    # For now, assuming N is manageable.
    logger.info(f"Precomputing similarity matrix for {n_samples} compounds...")
    sim_matrix = np.zeros((n_samples, n_samples))
    for i in range(n_samples):
        for j in range(i, n_samples):
            if i == j:
                sim_matrix[i, j] = 1.0
            else:
                sim = DataStructs.TanimotoSimilarity(fingerprints[i], fingerprints[j])
                sim_matrix[i, j] = sim
                sim_matrix[j, i] = sim
    
    splits = {}
    
    for fold in range(n_folds):
        logger.info(f"Processing fold {fold + 1}/{n_folds}")
        
        # For each fold, we need to create a new split.
        # To ensure diversity across folds, we might shuffle or rotate.
        # However, the task implies a standard 5-fold split where each fold has a test set.
        # We will simulate a 5-fold split by selecting a test set for each fold
        # from the remaining data, ensuring the test set meets the criteria.
        
        # For simplicity in this implementation, we will create 5 independent splits
        # by randomly shuffling the indices at the start of each fold (with a seed).
        # But the "Greedy" part implies a specific selection order.
        # Let's assume we are splitting the WHOLE dataset into 5 folds.
        # We need to partition the data into 5 test sets (one per fold) and 5 train sets.
        # A common approach is to select a test set, then the rest is train.
        # Then for the next fold, we select a DIFFERENT test set from the remaining?
        # Or we just do 5 independent greedy selections on the whole dataset?
        # The task says "for each of 5 folds". This usually means 5-fold CV.
        # In 5-fold CV, we partition data into 5 disjoint sets.
        # Let's implement a sequential selection:
        # Fold 0: Select test set T0 from all. Train = All - T0.
        # Fold 1: Select test set T1 from All - T0. Train = All - T0 - T1.
        # ... This reduces data for later folds.
        # Alternatively, we just do 5 independent splits on the full data for simplicity
        # if the task doesn't specify disjoint folds. But "5-fold" implies disjoint.
        # Let's try disjoint:
        
        remaining_indices = all_indices.copy()
        # Shuffle remaining_indices to introduce randomness in selection order if needed
        # But the greedy algorithm is deterministic given the start.
        # We need to vary the start for each fold.
        # Let's use a seed based on fold index.
        np.random.seed(42 + fold)
        np.random.shuffle(remaining_indices)
        
        test_set = []
        train_set = []
        
        # Step 1: Initialize test set with the compound furthest from the mean.
        # "Furthest from the mean" in fingerprint space.
        # Mean fingerprint = average of all fingerprints (as vectors).
        # Since we have bit vectors, we can convert to numpy arrays.
        fps_arr = np.array([np.array(fp) for fp in fingerprints]) # This might be slow for large N
        # Optimization: use the precomputed sim matrix? No, we need the vector.
        # Let's compute mean vector.
        mean_vec = np.mean(fps_arr, axis=0)
        
        # Calculate distance of each point from mean
        # Distance = 1 - Tanimoto(similarity to mean)? 
        # Or Euclidean? The task says "furthest from the mean".
        # In fingerprint space, Tanimoto distance to mean is a good metric.
        # But mean might not be a valid fingerprint.
        # Let's use Euclidean distance to mean vector as a proxy for "furthest".
        dists_from_mean = np.linalg.norm(fps_arr - mean_vec, axis=1)
        
        # Pick the index with max distance
        # But we must pick from remaining_indices
        candidate_indices = remaining_indices
        dists = dists_from_mean[candidate_indices]
        max_idx_local = np.argmax(dists)
        initial_idx = candidate_indices[max_idx_local]
        
        test_set.append(initial_idx)
        remaining_indices.remove(initial_idx)
        
        # Step 2 & 3: Iterate and select
        while remaining_indices:
            best_candidate = None
            max_min_sim = -1.0
            
            for candidate in remaining_indices:
                # Calculate min similarity to current test set
                sims = [DataStructs.TanimotoSimilarity(fingerprints[candidate], fingerprints[t]) for t in test_set]
                min_sim = min(sims)
                
                # We want the candidate that is MOST dissimilar to the current test set
                # i.e., max(min_sim)
                if min_sim > max_min_sim:
                    max_min_sim = min_sim
                    best_candidate = candidate
            
            # Step 3: Add to test set if distance > threshold
            # "Distance > threshold" -> 1 - sim > threshold -> sim < 1 - threshold
            # BUT the task says "Tanimoto < 0.85".
            # So we require max_min_sim < threshold (0.85).
            # If max_min_sim >= threshold, then this candidate is too similar to the test set.
            # We stop adding if we cannot find any candidate with sim < threshold?
            # The task says: "Add to test set if distance > threshold".
            # Let's interpret: If the best candidate (max min_sim) has sim < threshold, we add it.
            # If even the best candidate has sim >= threshold, we stop?
            # Or we just don't add it and continue?
            # Usually, in maximal dissimilarity, we stop when no more points satisfy the criterion.
            
            if max_min_sim < threshold:
                test_set.append(best_candidate)
                remaining_indices.remove(best_candidate)
            else:
                # No more points satisfy the dissimilarity criterion
                break
        
        # Step 4: Verify test set size >= 20
        if len(test_set) < min_test_size:
            logger.error(f"Fold {fold}: Insufficient test set size ({len(test_set)} < {min_test_size})")
            return None, "SIZE"
        
        # Verify Tanimoto threshold for all pairs in test set?
        # The greedy algorithm ensures min_sim < threshold for each new addition.
        # But we should double check.
        for i in range(len(test_set)):
            for j in range(i + 1, len(test_set)):
                sim = DataStructs.TanimotoSimilarity(fingerprints[test_set[i]], fingerprints[test_set[j]])
                if sim >= threshold:
                    logger.error(f"Fold {fold}: Tanimoto threshold violated ({sim} >= {threshold})")
                    return None, "THRESHOLD"
        
        train_set = [idx for idx in all_indices if idx not in test_set]
        splits[fold] = {'train': train_set, 'test': test_set}
        logger.info(f"Fold {fold}: Train={len(train_set)}, Test={len(test_set)}")
        
    return splits, "SUCCESS"

def save_splits(splits: Dict, output_dir: str):
    """
    Save split indices to pickle files.
    """
    logger = get_logger(__name__)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    for fold, indices in splits.items():
        filename = f"split_fold_{fold}.pkl"
        filepath = output_path / filename
        with open(filepath, 'wb') as f:
            pickle.dump(indices, f)
        logger.info(f"Saved split for fold {fold} to {filepath}")

def main():
    logger = setup_logging()
    init_random_seed(42)
    
    input_path = "data/processed/organophosphates_filtered.csv"
    output_dir = "data/processed/splits"
    
    if not os.path.exists(input_path):
        logger.error(f"Input file not found: {input_path}")
        # CRITICAL: Write invalid status and halt
        status_file = Path("data/processed/split_status.json")
        status_file.parent.mkdir(parents=True, exist_ok=True)
        with open(status_file, 'w') as f:
            json.dump({"status": "INVALID", "reason": "Input file not found"}, f)
        
        report_file = Path("data/processed/invalid_split_report.md")
        with open(report_file, 'w') as f:
            f.write("# Invalid Split Report\n\n")
            f.write("## Status: INVALID\n\n")
            f.write(f"The input file `{input_path}` was not found.\n\n")
            f.write("Statistical comparison is invalid.\n")
        exit(1)
    
    try:
        logger.info("Starting Greedy Maximal Dissimilarity Split")
        df, fps = load_fingerprints(input_path)
        
        splits, status = greedy_maximal_dissimilarity_split(fps, n_folds=N_FOLDS, threshold=TANIMOTO_THRESHOLD)
        
        if status != "SUCCESS":
            reason = "Insufficient Structural Diversity: Cannot achieve valid split"
            if status == "SIZE":
                reason = "Test set size < 20"
            elif status == "THRESHOLD":
                reason = "Tanimoto threshold not met"
            
            logger.error(reason)
            
            # Write invalid status
            status_file = Path("data/processed/split_status.json")
            status_file.parent.mkdir(parents=True, exist_ok=True)
            with open(status_file, 'w') as f:
                json.dump({"status": "INVALID", "reason": reason}, f)
            
            # Write invalid report
            report_file = Path("data/processed/invalid_split_report.md")
            with open(report_file, 'w') as f:
                f.write("# Invalid Split Report\n\n")
                f.write("## Status: INVALID\n\n")
                f.write(f"{reason}\n\n")
                f.write("Statistical comparison is invalid. See `data/processed/split_status.json` for details.\n")
            
            exit(1)
        
        # Save splits
        save_splits(splits, output_dir)
        
        # Write valid status
        status_file = Path("data/processed/split_status.json")
        status_file.parent.mkdir(parents=True, exist_ok=True)
        with open(status_file, 'w') as f:
            json.dump({"status": "VALID", "folds": N_FOLDS}, f)
        
        logger.info("Split completed successfully")
        
    except Exception as e:
        logger.error(f"Split failed with exception: {e}")
        # Write invalid status
        status_file = Path("data/processed/split_status.json")
        status_file.parent.mkdir(parents=True, exist_ok=True)
        with open(status_file, 'w') as f:
            json.dump({"status": "INVALID", "reason": str(e)}, f)
        
        report_file = Path("data/processed/invalid_split_report.md")
        with open(report_file, 'w') as f:
            f.write("# Invalid Split Report\n\n")
            f.write("## Status: INVALID\n\n")
            f.write(f"An exception occurred: {e}\n\n")
            f.write("Statistical comparison is invalid.\n")
        exit(1)

if __name__ == "__main__":
    main()
