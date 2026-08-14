import os
import numpy as np
import pandas as pd
import networkx as nx
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging

from nilearn.connectome import ConnectivityMeasure
from sklearn.decomposition import PCA
from statsmodels.stats.outliers_influence import variance_inflation_factor

from utils.logging import setup_logger
from utils.config import get_centrality_config, get_output_paths

logger = setup_logger(__name__)

def load_connectivity_matrix(subject_id: str, data_dir: Path) -> np.ndarray:
    """Load pre-computed connectivity matrix for a subject."""
    file_path = data_dir / "connectivity" / f"{subject_id}_matrix.npy"
    if not file_path.exists():
        raise FileNotFoundError(f"Connectivity matrix not found for {subject_id}")
    return np.load(file_path)

def extract_connectivity_matrix_for_subject(subject_id: str, fmriprep_dir: Path, atlas: str = "aal3") -> np.ndarray:
    """Extract functional connectivity matrix from fMRIPrep outputs."""
    # Placeholder for actual extraction logic if not pre-computed
    # In a real scenario, this would load preprocessed time series and compute correlation
    raise NotImplementedError("Extraction logic depends on specific fMRIPrep output structure")

def compute_centrality_metrics(matrix: np.ndarray) -> Dict[str, float]:
    """Compute degree, betweenness, and eigenvector centrality for all nodes."""
    G = nx.from_numpy_array(matrix)
    degree = nx.degree_centrality(G)
    betweenness = nx.betweenness_centrality(G)
    eigenvector = nx.eigenvector_centrality_numpy(G)
    
    return {
        "degree": degree,
        "betweenness": betweenness,
        "eigenvector": eigenvector
    }

def get_subject_list_from_directory(data_dir: Path) -> List[str]:
    """Get list of subject IDs from the data directory."""
    subjects = []
    for item in data_dir.iterdir():
        if item.is_dir() and item.name.startswith("sub-"):
            subjects.append(item.name)
    return subjects

def process_subject(subject_id: str, data_dir: Path) -> Dict[str, float]:
    """Process a single subject: load matrix, compute centrality, return metrics."""
    matrix = load_connectivity_matrix(subject_id, data_dir)
    metrics = compute_centrality_metrics(matrix)
    
    # Flatten metrics for storage
    flat_metrics = {}
    for metric_name, values in metrics.items():
        for node_idx, value in values.items():
            flat_metrics[f"{metric_name}_node_{node_idx}"] = value
    
    return flat_metrics

def load_raw_centrality_metrics(input_path: Path) -> pd.DataFrame:
    """Load raw centrality metrics from CSV."""
    if not input_path.exists():
        raise FileNotFoundError(f"Input metrics file not found: {input_path}")
    return pd.read_csv(input_path)

def calculate_vif(df: pd.DataFrame, features: List[str]) -> pd.Series:
    """Calculate Variance Inflation Factor for given features."""
    X = df[features].values
    # Add constant for intercept
    X_with_const = np.column_stack([np.ones(X.shape[0]), X])
    vif_data = []
    for i in range(X.shape[1]):
        vif = variance_inflation_factor(X_with_const, i + 1)
        vif_data.append(vif)
    return pd.Series(vif_data, index=features)

def apply_pca_transformation(df: pd.DataFrame, features: List[str], n_components: int = 1) -> pd.DataFrame:
    """Apply PCA to features and return transformed dataframe."""
    X = df[features].values
    pca = PCA(n_components=n_components)
    principal_components = pca.fit_transform(X)
    
    # Create new dataframe with PCA components
    pca_df = pd.DataFrame(principal_components, columns=[f"PCA_Component_{i+1}" for i in range(n_components)])
    
    # Keep other columns (Age, Sex, Mean_FD)
    other_cols = [col for col in df.columns if col not in features]
    pca_df[other_cols] = df[other_cols].values
    
    return pca_df

def run_centrality_analysis(input_path: Path, output_path: Path, vif_threshold: float = 5.0) -> pd.DataFrame:
    """
    Run VIF check on centrality metrics. If VIF > threshold, apply PCA.
    Output: model_predictors.csv with either Global_Centrality or PCA_Component + covariates.
    """
    logger.info(f"Loading raw centrality metrics from {input_path}")
    df = load_raw_centrality_metrics(input_path)
    
    # Identify centrality features (degree, betweenness, eigenvector)
    centrality_features = [col for col in df.columns if col.startswith(("degree_node_", "betweenness_node_", "eigenvector_node_"))]
    
    if not centrality_features:
        raise ValueError("No centrality features found in input data")
    
    logger.info(f"Checking VIF for {len(centrality_features)} centrality features")
    vif_results = calculate_vif(df, centrality_features)
    
    max_vif = vif_results.max()
    logger.info(f"Max VIF: {max_vif:.2f} (Threshold: {vif_threshold})")
    
    if max_vif > vif_threshold:
        logger.info("VIF exceeds threshold. Applying PCA transformation.")
        # Keep only Age, Sex, Mean_FD for now, will add PCA component later
        covariates = [col for col in df.columns if col in ["Age", "Sex", "Mean_FD"]]
        
        # Apply PCA to centrality features
        pca_df = apply_pca_transformation(df, centrality_features, n_components=1)
        
        # Rename PCA component for clarity
        pca_df = pca_df.rename(columns={"PCA_Component_1": "PCA_Centrality"})
        
        # Ensure covariates are present
        for cov in covariates:
            if cov not in pca_df.columns:
                if cov in df.columns:
                    pca_df[cov] = df[cov]
        
        output_df = pca_df[["PCA_Centrality"] + covariates]
        logger.info("PCA transformation applied. Outputting PCA_Centrality + covariates.")
    else:
        logger.info("VIF within acceptable range. Computing Global Centrality.")
        # Compute Global Centrality as mean of fixed subset (indices 1-10)
        # Assuming node indices are 0-based in the column names, so 1-10 means indices 1 to 10
        fixed_indices = list(range(1, 11))
        degree_cols = [f"degree_node_{i}" for i in fixed_indices]
        betweenness_cols = [f"betweenness_node_{i}" for i in fixed_indices]
        eigenvector_cols = [f"eigenvector_node_{i}" for i in fixed_indices]
        
        # Filter to existing columns
        valid_degree_cols = [c for c in degree_cols if c in df.columns]
        valid_betweenness_cols = [c for c in betweenness_cols if c in df.columns]
        valid_eigenvector_cols = [c for c in eigenvector_cols if c in df.columns]
        
        all_fixed_cols = valid_degree_cols + valid_betweenness_cols + valid_eigenvector_cols
        
        if not all_fixed_cols:
            raise ValueError("No valid fixed region columns found for Global Centrality calculation")
        
        df["Global_Centrality"] = df[all_fixed_cols].mean(axis=1)
        
        covariates = [col for col in df.columns if col in ["Age", "Sex", "Mean_FD"]]
        output_df = df[["Global_Centrality"] + covariates]
        logger.info("Global Centrality computed. Outputting Global_Centrality + covariates.")
    
    # Save to output path
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_df.to_csv(output_path, index=False)
    logger.info(f"Saved model predictors to {output_path}")
    
    return output_df

def main():
    """Main entry point for centrality analysis task T022."""
    config = get_centrality_config()
    output_paths = get_output_paths()
    
    input_path = output_paths["centrality_raw_metrics"]
    output_path = output_paths["model_predictors"]
    vif_threshold = config.get("vif_threshold", 5.0)
    
    run_centrality_analysis(input_path, output_path, vif_threshold)

if __name__ == "__main__":
    main()
