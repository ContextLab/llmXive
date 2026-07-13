"""
Task T016: Validate synthetic cloud masks against real cloud masks using Kolmogorov-Smirnov test.

This script performs the following:
1. Loads real cloud mask subsets from data/raw/real_cloud_masks_subset/
2. Generates synthetic cloud masks using the degradation pipeline (code/lib/degradation.py)
3. Computes statistical distributions (pixel density, cluster sizes) for both
4. Performs Kolmogorov-Smirnov (KS) tests to compare distributions
5. Outputs similarity scores to data/results/mask_similarity_score.json
6. If similarity < 0.8, logs recommendations for tuning degradation parameters
"""

import os
import sys
import json
import logging
import numpy as np
from pathlib import Path
from scipy import stats
from typing import Dict, List, Tuple, Optional
from PIL import Image

# Project imports
from lib.degradation import generate_cloud_mask, validate_degradation_params
from lib.logging_config import setup_logging, get_logger
from lib.config import load_environment_config, get_config

# Configure logging
logger = get_logger(__name__)

def load_real_masks(mask_dir: Path) -> List[np.ndarray]:
    """
    Load real cloud masks from the specified directory.
    Expects .tif or .png files containing binary masks (0=clear, 1=cloud).
    """
    masks = []
    if not mask_dir.exists():
        logger.warning(f"Real mask directory not found: {mask_dir}")
        return masks
        
    for file_path in mask_dir.glob("*"):
        if file_path.suffix.lower() in ['.tif', '.png', '.jpg', '.jpeg']:
            try:
                img = Image.open(file_path).convert('L')
                mask = np.array(img)
                # Normalize to 0-1 if needed
                if mask.max() > 1:
                    mask = mask / 255.0
                masks.append(mask)
                logger.info(f"Loaded real mask: {file_path.name}")
            except Exception as e:
                logger.error(f"Failed to load {file_path}: {e}")
    
    if not masks:
        logger.warning(f"No valid masks found in {mask_dir}")
    
    return masks

def extract_mask_statistics(masks: List[np.ndarray]) -> Dict[str, np.ndarray]:
    """
    Extract statistical features from cloud masks:
    - Pixel density (fraction of cloud pixels)
    - Cluster sizes (connected component analysis)
    - Edge density
    """
    if not masks:
        return {
            'pixel_densities': np.array([]),
            'cluster_sizes': np.array([]),
            'edge_densities': np.array([])
        }
    
    pixel_densities = []
    cluster_sizes = []
    edge_densities = []
    
    from scipy import ndimage
    
    for mask in masks:
        # Pixel density
        density = np.mean(mask)
        pixel_densities.append(density)
        
        # Cluster analysis (connected components)
        labeled_array, num_features = ndimage.label(mask > 0.5)
        if num_features > 0:
            # Get sizes of each component
            sizes = np.bincount(labeled_array.ravel())
            sizes = sizes[1:]  # Remove background
            cluster_sizes.extend(sizes)
        
        # Edge density (using Sobel-like approximation)
        if mask.ndim == 2:
            # Simple edge detection: count pixels with non-zero neighbors
            padded = np.pad(mask, 1, mode='edge')
            diff = np.abs(padded[2:, 1:-1] - padded[:-2, 1:-1]) + \
                   np.abs(padded[1:-1, 2:] - padded[1:-1, :-2])
            edges = np.sum(diff > 0.1)
            edge_densities.append(edges / mask.size)
    
    return {
        'pixel_densities': np.array(pixel_densities),
        'cluster_sizes': np.array(cluster_sizes) if cluster_sizes else np.array([]),
        'edge_densities': np.array(edge_densities)
    }

