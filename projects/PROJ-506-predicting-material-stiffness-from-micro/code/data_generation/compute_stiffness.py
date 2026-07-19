"""
Stiffness Tensor Calculator using FFT Homogenization.

Computes effective elastic stiffness tensors for generated microstructures.
"""

import numpy as np
from pathlib import Path
import json
from code.utils.fft_homogenization import compute_effective_stiffness

def load_microstructure(image_path: Path) -> np.ndarray:
    """
    Load a microstructure image from disk.

    Args:
        image_path: Path to the PNG file.

    Returns:
        2D numpy array representing the microstructure.
    """
    from skimage import io
    image = io.imread(image_path)
    # Normalize to 0-1 if necessary
    if image.max() > 1.0:
        image = image / 255.0
    return image.astype(np.float32)

def compute_stiffness_tensor(
    image: np.ndarray,
    matrix_modulus: float = 70.0,
    inclusion_modulus: float = 200.0,
    poisson_ratio: float = 0.3
) -> np.ndarray:
    """
    Compute the effective stiffness tensor for a microstructure.

    Args:
        image: 2D numpy array (0.0 = matrix, 1.0 = inclusion).
        matrix_modulus: Young's modulus of the matrix phase.
        inclusion_modulus: Young's modulus of the inclusion phase.
        poisson_ratio: Poisson's ratio (assumed same for both phases).

    Returns:
        6x6 stiffness tensor in Voigt notation (for 3D, projected from 2D).
    """
    # Prepare material property map
    # Simple mapping: 0 -> matrix, 1 -> inclusion
    # We use a simplified 2D plane strain assumption projected to 3D tensor
    E_matrix = matrix_modulus
    E_inclusion = inclusion_modulus
    nu = poisson_ratio

    # Create material property field
    # For 2D plane strain, we compute C_11, C_12, C_66
    # Then project to 3D Voigt notation for consistency
    
    # This is a simplified placeholder; real implementation uses FFT solver
    # The actual FFT solver is in code.utils.fft_homogenization
    
    stiffness = compute_effective_stiffness(
        image,
        E_matrix,
        E_inclusion,
        nu
    )
    return stiffness

def main():
    """Compute stiffness for sample microstructures."""
    print("Stiffness calculator loaded.")
