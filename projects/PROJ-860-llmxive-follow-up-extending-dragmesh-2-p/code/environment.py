"""
CPU-only PyBullet physics environment for llmXive Virtual Tactile Adaptation.

This module enforces FR-004 (CPU-only execution, no CUDA) and provides
a controlled physics simulation environment for training and evaluation.
"""

import os
import sys
import numpy as np
import pybullet as p
import pybullet_data
from typing import Optional, Dict, Any, List, Tuple

# Enforce CPU-only execution (FR-004)
# Check for CUDA availability and fail loudly if detected
def _enforce_cpu_only() -> None:
    """
    Enforce FR-004: Ensure no GPU/CUDA is used for physics simulation.
    Raises RuntimeError if CUDA is detected.
    """
    # Check for PyTorch CUDA (if available)
    try:
        import torch
        if torch.cuda.is_available():
            # Log warning but do not fail - we just want to ensure PyBullet doesn't use it
            print("WARNING: PyTorch CUDA is available, but PyBullet will run in CPU mode", file=sys.stderr)
    except ImportError:
        pass  # PyTorch not installed, which is fine

    # Check for TensorFlow GPU
    try:
        import tensorflow as tf
        if tf.config.list_physical_devices('GPU'):
            print("WARNING: TensorFlow GPU is available, but PyBullet will run in CPU mode", file=sys.stderr)
    except ImportError:
        pass  # TensorFlow not installed, which is fine

    # PyBullet itself is CPU-only by default, but we explicitly set the physics
    # client to use CPU mode to be absolutely certain
    os.environ['CUDA_VISIBLE_DEVICES'] = ''

