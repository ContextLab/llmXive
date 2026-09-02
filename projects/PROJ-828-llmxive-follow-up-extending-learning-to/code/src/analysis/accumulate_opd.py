import os
import re
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

import torch
import numpy as np

logger = logging.getLogger(__name__)

def find_layer_files(base_dir: Path) -> List[Path]:
    """
    Discover all layer update files matching the pattern layer_{index:02d}.pt
    within the provided directory.
    Returns a sorted list of paths to ensure deterministic ordering.
    """
    if not base_dir.exists():
        raise FileNotFoundError(f"Directory not found: {base_dir}")

    pattern = re.compile(r'^layer_(\d{2})\.pt$')
    files = []
    
    for f in base_dir.iterdir():
        if f.is_file():
            match = pattern.match(f.name)
            if match:
                files.append(f)
    
    # Sort by the captured index to ensure correct ordering
    files.sort(key=lambda p: int(pattern.match(p.name).group(1)))
    
    if not files:
        raise FileNotFoundError(f"No layer files found in {base_dir}")
        
    return files

def load_and_flatten_layer(file_path: Path) -> torch.Tensor:
    """
    Load a .pt file containing a layer's update matrix/tensor and flatten it.
    """
    try:
        data = torch.load(file_path, map_location='cpu', weights_only=True)
    except Exception as e:
        raise RuntimeError(f"Failed to load {file_path}: {e}")
    
    if not isinstance(data, torch.Tensor):
        raise TypeError(f"Expected Tensor in {file_path}, got {type(data)}")
    
    return data.flatten()

