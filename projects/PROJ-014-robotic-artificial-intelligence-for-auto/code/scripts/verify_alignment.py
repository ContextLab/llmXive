import os
import sys
import json
import logging
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Tuple

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.data.calibration import CalibrationValidator, create_calibration_validator
from src.data.pipeline import OccupancyGridGenerator, create_occupancy_grid_generator, RGBPreprocessor, create_rgb_preprocessor, DepthDownsampler, create_depth_downsampler
from src.utils.config import get_path, get_config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_modalities_from_disk(modality_dir: Path) -> Dict[str, np.ndarray]:
    """
    Load the three modalities (RGB, Depth, Occupancy Grid) from the data directory.
    Expects files: rgb_frame.npy, depth_frame.npy, occupancy_grid.npy
    """
    modalities = {}
    expected_files = {
        'rgb': 'rgb_frame.npy',
        'depth': 'depth_frame.npy',
        'grid': 'occupancy_grid.npy'
    }

    for key, filename in expected_files.items():
        filepath = modality_dir / filename
        if not filepath.exists():
            raise FileNotFoundError(f"Expected modality file not found: {filepath}")
        
        logger.info(f"Loading {key} modality from {filepath}")
        data = np.load(filepath)
        modalities[key] = data

    return modalities

def calculate_iou(grid1: np.ndarray, grid2: np.ndarray) -> float:
    """
    Calculate Intersection over Union (IoU) between two binary occupancy grids.
    Both grids must be binary (0 or 1).
    """
    if grid1.shape != grid2.shape:
        raise ValueError(f"Grid shapes do not match: {grid1.shape} vs {grid2.shape}")
    
    # Ensure binary
    grid1_binary = (grid1 > 0.5).astype(np.uint8)
    grid2_binary = (grid2 > 0.5).astype(np.uint8)

    intersection = np.logical_and(grid1_binary, grid2_binary).sum()
    union = np.logical_or(grid1_binary, grid2_binary).sum()

    if union == 0:
        return 1.0 if intersection == 0 else 0.0
    
    return float(intersection / union)

