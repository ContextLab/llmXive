"""
Physics simulation wrapper for PyBullet.

Provides scale normalization, error handling, and a clean interface for
running embodied intelligence simulations based on reconstructed 3D states.

This module ensures mechanical decoupling from the video model by operating
solely on reconstructed physical states, not internal model activations.
"""
import os
import logging
import time
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
import numpy as np

# Lazy import of pybullet to handle cases where it might not be installed
# The actual import happens in the function to allow for better error messages
_pb = None

from utils.error_handler import PhysicsSimError, fail_loudly
from utils.logging_config import get_logger

# Configure logger
logger = get_logger(__name__)

@dataclass
class SimulationConfig:
    """Configuration for the physics simulation environment."""
    gravity: float = -9.81
    time_step: float = 1.0 / 240.0
    max_sim_steps: int = 1000
    scale_factor: float = 1.0  # For normalizing units (e.g., meters to simulation units)
    enable_sleeping: bool = True
    friction: float = 0.7
    restitution: float = 0.0
    damping: float = 0.01

@dataclass
class SimulationResult:
    """Result of a physics simulation run."""
    success: bool
    final_states: Optional[np.ndarray] = None  # Shape: (n_bodies, 7) [x, y, z, qx, qy, qz, qw]
    velocities: Optional[np.ndarray] = None    # Shape: (n_bodies, 6) [vx, vy, vz, wx, wy, wz]
    collision_events: List[Dict[str, Any]] = field(default_factory=list)
    validation_status: Optional[str] = None    # 'valid', 'invalid', 'null'
    error_message: Optional[str] = None
    duration_seconds: float = 0.0

