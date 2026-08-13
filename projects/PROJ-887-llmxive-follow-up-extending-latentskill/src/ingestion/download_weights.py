"""
Download LoRA weights for ALFWorld and Search-QA benchmarks.

This script fetches real LoRA weights from HuggingFace datasets.
If real weights are unavailable, it generates synthetic proxy weights
as per specification Assumptions.
"""

import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import numpy as np

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.utils.config import get_project_root, get_data_path, ensure_directories
from src.validate.citation_check import verify_sources, load_data_sources

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_real_weights(
    dataset_name: str,
    file_path: str,
    max_files: int = 10
) -> Optional[Tuple[np.ndarray, np.ndarray]]:
    """
    Attempt to load real LoRA weights from a HuggingFace dataset.

    Args:
        dataset_name: HuggingFace dataset name (e.g., 'latent-skills/alfworld-weights')
        file_path: Path pattern within the dataset (e.g., 'weights/alfworld/*.npz')
        max_files: Maximum number of weight files to process

    Returns:
        Tuple of (A_matrix, B_matrix) if successful, None otherwise
    """
    try:
        from datasets import load_dataset
        import glob

        logger.info(f"Attempting to load real weights from {dataset_name}")

        # Load dataset
        dataset = load_dataset(dataset_name, split="train")

        # Find weight files
        weight_files = []
        for item in dataset:
            if 'file_path' in item and item['file_path'].endswith('.npz'):
                weight_files.append(item['file_path'])

        if not weight_files:
            logger.warning(f"No .npz files found in dataset {dataset_name}")
            return None

        # Limit to max_files
        weight_files = weight_files[:max_files]
        logger.info(f"Found {len(weight_files)} weight files")

        # Load first available weight file as representative
        # In a real scenario, we might want to aggregate multiple files
        first_file = weight_files[0]

        # Try to download and load the file
        # Note: This is a simplified approach; real implementation might need
        # more sophisticated file handling
        if 'hf://' in first_file or first_file.startswith('hf://'):
            # HuggingFace datasets handles this automatically
            file_data = dataset[first_file]
            # Assuming the dataset contains the actual arrays
            if 'A' in file_data and 'B' in file_data:
                A = np.array(file_data['A'])
                B = np.array(file_data['B'])
                return A, B
        else:
            # Try to load from local path if already downloaded
            local_path = Path(file_path)
            if local_path.exists():
                data = np.load(local_path)
                if 'A' in data and 'B' in data:
                    return data['A'], data['B']

        logger.warning(f"Could not load weights from {first_file}")
        return None

    except Exception as e:
        logger.warning(f"Failed to load real weights: {e}")
        return None

def generate_proxy_weights(
    in_features: int = 4096,
    out_features: int = 1024,
    seed: int = 42
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Generate synthetic proxy weights using random normal distributions.

    Args:
        in_features: Input dimension
        out_features: Output dimension
        seed: Random seed for reproducibility

    Returns:
        Tuple of (A_matrix, B_matrix)
    """
    logger.info(f"Generating synthetic proxy weights: {in_features}x{out_features}")
    np.random.seed(seed)

    # Generate A and B matrices with random normal distribution
    # LoRA typically uses low-rank decomposition: W + BA
    A = np.random.normal(0, 0.02, (out_features, in_features))
    B = np.random.normal(0, 0.02, (in_features, out_features))

    return A, B

def save_weights(
    A: np.ndarray,
    B: np.ndarray,
    output_path: Path,
    source_type: str
) -> None:
    """
    Save weights to an NPZ file.

    Args:
        A: First weight matrix
        B: Second weight matrix
        output_path: Path to save the NPZ file
        source_type: Type of source ('real' or 'synthetic')
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    np.savez(
        output_path,
        A=A,
        B=B,
        source_type=source_type,
        A_shape=A.shape,
        B_shape=B.shape
    )

    logger.info(f"Saved weights to {output_path}")
    logger.info(f"  A shape: {A.shape}")
    logger.info(f"  B shape: {B.shape}")
    logger.info(f"  Source: {source_type}")

def process_dataset(
    dataset_name: str,
    file_pattern: str,
    output_filename: str,
    in_features: int = 4096,
    out_features: int = 1024
) -> None:
    """
    Process a dataset: try to load real weights, fall back to synthetic if needed.

    Args:
        dataset_name: HuggingFace dataset name
        file_pattern: Pattern for weight files within the dataset
        output_filename: Name of the output file
        in_features: Input dimension for synthetic weights
        out_features: Output dimension for synthetic weights
    """
    logger.info(f"Processing dataset: {dataset_name}")

    output_path = get_data_path() / "raw" / output_filename
    ensure_directories()

    # Try to load real weights first
    real_weights = load_real_weights(dataset_name, file_pattern)

    if real_weights is not None:
        A, B = real_weights
        save_weights(A, B, output_path, "real")
    else:
        logger.warning(f"Real weights not available for {dataset_name}, generating synthetic")
        A, B = generate_proxy_weights(in_features, out_features)
        save_weights(A, B, output_path, "synthetic")

def main() -> None:
    """Main entry point for the download_weights script."""
    logger.info("Starting weight download process")

    # Verify citation check was run first
    logger.info("Verifying citation check results...")
    verification_path = get_data_path() / "processed" / "citation_verification.json"

    if not verification_path.exists():
        logger.warning("Citation verification file not found. Running citation check...")
        from src.validate.citation_check import main as citation_main
        citation_main()

    # Load data sources to verify datasets exist
    data_sources = load_data_sources()

    # Process ALFWorld weights
    process_dataset(
        dataset_name="latent-skills/alfworld-weights",
        file_pattern="weights/alfworld/*.npz",
        output_filename="alfworld_weights.npz",
        in_features=4096,
        out_features=1024
    )

    # Process Search-QA weights
    process_dataset(
        dataset_name="latent-skills/searchqa-weights",
        file_pattern="weights/searchqa/*.npz",
        output_filename="searchqa_weights.npz",
        in_features=4096,
        out_features=1024
    )

    logger.info("Weight download process completed")

if __name__ == "__main__":
    main()
