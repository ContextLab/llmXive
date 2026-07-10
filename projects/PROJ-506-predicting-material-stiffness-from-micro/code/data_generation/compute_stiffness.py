"""
Compute effective elastic stiffness tensors using FFT-based homogenization.
"""
import numpy as np
from pathlib import Path
import json
from code.utils.fft_homogenization import compute_effective_stiffness

def load_microstructure(image_path: Path) -> np.ndarray:
    """Load binary microstructure image."""
    from skimage.io import imread
    image = imread(str(image_path))
    return (image > 128).astype(np.float32)

def compute_stiffness_tensor(image_path: Path, seed: int) -> dict:
    """
    Compute effective stiffness tensor for a microstructure.
    
    Returns:
        Dictionary with stiffness tensor, density, and seed.
    """
    microstructure = load_microstructure(image_path)
    density = np.mean(microstructure)
    
    # Compute effective stiffness using FFT homogenization
    # Assuming isotropic base material properties
    E_base = 210.0  # GPa
    nu_base = 0.3
    
    stiffness_tensor = compute_effective_stiffness(
        microstructure, 
        E_base=E_base, 
        nu_base=nu_base
    )
    
    return {
        "seed": seed,
        "density": float(density),
        "stiffness_tensor": stiffness_tensor.tolist(),
        "image_path": str(image_path)
    }

def main():
    """CLI entry point for stiffness computation."""
    import argparse
    parser = argparse.ArgumentParser(description="Compute stiffness tensors")
    parser.add_argument("--input_dir", type=str, default="data/raw", help="Input directory with PNGs")
    parser.add_argument("--output_file", type=str, default="data/raw/stiffness_metadata.json", help="Output JSON")
    args = parser.parse_args()
    
    input_path = Path(args.input_dir)
    output_path = Path(args.output_file)
    
    results = []
    for i, img_file in enumerate(sorted(input_path.glob("micro_*.png"))):
        try:
            seed = int(img_file.stem.split("_")[1])
            result = compute_stiffness_tensor(img_file, seed)
            results.append(result)
            print(f"Computed stiffness for {img_file.name}")
        except Exception as e:
            print(f"Failed to compute stiffness for {img_file.name}: {e}")
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
        
    print(f"Saved stiffness metadata to {output_path}")

if __name__ == "__main__":
    main()