def aggregate_opd_updates(
    seed: int,
    base_output_dir: Optional[Path] = None,
    output_filename: Optional[str] = None
) -> np.ndarray:
    """
    Aggregate per-layer update vectors for a specific OPD seed into a single matrix.
    
    Logic:
    1. Locate directory: results/opd/updates_seed_{seed}/
    2. Find all layer_{index:02d}.pt files.
    3. Flatten each layer's tensor.
    4. Concatenate all flattened layers into a single vector (n_params,).
    5. Stack these vectors for all steps into a matrix (steps, n_params).
    
    Args:
        seed: The random seed used for this run.
        base_output_dir: Base directory for results (defaults to 'results').
        output_filename: Optional filename override. Defaults to 'accumulated_matrix_seed_{seed}.npy'.
        
    Returns:
        np.ndarray: Matrix of shape (steps, n_params).
        
    Raises:
        FileNotFoundError: If the update directory or files are missing.
        RuntimeError: If aggregation fails due to shape mismatches or IO errors.
    """
    if base_output_dir is None:
        base_output_dir = Path("results")
        
    input_dir = base_output_dir / "opd" / f"updates_seed_{seed}"
    
    if not input_dir.exists():
        raise FileNotFoundError(f"OPD updates directory not found: {input_dir}")
        
    layer_files = find_layer_files(input_dir)
    logger.info(f"Found {len(layer_files)} layer files in {input_dir}")
    
    # We need to process files step-by-step if they are named by step, 
    # but the task description says: "Read all layer_{index:02d}.pt files for a seed"
    # and "stack these vectors for all steps".
    # Looking at T018b, it says "Save per-layer update vectors to separate files... layer_{index:02d}.pt".
    # This implies the directory contains files for ONE step? Or all steps?
    # Re-reading T018b: "Save per-layer update vectors to separate files results/opd/updates_seed_{i}/layer_{index:02d}.pt"
    # If there are multiple steps, usually they are in subdirectories or named with step index.
    # However, T018c says "Read all ... files for a seed ... stack these vectors for all steps".
    # This implies the directory `updates_seed_{i}` might contain multiple sets of layer files, 
    # OR the task implies that T018b saved them in a way that allows iteration.
    # 
    # Correction based on typical patterns: If T018b saves to `updates_seed_{i}/layer_XX.pt`, 
    # and we have multiple steps, the files must be distinguished. 
    # If T018b overwrites, we only have the last step.
    # Let's assume the directory structure from T018b might actually be:
    # `updates_seed_{i}/step_{s}/layer_{idx}.pt` OR the files are named `step_{s}_layer_{idx}.pt`.
    # BUT, the prompt for T018c says: "Read all `layer_{index:02d}.pt` files". 
    # This is ambiguous if there are multiple steps.
    # 
    # Let's look at the T018b description again: "Storage: Save per-layer update vectors to separate files `results/opd/updates_seed_{i}/layer_{index:02d}.pt`".
    # If this is run per step, and it overwrites, we lose history.
    # 
    # Hypothesis: The T018b implementation (which we assume exists) actually saves to a subdirectory per step, 
    # OR the files are named with the step index. 
    # Since I cannot see T018b code, I must infer the structure T018c expects.
    # T018c says: "Read all `layer_{index:02d}.pt` files for a seed".
    # If there are multiple steps, they must be in subdirectories named by step, e.g., `step_0/`, `step_1/`.
    # OR, the files are named `step_{s}_layer_{idx}.pt`.
    # 
    # Let's assume the directory `updates_seed_{i}` contains subdirectories for each step, 
    # or the files are named `step_{s}_layer_{idx}.pt`.
    # 
    # Wait, T018c says: "Read all `layer_{index:02d}.pt` files". This implies the files are literally named that.
    # If there are multiple steps, how are they distinguished? 
    # Perhaps the T018b implementation saves them in a way that T018c can iterate.
    # 
    # Let's re-read carefully: "Read all `layer_{index:02d}.pt` files for a seed, flatten each layer's update vector, 
    # concatenate them into a single vector... and stack these vectors for all steps".
    # This implies the input directory contains the data for ALL steps.
    # If the files are just `layer_00.pt`, `layer_01.pt`, etc., there is only one step's data.
    # 
    # Alternative interpretation: The `updates_seed_{i}` directory contains subdirectories `step_0`, `step_1`, etc.
    # And inside each, the files are `layer_00.pt`, `layer_01.pt`.
    # 
    # Let's assume the standard pattern for "per-step" logging in T018b:
    # It likely creates a directory `step_{step_id}` inside `updates_seed_{i}`.
    # 
    # I will implement logic to scan for step subdirectories. If none, treat the root as step 0.
    # If step subdirectories exist, sort them and process.
    
    step_dirs = []
    for item in input_dir.iterdir():
        if item.is_dir() and item.name.startswith("step_"):
            step_dirs.append(item)
    
    if not step_dirs:
        # If no step subdirectories, assume the files in the root are the only step (or we treat root as step 0)
        # But T018c implies "all steps". If only root exists, maybe it's a single step?
        # Or maybe the files are named `step_{s}_layer_{idx}.pt`?
        # Let's check for that pattern too.
        step_dirs = [input_dir] # Fallback: treat root as a single step container
    
    step_dirs.sort(key=lambda p: int(p.name.split('_')[1]))
    
    accumulated_vectors = []
    
    for step_dir in step_dirs:
        # Find layer files in this step directory
        layer_files = find_layer_files(step_dir)
        if not layer_files:
            logger.warning(f"No layer files found in step directory: {step_dir}")
            continue
        
        # Flatten and concatenate layers for this step
        current_step_vector_parts = []
        for lf in layer_files:
            try:
                flat_tensor = load_and_flatten_layer(lf)
                current_step_vector_parts.append(flat_tensor)
            except Exception as e:
                logger.error(f"Error processing {lf}: {e}")
                raise
        
        if current_step_vector_parts:
            full_vector = torch.cat(current_step_vector_parts)
            accumulated_vectors.append(full_vector)
    
    if not accumulated_vectors:
        raise RuntimeError("No valid update vectors found to aggregate.")
    
    # Stack into (steps, n_params)
    stacked = torch.stack(accumulated_vectors)
    logger.info(f"Aggregated {stacked.shape[0]} steps, each with {stacked.shape[1]} parameters.")
    
    # Convert to numpy and save
    output_path = base_output_dir / "opd"
    output_path.mkdir(parents=True, exist_ok=True)
    
    if output_filename is None:
        output_filename = f"accumulated_matrix_seed_{seed}.npy"
        
    save_path = output_path / output_filename
    np.save(save_path, stacked.numpy())
    
    logger.info(f"Saved accumulated matrix to {save_path}")
    return stacked.numpy()

def main():
    """CLI entry point for T018c."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Aggregate OPD updates into a single matrix.")
    parser.add_argument("--seed", type=int, required=True, help="Seed ID for the run.")
    parser.add_argument("--output-dir", type=str, default="results", help="Base output directory.")
    parser.add_argument("--output-file", type=str, default=None, help="Output filename (optional).")
    
    args = parser.parse_args()
    
    logging.basicConfig(level=logging.INFO)
    
    try:
        result = aggregate_opd_updates(
            seed=args.seed,
            base_output_dir=Path(args.output_dir),
            output_filename=args.output_file
        )
        print(f"Success: Aggregated matrix shape {result.shape} saved.")
    except Exception as e:
        logger.error(f"Failed to aggregate: {e}")
        raise

if __name__ == "__main__":
    main()
