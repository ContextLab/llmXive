import os
import logging
import numpy as np
import pandas as pd
import nibabel as nib
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Any
from sklearn.decomposition import PCA
from sklearn.linear_model import LogisticRegression
from sklearn.feature_selection import RFE
from sklearn.preprocessing import StandardScaler
import config

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_connectivity_matrix(subject_id: str) -> np.ndarray:
    """Load a single subject's connectivity matrix."""
    path = Path(config.DATA_PROCESSED_DIR) / f"connectivity_matrix_{subject_id}.npy"
    if not path.exists():
        raise FileNotFoundError(f"Connectivity matrix not found for {subject_id} at {path}")
    return np.load(path)

def save_connectivity_matrix(subject_id: str, matrix: np.ndarray) -> None:
    """Save a single subject's connectivity matrix."""
    path = Path(config.DATA_PROCESSED_DIR) / f"connectivity_matrix_{subject_id}.npy"
    np.save(path, matrix)
    logger.info(f"Saved connectivity matrix for {subject_id} to {path}")

def apply_pca_to_connectivity(subject_id: str, n_components: int = 200) -> np.ndarray:
    """Apply PCA to a subject's connectivity matrix and return flattened features."""
    matrix = load_connectivity_matrix(subject_id)
    # Flatten upper triangle (excluding diagonal) or full matrix depending on spec
    # Spec implies 200x200 matrix -> 200 components.
    # Usually connectivity matrices are symmetric. We flatten to 1D vector.
    # If the matrix is 200x200, flattening gives 40000 features.
    # PCA reduces this to n_components (200).
    flat_matrix = matrix.flatten()
    
    # Reshape for PCA (n_samples, n_features)
    X = flat_matrix.reshape(1, -1)
    
    pca = PCA(n_components=n_components, random_state=42)
    reduced = pca.fit_transform(X)
    
    return reduced[0]  # Return 1D array of shape (n_components,)

def load_subject_connectivity_matrices(subject_ids: List[str]) -> Tuple[np.ndarray, List[str]]:
    """Load connectivity features for all subjects, applying PCA."""
    features = []
    valid_ids = []
    
    for sid in subject_ids:
        try:
            feat = apply_pca_to_connectivity(sid, n_components=config.ATLAS_N)
            features.append(feat)
            valid_ids.append(sid)
        except FileNotFoundError as e:
            logger.warning(f"Skipping {sid}: {e}")
    
    if not features:
        raise ValueError("No valid connectivity matrices found for any subject.")
    
    return np.array(features), valid_ids

def load_phenotypic_data() -> Tuple[np.ndarray, np.ndarray]:
    """Load phenotype data (labels) for modeling."""
    # Assuming valid_subjects.csv contains diagnosis info
    valid_subjects_path = Path(config.DATA_DERIVED_DIR) / "valid_subjects.csv"
    if not valid_subjects_path.exists():
        raise FileNotFoundError(f"valid_subjects.csv not found at {valid_subjects_path}")
    
    df = pd.read_csv(valid_subjects_path)
    # Map diagnosis to binary: ADHD=1, Control=0 (adjust based on actual values if needed)
    # Assuming 'diagnosis' column has values like 'ADHD', 'Control'
    if 'diagnosis' not in df.columns:
        raise ValueError("Column 'diagnosis' not found in valid_subjects.csv")
    
    labels = (df['diagnosis'].str.upper() == 'ADHD').astype(int).values
    # We need to align this with the features list from load_subject_connectivity_matrices
    # The order must match the subject_ids passed to that function.
    # This function returns the full list, so we assume the caller handles alignment.
    return labels, df['subject_id'].values

