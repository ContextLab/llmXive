import os
import numpy as np
import pandas as pd
import networkx as nx
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging
import glob

# Import logging utilities from project utils
try:
    from utils.logging import setup_logger
except ImportError:
    # Fallback if running directly without package context
    logging.basicConfig(level=logging.INFO)
    def setup_logger(name): return logging.getLogger(name)

logger = setup_logger(__name__)

def get_subject_list_from_directory(data_dir: Path) -> List[str]:
    """
    Scans the data directory for subject folders (e.g., sub-01, sub-02).
    Returns a list of subject IDs.
    """
    if not data_dir.exists():
        logger.warning(f"Data directory does not exist: {data_dir}")
        return []
    
    subjects = []
    for item in sorted(data_dir.iterdir()):
        if item.is_dir() and item.name.startswith('sub-'):
            subjects.append(item.name)
    return subjects

def load_connectivity_matrix(subject_id: str, connectivity_dir: Path) -> Optional[np.ndarray]:
    """
    Loads a pre-computed connectivity matrix for a subject.
    Expects file: {connectivity_dir}/{subject_id}_matrix.npy
    """
    file_path = connectivity_dir / f"{subject_id}_matrix.npy"
    if not file_path.exists():
        logger.warning(f"Connectivity matrix not found for {subject_id} at {file_path}")
        return None
    return np.load(file_path)

def extract_connectivity_matrix_for_subject(subject_id: str, fmriprep_dir: Path, atlas_name: str = 'aal3') -> np.ndarray:
    """
    Extracts functional connectivity matrix for a subject using nilearn.
    This is a placeholder implementation as nilearn is not in the provided API surface imports,
    but the task T019/T020 implementation logic would go here.
    For T021, we assume this has been done or the file exists.
    """
    # In a real implementation, this would use nilearn.connectome.ConnectivityMeasure
    # to extract the matrix from fMRIPrep outputs and save it.
    # Since T019 was marked as failed/missing, we ensure the path exists or raise.
    conn_dir = fmriprep_dir.parent / "connectivity" # Assuming processed structure
    # This function is primarily a stub for the API surface requirement.
    # The actual heavy lifting for T019 is assumed to be handled by the preprocessing pipeline
    # or a separate execution step that generates the .npy files.
    raise NotImplementedError("Connectivity extraction requires nilearn and preprocessed fMRI data. "
                              "This function is a placeholder for the API surface. "
                              "Ensure T019 is implemented to generate .npy files before calling centrality metrics.")

def compute_centrality_metrics(connectivity_matrix: np.ndarray, subject_id: str) -> Dict[str, float]:
    """
    Computes degree, betweenness, and eigenvector centrality for a connectivity matrix.
    """
    if connectivity_matrix is None:
        return {}
    
    # Convert to graph (assuming symmetric adjacency)
    # Thresholding might be needed, but we use raw values for weighted centrality
    G = nx.from_numpy_array(connectivity_matrix)
    
    metrics = {
        'subject_id': subject_id,
        'degree_centrality_mean': np.mean(list(nx.degree_centrality(G).values())),
        'betweenness_centrality_mean': np.mean(list(nx.betweenness_centrality(G).values())),
        'eigenvector_centrality_mean': np.mean(list(nx.eigenvector_centrality(G, max_iter=1000).values()))
    }
    return metrics

def process_subject(subject_id: str, data_dir: Path, output_dir: Path) -> Optional[Dict]:
    """
    Processes a single subject: loads matrix, computes centrality, returns metrics.
    """
    conn_dir = data_dir / "connectivity"
    matrix = load_connectivity_matrix(subject_id, conn_dir)
    if matrix is None:
        return None
    
    metrics = compute_centrality_metrics(matrix, subject_id)
    return metrics

def run_centrality_analysis(data_dir: Path, output_dir: Path) -> pd.DataFrame:
    """
    Runs centrality analysis for all subjects and saves to CSV.
    """
    subjects = get_subject_list_from_directory(data_dir)
    all_metrics = []
    
    for sub in subjects:
        try:
            metrics = process_subject(sub, data_dir, output_dir)
            if metrics:
                all_metrics.append(metrics)
        except Exception as e:
            logger.error(f"Error processing {sub}: {e}")
    
    if not all_metrics:
        logger.warning("No centrality metrics computed.")
        return pd.DataFrame()
    
    df = pd.DataFrame(all_metrics)
    output_path = output_dir / "subject_id_metrics.csv"
    df.to_csv(output_path, index=False)
    logger.info(f"Saved centrality metrics to {output_path}")
    return df

