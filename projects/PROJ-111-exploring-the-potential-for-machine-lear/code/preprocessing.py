import os
import logging
import numpy as np
import json
import psutil
import sys
from pathlib import Path
from typing import Tuple, List, Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_available_memory() -> int:
    """Get available system memory in bytes."""
    return psutil.virtual_memory().available

def check_memory_usage(required_gb: float = 6.0) -> bool:
    """Check if required memory is available."""
    required_bytes = required_gb * (1024 ** 3)
    available = get_available_memory()
    if available < required_bytes:
        logger.warning(f"Insufficient memory: Required {required_gb}GB, Available {available/(1024**3):.2f}GB")
        return False
    logger.info(f"Memory check passed: Required {required_gb}GB, Available {available/(1024**3):.2f}GB")
    return True

def load_raw_data(raw_dir: str) -> Dict[str, np.ndarray]:
    """
    Load raw spin configuration data from .npy files in the raw directory.
    Expects files named like: spins_heisenberg_L16_T0.5.npy
    Returns a dictionary mapping (model, L, T) to data arrays.
    """
    raw_path = Path(raw_dir)
    data_dict = {}
    
    if not raw_path.exists():
        raise FileNotFoundError(f"Raw data directory not found: {raw_path}")
    
    for file_path in raw_path.glob("*.npy"):
        # Parse filename: spins_<model>_L<L>_T<T>.npy
        parts = file_path.stem.split('_')
        if len(parts) < 5:
            logger.warning(f"Skipping malformed filename: {file_path.name}")
            continue
        
        model = parts[1] # e.g., 'heisenberg' or 'xy'
        try:
            # Extract L and T from parts[3] and parts[4]
            # parts[3] is like 'L16', parts[4] is like 'T0.5'
            L = int(parts[3][1:]) # Remove 'L' prefix
            T = float(parts[4][1:]) # Remove 'T' prefix
        except (IndexError, ValueError) as e:
            logger.warning(f"Failed to parse L/T from {file_path.name}: {e}")
            continue
        
        logger.info(f"Loading {file_path.name}: Model={model}, L={L}, T={T}")
        data = np.load(file_path)
        data_dict[(model, L, T)] = data
    
    if not data_dict:
        raise ValueError("No valid data files found in raw directory.")
    
    return data_dict

def normalize_spins(data: np.ndarray) -> np.ndarray:
    """
    Normalize spin vectors to unit length along the spin axis (axis=1 for [N, 3, L, L]).
    Input shape: [N, 3, L, L] or [N, L, L, 3] -> handled by axis logic.
    We expect [N, 3, L, L] based on task description.
    """
    # Ensure data is float
    data = data.astype(np.float32)
    
    # Calculate norm along the spin dimension (axis=1 for [N, 3, L, L])
    # If input is [N, L, L, 3], we need to move axis.
    # Assuming input is already [N, 3, L, L] as per T005 description.
    if data.ndim == 4:
        # Check if shape[1] is 3 (spins) or shape[1] is L (spatial)
        if data.shape[1] == 3:
            norm = np.linalg.norm(data, axis=1, keepdims=True)
        else:
            # Assume [N, L, L, 3], move to [N, 3, L, L] first
            data = np.moveaxis(data, -1, 1)
            norm = np.linalg.norm(data, axis=1, keepdims=True)
    elif data.ndim == 3:
        # [N, 3, L] or [N, L, 3]
        if data.shape[1] == 3:
            norm = np.linalg.norm(data, axis=1, keepdims=True)
        else:
            data = np.moveaxis(data, -1, 1)
            norm = np.linalg.norm(data, axis=1, keepdims=True)
    else:
        raise ValueError(f"Unexpected data shape for normalization: {data.shape}")
    
    # Avoid division by zero
    norm = np.where(norm == 0, 1.0, norm)
    normalized = data / norm
    
    return normalized

