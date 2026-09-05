"""
Stiffness tensor calculator using FFT-based homogenization.

Computes effective elastic stiffness tensors for generated microstructures.
"""
import numpy as np
from pathlib import Path
import json
import logging
import argparse
from skimage import io
from code.utils.fft_homogenization import compute_effective_stiffness

logger = logging.getLogger(__name__)

def load_microstructure(image_path: Path) -> np.ndarray:
    """
    Load a microstructure image from disk.
    
    Args:
        image_path: Path to the PNG image file
        
    Returns:
        2D numpy array (binary: 0=void, 1=inclusion)
    """
    if not image_path.exists():
        raise FileNotFoundError(f"Microstructure image not found: {image_path}")
        
    image = io.imread(image_path)
    # Convert to binary (threshold at 128)
    # Handle grayscale or RGB
    if image.ndim == 3:
        # Convert RGB to grayscale if needed
        image = np.mean(image, axis=2)
    
    binary = (image > 128).astype(np.float32)
    return binary

def compute_stiffness_tensor(
    image: np.ndarray,
    inclusion_stiffness: float = 200.0,
    void_stiffness: float = 0.01
) -> np.ndarray:
    """
    Compute the effective stiffness tensor for a microstructure.
    
    Args:
        image: Binary microstructure image (float32, values 0.0 or 1.0)
        inclusion_stiffness: Young's modulus of inclusion phase (GPa)
        void_stiffness: Young's modulus of void phase (GPa)
        
    Returns:
        4x4 stiffness tensor in Voigt notation (plane strain)
    """
    # Define material properties for 2D plane strain
    # Using isotropic materials with same Poisson's ratio
    nu = 0.3
    
    # Create phase map (0 = void, 1 = inclusion)
    phase_map = np.zeros_like(image, dtype=np.int32)
    phase_map[image > 0.5] = 1  # Inclusion phase
    
    # Call FFT homogenization solver
    stiffness_tensor = compute_effective_stiffness(
        phase_map=phase_map,
        inclusion_E=inclusion_stiffness,
        void_E=void_stiffness,
        nu=nu
    )
    
    return stiffness_tensor

def main(args) -> int:
    """
    Main entry point for stiffness computation.
    
    Args:
        args: Namespace with input_dir, output_dir, metadata_file
        
    Returns:
        Exit code (0 for success, 1 for failure)
    """
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    metadata_file = Path(args.metadata_file)
    
    if not input_dir.exists():
        logger.error(f"Input directory does not exist: {input_dir}")
        return 1
        
    if not metadata_file.exists():
        logger.error(f"Metadata file does not exist: {metadata_file}")
        return 1
    
    # Load metadata
    with open(metadata_file, 'r') as f:
        metadata = json.load(f)
    
    logger.info(f"Computing stiffness tensors for {len(metadata)} microstructures...")
    
    success_count = 0
    failure_count = 0
    
    for entry in metadata:
        image_path = Path(entry['image_path'])
        seed = entry['seed']
        
        # Resolve relative path if needed
        if not image_path.is_absolute():
            image_path = input_dir / image_path
        
        try:
            # Load image
            image = load_microstructure(image_path)
            
            # Compute stiffness tensor
            stiffness = compute_stiffness_tensor(image)
            
            # Update metadata with stiffness tensor
            entry['stiffness_tensor'] = stiffness.tolist()
            
            logger.info(f"Computed stiffness for seed {seed}: C11={stiffness[0,0]:.2f} GPa")
            success_count += 1
            
        except Exception as e:
            logger.error(f"Failed to compute stiffness for seed {seed}: {e}")
            import traceback
            traceback.print_exc()
            failure_count += 1
            # Continue processing other entries
    
    # Save updated metadata
    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    logger.info(f"Stiffness computation complete. "
               f"Success: {success_count}, Failed: {failure_count}. "
               f"Updated metadata saved to {metadata_file}")
    
    return 0 if failure_count == 0 else 1

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Compute stiffness tensors")
    parser.add_argument("--input_dir", type=str, default="data/raw",
                      help="Directory containing microstructure images")
    parser.add_argument("--output_dir", type=str, default="data/raw",
                      help="Directory to save results")
    parser.add_argument("--metadata_file", type=str, default="data/raw/metadata.json",
                      help="Path to metadata JSON file")
    args = parser.parse_args()
    exit(main(args))
