import os
import logging
import numpy as np
import pandas as pd
import nibabel as nib
from pathlib import Path
from sklearn.decomposition import PCA
from sklearn.feature_selection import RFE
from sklearn.linear_model import Ridge
from typing import List, Tuple, Optional, Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
DEFAULT_DATA_DIR = Path("data")
CONNECTIVITY_DIR = DEFAULT_DATA_DIR / "processed"
DERIVED_DIR = DEFAULT_DATA_DIR / "derived"
PCA_COMPONENTS = 200
TARGET_FEATURE_COUNT = 30  # Midpoint of 20-50 range as per task requirement

def load_connectivity_matrix(subject_id: str, data_dir: Path = CONNECTIVITY_DIR) -> np.ndarray:
    """
    Load a single subject's connectivity matrix from disk.
    Expects file: data/processed/connectivity_matrix_{subject_id}.npy
    """
    file_path = data_dir / f"connectivity_matrix_{subject_id}.npy"
    if not file_path.exists():
        raise FileNotFoundError(f"Connectivity matrix not found for subject {subject_id} at {file_path}")
    return np.load(file_path)

def save_connectivity_matrix(matrix: np.ndarray, subject_id: str, data_dir: Path = CONNECTIVITY_DIR) -> Path:
    """
    Save a connectivity matrix to disk.
    """
    data_dir.mkdir(parents=True, exist_ok=True)
    file_path = data_dir / f"connectivity_matrix_{subject_id}.npy"
    np.save(file_path, matrix)
    logger.info(f"Saved connectivity matrix for {subject_id} to {file_path}")
    return file_path

def apply_pca_to_connectivity(
    matrices: List[np.ndarray],
    n_components: int = PCA_COMPONENTS,
    random_state: int = 42
) -> Tuple[np.ndarray, PCA]:
    """
    Apply PCA to a list of connectivity matrices.
    Flattens matrices (200x200 -> 40000 features) before PCA, then reduces to n_components.
    Returns the reduced feature matrix (N_samples x n_components) and the fitted PCA object.
    """
    if not matrices:
        raise ValueError("No connectivity matrices provided for PCA.")

    # Flatten matrices: (N, 200, 200) -> (N, 40000)
    n_samples = len(matrices)
    flattened = np.array([m.flatten() for m in matrices])
    logger.info(f"Flattened {n_samples} connectivity matrices to shape {flattened.shape}")

    pca = PCA(n_components=n_components, random_state=random_state)
    reduced_features = pca.fit_transform(flattened)
    
    logger.info(f"PCA explained variance ratio (sum): {np.sum(pca.explained_variance_ratio_):.4f}")
    logger.info(f"Reduced feature matrix shape: {reduced_features.shape}")
    
    return reduced_features, pca

def load_subject_connectivity_matrices(subject_ids: List[str], data_dir: Path = CONNECTIVITY_DIR) -> List[np.ndarray]:
    """
    Load connectivity matrices for a list of subjects.
    """
    matrices = []
    for sid in subject_ids:
        try:
            mat = load_connectivity_matrix(sid, data_dir)
            matrices.append(mat)
        except FileNotFoundError as e:
            logger.warning(f"Skipping {sid}: {e}")
    return matrices

def perform_feature_selection_rfe(
    feature_matrix: np.ndarray,
    target_vector: np.ndarray,
    n_features_to_select: int = TARGET_FEATURE_COUNT,
    estimator: Optional[Ridge] = None
) -> Tuple[np.ndarray, np.ndarray, RFE]:
    """
    Perform Recursive Feature Elimination (RFE) on the PCA-reduced connectivity features.
    Uses Ridge Regression as the estimator.
    
    Args:
        feature_matrix: (N_samples, N_features) PCA output.
        target_vector: (N_samples,) Target values (e.g., ADHD-RS scores).
        n_features_to_select: Number of features to retain (default 30).
        estimator: Optional Ridge estimator. If None, creates default.
        
    Returns:
        reduced_features: (N_samples, n_features_to_select)
        support_mask: Boolean mask of selected features.
        rfe_estimator: Fitted RFE object.
    """
    if feature_matrix.shape[0] != target_vector.shape[0]:
        raise ValueError("Feature matrix and target vector must have same number of samples.")
    
    if estimator is None:
        estimator = Ridge()
    
    rfe = RFE(estimator=estimator, n_features_to_select=n_features_to_select, step=1)
    rfe.fit(feature_matrix, target_vector)
    
    selected_features = feature_matrix[:, rfe.support_]
    logger.info(f"RFE selected {rfe.n_features_to_select} features out of {feature_matrix.shape[1]}")
    logger.info(f"Selected feature indices: {np.where(rfe.support_)[0]}")
    
    return selected_features, rfe.support_, rfe

