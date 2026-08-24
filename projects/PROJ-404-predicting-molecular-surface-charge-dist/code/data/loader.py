import os
import gc
import sys
import traceback
from typing import Optional, Iterator, Dict, Any, List
import torch
import numpy as np
from datasets import load_dataset
from data.dataset import MoleculeData
from utils import get_logger

logger = get_logger(__name__)

# Constants for memory management
MEMORY_LIMIT_GB = 2.0  # Conservative limit for free-tier runners

def get_memory_usage() -> float:
    """Get current memory usage in GB."""
    try:
        import resource
        usage = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        # On macOS ru_maxrss is in bytes, on Linux in KB
        if sys.platform == 'darwin':
            return usage / (1024 ** 3)
        else:
            return (usage * 1024) / (1024 ** 3)
    except Exception:
        logger.warning("Could not determine memory usage, returning 0.0")
        return 0.0

def adaptive_sample_size(batch_size: int, target_gb: float = MEMORY_LIMIT_GB) -> int:
    """
    Calculate max samples based on memory constraints.
    
    Args:
        batch_size: Target batch size for training
        target_gb: Target memory limit in GB
        
    Returns:
        Maximum number of samples that fit in memory
    """
    # Estimate per-molecule overhead (approximate for QM9-like data)
    # x: N_atoms * 1 (atomic number), pos: N_atoms * 3, y: N_atoms * 1
    # Assuming avg N_atoms ~ 10, overhead ~ 500 bytes per molecule + overhead
    estimated_bytes_per_mol = 5000  # Conservative estimate including PyG overhead
    
    max_bytes = target_gb * (1024 ** 3)
    max_samples = int(max_bytes / estimated_bytes_per_mol)
    
    # Ensure at least 1 batch
    return max(max_samples, batch_size * 2)

def run_memory_probe(batch_size: int = 32) -> None:
    """
    Probe memory usage by loading a small batch.
    
    Args:
        batch_size: Number of molecules to load for probing
    """
    logger.info("Running memory probe...")
    try:
        # Load a small sample to measure actual overhead
        dataset = load_dataset("qm9", split="train", streaming=True)
        sample_batch = []
        for i, item in enumerate(dataset):
            if i >= batch_size:
                break
            sample_batch.append(item)
        
        # Convert to MoleculeData to measure actual overhead
        molecules = []
        for item in sample_batch:
            mol = MoleculeData(
                x=torch.tensor(item['atomic_numbers'], dtype=torch.long),
                pos=torch.tensor(item['positions'], dtype=torch.float32),
                y=torch.tensor(item['charges'], dtype=torch.float32),
                scaffold_id=str(i)
            )
            molecules.append(mol)
        
        usage_before = get_memory_usage()
        # Force garbage collection
        gc.collect()
        usage_after = get_memory_usage()
        
        logger.info(f"Memory probe complete. Usage: {usage_after:.2f} GB")
        
        # Clean up
        del molecules, sample_batch, dataset
        gc.collect()
        
    except Exception as e:
        logger.error(f"Memory probe failed: {e}")
        raise

def create_streaming_loader(
    split: str = "train",
    batch_size: int = 32,
    num_workers: int = 0
) -> Iterator[MoleculeData]:
    """
    Create a streaming data loader for QM9 with Merz-Kollman charges.
    
    Args:
        split: Dataset split ('train', 'val', 'test')
        batch_size: Batch size for iteration
        num_workers: Number of worker processes (0 for single-process)
        
    Yields:
        Validated MoleculeData objects
    """
    # Map split to dataset configuration
    # QM9 dataset on HuggingFace
    try:
        logger.info(f"Loading dataset with streaming=True for split: {split}")
        dataset = load_dataset("qm9", split=split, streaming=True)
    except Exception as e:
        logger.error(f"Failed to load dataset from HuggingFace: {e}")
        raise RuntimeError(f"Real data fetch failed: {e}")

    # Apply scaffold split indices if available
    # For now, use the raw stream with validation
    logger.info("Starting data validation and filtering...")
    
    count = 0
    for item in dataset:
        try:
            # Validate and transform item
            mol = validate_and_transform(item)
            if mol is not None:
                yield mol
                count += 1
                if count % 1000 == 0:
                    logger.debug(f"Processed {count} molecules")
        except Exception as e:
            logger.warning(f"Skipping molecule due to validation error: {e}")
            continue