def reshape_to_batch(data: np.ndarray) -> np.ndarray:
    """
    Reshape data to [batch, 3, L, L].
    Input might be [N, 3, L, L] or [N, L, L, 3].
    """
    if data.ndim == 4:
        if data.shape[1] == 3:
            return data
        elif data.shape[-1] == 3:
            return np.moveaxis(data, -1, 1)
        else:
            raise ValueError(f"Cannot determine spin axis for shape {data.shape}")
    else:
        raise ValueError(f"Expected 4D data for reshaping, got {data.shape}")

def stratified_split(
    data_dict: Dict[str, np.ndarray], 
    train_ratio: float = 0.8, 
    val_ratio: float = 0.1, 
    test_ratio: float = 0.1,
    seed: int = 42
) -> Tuple[Dict[str, np.ndarray], Dict[str, np.ndarray], Dict[str, np.ndarray]]:
    """
    Perform a stratified train/val/test split based on temperature bins.
    Ensures that the sample count between any two temperature bins does not 
    deviate by more than 5 samples in the resulting splits (enforced by assertion).
    """
    np.random.seed(seed)
    
    train_dict = {}
    val_dict = {}
    test_dict = {}
    
    # Group data by temperature to ensure stratification
    # We iterate over the keys (model, L, T)
    # We want to split the TOTAL dataset such that each T bin has balanced representation
    
    # Collect all samples with their temperature labels
    samples = []
    labels = []
    keys = []
    
    for key, arr in data_dict.items():
        model, L, T = key
        # Flatten if necessary to get per-sample
        # Assuming arr is [N, 3, L, L]
        n_samples = arr.shape[0]
        for i in range(n_samples):
            samples.append(arr[i])
            labels.append(T)
            keys.append(key)
    
    samples = np.array(samples)
    labels = np.array(labels)
    unique_labels = np.unique(labels)
    
    logger.info(f"Total samples: {len(samples)}, Unique temperatures: {len(unique_labels)}")
    
    # Check sample count per temperature bin
    counts = {}
    for label in unique_labels:
        counts[label] = np.sum(labels == label)
    
    # CRITICAL ASSERTION FOR T015:
    # Check if the maximum absolute difference in sample count between any two temperature bins exceeds 5.
    # This ensures that the dataset is balanced enough for stratified processing.
    if len(counts) > 1:
        max_count = max(counts.values())
        min_count = min(counts.values())
        diff = max_count - min_count
        
        if diff > 5:
            raise ValueError(
                f"Maximum absolute difference in sample count between temperature bins exceeds 5. "
                f"Max count: {max_count}, Min count: {min_count}, Difference: {diff}. "
                f"Counts: {counts}. "
                f"Dataset is too imbalanced for robust stratified analysis."
            )
        else:
            logger.info(f"Stratification check passed. Max diff: {diff} (<= 5).")
    
    # Perform stratified split
    # Since we verified counts are balanced (diff <= 5), we can split proportionally
    # or simply split the whole array if we want to maintain the exact bin distribution.
    # Standard stratified split:
    
    indices = np.arange(len(samples))
    np.random.shuffle(indices)
    
    train_indices = []
    val_indices = []
    test_indices = []
    
    for label in unique_labels:
        label_indices = indices[labels[indices] == label]
        n = len(label_indices)
        
        n_train = int(n * train_ratio)
        n_val = int(n * val_ratio)
        
        # Split this label's indices
        train_part = label_indices[:n_train]
        val_part = label_indices[n_train:n_train+n_val]
        test_part = label_indices[n_train+n_val:]
        
        train_indices.extend(train_part)
        val_indices.extend(val_part)
        test_indices.extend(test_part)
    
    train_indices = np.array(train_indices)
    val_indices = np.array(val_indices)
    test_indices = np.array(test_indices)
    
    # Reconstruct dictionaries (optional, or just return arrays)
    # For simplicity, we return arrays and let the caller group if needed.
    # But the task asks for split of the data_dict.
    # Let's group back by key to match the input structure if possible, 
    # or just return the split arrays with temperature info.
    
    # To strictly follow "stratified_split" returning dicts:
    # We will group the split samples back into (model, L, T) buckets.
    
    def group_by_key(indices, samples, keys):
        result = {}
        for idx in indices:
            key = keys[idx]
            if key not in result:
                result[key] = []
            result[key].append(samples[idx])
        
        # Convert lists to arrays
        for key in result:
            result[key] = np.array(result[key])
        return result
    
    train_dict = group_by_key(train_indices, samples, keys)
    val_dict = group_by_key(val_indices, samples, keys)
    test_dict = group_by_key(test_indices, samples, keys)
    
    logger.info(f"Split complete: Train={len(train_indices)}, Val={len(val_indices)}, Test={len(test_indices)}")
    
    return train_dict, val_dict, test_dict

