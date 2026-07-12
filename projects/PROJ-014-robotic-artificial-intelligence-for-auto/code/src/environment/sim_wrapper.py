"""
Simulation Wrapper for CARLA/KITTI with Noise Injection.

Implements FR-004 (Noise Injection) and supports US-1 (Baseline Environment).
This module provides a unified interface to wrap simulation environments,
injecting controlled noise into observations (RGB, Depth, LiDAR) to test
sensory fidelity and agent robustness.

It does not depend on CARLA being installed at import time but expects
it to be available when `SimWrapper` is instantiated with a CARLA backend.
For testing without CARLA, it supports a 'dummy' backend mode.
"""

import numpy as np
import json
from typing import Any, Dict, List, Optional, Tuple, Union
from pathlib import Path
import random

# Optional import for CARLA; handled gracefully if missing
try:
    import carla
    CARLA_AVAILABLE = True
except ImportError:
    CARLA_AVAILABLE = False

from src.utils.config import get_path, get_hyperparameter


class NoiseConfig:
    """Configuration for noise injection parameters."""

    def __init__(
        self,
        rgb_noise_type: str = "gaussian",
        rgb_noise_std: float = 0.05,
        depth_noise_type: str = "dropout",
        depth_dropout_rate: float = 0.1,
        lidar_noise_type: str = "range",
        lidar_noise_std: float = 0.1,
        lidar_dropout_rate: float = 0.05,
        enabled: bool = True
    ):
        self.rgb_noise_type = rgb_noise_type
        self.rgb_noise_std = rgb_noise_std
        self.depth_noise_type = depth_noise_type
        self.depth_dropout_rate = depth_dropout_rate
        self.lidar_noise_type = lidar_noise_type
        self.lidar_noise_std = lidar_noise_std
        self.lidar_dropout_rate = lidar_dropout_rate
        self.enabled = enabled

    @classmethod
    def from_config(cls, config_dict: Optional[Dict[str, Any]] = None) -> "NoiseConfig":
        """Load noise config from a dictionary or hyperparameters."""
        if config_dict is None:
            config_dict = {}
        
        # Merge with defaults from hyperparameters if available
        hp = get_hyperparameter("noise_config", {})
        merged = {**hp, **config_dict}

        return cls(
            rgb_noise_type=merged.get("rgb_noise_type", "gaussian"),
            rgb_noise_std=merged.get("rgb_noise_std", 0.05),
            depth_noise_type=merged.get("depth_noise_type", "dropout"),
            depth_dropout_rate=merged.get("depth_dropout_rate", 0.1),
            lidar_noise_type=merged.get("lidar_noise_type", "range"),
            lidar_noise_std=merged.get("lidar_noise_std", 0.1),
            lidar_dropout_rate=merged.get("lidar_dropout_rate", 0.05),
            enabled=merged.get("enabled", True)
        )


