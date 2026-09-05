"""
T030: Metrics Evaluation Script
Runs P-PSNR, P-SSIM, Chamfer Distance, and GDS on all samples from the NNF-varied dataset.
Outputs results to data/results/metrics.csv
"""
import os
import sys
import json
import logging
import argparse
import csv
from pathlib import Path
from typing import List, Dict, Any

# Project imports
from lib.metrics import (
    compute_p_psnr,
    compute_p_ssim,
    compute_chamfer_distance,
    compute_geometric_divergence_score,
    normalize_point_cloud,
    save_metrics_to_file
)
from lib.logging_config import setup_logging, get_logger
from lib.config import load_environment_config, set_random_seed

# Add parent directory to path if running as script
if 'code' in os.getcwd():
    sys.path.insert(0, os.path.dirname(os.getcwd()))
else:
    project_root = Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(project_root / 'code'))

def setup_directories():
    """Create necessary output directories."""
    config = load_environment_config()
    results_dir = Path(config['paths']['results'])
    results_dir.mkdir(parents=True, exist_ok=True)
    return config

def load_degraded_manifest(manifest_path: Path) -> List[Dict[str, Any]]:
    """Load the manifest of NNF-varied scenes."""
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest not found: {manifest_path}")
    
    with open(manifest_path, 'r') as f:
        manifest = json.load(f)
    
    return manifest.get('samples', [])

def load_point_cloud(path: Path):
    """
    Load a point cloud file (.ply).
    Returns numpy arrays for coordinates and colors if available.
    """
    try:
        import numpy as np
        import open3d as o3d
        
        pcd = o3d.io.read_point_cloud(str(path))
        
        if not pcd.has_points():
            return None, None, None
        
        points = np.asarray(pcd.points)
        
        colors = None
        if pcd.has_colors():
            colors = np.asarray(pcd.colors)
        
        return points, colors, pcd
        
    except ImportError as e:
        logging.error(f"Missing dependency for point cloud loading: {e}")
        raise
    except Exception as e:
        logging.error(f"Error loading point cloud {path}: {e}")
        raise

