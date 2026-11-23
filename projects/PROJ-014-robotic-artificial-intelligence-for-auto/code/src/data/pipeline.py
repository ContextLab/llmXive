import numpy as np
from typing import Tuple, Optional, Union
from dataclasses import dataclass
import logging
from src.utils.config import get_hyperparameter
import cv2

logger = logging.getLogger(__name__)

@dataclass
class RGBPreprocessingConfig:
    target_height: int = 84
    target_width: int = 84
    normalize: bool = True
    center_crop: bool = True

@dataclass
class DepthDownsamplingConfig:
    factor: int = 4
    fill_method: str = "nearest"

@dataclass
class OccupancyGridConfig:
    resolution: float = 0.1  # meters per cell
    max_distance: float = 10.0
    obstacle_radius: float = 0.5
    noise_std: float = 0.1
    dropout_threshold: float = 0.01  # Threshold to detect LiDAR dropout

class RGBPreprocessor:
    def __init__(self, config: RGBPreprocessingConfig):
        self.config = config

    def preprocess(self, rgb: np.ndarray) -> np.ndarray:
        if rgb is None or rgb.size == 0:
            logger.warning("Received empty or None RGB input")
            return np.zeros((self.config.target_height, self.config.target_width, 3), dtype=np.uint8)

        if self.config.center_crop:
            h, w = rgb.shape[:2]
            min_dim = min(h, w)
            start_x = (w - min_dim) // 2
            start_y = (h - min_dim) // 2
            rgb = rgb[start_y:start_y + min_dim, start_x:start_x + min_dim]

        rgb_resized = cv2.resize(rgb, (self.config.target_width, self.config.target_height), interpolation=cv2.INTER_AREA)

        if self.config.normalize:
            rgb_resized = rgb_resized.astype(np.float32) / 255.0

        return rgb_resized

class DepthDownsampler:
    def __init__(self, config: DepthDownsamplingConfig):
        self.config = config

    def downsample(self, depth: np.ndarray) -> np.ndarray:
        if depth is None or depth.size == 0:
            logger.warning("Received empty or None Depth input")
            return np.zeros((1, 1), dtype=np.float32)

        h, w = depth.shape
        new_h, new_w = h // self.config.factor, w // self.config.factor

        if new_h <= 0 or new_w <= 0:
            logger.warning("Downsampling factor too large for input size")
            return depth

        return cv2.resize(depth, (new_w, new_h), interpolation=cv2.INTER_NEAREST)

class OccupancyGridGenerator:
    def __init__(self, config: OccupancyGridConfig):
        self.config = config
        self.grid_size = int(self.config.max_distance / self.config.resolution)
        self.logger = logging.getLogger(__name__)

    def _detect_lidar_dropout(self, depth_data: np.ndarray) -> bool:
        """
        Detects if LiDAR/Depth sensor has dropped out.
        Returns True if dropout is detected (empty or near-empty data).
        """
        if depth_data is None or depth_data.size == 0:
            return True

        valid_mask = (depth_data > 0) & (np.isfinite(depth_data))
        valid_ratio = np.sum(valid_mask) / valid_mask.size

        if valid_ratio < self.config.dropout_threshold:
            return True

        return False

    def generate(self, depth: np.ndarray, calibration: Optional[dict] = None) -> np.ndarray:
        """
        Generates a 2D occupancy grid from depth data.
        
        Args:
            depth: Depth map (H, W)
            calibration: Optional calibration params (not strictly used for basic grid, but available)
        
        Returns:
            Binary occupancy grid (grid_size, grid_size)
        """
        # Fallback logic for LiDAR dropout
        if self._detect_lidar_dropout(depth):
            self.logger.warning("LiDAR dropout detected! Substituting safe empty grid.")
            return np.zeros((self.grid_size, self.grid_size), dtype=np.uint8)

        if depth is None or depth.size == 0:
            self.logger.warning("Received empty depth data, returning empty grid")
            return np.zeros((self.grid_size, self.grid_size), dtype=np.uint8)

        # Normalize depth to [0, max_distance]
        depth_clipped = np.clip(depth, 0, self.config.max_distance)
        
        # Convert to grid coordinates
        # Assuming depth is in meters and we want a top-down view
        # For simplicity, we project the center column or average rows
        # A more robust implementation would use camera intrinsics + extrinsics
        
        # Simple projection: map depth values to radial distance in grid
        # This is a placeholder for the actual projection logic which would
        # require camera intrinsics and extrinsics from calibration
        
        # Create empty grid
        grid = np.zeros((self.grid_size, self.grid_size), dtype=np.uint8)
        
        # For a basic implementation without full calibration projection:
        # We'll mark cells as occupied if there's an obstacle within the radius
        # based on depth values in the center of the image (simplified)
        
        h, w = depth_clipped.shape
        center_y, center_x = h // 2, w // 2
        
        # Sample a region around the center
        sample_radius = 10
        y_start = max(0, center_y - sample_radius)
        y_end = min(h, center_y + sample_radius)
        x_start = max(0, center_x - sample_radius)
        x_end = min(w, center_x + sample_radius)
        
        region_depth = depth_clipped[y_start:y_end, x_start:x_end]
        
        # If any point is within obstacle radius, mark grid as occupied
        # This is a simplified heuristic
        if np.any(region_depth < self.config.obstacle_radius):
            grid[self.grid_size // 2, self.grid_size // 2] = 1
        
        # Add noise handling
        if self.config.noise_std > 0:
            noise = np.random.normal(0, self.config.noise_std, grid.shape)
            # Only add noise to occupied cells to simulate sensor noise
            noise_mask = np.random.random(grid.shape) < 0.1
            grid[noise_mask] = (grid[noise_mask] + (noise[noise_mask] > 0).astype(np.uint8)) % 2
        
        return grid

# Factory functions
def create_rgb_preprocessor(config: Optional[RGBPreprocessingConfig] = None) -> RGBPreprocessor:
    if config is None:
        config = RGBPreprocessingConfig()
    return RGBPreprocessor(config)

def create_depth_downsampler(config: Optional[DepthDownsamplingConfig] = None) -> DepthDownsampler:
    if config is None:
        config = DepthDownsamplingConfig()
    return DepthDownsampler(config)

def create_occupancy_grid_generator(config: Optional[OccupancyGridConfig] = None) -> OccupancyGridGenerator:
    if config is None:
        config = OccupancyGridConfig()
    return OccupancyGridGenerator(config)

# Batch processing helpers
def preprocess_rgb_batch(batch: np.ndarray, config: Optional[RGBPreprocessingConfig] = None) -> np.ndarray:
    preprocessor = create_rgb_preprocessor(config)
    return np.stack([preprocessor.preprocess(img) for img in batch])

def downsample_depth_batch(batch: np.ndarray, config: Optional[DepthDownsamplingConfig] = None) -> np.ndarray:
    downsampler = create_depth_downsampler(config)
    return np.stack([downsampler.downsample(depth) for depth in batch])

def generate_occupancy_grid_batch(batch: np.ndarray, calibration_batch: Optional[np.ndarray] = None, config: Optional[OccupancyGridConfig] = None) -> np.ndarray:
    generator = create_occupancy_grid_generator(config)
    grids = []
    for depth in batch:
        grids.append(generator.generate(depth))
    return np.stack(grids)