class SimWrapper:
    """
    Wrapper for CARLA/KITTI simulation environments.

    Responsibilities:
    1. Initialize the underlying simulation client/vehicle.
    2. Inject noise into sensor observations (RGB, Depth, LiDAR) based on NoiseConfig.
    3. Provide a unified observation interface for the agent.
    4. Handle environment resets and step functions.
    """

    def __init__(
        self,
        env_type: str = "carla",
        host: str = "localhost",
        port: int = 2000,
        noise_config: Optional[NoiseConfig] = None,
        seed: Optional[int] = None
    ):
        """
        Initialize the simulation wrapper.

        Args:
            env_type: Type of environment ('carla', 'kitti', or 'dummy').
            host: CARLA server host.
            port: CARLA server port.
            noise_config: Configuration for noise injection.
            seed: Random seed for noise generation.
        """
        self.env_type = env_type
        self.host = host
        self.port = port
        self.noise_config = noise_config or NoiseConfig.from_config()
        self.seed = seed
        
        if seed is not None:
            random.seed(seed)
            np.random.seed(seed)

        self.client = None
        self.world = None
        self.actor_list = []
        self.sensor_list = []
        self.vehicle = None

        if env_type == "carla":
            if not CARLA_AVAILABLE:
                raise RuntimeError(
                    "CARLA is required for 'carla' environment type but is not installed. "
                    "Install with: pip install carla"
                )
            self._init_carla()
        elif env_type == "dummy":
            self._init_dummy()
        else:
            raise ValueError(f"Unsupported environment type: {env_type}")

    def _init_carla(self) -> None:
        """Initialize CARLA client and world."""
        try:
            self.client = carla.Client(self.host, self.port)
            self.client.set_timeout(10.0)
            self.world = self.client.get_world()
            # Set a deterministic weather for reproducibility if seed is set
            if self.seed is not None:
                weather = carla.WeatherParameters()
                # Simple deterministic mapping from seed to weather parameters
                weather.cloudiness = (self.seed % 100)
                weather.precipitation = (self.seed * 7) % 50
                self.world.set_weather(weather)
        except Exception as e:
            raise RuntimeError(f"Failed to initialize CARLA: {e}")

    def _init_dummy(self) -> None:
        """Initialize a dummy environment for testing without CARLA."""
        # In dummy mode, we simulate the interface but generate synthetic data
        pass

    def set_noise_config(self, noise_config: NoiseConfig) -> None:
        """Update noise configuration dynamically."""
        self.noise_config = noise_config

    def inject_noise(
        self,
        observation: np.ndarray,
        sensor_type: str = "rgb"
    ) -> np.ndarray:
        """
        Inject noise into an observation array.

        Args:
            observation: Numpy array of sensor data.
            sensor_type: One of 'rgb', 'depth', 'lidar'.

        Returns:
            Noisy observation array.
        """
        if not self.noise_config.enabled:
            return observation

        if sensor_type == "rgb":
            return self._inject_rgb_noise(observation)
        elif sensor_type == "depth":
            return self._inject_depth_noise(observation)
        elif sensor_type == "lidar":
            return self._inject_lidar_noise(observation)
        else:
            raise ValueError(f"Unknown sensor type: {sensor_type}")

    def _inject_rgb_noise(self, obs: np.ndarray) -> np.ndarray:
        """Inject noise into RGB observations."""
        if obs.dtype == np.uint8:
            obs_float = obs.astype(np.float32) / 255.0
        else:
            obs_float = obs.astype(np.float32)

        noise_type = self.noise_config.rgb_noise_type
        std = self.noise_config.rgb_noise_std

        if noise_type == "gaussian":
            noise = np.random.normal(0, std, obs_float.shape)
            noisy = obs_float + noise
        elif noise_type == "salt_pepper":
            noisy = obs_float.copy()
            mask = np.random.random(obs_float.shape[:2]) < (std * 2)
            noisy[mask, :] = np.random.choice([0, 1], size=(np.sum(mask), obs_float.shape[-1]))
        elif noise_type == "blur":
            # Simple box blur approximation for noise simulation
            from scipy.ndimage import gaussian_filter
            noisy = gaussian_filter(obs_float, sigma=std * 2)
        else:
            noisy = obs_float

        if obs.dtype == np.uint8:
            noisy = np.clip(noisy * 255, 0, 255).astype(np.uint8)
        else:
            noisy = np.clip(noisy, 0, 1).astype(obs.dtype)

        return noisy

    def _inject_depth_noise(self, obs: np.ndarray) -> np.ndarray:
        """Inject noise into Depth observations."""
        noise_type = self.noise_config.depth_noise_type
        dropout_rate = self.noise_config.depth_dropout_rate
        std = self.noise_config.rgb_noise_std  # Reusing std for gaussian depth noise

        if noise_type == "dropout":
            mask = np.random.random(obs.shape) > dropout_rate
            noisy = obs * mask
        elif noise_type == "gaussian":
            noise = np.random.normal(0, std, obs.shape)
            noisy = obs + noise
            noisy = np.maximum(noisy, 0)  # Depth cannot be negative
        else:
            noisy = obs

        return noisy.astype(obs.dtype)

    def _inject_lidar_noise(self, obs: np.ndarray) -> np.ndarray:
        """
        Inject noise into LiDAR point clouds.

        Args:
            obs: Numpy array of shape (N, 4) where 4 is (x, y, z, intensity)
                 or (N, 3) for (x, y, z).
        """
        if obs.size == 0:
            return obs

        noise_type = self.noise_config.lidar_noise_type
        std = self.noise_config.lidar_noise_std
        dropout_rate = self.noise_config.lidar_dropout_rate

        if noise_type == "range":
            # Add gaussian noise to distance
            points = obs.copy().astype(np.float32)
            if points.shape[1] == 4:
                x, y, z, intensity = points[:, 0], points[:, 1], points[:, 2], points[:, 3]
            else:
                x, y, z = points[:, 0], points[:, 1], points[:, 2]
                intensity = np.ones_like(x)

            dist = np.sqrt(x**2 + y**2 + z**2)
            noise = np.random.normal(0, std * dist, dist.shape)
            dist_noisy = dist + noise
            
            # Normalize direction and apply new distance
            with np.errstate(divide='ignore', invalid='ignore'):
                x_new = (x / np.where(dist > 0, dist, 1)) * dist_noisy
                y_new = (y / np.where(dist > 0, dist, 1)) * dist_noisy
                z_new = (z / np.where(dist > 0, dist, 1)) * dist_noisy

            points[:, 0] = x_new
            points[:, 1] = y_new
            points[:, 2] = z_new
            noisy = points
        
        elif noise_type == "dropout":
            mask = np.random.random(obs.shape[0]) > dropout_rate
            noisy = obs[mask]
        else:
            noisy = obs

        return noisy

    def reset(self) -> Dict[str, np.ndarray]:
        """
        Reset the environment and return initial observation.

        Returns:
            Dictionary of sensor observations.
        """
        if self.env_type == "carla":
            # In a real implementation, this would spawn a vehicle and sensors
            # For now, we return a placeholder or dummy data
            # TODO: Implement proper CARLA reset logic
            pass
        
        return self._generate_dummy_observation()

    def step(self, action: Any) -> Tuple[Dict[str, np.ndarray], float, bool, Dict[str, Any]]:
        """
        Take a step in the environment.

        Args:
            action: Action to take (e.g., control command).

        Returns:
            Tuple of (observation, reward, done, info).
        """
        if self.env_type == "carla":
            # TODO: Implement proper CARLA step logic
            pass

        obs = self._generate_dummy_observation()
        reward = 0.0
        done = False
        info = {}
        return obs, reward, done, info

    def _generate_dummy_observation(self) -> Dict[str, np.ndarray]:
        """Generate a dummy observation for testing without CARLA."""
        # Generate synthetic data matching expected shapes
        rgb = np.zeros((84, 84, 3), dtype=np.uint8)
        depth = np.zeros((84, 84), dtype=np.float32)
        lidar = np.zeros((0, 4), dtype=np.float32)

        # Inject noise if enabled
        rgb = self.inject_noise(rgb, "rgb")
        depth = self.inject_noise(depth, "depth")
        lidar = self.inject_noise(lidar, "lidar")

        return {
            "rgb": rgb,
            "depth": depth,
            "lidar": lidar
        }

    def close(self) -> None:
        """Clean up resources."""
        if self.env_type == "carla" and self.client:
            # Destroy actors
            if self.actor_list:
                self.client.apply_batch([carla.command.DestroyActor(x.id) for x in self.actor_list])
            self.client = None
            self.world = None

    def get_status(self) -> Dict[str, Any]:
        """Return current status of the wrapper."""
        return {
            "env_type": self.env_type,
            "noise_enabled": self.noise_config.enabled,
            "noise_config": {
                "rgb_noise_type": self.noise_config.rgb_noise_type,
                "rgb_noise_std": self.noise_config.rgb_noise_std,
                "depth_noise_type": self.noise_config.depth_noise_type,
                "depth_dropout_rate": self.noise_config.depth_dropout_rate,
                "lidar_noise_type": self.noise_config.lidar_noise_type,
                "lidar_noise_std": self.noise_config.lidar_noise_std,
                "lidar_dropout_rate": self.noise_config.lidar_dropout_rate
            },
            "carla_available": CARLA_AVAILABLE
        }


def create_sim_wrapper(
    env_type: str = "carla",
    noise_config_dict: Optional[Dict[str, Any]] = None,
    seed: Optional[int] = None,
    **kwargs
) -> SimWrapper:
    """
    Factory function to create a SimWrapper instance.

    Args:
        env_type: Type of environment ('carla', 'kitti', 'dummy').
        noise_config_dict: Dictionary of noise configuration parameters.
        seed: Random seed.
        **kwargs: Additional arguments passed to SimWrapper.

    Returns:
        SimWrapper instance.
    """
    noise_config = NoiseConfig.from_config(noise_config_dict)
    return SimWrapper(
        env_type=env_type,
        noise_config=noise_config,
        seed=seed,
        **kwargs
    )