def validate_and_transform(item: Dict[str, Any]) -> Optional[MoleculeData]:
    """
    Validate a raw dataset item and transform it to MoleculeData.
    
    Implements T015 requirements:
    - Filter molecules with undefined bonds (represented as -1 in connectivity)
    - Impute missing coordinates with mean of available coordinates
    - Ensure non-null charges
    
    Args:
        item: Raw dataset item from HuggingFace
        
    Returns:
        Validated MoleculeData or None if molecule should be filtered
    """
    try:
        atomic_numbers = item.get('atomic_numbers')
        positions = item.get('positions')
        charges = item.get('charges')
        connectivity = item.get('connectivity', None)
        
        # Check for None/missing basic attributes
        if atomic_numbers is None or positions is None or charges is None:
            logger.warning("Missing basic attributes, filtering molecule")
            return None
        
        # Convert to tensors
        x = torch.tensor(atomic_numbers, dtype=torch.long)
        pos = torch.tensor(positions, dtype=torch.float32)
        y = torch.tensor(charges, dtype=torch.float32)
        
        # T015: Check for non-null charges
        if torch.isnan(y).any() or torch.isinf(y).any():
            logger.warning("NaN or Inf charges detected, filtering molecule")
            return None
        
        # T015: Handle missing coordinates
        if pos.isnan().any() or pos.isinf().any():
            logger.info("Missing/invalid coordinates detected, attempting imputation")
            # Impute with mean of valid coordinates
            valid_mask = ~(pos.isnan() | pos.isinf())
            if valid_mask.any():
                mean_pos = pos[valid_mask].mean(dim=0)
                pos[~valid_mask] = mean_pos
                logger.debug(f"Imputed {(~valid_mask).sum().item()} coordinate entries with mean")
            else:
                logger.warning("All coordinates invalid, filtering molecule")
                return None
        
        # T015: Handle undefined bonds in connectivity
        if connectivity is not None:
            conn_tensor = torch.tensor(connectivity, dtype=torch.long)
            # Check for -1 (undefined bonds)
            if (conn_tensor == -1).any():
                logger.warning("Undefined bonds (-1) detected, filtering molecule")
                return None
            # Validate connectivity alignment (number of edges vs atoms)
            num_atoms = len(x)
            if conn_tensor.shape[0] != num_atoms or conn_tensor.shape[1] != num_atoms:
                logger.warning(f"Connectivity shape {conn_tensor.shape} does not match atom count {num_atoms}, filtering")
                return None
        
        # Create MoleculeData object
        # scaffold_id will be set by the splitting logic later
        return MoleculeData(
            x=x,
            pos=pos,
            y=y,
            scaffold_id=""  # Placeholder, will be set by apply_scaffold_split
        )
        
    except Exception as e:
        logger.error(f"Error transforming molecule: {e}")
        raise

def validate_data_integrity(molecule: MoleculeData) -> bool:
    """
    Perform final integrity checks on a MoleculeData object.
    
    Args:
        molecule: MoleculeData object to validate
        
    Returns:
        True if molecule passes all checks, False otherwise
    """
    try:
        # Check dimensions match
        if len(molecule.x) != len(molecule.pos):
            logger.error(f"Dimension mismatch: x ({len(molecule.x)}) != pos ({len(molecule.pos)})")
            return False
        
        if len(molecule.x) != len(molecule.y):
            logger.error(f"Dimension mismatch: x ({len(molecule.x)}) != y ({len(molecule.y)})")
            return False
        
        # Check for NaN/Inf in all tensors
        if torch.isnan(molecule.x).any() or torch.isinf(molecule.x).any():
            logger.error("NaN/Inf in atomic numbers")
            return False
            
        if torch.isnan(molecule.pos).any() or torch.isinf(molecule.pos).any():
            logger.error("NaN/Inf in positions")
            return False
            
        if torch.isnan(molecule.y).any() or torch.isinf(molecule.y).any():
            logger.error("NaN/Inf in charges")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"Integrity check failed: {e}")
        return False

def filter_invalid_molecules(
    iterator: Iterator[MoleculeData]
) -> Iterator[MoleculeData]:
    """
    Filter an iterator of molecules, keeping only valid ones.
    
    Args:
        iterator: Iterator of MoleculeData objects
        
    Yields:
        Only valid MoleculeData objects
    """
    valid_count = 0
    invalid_count = 0
    
    for mol in iterator:
        if validate_data_integrity(mol):
            valid_count += 1
            yield mol
        else:
            invalid_count += 1
            logger.debug(f"Filtered invalid molecule. Total invalid: {invalid_count}")
    
    logger.info(f"Filtering complete: {valid_count} valid, {invalid_count} invalid")

# Main execution block for testing
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test data loader with validation")
    parser.add_argument("--split", type=str, default="train", help="Dataset split")
    parser.add_argument("--limit", type=int, default=100, help="Limit number of molecules to process")
    args = parser.parse_args()
    
    logger.info(f"Starting data loader test for split: {args.split}")
    
    loader = create_streaming_loader(split=args.split, batch_size=1)
    
    processed = 0
    for mol in loader:
        if processed >= args.limit:
            break
        
        # Verify the molecule passes integrity checks
        if validate_data_integrity(mol):
            processed += 1
            if processed % 10 == 0:
                logger.info(f"Processed {processed} valid molecules")
        else:
            logger.warning(f"Molecule failed integrity check at index {processed}")
    
    logger.info(f"Test complete. Processed {processed} molecules.")