def save_processed_data(data: np.ndarray, output_path: str, metadata: Dict[str, Any] = None):
    """Save processed data to .npy file."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    np.save(path, data)
    logger.info(f"Saved processed data to {output_path}")
    
    if metadata:
        meta_path = str(path) + '.json'
        with open(meta_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        logger.info(f"Saved metadata to {meta_path}")

def main():
    """Main entry point for preprocessing pipeline."""
    config = {
        "raw_dir": "data/raw",
        "processed_dir": "data/processed",
        "train_ratio": 0.8,
        "val_ratio": 0.1,
        "test_ratio": 0.1,
        "seed": 42
    }
    
    logger.info("Starting preprocessing pipeline...")
    
    # Check memory
    if not check_memory_usage():
        logger.error("Memory check failed. Aborting.")
        sys.exit(1)
    
    try:
        # Load raw data
        raw_data = load_raw_data(config["raw_dir"])
        logger.info(f"Loaded {len(raw_data)} datasets.")
        
        # Combine all data for normalization and reshaping
        # We process each (model, L, T) group individually to maintain structure
        processed_data = {}
        
        all_samples = []
        all_labels = [] # (model, L, T)
        
        for key, arr in raw_data.items():
            logger.info(f"Processing {key}...")
            # Normalize
            norm_arr = normalize_spins(arr)
            # Reshape
            reshaped = reshape_to_batch(norm_arr)
            
            # Store temporarily
            all_samples.append(reshaped)
            all_labels.append(key)
        
        # Concatenate all samples if needed, or process split on the fly
        # For the split function, we need a flat list of samples
        # But our split function expects a dict or flat array.
        # Let's flatten for split logic
        
        flat_samples = np.concatenate(all_samples, axis=0)
        # Create a flat list of keys corresponding to samples
        flat_keys = []
        for i, arr in enumerate(all_samples):
            n = arr.shape[0]
            flat_keys.extend([all_labels[i]] * n)
        
        # Perform stratified split
        train_dict, val_dict, test_dict = stratified_split(
            {}, # We pass empty dict because we use flat_samples logic inside, 
                # but the function signature expects data_dict. 
                # Actually, the function above was rewritten to take data_dict.
                # Let's refactor the call to match the implementation.
        )
        
        # Since the implementation of stratified_split above takes data_dict and iterates it,
        # we need to pass the original raw_data structure or a structure with all samples.
        # Let's reconstruct a single dict with all samples grouped by (model, L, T)
        # But we already have raw_data. The issue is raw_data has raw data.
        # We need to pass the normalized/reshaped data to split.
        
        # Re-do the split logic properly with the normalized data
        # We need to feed the normalized data into the split function.
        # Let's create a temporary dict with normalized data
        normalized_data_dict = {}
        for i, key in enumerate(all_labels):
            normalized_data_dict[key] = all_samples[i]
        
        train_dict, val_dict, test_dict = stratified_split(
            normalized_data_dict,
            config["train_ratio"],
            config["val_ratio"],
            config["test_ratio"],
            config["seed"]
        )
        
        # Save results
        for split_name, split_dict in [("train", train_dict), ("val", val_dict), ("test", test_dict)]:
            for key, arr in split_dict.items():
                model, L, T = key
                filename = f"{split_name}_{model}_L{L}_T{T}.npy"
                output_file = os.path.join(config["processed_dir"], filename)
                save_processed_data(arr, output_file, {
                    "split": split_name,
                    "model": model,
                    "L": L,
                    "T": T,
                    "shape": arr.shape
                })
        
        logger.info("Preprocessing pipeline completed successfully.")
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        raise

if __name__ == "__main__":
    main()