def process_sample(sample_id: str, sample_data: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compute all metrics for a single sample.
    Returns a dictionary with metrics and sample info.
    """
    logger = get_logger(__name__)
    
    # Determine paths based on sample data
    # Expecting sample_data to have keys like 'degraded_scene', 'baseline_ply', 'inpainted_ply', 'gt_lidar'
    degraded_path = Path(sample_data.get('degraded_scene', ''))
    baseline_path = Path(sample_data.get('baseline_ply', ''))
    inpainted_path = Path(sample_data.get('inpainted_ply', ''))
    gt_lidar_path = Path(sample_data.get('gt_lidar', ''))
    
    # Load point clouds
    try:
        # Load Ground Truth LiDAR
        gt_points, gt_colors, _ = load_point_cloud(gt_lidar_path)
        if gt_points is None:
            logger.warning(f"GT LiDAR empty or missing for {sample_id}: {gt_lidar_path}")
            return None
        
        # Load Baseline Reconstruction
        base_points, base_colors, _ = load_point_cloud(baseline_path)
        if base_points is None:
            logger.warning(f"Baseline PLY empty or missing for {sample_id}: {baseline_path}")
            return None
        
        # Load Inpainted Reconstruction (if available, else use baseline for comparison logic)
        inpainted_points = None
        if inpainted_path.exists():
            inpainted_points, _, _ = load_point_cloud(inpainted_path)
            if inpainted_points is None:
                logger.warning(f"Inpainted PLY empty for {sample_id}: {inpainted_path}")
                # Fallback: treat as missing, will compute GDS as NaN or 0 depending on logic
        else:
            logger.warning(f"Inpainted PLY not found for {sample_id}: {inpainted_path}")
        
        # Normalize point clouds to unit box for metric consistency
        # We normalize based on GT to ensure scale invariance
        gt_norm, scale_gt = normalize_point_cloud(gt_points)
        base_norm, _ = normalize_point_cloud(base_points, gt_bounds=gt_points) # Align to GT scale
        
        metrics = {
            'sample_id': sample_id,
            'degraded_scene': str(degraded_path),
            'baseline_ply': str(baseline_path),
            'inpainted_ply': str(inpainted_path) if inpainted_path.exists() else '',
            'gt_lidar': str(gt_lidar_path),
            'nnf_level': sample_data.get('nnf_level', 'unknown'),
            'scene_complexity': sample_data.get('scene_complexity', 'unknown'),
        }
        
        # 1. P-PSNR (Point-based PSNR)
        # Compute between Baseline and GT
        p_psnr_base = compute_p_psnr(base_norm, gt_norm)
        metrics['p_psnr_baseline'] = p_psnr_base
        
        if inpainted_points is not None:
            inpainted_norm, _ = normalize_point_cloud(inpainted_points, gt_bounds=gt_points)
            p_psnr_inpaint = compute_p_psnr(inpainted_norm, gt_norm)
            metrics['p_psnr_inpainted'] = p_psnr_inpaint
        else:
            metrics['p_psnr_inpainted'] = None
        
        # 2. P-SSIM (Point-based SSIM)
        p_ssim_base = compute_p_ssim(base_norm, gt_norm)
        metrics['p_ssim_baseline'] = p_ssim_base
        
        if inpainted_points is not None:
            p_ssim_inpaint = compute_p_ssim(inpainted_norm, gt_norm)
            metrics['p_ssim_inpainted'] = p_ssim_inpaint
        else:
            metrics['p_ssim_inpainted'] = None
        
        # 3. Chamfer Distance (CD)
        cd_base = compute_chamfer_distance(base_norm, gt_norm)
        metrics['chamfer_distance_baseline'] = cd_base
        
        if inpainted_points is not None:
            cd_inpaint = compute_chamfer_distance(inpainted_norm, gt_norm)
            metrics['chamfer_distance_inpainted'] = cd_inpaint
        else:
            metrics['chamfer_distance_inpainted'] = None
        
        # 4. Geometric Divergence Score (GDS)
        # GDS compares Baseline vs Inpainted to detect recovery vs hallucination
        # If inpainted is not available, GDS is undefined (NaN)
        if inpainted_points is not None:
            gds = compute_geometric_divergence_score(base_norm, inpainted_norm, gt_norm)
            metrics['gds'] = gds
        else:
            metrics['gds'] = float('nan')
        
        return metrics
        
    except Exception as e:
        logger.error(f"Error processing sample {sample_id}: {e}", exc_info=True)
        return None

def save_metrics_to_csv(metrics_list: List[Dict[str, Any]], output_path: Path):
    """Save computed metrics to a CSV file."""
    if not metrics_list:
        logging.warning("No metrics to save.")
        return
    
    # Determine fieldnames
    fieldnames = list(metrics_list[0].keys())
    
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in metrics_list:
            # Handle NaN values for CSV
            clean_row = {}
            for k, v in row.items():
                if isinstance(v, float) and (v != v): # NaN check
                    clean_row[k] = 'NaN'
                else:
                    clean_row[k] = v
            writer.writerow(clean_row)
    
    logging.info(f"Metrics saved to {output_path}")

def main():
    """Main entry point for T030."""
    parser = argparse.ArgumentParser(description="Evaluate metrics on NNF-varied scenes.")
    parser.add_argument('--manifest', type=str, default=None, help='Path to degraded manifest JSON')
    parser.add_argument('--output', type=str, default=None, help='Path to output metrics CSV')
    args = parser.parse_args()
    
    # Setup logging
    config = setup_directories()
    setup_logging(config)
    logger = get_logger(__name__)
    
    # Set random seed for reproducibility
    seed = config.get('random_seed', 42)
    set_random_seed(seed)
    
    # Determine input paths
    if args.manifest:
        manifest_path = Path(args.manifest)
    else:
        # Default path from T014b output
        manifest_path = Path(config['paths']['processed']) / 'nnf_varied_scenes' / 'degraded_manifest.json'
    
    if args.output:
        output_path = Path(args.output)
    else:
        output_path = Path(config['paths']['results']) / 'metrics.csv'
    
    logger.info(f"Loading manifest from {manifest_path}")
    try:
        samples = load_degraded_manifest(manifest_path)
        logger.info(f"Found {len(samples)} samples to process.")
    except FileNotFoundError as e:
        logger.error(f"Failed to load manifest: {e}")
        sys.exit(1)
    
    if not samples:
        logger.warning("No samples found in manifest. Exiting.")
        sys.exit(0)
    
    results = []
    for i, sample in enumerate(samples):
        sample_id = sample.get('sample_id', f'sample_{i}')
        logger.info(f"Processing {i+1}/{len(samples)}: {sample_id}")
        
        metrics = process_sample(sample_id, sample, config)
        if metrics:
            results.append(metrics)
    
    logger.info(f"Successfully processed {len(results)} samples.")
    
    # Save results
    save_metrics_to_csv(results, output_path)
    
    # Also save a summary JSON if needed
    summary_path = output_path.with_suffix('.json')
    summary_data = {
        'total_samples': len(samples),
        'processed_samples': len(results),
        'output_file': str(output_path),
        'seed': seed
    }
    with open(summary_path, 'w') as f:
        json.dump(summary_data, f, indent=2)
    
    logger.info("Metrics evaluation complete.")

if __name__ == '__main__':
    main()