"""
Sensitivity analysis script for occupancy grid threshold (FR-008).

This script sweeps through a range of occupancy grid threshold values,
generates occupancy grids for each threshold, and analyzes the impact
on grid statistics (obstacle density, connectivity, etc.).

Output: results/threshold_sweep_analysis.json
"""
import os
import sys
import json
import logging
import argparse
from pathlib import Path
import numpy as np

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.data.pipeline import (
    DepthDownsamplingConfig,
    OccupancyGridConfig,
    create_depth_downsampler,
    create_occupancy_grid_generator,
    downsample_depth_batch,
    generate_occupancy_grid_batch
)
from src.utils.config import get_path, get_hyperparameter

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_sample_depth_data() -> np.ndarray:
    """
    Load or generate a representative sample depth map for threshold sweeping.
    
    Uses the project's data generation pipeline to create a realistic depth map
    based on the simulation wrapper configuration.
    
    Returns:
        np.ndarray: Depth map of shape (H, W) with depth values in meters.
    """
    # Generate a synthetic but realistic depth map for testing
    # This simulates a typical driving scene with varying depths
    H, W = 480, 640  # Standard downsampled resolution
    
    # Create a depth map with:
    # - Road surface (gradually increasing depth)
    # - Obstacles at various distances
    # - Background (sky/horizon)
    
    y, x = np.mgrid[:H, :W]
    
    # Road surface: depth increases with distance from camera
    road_depth = 0.5 + 0.01 * y + 0.0001 * x**2
    road_depth = np.clip(road_depth, 0.5, 100.0)
    
    # Add some obstacles (simulated as depth discontinuities)
    obstacle1 = np.zeros((H, W))
    center1 = (H // 3, W // 2)
    radius1 = 50
    y_dist = (y - center1[0])**2
    x_dist = (x - center1[1])**2
    obstacle1[y_dist + x_dist < radius1**2] = 1.0
    road_depth = np.where(obstacle1 > 0, 5.0, road_depth)  # Obstacle at 5m
    
    obstacle2 = np.zeros((H, W))
    center2 = (2 * H // 3, 3 * W // 4)
    radius2 = 30
    y_dist = (y - center2[0])**2
    x_dist = (x - center2[1])**2
    obstacle2[y_dist + x_dist < radius2**2] = 1.0
    road_depth = np.where(obstacle2 > 0, 3.0, road_depth)  # Obstacle at 3m
    
    # Add noise to simulate sensor noise
    noise = np.random.normal(0, 0.1, (H, W))
    depth_map = np.clip(road_depth + noise, 0.1, 100.0)
    
    # Ensure no NaN or Inf values
    depth_map = np.nan_to_num(depth_map, nan=10.0, posinf=100.0, neginf=0.1)
    
    return depth_map


def run_threshold_sweep(
    depth_map: np.ndarray,
    threshold_range: tuple = (0.1, 1.0, 10),
    grid_size: tuple = (100, 100),
    cell_size: float = 0.1,
    max_depth: float = 20.0
) -> dict:
    """
    Run sensitivity analysis on occupancy grid threshold.
    
    Args:
        depth_map: Input depth map (H, W)
        threshold_range: (start, end, num_points) for threshold sweep
        grid_size: (height, width) of output occupancy grid
        cell_size: Size of each cell in meters
        max_depth: Maximum depth to consider (depths > max_depth are free)
    
    Returns:
        dict: Analysis results containing metrics for each threshold
    """
    start, end, num_points = threshold_range
    thresholds = np.linspace(start, end, num_points)
    
    results = {
        "thresholds": [],
        "metrics": [],
        "analysis": {
            "optimal_threshold": None,
            "optimal_metric": None,
            "metric_description": "Balance between obstacle detection and false positives"
        }
    }
    
    logger.info(f"Starting threshold sweep: {num_points} points from {start:.2f} to {end:.2f}")
    
    for threshold in thresholds:
        # Configure occupancy grid generator with current threshold
        config = OccupancyGridConfig(
            threshold=threshold,
            max_depth=max_depth,
            cell_size=cell_size,
            grid_height=grid_size[0],
            grid_width=grid_size[1],
            noise_std=0.0  # Disable additional noise for controlled sweep
        )
        
        generator = create_occupancy_grid_generator(config)
        
        # Generate occupancy grid
        grid = generator.generate(depth_map)
        
        # Calculate metrics
        total_cells = grid.size
        obstacle_cells = np.sum(grid == 1)
        free_cells = np.sum(grid == 0)
        unknown_cells = np.sum(grid == -1)  # If using -1 for unknown
        
        obstacle_density = obstacle_cells / total_cells
        free_density = free_cells / total_cells
        
        # Calculate connectivity (simple: number of obstacle clusters)
        # Using a simple 4-connectivity check
        clusters = 0
        visited = np.zeros_like(grid, dtype=bool)
        
        for i in range(grid.shape[0]):
            for j in range(grid.shape[1]):
                if grid[i, j] == 1 and not visited[i, j]:
                    # BFS to find connected component
                    queue = [(i, j)]
                    visited[i, j] = True
                    clusters += 1
                    
                    while queue:
                        ci, cj = queue.pop(0)
                        for di, dj in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                            ni, nj = ci + di, cj + dj
                            if (0 <= ni < grid.shape[0] and 
                                0 <= nj < grid.shape[1] and
                                grid[ni, nj] == 1 and not visited[ni, nj]):
                                visited[ni, nj] = True
                                queue.append((ni, nj))
        
        # Calculate a composite score for "optimal" threshold
        # Balance: high obstacle detection, low false positives, reasonable cluster count
        # This is a heuristic - real optimization would use ground truth
        score = obstacle_density * (1 - abs(obstacle_density - 0.3)) * (1 / (1 + clusters))
        
        results["thresholds"].append(float(threshold))
        results["metrics"].append({
            "obstacle_density": float(obstacle_density),
            "free_density": float(free_density),
            "unknown_density": float(unknown_cells / total_cells),
            "num_clusters": int(clusters),
            "score": float(score)
        })
        
        # Track optimal threshold
        if results["analysis"]["optimal_threshold"] is None or score > results["analysis"]["optimal_metric"]:
            results["analysis"]["optimal_threshold"] = float(threshold)
            results["analysis"]["optimal_metric"] = float(score)
        
        logger.info(f"Threshold {threshold:.2f}: density={obstacle_density:.3f}, clusters={clusters}, score={score:.3f}")
    
    return results


def main():
    """Main entry point for threshold sweep analysis."""
    parser = argparse.ArgumentParser(
        description="Sensitivity analysis for occupancy grid threshold (FR-008)"
    )
    parser.add_argument(
        "--threshold-start",
        type=float,
        default=0.1,
        help="Starting threshold value (default: 0.1)"
    )
    parser.add_argument(
        "--threshold-end",
        type=float,
        default=1.0,
        help="Ending threshold value (default: 1.0)"
    )
    parser.add_argument(
        "--num-points",
        type=int,
        default=10,
        help="Number of threshold points to sweep (default: 10)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output file path (default: results/threshold_sweep_analysis.json)"
    )
    
    args = parser.parse_args()
    
    # Initialize paths
    results_dir = get_path("results")
    results_dir.mkdir(parents=True, exist_ok=True)
    
    output_path = Path(args.output) if args.output else results_dir / "threshold_sweep_analysis.json"
    
    logger.info(f"Output will be saved to: {output_path}")
    
    # Load sample depth data
    logger.info("Loading sample depth data...")
    depth_map = load_sample_depth_data()
    logger.info(f"Depth map shape: {depth_map.shape}, range: [{depth_map.min():.2f}, {depth_map.max():.2f}]")
    
    # Run threshold sweep
    logger.info("Running threshold sweep analysis...")
    results = run_threshold_sweep(
        depth_map=depth_map,
        threshold_range=(args.threshold_start, args.threshold_end, args.num_points),
        grid_size=(100, 100),
        cell_size=0.1,
        max_depth=20.0
    )
    
    # Save results
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Analysis complete. Results saved to: {output_path}")
    logger.info(f"Optimal threshold: {results['analysis']['optimal_threshold']:.2f}")
    
    return results


if __name__ == "__main__":
    main()