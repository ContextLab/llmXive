import os
import json
import csv
import logging
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import numpy as np

from utils.config import get_results_dir, get_processed_dir, get_data_dir
from eval.interpret import apply_grad_cam, generate_grad_cam_visualization
from utils.logging_config import get_logger

def setup_iou_logging():
    """Setup logging for IoU calculation."""
    logger = get_logger("iou_calculator")
    return logger

def load_grain_features(features_path: Optional[str] = None) -> Dict[str, float]:
    """
    Load grain size features from CSV.
    Returns a dict mapping image_id to grain_size_um.
    """
    if features_path is None:
        features_path = str(get_processed_dir() / "grain_features.csv")
    
    features = {}
    logger = logging.getLogger("iou_calculator")
    
    if not os.path.exists(features_path):
        logger.warning(f"Grain features file not found at {features_path}. "
                     "Returning empty dict. IoU calculation will rely on expert review.")
        return features
    
    with open(features_path, 'r', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            image_id = row['image_id']
            try:
                grain_size = float(row['grain_size_um'])
                features[image_id] = grain_size
            except (ValueError, KeyError) as e:
                logger.warning(f"Skipping invalid row in grain features: {row} - {e}")
    
    logger.info(f"Loaded {len(features)} grain size features from {features_path}")
    return features

def load_grad_cam_heatmaps(heatmap_dir: Optional[str] = None) -> Dict[str, np.ndarray]:
    """
    Load Grad-CAM heatmaps from the heatmap directory.
    Returns a dict mapping image_id (without extension) to heatmap array.
    """
    if heatmap_dir is None:
        heatmap_dir = str(get_results_dir() / "grad_cam_heatmaps")
    
    heatmap_dir = Path(heatmap_dir)
    heatmaps = {}
    logger = logging.getLogger("iou_calculator")
    
    if not heatmap_dir.exists():
        logger.warning(f"Heatmap directory not found at {heatmap_dir}. "
                     "Cannot calculate IoU. Returning empty dict.")
        return heatmaps
    
    for heatmap_file in heatmap_dir.glob("*.png"):
        # Extract image_id from filename (e.g., "img_001_heatmap.png" -> "img_001")
        image_id = heatmap_file.stem.replace("_heatmap", "")
        try:
            # Load heatmap as grayscale
            heatmap = np.array(heatmap_file, dtype=np.float32)
            if len(heatmap.shape) == 3:
                # Convert to grayscale if RGB
                heatmap = np.mean(heatmap, axis=2)
            # Normalize to [0, 1]
            if heatmap.max() > 0:
                heatmap = heatmap / heatmap.max()
            heatmaps[image_id] = heatmap
        except Exception as e:
            logger.warning(f"Failed to load heatmap {heatmap_file}: {e}")
    
    logger.info(f"Loaded {len(heatmaps)} Grad-CAM heatmaps from {heatmap_dir}")
    return heatmaps

def load_grain_boundaries(annotations_path: Optional[str] = None) -> Optional[Dict[str, np.ndarray]]:
    """
    Load manually annotated grain boundaries if available.
    Returns a dict mapping image_id to binary mask (1=boundary, 0=background).
    Returns None if no annotations file exists.
    """
    if annotations_path is None:
        # Try common locations
        annotations_path = str(get_data_dir() / "annotations" / "grain_boundaries.csv")
        if not os.path.exists(annotations_path):
            annotations_path = str(get_data_dir() / "grain_boundaries.csv")
    
    annotations_path = Path(annotations_path)
    
    if not annotations_path.exists():
        logger = logging.getLogger("iou_calculator")
        logger.info(f"No grain boundary annotations found at {annotations_path}. "
                   "Will generate expert review report instead of IoU calculation.")
        return None
    
    # Load annotations (assuming CSV with image_id and boundary mask paths or encoded data)
    # For now, we assume a simple format: image_id, boundary_mask_path
    boundaries = {}
    logger = logging.getLogger("iou_calculator")
    
    try:
        with open(annotations_path, 'r', newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                image_id = row['image_id']
                mask_path = row.get('boundary_mask_path')
                if mask_path and os.path.exists(mask_path):
                    mask = np.array(Path(mask_path), dtype=np.uint8)
                    boundaries[image_id] = mask
                else:
                    logger.warning(f"No valid boundary mask path for {image_id}")
    except Exception as e:
        logger.error(f"Failed to load grain boundaries from {annotations_path}: {e}")
        return None
    
    logger.info(f"Loaded {len(boundaries)} grain boundary annotations")
    return boundaries

def calculate_iou(heatmap: np.ndarray, boundary_mask: np.ndarray, threshold: float = 0.5) -> float:
    """
    Calculate Intersection over Union (IoU) between a Grad-CAM heatmap and grain boundary mask.
    
    Args:
        heatmap: Normalized Grad-CAM heatmap (values in [0, 1])
        boundary_mask: Binary mask of grain boundaries (0 or 1)
        threshold: Threshold to binarize the heatmap (default 0.5)
    
    Returns:
        IoU score (float between 0 and 1), or 0.0 if no overlap or invalid inputs
    """
    # Binarize heatmap
    heatmap_binary = (heatmap >= threshold).astype(np.uint8)
    
    # Ensure boundary mask is binary
    boundary_binary = (boundary_mask > 0).astype(np.uint8)
    
    # Calculate intersection and union
    intersection = np.logical_and(heatmap_binary, boundary_binary).sum()
    union = np.logical_or(heatmap_binary, boundary_binary).sum()
    
    if union == 0:
        return 0.0
    
    iou = intersection / union
    return float(iou)

def generate_expert_review_report(
    heatmaps: Dict[str, np.ndarray],
    grain_features: Dict[str, float],
    output_path: str
) -> Dict[str, Any]:
    """
    Generate an expert review report when manual annotations are not available.
    The report includes statistics on heatmap coverage and grain size correlation.
    
    Args:
        heatmaps: Dict of image_id -> heatmap arrays
        grain_features: Dict of image_id -> grain_size_um
        output_path: Path to write the JSON report
    
    Returns:
        Report dictionary
    """
    logger = logging.getLogger("iou_calculator")
    report = {
        "status": "expert_review_required",
        "reason": "No manual grain boundary annotations available for IoU calculation",
        "heatmaps_analyzed": len(heatmaps),
        "grain_features_available": len(grain_features),
        "common_images": 0,
        "statistics": {}
    }
    
    # Find common images
    common_images = set(heatmaps.keys()) & set(grain_features.keys())
    report["common_images"] = len(common_images)
    
    if len(common_images) > 0:
        # Calculate some basic statistics
        heatmap_areas = []
        grain_sizes = []
        
        for image_id in common_images:
            heatmap = heatmaps[image_id]
            # Estimate activation area (pixels with significant activation)
            activation_area = (heatmap > 0.1).sum()
            heatmap_areas.append(activation_area)
            grain_sizes.append(grain_features[image_id])
        
        if len(heatmap_areas) > 0:
            report["statistics"] = {
                "mean_activation_area_pixels": float(np.mean(heatmap_areas)),
                "std_activation_area_pixels": float(np.std(heatmap_areas)),
                "mean_grain_size_um": float(np.mean(grain_sizes)),
                "std_grain_size_um": float(np.std(grain_sizes)),
                "min_grain_size_um": float(np.min(grain_sizes)),
                "max_grain_size_um": float(np.max(grain_sizes))
            }
    
    # Write report
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Generated expert review report at {output_path}")
    return report

def calculate_iou_report(
    heatmaps: Dict[str, np.ndarray],
    boundaries: Dict[str, np.ndarray],
    output_path: str,
    threshold: float = 0.5,
    min_iou_threshold: float = 0.4
) -> Dict[str, Any]:
    """
    Calculate IoU scores for all image pairs and generate a report.
    
    Args:
        heatmaps: Dict of image_id -> heatmap arrays
        boundaries: Dict of image_id -> boundary masks
        output_path: Path to write the JSON report
        threshold: Threshold for binarizing heatmaps
        min_iou_threshold: Minimum IoU threshold for success (SC-005)
    
    Returns:
        Report dictionary with IoU statistics
    """
    logger = logging.getLogger("iou_calculator")
    report = {
        "status": "success",
        "threshold_used": threshold,
        "min_iou_threshold": min_iou_threshold,
        "total_pairs": 0,
        "successful_pairs": 0,
        "failed_pairs": 0,
        "iou_scores": [],
        "mean_iou": 0.0,
        "median_iou": 0.0,
        "min_iou": 0.0,
        "max_iou": 0.0,
        "pairs_above_threshold": 0,
        "pairs_below_threshold": 0
    }
    
    common_images = set(heatmaps.keys()) & set(boundaries.keys())
    report["total_pairs"] = len(common_images)
    
    if len(common_images) == 0:
        report["status"] = "no_common_images"
        report["reason"] = "No images found in both heatmaps and boundary annotations"
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        return report
    
    iou_scores = []
    for image_id in common_images:
        try:
            iou = calculate_iou(heatmaps[image_id], boundaries[image_id], threshold)
            iou_scores.append({
                "image_id": image_id,
                "iou": iou
            })
            
            if iou >= min_iou_threshold:
                report["successful_pairs"] += 1
                report["pairs_above_threshold"] += 1
            else:
                report["failed_pairs"] += 1
                report["pairs_below_threshold"] += 1
                
        except Exception as e:
            logger.warning(f"Failed to calculate IoU for {image_id}: {e}")
            report["failed_pairs"] += 1
    
    report["iou_scores"] = iou_scores
    
    if len(iou_scores) > 0:
        iou_values = [item["iou"] for item in iou_scores]
        report["mean_iou"] = float(np.mean(iou_values))
        report["median_iou"] = float(np.median(iou_values))
        report["min_iou"] = float(np.min(iou_values))
        report["max_iou"] = float(np.max(iou_values))
        
        # Check if overall performance meets threshold
        if report["mean_iou"] >= min_iou_threshold:
            report["status"] = "success"
        else:
            report["status"] = "below_threshold"
            report["message"] = f"Mean IoU ({report['mean_iou']:.4f}) is below threshold ({min_iou_threshold})"
    
    # Write report
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"IoU report written to {output_path}")
    logger.info(f"Mean IoU: {report['mean_iou']:.4f}, Pairs above threshold: {report['pairs_above_threshold']}/{report['total_pairs']}")
    return report

def main():
    """Main entry point for IoU calculation."""
    logger = setup_iou_logging()
    logger.info("Starting IoU calculation for Grad-CAM heatmaps vs grain boundaries")
    
    # Load data
    grain_features = load_grain_features()
    heatmaps = load_grad_cam_heatmaps()
    boundaries = load_grain_boundaries()
    
    # Determine output path
    output_path = str(get_results_dir() / "interpretability_iou.json")
    
    if boundaries is None:
        # No annotations available, generate expert review report
        logger.info("No grain boundary annotations found. Generating expert review report.")
        report = generate_expert_review_report(heatmaps, grain_features, output_path)
    else:
        # Calculate IoU
        report = calculate_iou_report(
            heatmaps, 
            boundaries, 
            output_path,
            threshold=0.5,
            min_iou_threshold=0.4
        )
    
    logger.info(f"IoU calculation complete. Report saved to {output_path}")
    return report

if __name__ == "__main__":
    main()