def load_phenotypic_data(subject_ids: List[str]) -> Tuple[pd.DataFrame, np.ndarray]:
    """
    Load phenotypic data from data/derived/valid_subjects.csv (or similar source).
    Returns the full dataframe and the target vector corresponding to subject_ids.
    Assumes 'subject_id' and 'adhd_rs_total' columns exist.
    """
    phenotypic_path = DERIVED_DIR / "valid_subjects.csv"
    if not phenotypic_path.exists():
        # Fallback to raw if derived doesn't exist yet, though task implies derived exists
        phenotypic_path = DEFAULT_DATA_DIR / "raw" / "valid_subjects.csv"
    
    if not phenotypic_path.exists():
        raise FileNotFoundError(f"Phenotypic data not found at {phenotypic_path}")
    
    df = pd.read_csv(phenotypic_path)
    
    # Filter for requested subjects
    subset_df = df[df['subject_id'].isin(subject_ids)].sort_values('subject_id')
    
    # Ensure order matches subject_ids
    subject_id_to_idx = {sid: i for i, sid in enumerate(subset_df['subject_id'])}
    ordered_indices = [subject_id_to_idx[sid] for sid in subject_ids if sid in subject_id_to_idx]
    subset_df = subset_df.iloc[ordered_indices]
    
    if 'adhd_rs_total' not in subset_df.columns:
        # Fallback column name if different
        target_col = [c for c in subset_df.columns if 'adhd' in c.lower() and 'total' in c.lower()]
        if not target_col:
            raise ValueError("Could not find ADHD-RS target column in phenotypic data.")
        target_vector = subset_df[target_col[0]].values
    else:
        target_vector = subset_df['adhd_rs_total'].values
        
    return subset_df, target_vector

def save_reduced_features(
    reduced_features: np.ndarray,
    subject_ids: List[str],
    selected_feature_indices: np.ndarray,
    output_path: Path = DERIVED_DIR / "connectivity_features_reduced.csv"
) -> Path:
    """
    Save the reduced feature set to a CSV file.
    Columns: subject_id, feature_0, feature_1, ...
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    feature_names = [f"pca_comp_{i}" for i in selected_feature_indices]
    columns = ['subject_id'] + feature_names
    
    df_out = pd.DataFrame(reduced_features, columns=feature_names)
    df_out.insert(0, 'subject_id', subject_ids)
    
    df_out.to_csv(output_path, index=False)
    logger.info(f"Saved reduced connectivity features to {output_path} with shape {df_out.shape}")
    return output_path

def main():
    """
    Main entry point for T023c: Feature Selection on Connectivity PCA components.
    
    Steps:
    1. Load valid subjects (from T005 output).
    2. Load connectivity matrices (from T022a/b output).
    3. Apply PCA (from T023a logic, re-computed or loaded if cached).
    4. Load target variable (ADHD-RS).
    5. Perform RFE to reduce to ~30 features.
    6. Save results to data/derived/connectivity_features_reduced.csv.
    """
    logger.info("Starting Feature Selection (RFE) on Connectivity PCA components...")
    
    # 1. Load valid subjects
    valid_subjects_path = DERIVED_DIR / "valid_subjects.csv"
    if not valid_subjects_path.exists():
        raise FileNotFoundError(f"Valid subjects list not found at {valid_subjects_path}. Run T005 first.")
    
    valid_df = pd.read_csv(valid_subjects_path)
    subject_ids = valid_df['subject_id'].tolist()
    logger.info(f"Loaded {len(subject_ids)} valid subjects.")
    
    if len(subject_ids) == 0:
        raise ValueError("No valid subjects found to process.")
    
    # 2. Load connectivity matrices
    logger.info("Loading connectivity matrices...")
    matrices = load_subject_connectivity_matrices(subject_ids)
    
    if len(matrices) < 2:
        raise ValueError("Need at least 2 subjects for PCA and RFE.")
    
    # 3. Apply PCA
    logger.info("Applying PCA to connectivity matrices...")
    pca_features, pca_model = apply_pca_to_connectivity(matrices, n_components=PCA_COMPONENTS)
    
    # 4. Load target
    logger.info("Loading phenotypic data for target variable...")
    _, target_vector = load_phenotypic_data(subject_ids)
    
    # 5. Perform RFE
    logger.info(f"Performing RFE to select {TARGET_FEATURE_COUNT} features...")
    reduced_features, support_mask, rfe_model = perform_feature_selection_rfe(
        pca_features, target_vector, n_features_to_select=TARGET_FEATURE_COUNT
    )
    
    # 6. Save output
    output_path = save_reduced_features(reduced_features, subject_ids, np.where(support_mask)[0])
    
    logger.info("Feature selection complete.")
    return output_path

if __name__ == "__main__":
    main()