import os
import logging
import numpy as np
import pandas as pd
import nibabel as nib
from pathlib import Path
from sklearn.decomposition import PCA
from sklearn.linear_model import LogisticRegression
from sklearn.feature_selection import SelectFromModel
from sklearn.preprocessing import StandardScaler
import config

# Setup logger
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

def load_connectivity_matrix(subject_id: str) -> np.ndarray:
    """
    Load a single subject's connectivity matrix from disk.
    Expected path: data/processed/connectivity_matrix_{subject_id}.npy
    """
    path = Path(config.PROJECT_ROOT) / "data" / "processed" / f"connectivity_matrix_{subject_id}.npy"
    if not path.exists():
        raise FileNotFoundError(f"Connectivity matrix not found for subject {subject_id} at {path}")
    return np.load(path)

def save_connectivity_matrix(matrix: np.ndarray, subject_id: str) -> None:
    """Save a connectivity matrix to disk."""
    path = Path(config.PROJECT_ROOT) / "data" / "processed" / f"connectivity_matrix_{subject_id}.npy"
    np.save(path, matrix)
    logger.info(f"Saved connectivity matrix for {subject_id} to {path}")

def load_subject_connectivity_matrices(subject_ids: list) -> tuple:
    """
    Load connectivity matrices for a list of subjects.
    Returns: (X_connectivity: np.ndarray, valid_subject_ids: list)
    X_connectivity shape: (n_subjects, n_features) where n_features = n_rois * n_rois (flattened)
    """
    matrices = []
    valid_ids = []
    for sid in subject_ids:
        try:
            mat = load_connectivity_matrix(sid)
            # Flatten the 200x200 matrix to 40000 features
            flat_mat = mat.flatten()
            matrices.append(flat_mat)
            valid_ids.append(sid)
        except FileNotFoundError as e:
            logger.warning(f"Skipping {sid}: {e}")
    
    if not matrices:
        raise ValueError("No connectivity matrices loaded. Check subject IDs and data availability.")
    
    X = np.vstack(matrices)
    return X, valid_ids

def load_phenotypic_data() -> pd.DataFrame:
    """
    Load phenotypic data (diagnosis/ADHD scores) for subjects.
    Expected source: data/derived/valid_subjects.csv or similar.
    Returns DataFrame with subject_id and target variable.
    """
    # Assuming valid_subjects.csv contains diagnosis info as per T005a
    path = Path(config.PROJECT_ROOT) / "data" / "derived" / "valid_subjects.csv"
    if not path.exists():
        # Fallback to a standard phenotype file if valid_subjects doesn't have scores
        # But per T005a spec, it should have diagnosis. We'll assume a column 'diagnosis' (0/1)
        # If the actual file has ADHD-RS scores, we might need a different column.
        # For T023c (Logistic Regression), we need binary labels.
        raise FileNotFoundError(f"Phenotypic data not found at {path}")
    
    df = pd.read_csv(path)
    # Ensure subject_id is string
    if 'subject_id' in df.columns:
        df['subject_id'] = df['subject_id'].astype(str)
    return df

def apply_pca_to_connectivity(X: np.ndarray, n_components: int = 200) -> tuple:
    """
    Apply PCA to connectivity features.
    X: (n_subjects, n_features)
    Returns: (X_pca, pca_model)
    """
    logger.info(f"Applying PCA to {X.shape[0]} subjects with {X.shape[1]} features, reducing to {n_components} components.")
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    pca = PCA(n_components=n_components)
    X_pca = pca.fit_transform(X_scaled)
    
    logger.info(f"PCA explained variance ratio sum: {np.sum(pca.explained_variance_ratio_):.4f}")
    return X_pca, pca, scaler