def perform_feature_selection_rfe(X: np.ndarray, y: np.ndarray, n_features_to_select: int = 50) -> Tuple[np.ndarray, np.ndarray]:
    """
    Perform Recursive Feature Elimination (RFE) using Logistic Regression to select top features.
    
    Args:
        X: Feature matrix (n_samples, n_features) - PCA components
        y: Target labels (n_samples,)
        n_features_to_select: Number of features to retain (default 50 to address N=100, p=200)
    
    Returns:
        X_reduced: Feature matrix with selected features
        selector: The fitted RFE selector object
    """
    logger.info(f"Starting RFE feature selection. Input shape: {X.shape}, selecting {n_features_to_select} features.")
    
    # Scale features for Logistic Regression
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # Initialize Logistic Regression with L1 penalty (L-Regularized)
    # Note: LogisticRegression with penalty='l1' requires solver='liblinear' or 'saga'
    base_estimator = LogisticRegression(penalty='l1', solver='liblinear', max_iter=1000, random_state=42)
    
    # Perform RFE
    rfe = RFE(estimator=base_estimator, n_features_to_select=n_features_to_select, step=1)
    rfe.fit(X_scaled, y)
    
    # Get the mask of selected features
    support_mask = rfe.support_
    X_reduced = X[:, support_mask]
    
    logger.info(f"RFE completed. Selected {np.sum(support_mask)} features. Output shape: {X_reduced.shape}")
    
    return X_reduced, rfe

def save_reduced_features(X_reduced: np.ndarray, subject_ids: List[str], output_path: str) -> None:
    """Save the reduced feature set to CSV."""
    df = pd.DataFrame(X_reduced)
    df.insert(0, 'subject_id', subject_ids)
    df.to_csv(output_path, index=False)
    logger.info(f"Saved reduced features to {output_path} with shape {df.shape}")

def main() -> str:
    """
    Main entry point for T023c: Feature Selection on PCA components.
    
    1. Load connectivity matrices for valid subjects.
    2. Apply PCA (already done in load_subject_connectivity_matrices -> returns 200 components).
    3. Load phenotype data.
    4. Perform RFE (L1 Logistic Regression) to reduce features.
    5. Save to data/derived/connectivity_features_reduced.csv.
    """
    # Ensure directories exist
    Path(config.DATA_DERIVED_DIR).mkdir(parents=True, exist_ok=True)
    
    # Load valid subjects
    valid_subjects_path = Path(config.DATA_DERIVED_DIR) / "valid_subjects.csv"
    if not valid_subjects_path.exists():
        raise FileNotFoundError(f"Missing {valid_subjects_path}")
    
    df_valid = pd.read_csv(valid_subjects_path)
    subject_ids = df_valid['subject_id'].tolist()
    
    if not subject_ids:
        raise ValueError("No valid subjects found.")
    
    logger.info(f"Processing {len(subject_ids)} subjects for feature selection.")
    
    # Load PCA features (X) and Labels (y)
    # Note: load_subject_connectivity_matrices returns X and valid_ids
    # load_phenotypic_data returns y and all_ids. We must ensure alignment.
    # Since both use valid_subjects.csv order, we assume alignment if we pass the same list.
    X, _ = load_subject_connectivity_matrices(subject_ids)
    y, _ = load_phenotypic_data() # Returns y for all subjects in valid_subjects.csv order
    
    # Filter y to match X (in case load_phenotypic_data returned more than we have features for)
    # But load_phenotypic_data reads the same file, so it should be aligned if we didn't skip any in load_subject_connectivity_matrices.
    # For safety, we use the subject_ids from the feature loader.
    # Re-load y specifically for the subjects we have features for.
    df_valid_subset = df_valid[df_valid['subject_id'].isin(subject_ids)]
    y_aligned = (df_valid_subset['diagnosis'].str.upper() == 'ADHD').astype(int).values
    
    if X.shape[0] != y_aligned.shape[0]:
        raise ValueError(f"Shape mismatch: X has {X.shape[0]} rows, y has {y_aligned.shape[0]} rows.")
    
    # Determine number of features to select
    # To address N=100, p=200 underpowered ratio, select a smaller subset (e.g., 50 or 10% of N)
    n_features_to_select = min(50, X.shape[1]) 
    
    # Perform Feature Selection
    X_reduced, rfe = perform_feature_selection_rfe(X, y_aligned, n_features_to_select=n_features_to_select)
    
    # Save output
    output_path = str(Path(config.DATA_DERIVED_DIR) / "connectivity_features_reduced.csv")
    save_reduced_features(X_reduced, subject_ids, output_path)
    
    logger.info(f"T023c completed successfully. Output: {output_path}")
    return output_path

if __name__ == "__main__":
    main()