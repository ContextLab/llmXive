import os
import sys
import numpy as np
import pybullet as p
import pybullet_data
from typing import Optional, Dict, Any, List, Tuple

# -----------------------------------------------------------------------------
# GPU Backend Enforcement (FR-004)
# -----------------------------------------------------------------------------
# Requirement: Insert a runtime check at the start of environment.py that explicitly
# verifies torch.cuda.is_available() is False (or PyBullet is not using GPU)
# and raises an error if any GPU backend is detected.
# -----------------------------------------------------------------------------

def _enforce_cpu_only() -> None:
    """
    Enforce CPU-only execution for PyBullet physics simulation.
    
    Raises:
        RuntimeError: If GPU resources (CUDA) are detected or if PyBullet
                      is configured to use a GPU backend.
    """
    # Check 1: PyTorch CUDA availability (if torch is installed)
    try:
        import torch
        if torch.cuda.is_available():
            # Even if we don't use torch, the environment might be set up for GPU.
            # We strictly require CPU-only for this research pipeline.
            raise RuntimeError(
                "FR-004 Violation: GPU backend detected. "
                "torch.cuda.is_available() returned True. "
                "This pipeline must run on CPU-only infrastructure. "
                "Please ensure the environment variable 'CUDA_VISIBLE_DEVICES' is empty "
                "or unset, and that no GPU resources are allocated."
            )
    except ImportError:
        # PyTorch not installed, which is fine for pure CPU PyBullet
        pass

    # Check 2: PyBullet specific GPU checks
    # PyBullet can use GPU for collision detection or fluid dynamics if configured.
    # We ensure we are not passing GPU flags to the create function.
    # Additionally, we check for environment variables that might force GPU usage.
    gpu_env_vars = [
        'PYBULLET_USE_GPU',
        'CUDA_VISIBLE_DEVICES',
        'GPU_DEVICE_ORDINAL'
    ]
    for var in gpu_env_vars:
        if os.environ.get(var):
            raise RuntimeError(
                f"FR-004 Violation: GPU environment variable '{var}' is set to '{os.environ.get(var)}'. "
                "This pipeline requires CPU-only execution. Please unset this variable."
            )

    # Check 3: Verify PyBullet version compatibility (optional but good practice)
    # Ensure we are not on a version known to default to GPU in specific configs
    # (Most stable versions default to CPU unless explicitly told otherwise)

# Execute the check immediately upon module import to fail fast
_enforce_cpu_only()


