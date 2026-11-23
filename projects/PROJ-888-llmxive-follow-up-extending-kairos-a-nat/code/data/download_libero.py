"""
Data download module for LIBERO dataset.
Fetches real HDF5 data from HuggingFace Datasets.
NO synthetic fallback.
"""
import os
import sys
from pathlib import Path
from typing import Optional

# Add parent to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utils.logging import get_logger, DataFetchError
from config import DATA_DIR, SUBSET_SIZE

logger = get_logger(__name__)

def download_libero_subset(
    dataset_name: str = "libero",
    subset_size: int = SUBSET_SIZE,
    output_dir: Optional[Path] = None
) -> Path:
    """
    Download a subset of the LIBERO dataset from HuggingFace.
    
    Args:
        dataset_name: Name of the dataset on HuggingFace.
        subset_size: Number of episodes to fetch/limit to.
        output_dir: Directory to save the data.
        
    Returns:
        Path to the downloaded/saved file.
        
    Raises:
        DataFetchError: If the real data cannot be fetched.
    """
    if output_dir is None:
        output_dir = DATA_DIR
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_path = output_dir / f"{dataset_name}_subset.h5"
    
    if output_path.exists():
        logger.info(f"Dataset subset already exists at {output_path}. Skipping download.")
        return output_path

    try:
        logger.info(f"Fetching real data from HuggingFace: {dataset_name} (limit={subset_size})")
        
        from datasets import load_dataset
        
        # Use the verified LIBERO dataset ID on HuggingFace
        actual_dataset_name = "haoyuzhou00/libero"
        
        # Load with streaming to handle large datasets, then take a subset
        dataset = load_dataset(actual_dataset_name, split="train", streaming=True)
        
        # Take the first N episodes
        episodes = []
        count = 0
        for item in dataset:
            if count >= subset_size:
                break
            episodes.append(item)
            count += 1
        
        if not episodes:
            raise DataFetchError("No data fetched from HuggingFace. The dataset might be empty or inaccessible.")
        
        logger.info(f"Fetched {count} episodes.")
        
        # Convert to HDF5 format
        import h5py
        import numpy as np
        
        with h5py.File(output_path, 'w') as f:
            # Create a group for episodes
            ep_group = f.create_group("episodes")
            
            for i, ep in enumerate(episodes):
                ep_data = ep_group.create_group(f"episode_{i}")
                
                # Handle observations
                if 'observations' in ep:
                    obs = ep['observations']
                    # Convert to numpy if not already
                    if isinstance(obs, dict):
                        for k, v in obs.items():
                            if isinstance(v, list):
                                obs[k] = np.array(v)
                        # Flatten dict to array if needed, or store as compound
                        # For simplicity, we store the values concatenated if they are 1D
                        # or store as a group if complex. 
                        # LIBERO obs usually has 'agent_pos', 'gripper_pos', etc.
                        # We will store each key as a dataset if it's a list/array
                        for k, v in obs.items():
                            if isinstance(v, (list, np.ndarray)):
                                arr = np.array(v)
                                ep_data.create_dataset(f"obs_{k}", data=arr)
                    elif isinstance(obs, np.ndarray):
                        ep_data.create_dataset("observations", data=obs)
                
                # Handle actions
                if 'actions' in ep:
                    acts = ep['actions']
                    if isinstance(acts, list):
                        acts = np.array(acts)
                    ep_data.create_dataset("actions", data=acts)
                
                # Store metadata
                ep_data.attrs["episode_id"] = i
                ep_data.attrs["length"] = len(ep.get('actions', [])) if 'actions' in ep else 0
        
        logger.info(f"Saved subset to {output_path}")
        return output_path

    except Exception as e:
        logger.error(f"Failed to fetch real data: {e}")
        # CRITICAL: Do NOT fall back to synthetic data. Fail loudly.
        raise DataFetchError(f"Real data fetch failed for {actual_dataset_name}. No synthetic fallback allowed.") from e