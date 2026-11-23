"""
Preprocessing module for fMRI data analysis.

This module handles:
- Loading atlas and exclusion contracts
- Extracting BOLD time series for Power 264 nodes (excluding VS overlap)
- Extracting Ventral Striatum (VS) ROI time series from task-fMRI data
"""
import os
import json
import logging
import sys
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from nibabel import load as nib_load
from nibabel.spatialimages import SpatialImage

from config import ensure_directories
from streaming_utils import stream_nifti_by_time_chunks, extract_roi_timeseries_streaming
from state_manager import update_state_artifact

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_atlas_contract(atlas_path: str) -> Dict[str, Any]:
    """
    Load the Power 264 atlas contract JSON.
    
    Args:
        atlas_path: Path to the atlas JSON file.
        
    Returns:
        Dictionary containing atlas node definitions.
    """
    with open(atlas_path, 'r') as f:
        return json.load(f)

def load_exclusion_contract(exclusion_path: str) -> List[int]:
    """
    Load the exclusion contract JSON listing nodes to exclude.
    
    Args:
        exclusion_path: Path to the exclusion JSON file.
        
    Returns:
        List of node indices to exclude.
    """
    with open(exclusion_path, 'r') as f:
        data = json.load(f)
    return data.get('excluded_node_indices', [])

def get_node_coordinates(atlas_data: Dict[str, Any]) -> Dict[int, Tuple[float, float, float]]:
    """
    Extract node coordinates from atlas data.
    
    Args:
        atlas_data: The loaded atlas dictionary.
        
    Returns:
        Dictionary mapping node ID to (x, y, z) coordinates.
    """
    nodes = {}
    for node in atlas_data.get('nodes', []):
        node_id = node.get('id')
        coords = node.get('coordinates')
        if node_id is not None and coords is not None:
            nodes[node_id] = (coords[0], coords[1], coords[2])
    return nodes

def map_coords_to_indices(
    coords: Dict[int, Tuple[float, float, float]], 
    exclusion_indices: List[int]
) -> List[int]:
    """
    Map node coordinates to a list of valid indices (excluding specified ones).
    
    Args:
        coords: Dictionary of node ID to coordinates.
        exclusion_indices: List of node indices to exclude.
        
    Returns:
        List of valid node indices.
    """
    all_indices = sorted(coords.keys())
    return [i for i in all_indices if i not in exclusion_indices]

def extract_timeseries_for_nodes(
    nifti_path: str, 
    valid_indices: List[int], 
    atlas_coords: Dict[int, Tuple[float, float, float]]
) -> np.ndarray:
    """
    Extract BOLD time series for a specific set of node indices using streaming.
    
    Args:
        nifti_path: Path to the NIfTI file.
        valid_indices: List of node indices to extract.
        atlas_coords: Dictionary of node coordinates.
        
    Returns:
        2D numpy array of shape (time_points, num_nodes).
    """
    # Prepare ROI definitions for streaming
    rois = []
    for idx in valid_indices:
        if idx in atlas_coords:
            rois.append({
                'id': idx,
                'coords': atlas_coords[idx]
            })
    
    if not rois:
        return np.array([])

    # Use streaming utility to extract timeseries
    # This assumes extract_roi_timeseries_streaming returns a dict {id: timeseries}
    try:
        roi_timeseries = extract_roi_timeseries_streaming(nifti_path, rois)
        
        # Assemble into a matrix
        # Sort by ID to ensure consistent column order
        sorted_ids = sorted(roi_timeseries.keys())
        n_timepoints = len(roi_timeseries[sorted_ids[0]])
        n_nodes = len(sorted_ids)
        
        matrix = np.zeros((n_timepoints, n_nodes))
        for i, node_id in enumerate(sorted_ids):
            matrix[:, i] = roi_timeseries[node_id]
            
        return matrix
    except Exception as e:
        logger.error(f"Failed to extract timeseries for {nifti_path}: {e}")
        raise