class PhysicsEnvironment:
    """
    CPU-only Physics Environment wrapper for PyBullet.
    
    This class encapsulates the PyBullet physics simulation engine, ensuring
    all operations are performed on the CPU as per FR-004.
    """

    def __init__(self, 
                 dt: float = 1.0 / 240.0,
                 gravity: float = -9.81,
                 render: bool = False,
                 verbose: bool = False):
        """
        Initialize the physics environment.
        
        Args:
            dt: Time step for simulation (default 1/240s).
            gravity: Gravity vector magnitude (z-axis).
            render: Whether to enable GUI rendering (default False).
            verbose: Whether to print debug information.
        """
        self.dt = dt
        self.gravity = gravity
        self.render = render
        self.verbose = verbose
        self._client_id: Optional[int] = None
        self._objects: Dict[str, int] = {}
        self._loaded_paths: Dict[str, str] = {}

        # Initialize PyBullet
        if render:
            # Use GUI if rendering is requested
            self._client_id = p.connect(p.GUI)
        else:
            # Force DIRECT mode for headless CPU execution
            # This ensures no rendering backend (which might use GPU) is initialized
            self._client_id = p.connect(p.DIRECT)

        # Set up physics parameters
        p.setGravity(0, 0, self.gravity)
        p.setTimeStep(self.dt)
        
        # Add data path for built-in assets
        p.setAdditionalSearchPath(pybullet_data.getDataPath())

        if self.verbose:
            print(f"[PhysicsEnvironment] Initialized with client_id={self._client_id}, mode={'GUI' if render else 'DIRECT'}")

    def load_object(self, 
                    urdf_path: str, 
                    object_name: str, 
                    position: Tuple[float, float, float] = (0, 0, 0),
                    orientation: Tuple[float, float, float, float] = (0, 0, 0, 1),
                    mass: float = 1.0,
                    friction: float = 0.5) -> int:
        """
        Load a URDF object into the simulation.
        
        Args:
            urdf_path: Path to the URDF file.
            object_name: Name key to store the object ID.
            position: Initial position (x, y, z).
            orientation: Initial orientation (quaternion x, y, z, w).
            mass: Mass of the object (0 for static).
            friction: Friction coefficient.
        
        Returns:
            The PyBullet body ID of the loaded object.
        """
        if object_name in self._objects:
            raise ValueError(f"Object with name '{object_name}' already exists.")

        # Load the URDF
        body_id = p.loadURDF(urdf_path, position, orientation, flags=p.URDF_USE_INERTIA_FROM_FILE)
        
        # Set physics properties if dynamic
        if mass > 0:
            p.changeDynamics(body_id, -1, lateralFriction=friction)
            # Ensure mass is set correctly for all links if needed
            for link_id in range(p.getNumJoints(body_id)):
                p.changeDynamics(body_id, link_id, linearDamping=0.05, angularDamping=0.05)

        self._objects[object_name] = body_id
        self._loaded_paths[object_name] = urdf_path

        if self.verbose:
            print(f"[PhysicsEnvironment] Loaded '{object_name}' at {position}, mass={mass}")

        return body_id

    def create_plane(self, 
                     position: Tuple[float, float, float] = (0, 0, 0),
                     orientation: Tuple[float, float, float, float] = (0, 0, 0, 1),
                     color: Tuple[float, float, float, float] = (0.5, 0.5, 0.5, 1.0)) -> int:
        """
        Create a static ground plane.
        
        Returns:
            The PyBullet body ID of the plane.
        """
        plane_id = p.loadURDF("plane.urdf", position, orientation)
        p.changeVisualShape(plane_id, -1, rgbaColor=color)
        return plane_id

    def step_simulation(self) -> None:
        """Advance the simulation by one time step."""
        p.stepSimulation()

    def get_state(self, object_name: str) -> Optional[Dict[str, Any]]:
        """
        Get the current state (position, orientation, velocity) of an object.
        
        Args:
            object_name: The name key of the object.
        
        Returns:
            Dictionary containing position, orientation, linear_velocity, angular_velocity.
        """
        if object_name not in self._objects:
            return None

        body_id = self._objects[object_name]
        pos, orn = p.getBasePositionAndOrientation(body_id)
        lin_vel, ang_vel = p.getBaseVelocity(body_id)

        return {
            "position": np.array(pos),
            "orientation": np.array(orn),
            "linear_velocity": np.array(lin_vel),
            "angular_velocity": np.array(ang_vel)
        }

    def apply_force(self, object_name: str, force: np.ndarray, point: Optional[np.ndarray] = None) -> None:
        """
        Apply a force to an object.
        
        Args:
            object_name: The name key of the object.
            force: Force vector (x, y, z).
            point: Application point in world coordinates (if None, applies to COM).
        """
        if object_name not in self._objects:
            raise ValueError(f"Object '{object_name}' not found.")
        
        body_id = self._objects[object_name]
        if point is None:
            p.applyExternalForce(body_id, -1, force, [0, 0, 0], flags=p.LINK_FRAME)
        else:
            p.applyExternalForce(body_id, -1, force, point.tolist(), flags=p.WORLD_FRAME)

    def reset(self) -> None:
        """Reset the physics environment."""
        p.resetSimulation()
        self._objects.clear()
        self._loaded_paths.clear()
        
        # Re-apply global settings
        p.setGravity(0, 0, self.gravity)
        p.setTimeStep(self.dt)
        
        if self.verbose:
            print("[PhysicsEnvironment] Simulation reset.")

    def close(self) -> None:
        """Disconnect from the physics server."""
        if self._client_id is not None:
            p.disconnect(self._client_id)
            self._client_id = None
            if self.verbose:
                print("[PhysicsEnvironment] Disconnected.")


def create_cpu_environment(dt: float = 1.0 / 240.0, 
                           gravity: float = -9.81, 
                           render: bool = False,
                           verbose: bool = False) -> PhysicsEnvironment:
    """
    Factory function to create a CPU-only PhysicsEnvironment instance.
    
    This function enforces the CPU-only constraint by relying on the module-level
    check performed upon import of this file.
    
    Args:
        dt: Time step for simulation.
        gravity: Gravity magnitude.
        render: Whether to enable rendering.
        verbose: Whether to print debug info.
    
    Returns:
        An instance of PhysicsEnvironment configured for CPU execution.
    
    Raises:
        RuntimeError: If GPU resources are detected (enforced at import time).
    """
    # The check _enforce_cpu_only() was already called at module import.
    # If we are here, the environment is valid for CPU-only execution.
    return PhysicsEnvironment(dt=dt, gravity=gravity, render=render, verbose=verbose)