def perform_ks_test(stats1: np.ndarray, stats2: np.ndarray, name: str = "distribution") -> Dict[str, float]:
    """
    Perform Kolmogorov-Smirnov test between two distributions.
    Returns D statistic and p-value.
    """
    if len(stats1) < 5 or len(stats2) < 5:
        logger.warning(f"Insufficient samples for KS test on {name}: {len(stats1)} vs {len(stats2)}")
        return {'D': 1.0, 'p_value': 0.0, 'similarity': 0.0}
    
    # Filter out zeros for cluster sizes to avoid division issues
    if name == "cluster_sizes":
        stats1 = stats1[stats1 > 0]
        stats2 = stats2[stats2 > 0]
        if len(stats1) < 5 or len(stats2) < 5:
            logger.warning(f"Insufficient non-zero clusters for KS test on {name}")
            return {'D': 1.0, 'p_value': 0.0, 'similarity': 0.0}
    
    try:
        D, p_value = stats.ks_2samp(stats1, stats2)
        # Convert D to similarity (1 - D)
        similarity = max(0.0, 1.0 - D)
        return {'D': float(D), 'p_value': float(p_value), 'similarity': float(similarity)}
    except Exception as e:
        logger.error(f"KS test failed for {name}: {e}")
        return {'D': 1.0, 'p_value': 0.0, 'similarity': 0.0}

def generate_synthetic_masks(config: Dict, num_samples: int = 50) -> List[np.ndarray]:
    """
    Generate synthetic cloud masks using the degradation pipeline.
    """
    masks = []
    base_size = (1024, 1024)  # Standard patch size
    
    for i in range(num_samples):
        try:
            # Vary parameters slightly to create a distribution
            cloud_prob = config.get('cloud_probability', 0.3) + np.random.uniform(-0.1, 0.1)
            cloud_prob = max(0.0, min(1.0, cloud_prob))
            
            mask = generate_cloud_mask(
                shape=base_size,
                cloud_probability=cloud_prob,
                seed=i
            )
            masks.append(mask)
            logger.debug(f"Generated synthetic mask {i+1}/{num_samples}")
        except Exception as e:
            logger.error(f"Failed to generate synthetic mask {i}: {e}")
    
    return masks

def tune_parameters(current_config: Dict, results: Dict) -> Dict:
    """
    Suggest parameter tuning if similarity is below threshold.
    """
    new_config = current_config.copy()
    recommendations = []
    
    if results.get('pixel_density', {}).get('similarity', 1.0) < 0.8:
        # Adjust cloud probability
        current_prob = new_config.get('cloud_probability', 0.3)
        new_config['cloud_probability'] = current_prob + 0.05
        recommendations.append("Increase cloud_probability to match real mask density")
    
    if results.get('cluster_sizes', {}).get('similarity', 1.0) < 0.8:
        # Adjust fractal dimension or smoothing
        current_smooth = new_config.get('smoothing_sigma', 5.0)
        new_config['smoothing_sigma'] = current_smooth * 1.2
        recommendations.append("Increase smoothing_sigma to match cluster size distribution")
    
    if results.get('edge_density', {}).get('similarity', 1.0) < 0.8:
        # Adjust noise or edge parameters
        current_noise = new_config.get('noise_fraction', 0.0)
        new_config['noise_fraction'] = min(0.3, current_noise + 0.05)
        recommendations.append("Adjust noise_fraction to match edge density")
    
    return new_config, recommendations