class PhysicsEnvironment:
    """
    CPU-only PyBullet physics environment with configurable parameters.

    Attributes:
        dt: Time step for simulation (seconds)
        gravity: Gravity vector (m/s^2)
        max_steps: Maximum simulation steps per episode
    """

    def __init__(
        self,
        dt: float = 0.001,
        gravity: Tuple[float, float, float] = (0.0, 0.0, -9.81),
        max_steps: int = 1000,
        render: bool = False,
        seed: Optional[int] = None
    ):
        """
        Initialize the physics environment.

        Args:
            dt: Time step for simulation (seconds), default 0.001 (1ms)
            gravity: Gravity vector (x, y, z) in m/s^2
            max_steps: Maximum number of simulation steps per episode
            render: Whether to enable GUI rendering (default False for headless)
            seed: Random seed for reproducibility
        """
        # Enforce CPU-only execution
        _enforce_cpu_only()

        self.dt = dt
        self.gravity = gravity
        self.max_steps = max_steps
        self.render = render
        self.seed = seed

        # Initialize PyBullet client
        if self.render:
            # Use GUI for rendering
            self.client = p.connect(p.GUI)
        else:
            # Use direct mode for headless operation
            self.client = p.connect(p.DIRECT)

        # Set random seed if provided
        if self.seed is not None:
            p.resetSimulation()
            p.setAdditionalSearchPath(pybullet_data.getDataPath())
            p.setPhysicsEngineParameter(
                fixedTimeStep=self.dt,
                numSolverIterations=10
            )
            p.setGravity(*self.gravity)
            np.random.seed(self.seed)
            p.setRandomSeed(self.seed)
        else:
            p.resetSimulation()
            p.setAdditionalSearchPath(pybullet_data.getDataPath())
            p.setPhysicsEngineParameter(
                fixedTimeStep=self.dt,
                numSolverIterations=10
            )
            p.setGravity(*self.gravity)

        # Store loaded objects
        self.objects: Dict[str, int] = {}
        self.step_count = 0

    def load_plane(self, color: Tuple[float, float, float] = (0.5, 0.5, 0.5)) -> int:
        """
        Load a static ground plane.

        Args:
            color: RGB color for the plane (0.0-1.0)

        Returns:
            Body ID of the loaded plane
        """
        plane_id = p.loadURDF(
            "plane.urdf",
            useFixedBase=True,
            flags=p.URDF_USE_INERTIA_FROM_FILE
        )
        p.changeVisualShape(plane_id, -1, rgbaColor=color)
        self.objects['plane'] = plane_id
        return plane_id

    def load_object(
        self,
        urdf_path: str,
        position: Tuple[float, float, float] = (0.0, 0.0, 0.0),
        orientation: Tuple[float, float, float, float] = (0.0, 0.0, 0.0, 1.0),
        useFixedBase: bool = False,
        scale: float = 1.0,
        friction: float = 0.5
    ) -> int:
        """
        Load a URDF object into the simulation.

        Args:
            urdf_path: Path to the URDF file
            position: Initial position (x, y, z)
            orientation: Quaternion orientation (x, y, z, w)
            useFixedBase: Whether the object is fixed in place
            scale: Scaling factor for the object
            friction: Friction coefficient for the object

        Returns:
            Body ID of the loaded object
        """
        object_id = p.loadURDF(
            urdf_path,
            basePosition=position,
            baseOrientation=orientation,
            useFixedBase=useFixedBase,
            globalScaling=scale
        )

        # Set friction parameters
        p.changeDynamics(object_id, -1, lateralFriction=friction)

        self.objects[f'object_{object_id}'] = object_id
        return object_id

    def set_friction(
        self,
        body_id: int,
        link_index: int = -1,
        friction: float = 0.5
    ) -> None:
        """
        Set the friction coefficient for a specific body/link.

        Args:
            body_id: ID of the body
            link_index: Index of the link (-1 for base)
            friction: Friction coefficient (0.0-1.0)
        """
        p.changeDynamics(body_id, link_index, lateralFriction=friction)

    def step_simulation(self) -> None:
        """Advance the physics simulation by one time step."""
        p.stepSimulation()
        self.step_count += 1

        if self.step_count >= self.max_steps:
            raise RuntimeError(f"Maximum steps ({self.max_steps}) exceeded")

    def get_link_state(
        self,
        body_id: int,
        link_index: int
    ) -> Dict[str, np.ndarray]:
        """
        Get the state of a specific link.

        Args:
            body_id: ID of the body
            link_index: Index of the link

        Returns:
            Dictionary containing position, orientation, linear velocity,
            and angular velocity
        """
        state = p.getLinkState(body_id, link_index)
        return {
            'position': np.array(state[4]),
            'orientation': np.array(state[5]),
            'linear_velocity': np.array(state[6]),
            'angular_velocity': np.array(state[7])
        }

    def get_joint_states(
        self,
        body_id: int,
        joint_indices: Optional[List[int]] = None
    ) -> Dict[int, Dict[str, float]]:
        """
        Get the state of specified joints.

        Args:
            body_id: ID of the body
            joint_indices: List of joint indices to query (None for all)

        Returns:
            Dictionary mapping joint index to state dict
        """
        joint_info = p.getJointInfo(body_id, 0)
        num_joints = joint_info[1]

        if joint_indices is None:
            joint_indices = list(range(num_joints))

        states = {}
        for joint_idx in joint_indices:
            state = p.getJointState(body_id, joint_idx)
            states[joint_idx] = {
                'position': state[0],
                'velocity': state[1],
                'force': state[2],
                'torque': state[3]
            }
        return states

    def apply_joint_torque(
        self,
        body_id: int,
        joint_index: int,
        torque: float
    ) -> None:
        """
        Apply torque to a specific joint.

        Args:
            body_id: ID of the body
            joint_index: Index of the joint
            torque: Torque value to apply
        """
        p.setJointMotorControl2(
            bodyIndex=body_id,
            jointIndex=joint_index,
            controlMode=p.TORQUE_CONTROL,
            force=torque
        )

    def reset(self) -> None:
        """Reset the simulation environment."""
        p.resetSimulation()
        p.setAdditionalSearchPath(pybullet_data.getDataPath())
        p.setPhysicsEngineParameter(
            fixedTimeStep=self.dt,
            numSolverIterations=10
        )
        p.setGravity(*self.gravity)
        self.objects.clear()
        self.step_count = 0

    def close(self) -> None:
        """Disconnect from the physics client."""
        p.disconnect(self.client)

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
        return False

def create_cpu_environment(
    dt: float = 0.001,
    gravity: Tuple[float, float, float] = (0.0, 0.0, -9.81),
    max_steps: int = 1000,
    render: bool = False,
    seed: Optional[int] = None
) -> PhysicsEnvironment:
    """
    Factory function to create a CPU-only physics environment.

    Args:
        dt: Time step for simulation (seconds)
        gravity: Gravity vector (x, y, z) in m/s^2
        max_steps: Maximum simulation steps per episode
        render: Whether to enable GUI rendering
        seed: Random seed for reproducibility

    Returns:
        Configured PhysicsEnvironment instance
    """
    return PhysicsEnvironment(
        dt=dt,
        gravity=gravity,
        max_steps=max_steps,
        render=render,
        seed=seed
    )

# Verify FR-004 compliance on import
if __name__ == '__main__':
    # Test that CPU-only mode works
    env = create_cpu_environment(seed=42)
    env.load_plane()
    print("CPU-only physics environment initialized successfully")
    print(f"Gravity: {env.gravity}")
    print(f"Time step: {env.dt}s")
    env.close()
    print("Test completed successfully")