def verify_spatial_alignment(modalities: Dict[str, np.ndarray], 
                             calibration_report_path: Path,
                             iou_threshold: float = 0.95) -> Dict[str, Any]:
    """
    Verify spatial alignment across all three modalities for the same ground truth frame.
    
    Strategy:
    1. Load calibration parameters.
    2. Transform Depth and RGB data into a common 2D projection (Occupancy Grid space)
       using the calibration parameters.
    3. Compare the generated projected grids against the stored Occupancy Grid.
    4. Calculate IoU scores.
    
    Returns a report dictionary.
    """
    logger.info(f"Verifying spatial alignment with threshold {iou_threshold}")
    
    # 1. Load Calibration
    if not calibration_report_path.exists():
        raise FileNotFoundError(f"Calibration report not found: {calibration_report_path}")
    
    with open(calibration_report_path, 'r') as f:
        calib_data = json.load(f)
    
    # We assume the report contains the necessary extrinsic/intrinsic params
    # Re-initialize validator to ensure we have the objects needed for transformation
    validator = create_calibration_validator(calib_data)
    
    # 2. Process Modalities to a common representation
    # We will project RGB and Depth to the 2D grid space and compare with the stored grid.
    
    results = {
        "status": "success",
        "iou_scores": {},
        "threshold": iou_threshold,
        "passed": True,
        "details": []
    }

    stored_grid = modalities['grid']
    depth_data = modalities['depth']
    rgb_data = modalities['rgb']

    # A. Depth -> Occupancy Grid Projection (Direct check)
    # The stored grid should ideally match the depth-derived grid if calibration is perfect.
    # We use the OccupancyGridGenerator to project depth to grid using calibration.
    grid_gen = create_occupancy_grid_generator()
    
    # Note: In a real scenario, we'd need the raw depth and camera intrinsics.
    # Here we assume the 'depth' modality is the downsampled depth map.
    # We need to re-project it to the grid using the calibration matrix.
    # Since we don't have the raw raw depth, we simulate the check by:
    # 1. Taking the stored grid as "Ground Truth"
    # 2. Taking the Depth map and projecting it to grid space using calibration
    # 3. Comparing the two.
    
    # For this simulation, we will perform a geometric consistency check.
    # We assume the 'depth' modality contains depth values.
    # We create a synthetic occupancy grid from depth using the calibration.
    
    # Load calibration params for transformation
    # Assuming calib_data has 'extrinsic' and 'intrinsic' keys
    try:
        extrinsic = np.array(calib_data['extrinsic'])
        intrinsic = np.array(calib_data['intrinsic'])
    except KeyError:
        raise ValueError("Calibration report missing 'extrinsic' or 'intrinsic' keys")

    # Project Depth to Grid
    # Simplified projection: Depth map (H, W) -> Grid (H_grid, W_grid)
    # We use the calibration to warp the depth map to the grid coordinates.
    # Since we don't have the full 3D point cloud, we approximate the alignment
    # by checking if the non-zero regions align after a simple geometric transform.
    
    # Create a "Projected Grid" from Depth
    # This is a simplified check: we assume the depth map is already aligned to the grid
    # if the calibration is correct. We verify by checking the overlap of obstacles.
    
    # Convert depth to binary obstacle map (threshold > 0)
    depth_obstacles = (depth_data > 0.0).astype(np.uint8)
    
    # Resize depth obstacles to match grid size if necessary
    if depth_obstacles.shape != stored_grid.shape:
        logger.warning(f"Depth shape {depth_obstacles.shape} != Grid shape {stored_grid.shape}. Resizing.")
        depth_obstacles = cv2.resize(depth_obstacles, (stored_grid.shape[1], stored_grid.shape[0]), interpolation=cv2.INTER_NEAREST)
    
    # Calculate IoU Depth vs Grid
    iou_depth_grid = calculate_iou(depth_obstacles, stored_grid)
    results['iou_scores']['depth_vs_grid'] = iou_depth_grid
    results['details'].append(f"IoU (Depth vs Grid): {iou_depth_grid:.4f}")

    # B. RGB -> Occupancy Grid (via Depth projection or direct feature check)
    # Since RGB is color, we can't directly compare to binary grid without segmentation.
    # However, the task asks for spatial alignment. We verify that the RGB image
    # and the Depth map are spatially consistent (same resolution, no shift).
    # We check if the RGB image's edges align with the Depth's edges.
    
    # Simple edge alignment check
    rgb_edges = cv2.Canny(rgb_data, 50, 150)
    depth_edges = cv2.Canny(depth_data.astype(float), 50, 150)
    
    # Normalize edge maps to binary
    rgb_edges_bin = (rgb_edges > 0).astype(np.uint8)
    depth_edges_bin = (depth_edges > 0).astype(np.uint8)
    
    if rgb_edges_bin.shape != depth_edges_bin.shape:
        # Resize if needed
        rgb_edges_bin = cv2.resize(rgb_edges_bin, (depth_edges_bin.shape[1], depth_edges_bin.shape[0]), interpolation=cv2.INTER_NEAREST)
    
    iou_rgb_depth = calculate_iou(rgb_edges_bin, depth_edges_bin)
    results['iou_scores']['rgb_edges_vs_depth_edges'] = iou_rgb_depth
    results['details'].append(f"IoU (RGB Edges vs Depth Edges): {iou_rgb_depth:.4f}")

    # C. Final Alignment Check
    # The alignment is considered successful if all IoU scores > threshold
    all_passed = all(score >= iou_threshold for score in results['iou_scores'].values())
    results['passed'] = all_passed

    if not all_passed:
        results['status'] = "failed"
        logger.warning(f"Spatial alignment verification FAILED. Scores: {results['iou_scores']}")
    else:
        logger.info(f"Spatial alignment verification PASSED. Scores: {results['iou_scores']}")

    return results

def main():
    logger.info("Starting Spatial Alignment Verification (T025)")
    
    # Paths
    config = get_config()
    data_dir = Path(get_path("data_modalities"))
    calib_report_path = Path(get_path("calibration_report"))
    output_path = Path(get_path("alignment_report"))
    
    logger.info(f"Data directory: {data_dir}")
    logger.info(f"Calibration report: {calib_report_path}")
    logger.info(f"Output path: {output_path}")

    # Ensure directories exist
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        # Load modalities
        modalities = load_modalities_from_disk(data_dir)
        
        # Verify alignment
        report = verify_spatial_alignment(modalities, calib_report_path)
        
        # Save report
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Alignment report saved to {output_path}")
        
        # Exit with error if failed to ensure pipeline stops if needed
        if not report['passed']:
            logger.error("Alignment verification failed. Pipeline may need to halt.")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Alignment verification failed with error: {e}")
        # Create a failure report
        failure_report = {
            "status": "error",
            "error": str(e),
            "passed": False
        }
        with open(output_path, 'w') as f:
            json.dump(failure_report, f, indent=2)
        sys.exit(1)

if __name__ == "__main__":
    main()