def extract_vs_roi_timeseries(
    nifti_path: str, 
    vs_coords: Tuple[float, float, float]
) -> np.ndarray:
    """
    Extract Ventral Striatum ROI time series from a NIfTI file.
    
    This function uses the streaming utility to extract the mean BOLD signal
    from the defined VS ROI coordinates.
    
    Args:
        nifti_path: Path to the NIfTI file.
        vs_coords: Tuple (x, y, z) defining the VS ROI center.
        
    Returns:
        1D numpy array of the VS time series.
    """
    roi_def = {
        'id': 'vs_roi',
        'coords': vs_coords
    }
    
    try:
        # extract_roi_timeseries_streaming expects a list of ROI definitions
        result = extract_roi_timeseries_streaming(nifti_path, [roi_def])
        if 'vs_roi' in result:
            return result['vs_roi']
        else:
            raise ValueError(f"ROI 'vs_roi' not found in extraction result for {nifti_path}")
    except Exception as e:
        logger.error(f"Failed to extract VS timeseries for {nifti_path}: {e}")
        raise

def process_subject(
    subject_id: str,
    task_nifti_path: str,
    atlas_path: str,
    exclusion_path: str,
    vs_roi_path: str,
    output_dir: str
) -> bool:
    """
    Process a single subject to extract Power 264 (excl VS) and VS ROI timeseries.
    
    Args:
        subject_id: The subject identifier.
        task_nifti_path: Path to the task-fMRI NIfTI file.
        atlas_path: Path to the Power 264 atlas JSON.
        exclusion_path: Path to the exclusion contract JSON.
        vs_roi_path: Path to the VS ROI definition JSON.
        output_dir: Directory to save output CSVs.
        
    Returns:
        True if processing succeeded, False otherwise.
    """
    try:
        # Load contracts
        atlas_data = load_atlas_contract(atlas_path)
        exclusion_indices = load_exclusion_contract(exclusion_path)
        
        # Load VS ROI definition
        with open(vs_roi_path, 'r') as f:
            vs_data = json.load(f)
        
        # Extract VS coordinates (assuming 'coordinates' key in the first ROI)
        # The format from create_roi_ventral_striatum_json is typically:
        # {"roi_name": "ventral_striatum", "coordinates": [x, y, z]}
        vs_coords = tuple(vs_data.get('coordinates', []))
        if not vs_coords or len(vs_coords) != 3:
            raise ValueError(f"Invalid VS coordinates in {vs_roi_path}")
        
        # Get Power node coordinates and filter
        atlas_coords = get_node_coordinates(atlas_data)
        valid_power_indices = map_coords_to_indices(atlas_coords, exclusion_indices)
        
        logger.info(f"Processing subject {subject_id}: {len(valid_power_indices)} Power nodes, VS ROI")
        
        # Extract Power 264 (excl VS) timeseries
        power_timeseries = extract_timeseries_for_nodes(
            task_nifti_path, valid_power_indices, atlas_coords
        )
        
        if power_timeseries.size > 0:
            power_df = pd.DataFrame(power_timeseries)
            power_df.columns = [f'node_{i}' for i in valid_power_indices]
            power_df.insert(0, 'subject_id', subject_id)
            power_df_path = os.path.join(output_dir, f'{subject_id}_power_timeseries.csv')
            power_df.to_csv(power_df_path, index=False)
            logger.info(f"Saved Power timeseries to {power_df_path}")
        
        # Extract VS ROI timeseries
        vs_timeseries = extract_vs_roi_timeseries(task_nifti_path, vs_coords)
        
        if vs_timeseries.size > 0:
            vs_df = pd.DataFrame({
                'subject_id': [subject_id] * len(vs_timeseries),
                'timepoint': range(len(vs_timeseries)),
                'vs_signal': vs_timeseries
            })
            vs_df_path = os.path.join(output_dir, f'{subject_id}_vs_timeseries.csv')
            vs_df.to_csv(vs_df_path, index=False)
            logger.info(f"Saved VS timeseries to {vs_df_path}")
            
            # Update state
            update_state_artifact(vs_df_path, "processed")
        
        return True
        
    except Exception as e:
        logger.error(f"Error processing subject {subject_id}: {e}")
        return False

