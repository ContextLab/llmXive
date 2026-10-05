import os
import logging
import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

# Ensure we can import from the project root if run as script
if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.logging import get_logger

logger = get_logger(__name__)

# Hardcoded mapping of Schaefer 400 ROI indices to network names
# This corresponds to the 7-network or 17-network parcellation.
# We focus on: Auditory, Motor, and Executive Control (Default Mode Network components often overlap).
# Based on Schaefer 2018 400 7Networks labels.
# Indices are 0-based.
NETWORK_MAPPING = {
    # Auditory Network (AV)
    'Auditory': list(range(33, 49)),  # Approx 16 ROIs in Auditory for 7-network
    # Motor Network (SM)
    'Motor': list(range(49, 73)),     # Approx 24 ROIs in Somatomotor Hand/Feet
    # Executive Control (Default Mode Network - Frontoparietal/DMN overlap)
    # In 7-network parcellation, Executive Control is often part of the Default Mode or Frontoparietal.
    # We select the 'Default Mode' and 'Frontoparietal' regions as proxies for Executive Control.
    # Adjusting based on standard 7-network Schaefer 400 mapping:
    # 0-12: Visual, 13-32: Somatomotor, 33-48: Auditory, 49-72: Somatomotor Hand, 73-96: Dorsal Attention,
    # 97-120: Salience/Ventral Attention, 121-144: Default Mode, 145-168: Frontoparietal, 169-192: Limbic?
    # Wait, 400 ROIs total. The 7-network mapping usually distributes them.
    # Let's use a robust mapping based on the standard Schaefer 400 7Networks labels file content.
    # Visual: 0-39 (40)
    # Somatomotor: 40-79 (40)
    # Dorsal Attention: 80-99 (20)
    # Salience/Ventral Attention: 100-119 (20)
    # Limbic: 120-139 (20)
    # Frontoparietal (Executive): 140-179 (40)
    # Default Mode: 180-219 (40) ... Wait, 400 total.
    # Let's assume the standard 7-network split for 400 ROIs:
    # Visual (1-40), Somatomotor (41-80), Dorsal Attn (81-100), Salience (101-120), Limbic (121-140),
    # Frontoparietal (141-180), Default Mode (181-220).
    # The 400 atlas usually has 400 labels.
    # Let's refine based on the actual Schaefer 400 7Networks file which has 400 rows.
    # Visual: 1-40
    # Somatomotor: 41-80
    # Dorsal Attention: 81-100
    # Ventral Attention: 101-120
    # Limbic: 121-140
    # Frontoparietal: 141-180
    # Default Mode: 181-220
    # Wait, 400 ROIs? The 7-network version of 400 usually has:
    # Visual: 40, Somatomotor: 40, Dorsal: 20, Ventral: 20, Limbic: 20, Frontoparietal: 40, Default: 40? That's 220.
    # Ah, the 400 atlas has 400 ROIs. The 7-network parcellation assigns each of the 400 to one of 7 networks.
    # Common distribution:
    # Visual: 40
    # Somatomotor: 40
    # Dorsal Attention: 40
    # Ventral Attention: 40
    # Limbic: 40
    # Frontoparietal: 80
    # Default Mode: 80
    # Total: 360? No.
    # Let's stick to the indices provided by the `download_atlas` logic if available, or a standard mapping.
    # Since we cannot run the download here, we assume the atlas file `data/atlas/schaefer_400.parquet`
    # contains a column 'network' and 'roi_index'.
    # We will load that file to get the exact indices dynamically to ensure correctness.
}

def load_connectivity_matrices(filepath: str) -> np.ndarray:
    """
    Load connectivity matrices from a .npy file.
    Expected shape: [N_subjects, N_ROIs, N_ROIs]
    """
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Connectivity matrices file not found: {filepath}")
    
    logger.info(f"Loading connectivity matrices from {filepath}")
    matrices = np.load(filepath, mmap_mode='r')
    
    if len(matrices.shape) != 3:
        raise ValueError(f"Expected 3D array [N, ROIs, ROIs], got shape {matrices.shape}")
    
    logger.info(f"Loaded matrices with shape: {matrices.shape}")
    return matrices

def load_atlas_annotations(atlas_path: str) -> pd.DataFrame:
    """
    Load the atlas annotations (ROI labels and network assignments).
    Expected to contain columns: 'roi_index', 'network', 'label'.
    """
    path = Path(atlas_path)
    if not path.exists():
        raise FileNotFoundError(f"Atlas file not found: {atlas_path}")
    
    logger.info(f"Loading atlas annotations from {atlas_path}")
    df = pd.read_parquet(atlas_path)
    
    required_cols = {'roi_index', 'network'}
    if not required_cols.issubset(df.columns):
        # Fallback if column names differ slightly
        if 'index' in df.columns and 'network' in df.columns:
            df.rename(columns={'index': 'roi_index'}, inplace=True)
        else:
            raise ValueError(f"Atlas must contain columns {required_cols}. Found: {df.columns.tolist()}")
    
    return df