def calculate_mean_fd(subject_id: str, fmriprep_dir: Path) -> Optional[float]:
    """
    Calculates Mean Framewise Displacement (FD) from fMRIPrep confounds.
    
    Args:
        subject_id: The subject ID (e.g., 'sub-01')
        fmriprep_dir: Path to the fMRIPrep derivatives directory (e.g., data/processed/fmriprep)
        
    Returns:
        Mean FD value or None if file not found.
    """
    # Construct path to confounds file
    # Expected pattern: data/processed/fmriprep/<subject_id>/func/<subject_id>_task-..._desc-confounds_timeseries.tsv
    # We search for the file matching the pattern
    pattern = str(fmriprep_dir / subject_id / "**" / "*desc-confounds_timeseries.tsv")
    files = glob.glob(pattern, recursive=True)
    
    if not files:
        logger.warning(f"No confounds file found for {subject_id} in {fmriprep_dir}")
        return None
    
    # Assume the first match is the correct one
    confounds_file = Path(files[0])
    
    try:
        df = pd.read_csv(confounds_file, sep='\t', comment='#')
        if 'framewise_displacement' not in df.columns:
            logger.warning(f"Column 'framewise_displacement' not found in {confounds_file}")
            return None
        
        fd_series = df['framewise_displacement']
        # Handle potential non-numeric values or NaNs
        fd_values = pd.to_numeric(fd_series, errors='coerce')
        mean_fd = fd_values.mean()
        
        if pd.isna(mean_fd):
            logger.warning(f"Mean FD is NaN for {subject_id}")
            return None
            
        return float(mean_fd)
        
    except Exception as e:
        logger.error(f"Error reading confounds for {subject_id}: {e}")
        return None

def calculate_fd(fmriprep_dir: Path, output_dir: Path) -> pd.DataFrame:
    """
    Main entry point for T021.
    Iterates through subjects in the fMRIPrep directory, calculates mean FD,
    and saves the results to data/processed/behavioral/fd_mean.csv.
    """
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Find all subject directories
    subjects = []
    if fmriprep_dir.exists():
        for item in sorted(fmriprep_dir.iterdir()):
            if item.is_dir() and item.name.startswith('sub-'):
                subjects.append(item.name)
    
    if not subjects:
        logger.warning(f"No subjects found in {fmriprep_dir}")
        return pd.DataFrame(columns=['subject_id', 'mean_fd'])

    results = []
    for sub_id in subjects:
        mean_fd = calculate_mean_fd(sub_id, fmriprep_dir)
        results.append({
            'subject_id': sub_id,
            'mean_fd': mean_fd
        })
    
    df = pd.DataFrame(results)
    output_path = output_dir / "fd_mean.csv"
    df.to_csv(output_path, index=False)
    logger.info(f"Saved mean FD to {output_path}")
    return df

def main():
    """
    Entry point for running the centrality and FD analysis.
    """
    # Configuration paths (hardcoded for this task execution, 
    # ideally loaded from utils.config in a real pipeline)
    base_dir = Path("data/processed")
    fmriprep_dir = base_dir / "fmriprep"
    centrality_output_dir = base_dir / "centrality"
    fd_output_dir = base_dir / "behavioral"
    
    logger.info("Starting Centrality and FD Analysis...")
    
    # 1. Run FD Calculation (T021)
    logger.info("Calculating Mean Framewise Displacement...")
    try:
        fd_df = calculate_fd(fmriprep_dir, fd_output_dir)
        print(f"FD Calculation Complete. Rows: {len(fd_df)}")
        if len(fd_df) > 0:
            print(fd_df.head())
    except Exception as e:
        logger.error(f"FD Calculation failed: {e}")
        raise
        
    # 2. Run Centrality Analysis (T020) - Placeholder for completeness
    # This would require connectivity matrices to be present
    # centrality_output_dir.mkdir(parents=True, exist_ok=True)
    # run_centrality_analysis(base_dir / "connectivity", centrality_output_dir)

if __name__ == "__main__":
    main()