def main():
    """
    Main execution function for T016.
    """
    # Load configuration
    config = load_environment_config()
    base_dir = Path(config.get('base_dir', '.'))
    
    # Define paths
    real_mask_dir = base_dir / 'data' / 'raw' / 'real_cloud_masks_subset'
    output_dir = base_dir / 'data' / 'results'
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = output_dir / 'mask_similarity_score.json'
    
    logger.info("Starting T016: Cloud Mask Validation")
    logger.info(f"Real mask directory: {real_mask_dir}")
    
    # Load real masks
    logger.info("Loading real cloud masks...")
    real_masks = load_real_masks(real_mask_dir)
    logger.info(f"Loaded {len(real_masks)} real masks")
    
    if len(real_masks) < 5:
        logger.error("Insufficient real masks for statistical comparison. Need at least 5 samples.")
        # Write failure report
        failure_report = {
            'status': 'failed',
            'reason': 'Insufficient real masks for KS test',
            'real_mask_count': len(real_masks),
            'required_minimum': 5
        }
        with open(output_file, 'w') as f:
            json.dump(failure_report, f, indent=2)
        return 1
    
    # Extract real mask statistics
    logger.info("Extracting real mask statistics...")
    real_stats = extract_mask_statistics(real_masks)
    
    # Generate synthetic masks
    logger.info("Generating synthetic masks for comparison...")
    degradation_config = {
        'cloud_probability': 0.3,
        'smoothing_sigma': 5.0,
        'noise_fraction': 0.0,
        'fractal_dimension': 2.5
    }
    synthetic_masks = generate_synthetic_masks(degradation_config, num_samples=50)
    logger.info(f"Generated {len(synthetic_masks)} synthetic masks")
    
    # Extract synthetic mask statistics
    logger.info("Extracting synthetic mask statistics...")
    synthetic_stats = extract_mask_statistics(synthetic_masks)
    
    # Perform KS tests
    logger.info("Performing Kolmogorov-Smirnov tests...")
    
    results = {
        'status': 'completed',
        'real_mask_count': len(real_masks),
        'synthetic_mask_count': len(synthetic_masks),
        'tests': {}
    }
    
    overall_similarity = 1.0
    
    # Test 1: Pixel Density
    if len(real_stats['pixel_densities']) > 0 and len(synthetic_stats['pixel_densities']) > 0:
        test_result = perform_ks_test(
            real_stats['pixel_densities'],
            synthetic_stats['pixel_densities'],
            "pixel_density"
        )
        results['tests']['pixel_density'] = test_result
        overall_similarity = min(overall_similarity, test_result['similarity'])
        logger.info(f"Pixel Density KS Test: D={test_result['D']:.3f}, p={test_result['p_value']:.3f}, similarity={test_result['similarity']:.3f}")
    
    # Test 2: Cluster Sizes
    if len(real_stats['cluster_sizes']) > 0 and len(synthetic_stats['cluster_sizes']) > 0:
        test_result = perform_ks_test(
            real_stats['cluster_sizes'],
            synthetic_stats['cluster_sizes'],
            "cluster_sizes"
        )
        results['tests']['cluster_sizes'] = test_result
        overall_similarity = min(overall_similarity, test_result['similarity'])
        logger.info(f"Cluster Sizes KS Test: D={test_result['D']:.3f}, p={test_result['p_value']:.3f}, similarity={test_result['similarity']:.3f}")
    
    # Test 3: Edge Density
    if len(real_stats['edge_densities']) > 0 and len(synthetic_stats['edge_densities']) > 0:
        test_result = perform_ks_test(
            real_stats['edge_densities'],
            synthetic_stats['edge_densities'],
            "edge_density"
        )
        results['tests']['edge_density'] = test_result
        overall_similarity = min(overall_similarity, test_result['similarity'])
        logger.info(f"Edge Density KS Test: D={test_result['D']:.3f}, p={test_result['p_value']:.3f}, similarity={test_result['similarity']:.3f}")
    
    # Overall similarity score
    results['overall_similarity'] = overall_similarity
    results['threshold'] = 0.8
    results['passed'] = overall_similarity >= 0.8
    
    # Tune parameters if needed
    if not results['passed']:
        logger.warning(f"Similarity {overall_similarity:.3f} < 0.8. Tuning degradation parameters...")
        tuned_config, recommendations = tune_parameters(degradation_config, results['tests'])
        results['tuning_recommended'] = True
        results['tuned_parameters'] = tuned_config
        results['recommendations'] = recommendations
        logger.info("Tuning recommendations:")
        for rec in recommendations:
            logger.info(f"  - {rec}")
    else:
        results['tuning_recommended'] = False
        results['recommendations'] = []
    
    # Write results
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Results written to {output_file}")
    logger.info(f"Overall similarity: {overall_similarity:.3f} (threshold: 0.8)")
    
    if results['passed']:
        logger.info("✓ Mask validation PASSED: Synthetic masks statistically similar to real masks")
        return 0
    else:
        logger.warning("✗ Mask validation FAILED: Synthetic masks differ significantly from real masks")
        logger.warning("Refer to tuning recommendations to improve degradation pipeline parameters")
        return 1

if __name__ == "__main__":
    setup_logging()
    sys.exit(main())