def perform_feature_selection_rfe(X_pca: np.ndarray, y: np.ndarray, 
                                  n_features_to_select: int = 50) -> tuple:
    """
    Perform feature selection using L1-regularized Logistic Regression (L1 penalty).
    This addresses the N=100, p=200 underpowered ratio by selecting a sparse subset.
    
    Args:
        X_pca: PCA-transformed features (n_samples, n_components)
        y: Binary labels (n_samples,)
        n_features_to_select: Number of features to retain.
    
    Returns:
        X_reduced: Selected features (n_samples, n_selected)
        selector: The fitted SelectFromModel object
    """
    logger.info(f"Performing L1-based feature selection: selecting top {n_features_to_select} from {X_pca.shape[1]} components.")
    
    # Use LogisticRegression with L1 penalty (solver='liblinear' or 'saga')
    # C is inverse of regularization strength. Smaller C = stronger regularization = more zeros.
    # We need to tune C or set it to select the desired number of features.
    # For exploratory analysis, we can try a fixed C or use SelectFromModel with a threshold.
    
    # Strategy: Use SelectFromModel with a LogisticRegression estimator.
    # We'll try to select exactly n_features_to_select features.
    # Since L1 induces sparsity, we can set max_features in the selector if using a different estimator,
    # but SelectFromModel with LogisticRegression selects based on coefficient magnitude > threshold.
    # To get exactly N features, we might need to adjust the threshold or use a different approach.
    # However, the task asks for "L-Regularized Logistic Regression" to reduce the space.
    # A common pattern is to fit L1, then keep the non-zero coefficients.
    # If we want a specific number, we can use SelectFromModel with a custom threshold or iterate C.
    
    # For simplicity and robustness with small N, we'll use a fixed C that typically yields ~25% sparsity
    # or use SelectFromModel with `max_features` if available (it's not directly on LogisticRegression).
    # Instead, we'll fit L1, get the non-zero indices, and if more than desired, take the top N by absolute value.
    
    clf = LogisticRegression(penalty='l1', solver='liblinear', C=0.1, max_iter=1000)
    clf.fit(X_pca, y)
    
    # Get the support mask (non-zero coefficients)
    support_mask = clf.coef_[0] != 0
    selected_indices = np.where(support_mask)[0]
    n_selected = len(selected_indices)
    
    logger.info(f"L1 selection retained {n_selected} features out of {X_pca.shape[1]}.")
    
    # If we have more than desired, trim to top N by absolute coefficient magnitude
    if n_selected > n_features_to_select:
        coef_abs = np.abs(clf.coef_[0])
        top_indices = np.argsort(coef_abs)[::-1][:n_features_to_select]
        # Re-filter the support mask to only these top indices
        final_mask = np.zeros(X_pca.shape[1], dtype=bool)
        final_mask[top_indices] = True
        selected_indices = top_indices
        n_selected = n_features_to_select
        logger.info(f"Trimmed to top {n_selected} features by coefficient magnitude.")
    elif n_selected == 0:
        # Fallback: if L1 killed everything, take top N by magnitude anyway
        logger.warning("L1 selection resulted in zero features. Falling back to top N by magnitude.")
        coef_abs = np.abs(clf.coef_[0])
        selected_indices = np.argsort(coef_abs)[::-1][:n_features_to_select]
        n_selected = n_features_to_select
    
    X_reduced = X_pca[:, selected_indices]
    logger.info(f"Final feature set shape: {X_reduced.shape}")
    
    return X_reduced, clf, selected_indices

def save_reduced_features(X_reduced: np.ndarray, subject_ids: list, 
                          feature_indices: np.ndarray, output_path: str) -> None:
    """
    Save the reduced feature matrix to CSV.
    Columns: subject_id, pca_comp_0, pca_comp_1, ... (only selected ones)
    """
    df = pd.DataFrame(X_reduced, columns=[f"pca_comp_{idx}" for idx in feature_indices])
    df.insert(0, 'subject_id', subject_ids)
    
    full_path = Path(config.PROJECT_ROOT) / output_path
    df.to_csv(full_path, index=False)
    logger.info(f"Saved reduced features to {full_path}")