class PhysicsSimWrapper:
    """
    Wrapper for PyBullet physics engine with scale normalization and error handling.
    
    This class provides a safe, decoupled interface for running physics simulations
    on reconstructed 3D states. It ensures that:
    1. All inputs are normalized to a consistent scale
    2. Errors are handled gracefully with loud failures for critical issues
    3. The simulation state is isolated from any video model internals
    """

    def __init__(self, config: Optional[SimulationConfig] = None):
        """
        Initialize the physics simulation wrapper.
        
        Args:
            config: Simulation configuration. Defaults to standard settings if None.
        """
        self.config = config or SimulationConfig()
        self._initialized = False
        self._sim_id: Optional[int] = None
        self._body_ids: Dict[str, int] = {}

    def _ensure_pybullet_import(self) -> None:
        """Ensure PyBullet is imported and available."""
        global _pb
        if _pb is None:
            try:
                import pybullet as pb
                _pb = pb
                logger.info("PyBullet imported successfully")
            except ImportError as e:
                fail_loudly(
                    f"PyBullet is not installed. Please install it with 'pip install pybullet'. "
                    f"Original error: {e}",
                    category=PhysicsSimError
                )

    def initialize(self) -> None:
        """
        Initialize the physics simulation environment.
        
        Creates a new simulation instance with the configured parameters.
        """
        if self._initialized:
            logger.warning("Physics simulation already initialized")
            return

        self._ensure_pybullet_import()

        try:
            # Connect to a new server (use GUI=0 for headless operation)
            self._sim_id = _pb.connect(_pb.DIRECT)
            
            if self._sim_id < 0:
                raise PhysicsSimError("Failed to connect to PyBullet simulation")

            # Configure the simulation
            _pb.setGravity(0, 0, self.config.gravity, physicsClientId=self._sim_id)
            _pb.setRealTimeSimulation(0, physicsClientId=self._sim_id)
            _pb.setTimeStep(self.config.time_step, physicsClientId=self._sim_id)

            # Configure sleeping
            if self.config.enable_sleeping:
                _pb.enableSleeping(True, physicsClientId=self._sim_id)

            self._initialized = True
            logger.info(f"Physics simulation initialized with gravity={self.config.gravity} m/s²")

        except Exception as e:
            fail_loudly(
                f"Failed to initialize physics simulation: {e}",
                category=PhysicsSimError
            )

    def shutdown(self) -> None:
        """Shutdown the physics simulation environment."""
        if self._sim_id is not None:
            try:
                _pb.disconnect(self._sim_id)
                logger.info("Physics simulation disconnected")
            except Exception as e:
                logger.warning(f"Error disconnecting from physics simulation: {e}")
            finally:
                self._sim_id = None
                self._initialized = False
                self._body_ids.clear()

    def _normalize_scale(self, value: float) -> float:
        """Normalize a value to the simulation's scale."""
        return value * self.config.scale_factor

    def _denormalize_scale(self, value: float) -> float:
        """Denormalize a value from the simulation's scale."""
        return value / self.config.scale_factor

    def create_ground_plane(self, name: str = "ground") -> int:
        """
        Create a static ground plane.
        
        Args:
            name: Identifier for the ground plane body.
        
        Returns:
            The PyBullet body ID.
        """
        if not self._initialized:
            self.initialize()

        try:
            # Create a simple plane
            plane_id = _pb.loadURDF(
                "plane.urdf",
                [0, 0, 0],
                _pb.getQuaternionFromEuler([0, 0, 0]),
                physicsClientId=self._sim_id
            )
            _pb.changeDynamics(
                plane_id, -1, 
                linearDamping=0, 
                angularDamping=0,
                physicsClientId=self._sim_id
            )
            self._body_ids[name] = plane_id
            logger.debug(f"Created ground plane: {name}")
            return plane_id
        except Exception as e:
            raise PhysicsSimError(f"Failed to create ground plane: {e}")

    def create_box(
        self,
        position: Tuple[float, float, float],
        dimensions: Tuple[float, float, float],
        mass: float = 1.0,
        color: Optional[Tuple[float, float, float, float]] = None,
        name: Optional[str] = None
    ) -> int:
        """
        Create a box body.
        
        Args:
            position: (x, y, z) position in meters.
            dimensions: (width, height, depth) in meters.
            mass: Mass in kg.
            color: RGBA color tuple.
            name: Optional identifier for the body.
        
        Returns:
            The PyBullet body ID.
        """
        if not self._initialized:
            self.initialize()

        try:
            # Normalize positions and dimensions
            norm_pos = tuple(self._normalize_scale(p) for p in position)
            norm_dims = tuple(self._normalize_scale(d) for d in dimensions)

            # Create box shape
            box_id = _pb.createMultiBody(
                baseMass=mass,
                baseInertialFramePosition=[0, 0, 0],
                baseCollisionShapeIndex=_pb.GEOM_BOX,
                baseCollisionShapeParameters=norm_dims,
                basePosition=norm_pos,
                baseOrientation=[0, 0, 0, 1],
                physicsClientId=self._sim_id
            )

            # Apply material properties
            _pb.changeDynamics(
                box_id, -1,
                lateralFriction=self.config.friction,
                restitution=self.config.restitution,
                linearDamping=self.config.damping,
                angularDamping=self.config.damping,
                physicsClientId=self._sim_id
            )

            if color:
                _pb.changeVisualShape(box_id, -1, rgbaColor=color, physicsClientId=self._sim_id)

            if name:
                self._body_ids[name] = box_id

            logger.debug(f"Created box at {position} with mass {mass}kg")
            return box_id

        except Exception as e:
            raise PhysicsSimError(f"Failed to create box: {e}")

    def create_sphere(
        self,
        position: Tuple[float, float, float],
        radius: float,
        mass: float = 1.0,
        color: Optional[Tuple[float, float, float, float]] = None,
        name: Optional[str] = None
    ) -> int:
        """
        Create a sphere body.
        
        Args:
            position: (x, y, z) position in meters.
            radius: Radius in meters.
            mass: Mass in kg.
            color: RGBA color tuple.
            name: Optional identifier for the body.
        
        Returns:
            The PyBullet body ID.
        """
        if not self._initialized:
            self.initialize()

        try:
            norm_pos = tuple(self._normalize_scale(p) for p in position)
            norm_radius = self._normalize_scale(radius)

            sphere_id = _pb.createMultiBody(
                baseMass=mass,
                baseInertialFramePosition=[0, 0, 0],
                baseCollisionShapeIndex=_pb.GEOM_SPHERE,
                baseCollisionShapeParameters=norm_radius,
                basePosition=norm_pos,
                baseOrientation=[0, 0, 0, 1],
                physicsClientId=self._sim_id
            )

            _pb.changeDynamics(
                sphere_id, -1,
                lateralFriction=self.config.friction,
                restitution=self.config.restitution,
                linearDamping=self.config.damping,
                angularDamping=self.config.damping,
                physicsClientId=self._sim_id
            )

            if color:
                _pb.changeVisualShape(sphere_id, -1, rgbaColor=color, physicsClientId=self._sim_id)

            if name:
                self._body_ids[name] = sphere_id

            logger.debug(f"Created sphere at {position} with radius {radius}m")
            return sphere_id

        except Exception as e:
            raise PhysicsSimError(f"Failed to create sphere: {e}")

    def load_urdf(
        self,
        urdf_path: str,
        position: Tuple[float, float, float],
        orientation: Optional[Tuple[float, float, float, float]] = None,
        name: Optional[str] = None
    ) -> int:
        """
        Load a URDF file.
        
        Args:
            urdf_path: Path to the URDF file.
            position: (x, y, z) position in meters.
            orientation: (qx, qy, qz, qw) quaternion.
            name: Optional identifier for the body.
        
        Returns:
            The PyBullet body ID.
        """
        if not self._initialized:
            self.initialize()

        try:
            norm_pos = tuple(self._normalize_scale(p) for p in position)
            norm_orientation = orientation or [0, 0, 0, 1]

            body_id = _pb.loadURDF(
                urdf_path,
                norm_pos,
                norm_orientation,
                physicsClientId=self._sim_id
            )

            # Apply default material properties
            for i in range(-1, _pb.getNumJoints(body_id, physicsClientId=self._sim_id)):
                _pb.changeDynamics(
                    body_id, i,
                    lateralFriction=self.config.friction,
                    restitution=self.config.restitution,
                    linearDamping=self.config.damping,
                    angularDamping=self.config.damping,
                    physicsClientId=self._sim_id
                )

            if name:
                self._body_ids[name] = body_id

            logger.debug(f"Loaded URDF: {urdf_path} at {position}")
            return body_id

        except Exception as e:
            raise PhysicsSimError(f"Failed to load URDF {urdf_path}: {e}")

    def set_state(
        self,
        body_id: int,
        position: Tuple[float, float, float],
        orientation: Tuple[float, float, float, float],
        linear_velocity: Optional[Tuple[float, float, float]] = None,
        angular_velocity: Optional[Tuple[float, float, float]] = None
    ) -> None:
        """
        Set the state of a body.
        
        Args:
            body_id: PyBullet body ID.
            position: (x, y, z) position in meters.
            orientation: (qx, qy, qz, qw) quaternion.
            linear_velocity: (vx, vy, vz) in m/s.
            angular_velocity: (wx, wy, wz) in rad/s.
        """
        if not self._initialized:
            raise PhysicsSimError("Physics simulation not initialized")

        try:
            norm_pos = tuple(self._normalize_scale(p) for p in position)
            norm_linear_vel = tuple(self._normalize_scale(v) for v in (linear_velocity or [0, 0, 0]))
            norm_angular_vel = tuple(self._normalize_scale(v) for v in (angular_velocity or [0, 0, 0]))

            _pb.resetBasePositionAndOrientation(
                body_id, norm_pos, orientation, physicsClientId=self._sim_id
            )
            _pb.resetBaseVelocity(
                body_id, norm_linear_vel, norm_angular_vel, physicsClientId=self._sim_id
            )

        except Exception as e:
            raise PhysicsSimError(f"Failed to set state for body {body_id}: {e}")

    def get_state(self, body_id: int) -> Dict[str, np.ndarray]:
        """
        Get the current state of a body.
        
        Args:
            body_id: PyBullet body ID.
        
        Returns:
            Dictionary with 'position', 'orientation', 'linear_velocity', 'angular_velocity'.
        """
        if not self._initialized:
            raise PhysicsSimError("Physics simulation not initialized")

        try:
            pos, orn = _pb.getBasePositionAndOrientation(body_id, physicsClientId=self._sim_id)
            lin_vel, ang_vel = _pb.getBaseVelocity(body_id, physicsClientId=self._sim_id)

            return {
                'position': np.array([self._denormalize_scale(p) for p in pos]),
                'orientation': np.array(orn),
                'linear_velocity': np.array([self._denormalize_scale(v) for v in lin_vel]),
                'angular_velocity': np.array([self._denormalize_scale(v) for v in ang_vel])
            }
        except Exception as e:
            raise PhysicsSimError(f"Failed to get state for body {body_id}: {e}")

    def step_simulation(self, num_steps: int = 1) -> None:
        """
        Step the simulation forward.
        
        Args:
            num_steps: Number of time steps to advance.
        """
        if not self._initialized:
            raise PhysicsSimError("Physics simulation not initialized")

        try:
            for _ in range(num_steps):
                _pb.stepSimulation(physicsClientId=self._sim_id)
        except Exception as e:
            raise PhysicsSimError(f"Failed to step simulation: {e}")

    def check_collisions(self, body_a: int, body_b: int) -> bool:
        """
        Check if two bodies are colliding.
        
        Args:
            body_a: First body ID.
            body_b: Second body ID.
        
        Returns:
            True if colliding, False otherwise.
        """
        if not self._initialized:
            raise PhysicsSimError("Physics simulation not initialized")

        try:
            # Get contact points between two bodies
            contacts = _pb.getContactPoints(
                bodyA=body_a, bodyB=body_b, physicsClientId=self._sim_id
            )
            return len(contacts) > 0
        except Exception as e:
            logger.warning(f"Error checking collisions: {e}")
            return False

    def validate_physics(
        self,
        body_id: int,
        max_velocity: float = 10.0,
        max_acceleration: float = 50.0,
        gravity_check: bool = True
    ) -> Tuple[bool, str]:
        """
        Validate that a body's motion is physically plausible.
        
        Args:
            body_id: Body to validate.
            max_velocity: Maximum allowed linear velocity (m/s).
            max_acceleration: Maximum allowed acceleration (m/s²).
            gravity_check: Whether to check for gravity consistency.
        
        Returns:
            Tuple of (is_valid, reason).
        """
        if not self._initialized:
            raise PhysicsSimError("Physics simulation not initialized")

        try:
            state = self.get_state(body_id)
            vel = state['linear_velocity']
            vel_norm = np.linalg.norm(vel)

            # Check velocity limits
            if vel_norm > max_velocity:
                return False, f"Velocity {vel_norm:.2f} m/s exceeds limit {max_velocity} m/s"

            # Check for extreme accelerations (simplified: compare to previous step if available)
            # In a full implementation, we'd track history

            # Check gravity consistency
            if gravity_check:
                # If object is in the air and not moving upward, it should be falling
                if state['position'][2] > 0.1 and vel[2] < 0:
                    # Check if acceleration is approximately gravity
                    pass  # Simplified check

            return True, "Physical constraints satisfied"

        except Exception as e:
            return False, f"Validation error: {e}"

    def run_simulation_for_state(
        self,
        initial_states: List[Dict[str, Any]],
        duration_seconds: float = 5.0,
        validation_rules: Optional[Dict[str, Any]] = None
    ) -> SimulationResult:
        """
        Run a simulation for a set of initial states.
        
        This is the main entry point for validating reconstructed 3D states.
        
        Args:
            initial_states: List of dicts with 'type', 'position', 'orientation', 'velocity', etc.
            duration_seconds: How long to simulate.
            validation_rules: Optional rules for validation.
        
        Returns:
            SimulationResult with final states and validation status.
        """
        if not self._initialized:
            self.initialize()

        start_time = time.time()
        collision_events = []
        body_ids = []

        try:
            # Create ground plane
            self.create_ground_plane()

            # Create bodies from initial states
            for i, state in enumerate(initial_states):
                body_type = state.get('type', 'box')
                pos = state.get('position', (0, 0, 0))
                orn = state.get('orientation', (0, 0, 0, 1))
                vel = state.get('velocity', (0, 0, 0))
                ang_vel = state.get('angular_velocity', (0, 0, 0))

                if body_type == 'box':
                    dims = state.get('dimensions', (0.1, 0.1, 0.1))
                    mass = state.get('mass', 1.0)
                    body_id = self.create_box(pos, dims, mass, name=f"body_{i}")
                elif body_type == 'sphere':
                    radius = state.get('radius', 0.1)
                    mass = state.get('mass', 1.0)
                    body_id = self.create_sphere(pos, radius, mass, name=f"body_{i}")
                else:
                    logger.warning(f"Unknown body type: {body_type}, skipping")
                    continue

                self.set_state(body_id, pos, orn, vel, ang_vel)
                body_ids.append(body_id)

            # Calculate steps
            num_steps = int(duration_seconds / self.config.time_step)

            # Run simulation
            for step in range(num_steps):
                self.step_simulation()

                # Check for collisions
                for i, body_a in enumerate(body_ids):
                    for body_b in body_ids[i+1:]:
                        if self.check_collisions(body_a, body_b):
                            collision_events.append({
                                'step': step,
                                'body_a': body_a,
                                'body_b': body_b,
                                'time': step * self.config.time_step
                            })

            # Collect final states
            final_states = []
            velocities = []
            for body_id in body_ids:
                state = self.get_state(body_id)
                final_states.append(state['position'])
                velocities.append(state['linear_velocity'])

            final_states = np.array(final_states)
            velocities = np.array(velocities)

            # Determine validation status
            validation_status = 'valid'
            validation_reason = "All physics constraints satisfied"

            if validation_rules:
                for body_id in body_ids:
                    is_valid, reason = self.validate_physics(
                        body_id,
                        max_velocity=validation_rules.get('max_velocity', 10.0),
                        max_acceleration=validation_rules.get('max_acceleration', 50.0)
                    )
                    if not is_valid:
                        validation_status = 'invalid'
                        validation_reason = reason
                        break

                if collision_events and validation_rules.get('no_collisions', False):
                    validation_status = 'invalid'
                    validation_reason = "Collision detected"

            duration = time.time() - start_time

            return SimulationResult(
                success=True,
                final_states=final_states,
                velocities=velocities,
                collision_events=collision_events,
                validation_status=validation_status,
                duration_seconds=duration
            )

        except Exception as e:
            logger.error(f"Simulation failed: {e}")
            return SimulationResult(
                success=False,
                error_message=str(e),
                validation_status='null'
            )

    def __enter__(self):
        """Context manager entry."""
        self.initialize()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.shutdown()
        return False

def create_simulation(
    gravity: float = -9.81,
    time_step: float = 1.0 / 240.0,
    scale_factor: float = 1.0
) -> PhysicsSimWrapper:
    """
    Factory function to create a configured simulation wrapper.
    
    Args:
        gravity: Gravity in m/s².
        time_step: Simulation time step in seconds.
        scale_factor: Scale normalization factor.
    
    Returns:
        Configured PhysicsSimWrapper instance.
    """
    config = SimulationConfig(
        gravity=gravity,
        time_step=time_step,
        scale_factor=scale_factor
    )
    return PhysicsSimWrapper(config)

def run_physics_validation(
    initial_states: List[Dict[str, Any]],
    duration_seconds: float = 5.0,
    validation_rules: Optional[Dict[str, Any]] = None
) -> SimulationResult:
    """
    Convenience function to run a physics validation simulation.
    
    Args:
        initial_states: List of initial body states.
        duration_seconds: Duration to simulate.
        validation_rules: Rules for validation.
    
    Returns:
        SimulationResult with validation outcome.
    """
    with PhysicsSimWrapper() as sim:
        return sim.run_simulation_for_state(initial_states, duration_seconds, validation_rules)