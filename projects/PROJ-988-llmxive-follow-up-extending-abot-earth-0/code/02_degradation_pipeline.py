"""
Degradation Pipeline for ABot-Earth.
Applies temporal shifts and systematically varies NNF (Normalized Noise Fraction)
to generate a dataset of degraded scenes for fidelity analysis.
"""
import os
import sys
import json
import logging
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional
import numpy as np

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.degradation import degrade_scene, validate_degradation_params
from lib.logging_config import setup_logging, get_logger
from lib.models import DegradedScene

logger = get_logger(__name__)

def setup_directories() -> Dict[str, Path]:
    """Ensure output directories exist."""
    base = Path(__file__).parent.parent
    dirs = {
        'patches': base / 'data' / 'processed' / 'patches_100m2',
        'nnf_varied': base / 'data' / 'processed' / 'nnf_varied_scenes',
        'manifest': base / 'data' / 'processed'
    }
    
    for key, path in dirs.items():
        path.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Directory ensured: {path}")
        
    return dirs

def load_patches_manifest(manifest_path: Optional[Path] = None) -> List[Dict[str, Any]]:
    """Load the manifest of extracted patches."""
    if manifest_path is None:
        manifest_path = Path(__file__).parent.parent / 'data' / 'processed' / 'patch_manifest.csv'
    
    if not manifest_path.exists():
        raise FileNotFoundError(f"Patch manifest not found: {manifest_path}")
    
    # Simple CSV loader (assuming format: sample_id, path, original_resolution, etc.)
    patches = []
    with open(manifest_path, 'r') as f:
        # Skip header if present, assuming simple line-based or CSV
        # Using a basic split for robustness if headers vary
        lines = f.readlines()
        if not lines:
            return []
        
        # Assume CSV format with headers
        import csv
        reader = csv.DictReader(lines)
        for row in reader:
            patches.append(row)
    
    logger.info(f"Loaded {len(patches)} patches from manifest.")
    return patches

def load_patch_image(patch_path: Path) -> np.ndarray:
    """Load a patch image from disk."""
    if not patch_path.exists():
        raise FileNotFoundError(f"Patch file not found: {patch_path}")
    
    from PIL import Image
    img = Image.open(patch_path)
    if img.mode != 'RGB':
        img = img.convert('RGB')
    return np.array(img)

def run_degradation_pipeline(
    patches: List[Dict[str, Any]],
    output_dir: Path,
    nnf_values: List[float],
    temporal_shift_days: List[int],
    base_resolution: float = 10.0,
    target_resolution: float = 30.0
) -> List[Dict[str, Any]]:
    """
    Run the degradation pipeline on a list of patches with varying NNF and temporal shifts.
    
    Args:
        patches: List of patch metadata dictionaries.
        output_dir: Directory to save degraded scenes.
        nnf_values: List of NNF values to sweep (e.g., [0.0, 0.1, 0.3, 0.5]).
        temporal_shift_days: List of temporal shifts to apply.
        base_resolution: Original resolution of patches.
        target_resolution: Target resolution for degradation.
        
    Returns:
        List of metadata dictionaries for the generated scenes.
    """
    results = []
    
    for patch_meta in patches:
        sample_id = patch_meta.get('sample_id', 'unknown')
        patch_path = Path(patch_meta['path'])
        
        logger.info(f"Processing patch: {sample_id}")
        
        try:
            image = load_patch_image(patch_path)
        except Exception as e:
            logger.error(f"Failed to load patch {sample_id}: {e}")
            continue
        
        # Sweep through NNF and temporal shifts
        for nnf in nnf_values:
            for shift in temporal_shift_days:
                # Generate unique ID for this variation
                var_id = f"{sample_id}_nnf{nnf:.1f}_shift{shift}"
                output_path = output_dir / f"{var_id}.png"
                
                # Run degradation
                try:
                    result = degrade_scene(
                        image=image,
                        original_resolution=base_resolution,
                        target_resolution=target_resolution,
                        cloud_coverage=0.1, # Fixed cloud coverage for this sweep, or parameterize
                        nnf=nnf,
                        temporal_shift_days=shift,
                        seed=42 # Fixed seed for reproducibility of the sweep
                    )
                    
                    # Save image
                    from PIL import Image
                    img_out = Image.fromarray(result['degraded_image'])
                    img_out.save(output_path)
                    
                    # Record metadata
                    meta = {
                        'variation_id': var_id,
                        'source_patch_id': sample_id,
                        'output_path': str(output_path),
                        'nnf': nnf,
                        'temporal_shift_days': shift,
                        'target_resolution': target_resolution,
                        'cloud_coverage': result['params']['cloud_coverage'],
                        'status': 'success'
                    }
                    results.append(meta)
                    
                except Exception as e:
                    logger.error(f"Degradation failed for {var_id}: {e}")
                    results.append({
                        'variation_id': var_id,
                        'source_patch_id': sample_id,
                        'status': 'failed',
                        'error': str(e)
                    })
    
    return results

def save_manifest(results: List[Dict[str, Any]], output_path: Path) -> None:
    """Save the degradation manifest to JSON."""
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Saved manifest to {output_path}")

def main():
    """Main entry point for the degradation pipeline."""
    parser = argparse.ArgumentParser(description="Run degradation pipeline with NNF sweep and temporal shifts.")
    parser.add_argument("--nnf-values", type=float, nargs="+", default=[0.0, 0.1, 0.2, 0.3, 0.5],
                      help="List of NNF values to sweep.")
    parser.add_argument("--temporal-shifts", type=int, nargs="+", default=[0, 30, 60, 90],
                      help="List of temporal shifts (days) to apply.")
    parser.add_argument("--base-resolution", type=float, default=10.0,
                      help="Original resolution of input patches (m/pixel).")
    parser.add_argument("--target-resolution", type=float, default=30.0,
                      help="Target resolution for degradation (m/pixel).")
    
    args = parser.parse_args()
    
    # Setup
    setup_logging(level=logging.INFO)
    dirs = setup_directories()
    
    # Load patches
    patches = load_patches_manifest()
    if not patches:
        logger.warning("No patches found. Exiting.")
        return
    
    # Run pipeline
    logger.info(f"Starting degradation sweep: {len(patches)} patches x {len(args.nnf_values)} NNFs x {len(args.temporal_shifts)} shifts")
    results = run_degradation_pipeline(
        patches=patches,
        output_dir=dirs['nnf_varied'],
        nnf_values=args.nnf_values,
        temporal_shift_days=args.temporal_shifts,
        base_resolution=args.base_resolution,
        target_resolution=args.target_resolution
    )
    
    # Save manifest
    manifest_path = dirs['manifest'] / 'degraded_manifest.json'
    save_manifest(results, manifest_path)
    
    success_count = sum(1 for r in results if r.get('status') == 'success')
    logger.info(f"Pipeline complete. {success_count}/{len(results)} successful.")

if __name__ == "__main__":
    main()