def main():
    """
    Main entry point for T023c: Feature Selection on PCA components.
    1. Load connectivity matrices (from T022a).
    2. Load phenotypic data (binary diagnosis).
    3. Apply PCA (from T023a logic, but re-run or load if T023a saved intermediate).
       Since T023a output is `connectivity_features_baseline.csv`, we can load that.
       However, to ensure consistency, we'll re-load raw matrices and apply PCA here 
       (or load the baseline CSV if it's just the PCA output).
    4. Perform L1-based feature selection.
    5. Save `data/derived/connectivity_features_reduced.csv`.
    """
    logger.info("Starting T023c: Feature Selection on Connectivity PCA Components.")
    
    # 1. Load valid subjects (from T005a)
    valid_subjects_path = Path(config.PROJECT_ROOT) / "data" / "derived" / "valid_subjects.csv"
    if not valid_subjects_path.exists():
        raise FileNotFoundError(f"Missing {valid_subjects_path}. Run T005a first.")
    
    valid_df = pd.read_csv(valid_subjects_path)
    subject_ids = valid_df['subject_id'].astype(str).tolist()
    
    # 2. Load connectivity matrices
    X_conn, loaded_ids = load_subject_connectivity_matrices(subject_ids)
    logger.info(f"Loaded {len(loaded_ids)} connectivity matrices. Shape: {X_conn.shape}")
    
    # 3. Load phenotypic data for labels
    # We expect 'diagnosis' column (0/1) from valid_subjects.csv
    # If the file has multiple diagnosis columns or codes, we might need to map them.
    # For now, assume 'diagnosis' is 0 or 1.
    if 'diagnosis' not in valid_df.columns:
        raise ValueError("Phenotypic data missing 'diagnosis' column. T023c requires binary labels.")
    
    y = valid_df.set_index('subject_id').loc[loaded_ids]['diagnosis'].values
    # Ensure binary
    if len(np.unique(y)) > 2:
        logger.warning("Diagnosis has more than 2 unique values. Converting to binary (ADHD vs Control).")
        # Heuristic: if values are like 0,1,2, maybe 0=Control, 1=ADHD, 2=Other? 
        # For safety, we'll assume 0=Control, >=1=ADHD if the data is 0/1/2.
        # But the task expects binary. Let's assume the data is clean 0/1.
        # If not, we might need to map. For now, let's just use the first two unique values if only 2 exist.
        # If more, we'll raise an error or binarize.
        unique_vals = np.unique(y)
        if len(unique_vals) == 2:
            pass # OK
        else:
            # Try to binarize: assume 0 is control, others are ADHD
            y = (y > 0).astype(int)
            logger.info(f"Binarized labels: 0={np.sum(y==0)}, 1={np.sum(y==1)}")
    
    # 4. Apply PCA (if not already done in T023a, but T023a output is a CSV)
    # T023a output: data/derived/connectivity_features_baseline.csv (200 components)
    # We can load that directly to avoid re-computing, ensuring consistency.
    baseline_path = Path(config.PROJECT_ROOT) / "data" / "derived" / "connectivity_features_baseline.csv"
    if baseline_path.exists():
        logger.info("Loading PCA features from T023a baseline CSV.")
        baseline_df = pd.read_csv(baseline_path)
        # Ensure subject_id matches order
        baseline_df['subject_id'] = baseline_df['subject_id'].astype(str)
        # Reindex to loaded_ids
        if not set(baseline_df['subject_id']).issuperset(set(loaded_ids)):
            raise ValueError("Baseline CSV missing subjects found in connectivity matrices.")
        baseline_df = baseline_df.set_index('subject_id').loc[loaded_ids].reset_index()
        X_pca = baseline_df.drop(columns=['subject_id']).values
    else:
        logger.warning("T023a baseline CSV not found. Re-computing PCA from raw matrices.")
        X_pca, _, _ = apply_pca_to_connectivity(X_conn, n_components=200)
    
    logger.info(f"PCA features shape: {X_pca.shape}")
    
    # 5. Perform Feature Selection (L1 Logistic Regression)
    # We want to reduce from 200 to a smaller set (e.g., 50)
    X_reduced, clf, selected_indices = perform_feature_selection_rfe(
        X_pca, y, n_features_to_select=50
    )
    
    # 6. Save output
    output_path = "data/derived/connectivity_features_reduced.csv"
    save_reduced_features(X_reduced, loaded_ids, selected_indices, output_path)
    
    logger.info("T023c completed successfully.")
    return output_path

if __name__ == "__main__":
    main()