def main():
    """
    Main entry point for preprocessing task T016c.
    Extracts VS ROI time series for all valid subjects.
    """
    # Define paths based on project structure
    base_dir = Path(__file__).resolve().parent.parent
    data_dir = base_dir / 'data'
    contracts_dir = data_dir / 'contracts'
    processed_dir = data_dir / 'processed'
    raw_dir = data_dir / 'raw'
    
    # Ensure directories exist
    ensure_directories([processed_dir])
    
    # Load configuration paths
    atlas_path = str(contracts_dir / 'atlas_power264.json')
    exclusion_path = str(contracts_dir / 'Power264_excl_vs_nodes.json')
    vs_roi_path = str(contracts_dir / 'roi_ventral_striatum.json')
    
    if not os.path.exists(atlas_path):
        logger.error(f"Atlas contract not found: {atlas_path}")
        sys.exit(1)
    if not os.path.exists(exclusion_path):
        logger.error(f"Exclusion contract not found: {exclusion_path}")
        sys.exit(1)
    if not os.path.exists(vs_roi_path):
        logger.error(f"VS ROI definition not found: {vs_roi_path}")
        sys.exit(1)
    
    # Get list of valid subjects from ingestion state
    # Assuming T012/T013 created a list of valid subjects in state/valid_subjects.json
    # or we scan data/raw for subject folders
    valid_subjects = []
    valid_subjects_file = base_dir / 'state' / 'valid_subjects.json'
    
    if valid_subjects_file.exists():
        with open(valid_subjects_file, 'r') as f:
            valid_subjects = json.load(f)
    else:
        # Fallback: scan raw directory for subject folders
        # Expected structure: data/raw/<subject_id>/...
        if raw_dir.exists():
            for item in raw_dir.iterdir():
                if item.is_dir() and item.name.startswith('sub-'):
                    valid_subjects.append(item.name)
        
        if not valid_subjects:
            logger.warning("No valid subjects found. Ensure data ingestion (T012) completed.")
            sys.exit(0)
    
    logger.info(f"Processing {len(valid_subjects)} subjects for VS ROI extraction")
    
    success_count = 0
    for subject_id in valid_subjects:
        # Locate task-fMRI NIfTI file
        # Expected structure: data/raw/<subject_id>/func/<task>_task-*_bold.nii.gz
        # We need to find the task file. Assuming a specific task name or pattern.
        # For HCP, task names might be "reward", "gamble", etc.
        # Let's assume we look for any bold file in the func directory
        subject_raw_dir = raw_dir / subject_id
        if not subject_raw_dir.exists():
            logger.warning(f"Raw directory for {subject_id} not found, skipping.")
            continue
        
        func_dir = subject_raw_dir / 'func'
        if not func_dir.exists():
            logger.warning(f"Func directory for {subject_id} not found, skipping.")
            continue
        
        # Find the task-fMRI file (excluding resting-state if possible, but T016c says task-fMRI)
        # HCP task files often contain 'task' in the name, resting-state does not
        task_files = [f for f in func_dir.glob('*task*bold.nii*')]
        if not task_files:
            # Fallback to any bold file if task-specific not found
            task_files = list(func_dir.glob('*bold.nii*'))
            
        if not task_files:
            logger.warning(f"No NIfTI files found for {subject_id}, skipping.")
            continue
        
        # Take the first task file found
        task_nifti_path = str(task_files[0])
        logger.info(f"Processing {subject_id} with file: {task_nifti_path}")
        
        success = process_subject(
            subject_id=subject_id,
            task_nifti_path=task_nifti_path,
            atlas_path=atlas_path,
            exclusion_path=exclusion_path,
            vs_roi_path=vs_roi_path,
            output_dir=str(processed_dir)
        )
        
        if success:
            success_count += 1
    
    logger.info(f"Preprocessing complete. Success: {success_count}/{len(valid_subjects)}")
    if success_count == 0:
        logger.error("No subjects were successfully processed.")
        sys.exit(1)

if __name__ == '__main__':
    main()