def get_roi_indices_for_networks(atlas_df: pd.DataFrame, target_networks: List[str]) -> List[int]:
    """
    Extract ROI indices belonging to the specified networks.
    """
    indices = []
    for net in target_networks:
        mask = atlas_df['network'].str.contains(net, case=False, na=False)
        net_indices = atlas_df.loc[mask, 'roi_index'].tolist()
        indices.extend(net_indices)
        logger.info(f"Network '{net}': {len(net_indices)} ROIs")
    
    indices = sorted(list(set(indices)))
    logger.info(f"Total unique ROIs for networks {target_networks}: {len(indices)}")
    return indices

def extract_network_metrics(matrices: np.ndarray, atlas_df: pd.DataFrame, 
                            target_networks: List[str], 
                            output_path: str) -> pd.DataFrame:
    """
    Extract and compute metrics for connections within and between target networks.
    Output: CSV with connection details and mean connectivity strength.
    """
    roi_indices = get_roi_indices_for_networks(atlas_df, target_networks)
    n_rois = len(roi_indices)
    n_subjects = matrices.shape[0]
    
    logger.info(f"Extracting metrics for {n_rois} ROIs across {n_subjects} subjects")
    
    if n_rois == 0:
        raise ValueError("No ROIs found for the specified networks.")
    
    # Create a mapping from global ROI index to local index for the filtered matrix
    roi_map = {global_idx: local_idx for local_idx, global_idx in enumerate(roi_indices)}
    
    results = []
    
    # We will compute the mean connectivity for each pair of ROIs (i, j) across subjects
    # and also per subject if needed. The task asks for "network metrics".
    # Common metric: Mean connectivity strength for edges within the network.
    # Let's output: subject_id, roi_i, roi_j, network_i, network_j, connectivity_value
    
    # To avoid O(N^2) explosion in memory if we store all pairs for all subjects,
    # we can aggregate or store selectively.
    # Requirement: "output data/processed/network_metrics.csv"
    # Verification: "contains only connections from the three specified networks"
    
    # Strategy: Iterate subjects, extract submatrix, compute stats.
    # Or: Compute mean edge weight per connection type across subjects.
    # Let's produce a summary per connection (ROI pair) and per subject?
    # Given the size (400x400 is 160k edges, filtered to ~10k), storing all for all subjects is feasible.
    
    # Let's create a DataFrame with:
    # subject_id, roi_i, roi_j, network_i, network_j, z_scored_corr
    
    # We need subject IDs. Assuming they are 0..N-1 or from a separate file.
    # Since we don't have subject IDs loaded here, we'll use index.
    
    records = []
    
    # Pre-fetch network names for each ROI index for speed
    roi_network_map = dict(zip(atlas_df['roi_index'], atlas_df['network']))
    
    for subj_idx in range(n_subjects):
        if subj_idx % 10 == 0:
            logger.info(f"Processing subject {subj_idx}/{n_subjects}")
        
        subj_matrix = matrices[subj_idx]
        
        for i, global_i in enumerate(roi_indices):
            for j, global_j in enumerate(roi_indices):
                if i >= j:
                    continue # Only upper triangle
                
                val = subj_matrix[global_i, global_j]
                
                net_i = roi_network_map.get(global_i, "Unknown")
                net_j = roi_network_map.get(global_j, "Unknown")
                
                records.append({
                    'subject_id': subj_idx,
                    'roi_i': global_i,
                    'roi_j': global_j,
                    'network_i': net_i,
                    'network_j': net_j,
                    'connectivity': float(val)
                })
    
    df_results = pd.DataFrame(records)
    
    # Write to CSV
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    df_results.to_csv(output_file, index=False)
    
    logger.info(f"Wrote network metrics to {output_path} ({len(df_results)} rows)")
    return df_results

def process_network_extraction(config: Dict[str, Any]) -> pd.DataFrame:
    """
    Main orchestration function for network metric extraction.
    """
    # Default paths based on project structure
    connectivity_path = config.get('connectivity_path', 'data/processed/connectivity_matrices.npy')
    atlas_path = config.get('atlas_path', 'data/atlas/schaefer_400.parquet')
    output_path = config.get('output_path', 'data/processed/network_metrics.csv')
    target_networks = config.get('target_networks', ['Auditory', 'Motor', 'Executive'])
    
    # Load data
    matrices = load_connectivity_matrices(connectivity_path)
    atlas_df = load_atlas_annotations(atlas_path)
    
    # Extract
    df = extract_network_metrics(matrices, atlas_df, target_networks, output_path)
    
    return df

def main():
    """
    Entry point for running the network extraction script.
    """
    logger.info("Starting Network Metrics Extraction")
    
    config = {
        'connectivity_path': 'data/processed/connectivity_matrices.npy',
        'atlas_path': 'data/atlas/schaefer_400.parquet',
        'output_path': 'data/processed/network_metrics.csv',
        'target_networks': ['Auditory', 'Motor', 'Executive']
    }
    
    try:
        result_df = process_network_extraction(config)
        logger.info(f"Extraction complete. Rows: {len(result_df)}")
    except Exception as e:
        logger.error(f"Network extraction failed: {e}")
        raise

if __name__ == "__main__":
    main()
