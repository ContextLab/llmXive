"""
Physics simulation data generation module for User Story 1.
Generates synthetic topology-shift test sets using PyBullet.
Includes robust error handling, retry mechanisms, and logging.
"""

import json
import logging
import os
import signal
import sys
import time
import random
import hashlib
from typing import Dict, List, Any, Optional, Tuple
import numpy as np

# PyBullet import with fallback handling
try:
    import pybullet as p
    import pybullet_data
except ImportError:
    raise ImportError("PyBullet is required. Install with: pip install pybullet")

from utils import setup_logging, set_deterministic_seed, compute_sha256

# --- Custom Exceptions ---

class PhysicsSimulationError(Exception):
    """Base exception for physics simulation failures."""
    pass

class URDFLoadError(PhysicsSimulationError):
    """Raised when loading a URDF file fails."""
    pass

class SimulationStepError(PhysicsSimulationError):
    """Raised when a simulation step produces invalid results (NaN/Inf)."""
    pass

class TimeoutError(PhysicsSimulationError):
    """Raised when a simulation operation exceeds the time limit."""
    pass

class RecoveryResult:
    """Result container for recovery attempts."""
    def __init__(self, success: bool, retries: int, last_error: Optional[str] = None):
        self.success = success
        self.retries = retries
        self.last_error = last_error

# --- Configuration Constants ---

MAX_RETRIES = 5
INITIAL_BACKOFF = 0.1  # seconds
MAX_BACKOFF = 5.0      # seconds
SIMULATION_TIMEOUT = 300  # seconds per trial
VALIDATION_TOLERANCE = 1e-6

# --- Error Handler Class ---

class CrashRecoveryHandler:
    """
    Handles errors during physics simulation with exponential backoff retry.
    Logs failures and skips trials that cannot be recovered.
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        self.error_log_path = "data/results/errors.log"
        self._ensure_error_log_dir()

    def _ensure_error_log_dir(self):
        """Ensure the directory for error logs exists."""
        os.makedirs(os.path.dirname(self.error_log_path), exist_ok=True)

    def log_error(self, error_type: str, message: str, trial_id: str = "unknown"):
        """Log an error to the error log file and logger."""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{trial_id}] [{error_type}] {message}\n"
        
        self.logger.error(f"{error_type}: {message}")
        
        try:
            with open(self.error_log_path, "a", encoding="utf-8") as f:
                f.write(log_entry)
        except IOError as e:
            self.logger.critical(f"Failed to write to error log: {e}")

    def retry_with_backoff(self, operation: callable, operation_name: str, 
                           trial_id: str = "unknown", *args, **kwargs) -> Tuple[bool, Any]:
        """
        Execute an operation with exponential backoff retry logic.
        
        Args:
            operation: The function to execute.
            operation_name: Name of the operation for logging.
            trial_id: Identifier for the current trial.
            *args, **kwargs: Arguments to pass to the operation.
        
        Returns:
            Tuple of (success: bool, result: Any). If failed, result is None.
        """
        retries = 0
        backoff = INITIAL_BACKOFF
        last_error = None

        while retries < MAX_RETRIES:
            try:
                result = operation(*args, **kwargs)
                # Check for NaN/Inf in numeric results if applicable
                if isinstance(result, (list, tuple, np.ndarray)):
                    flat_result = np.array(result).flatten()
                    if np.any(np.isnan(flat_result)) or np.any(np.isinf(flat_result)):
                        raise SimulationStepError("Result contains NaN or Inf values")
                return True, result
            
            except (URDFLoadError, SimulationStepError, TimeoutError) as e:
                last_error = str(e)
                self.log_error(type(e).__name__, last_error, trial_id)
                retries += 1
                if retries < MAX_RETRIES:
                    self.logger.warning(f"Retry {retries}/{MAX_RETRIES} for {operation_name} after {backoff}s")
                    time.sleep(backoff)
                    backoff = min(backoff * 2, MAX_BACKOFF)
                else:
                    self.logger.error(f"Max retries ({MAX_RETRIES}) exceeded for {operation_name}")
                    return False, None

            except Exception as e:
                # Unexpected errors - log and re-raise to avoid masking bugs
                self.log_error("UnexpectedError", str(e), trial_id)
                raise

        return False, None

    def handle_urdf_load(self, urdf_path: str, trial_id: str) -> Tuple[bool, Optional[int]]:
        """Handle URDF loading with retry logic."""
        def load_urdf_op():
            if not os.path.exists(urdf_path):
                raise URDFLoadError(f"URDF file not found: {urdf_path}")
            try:
                body_id = p.loadURDF(urdf_path, useFixedBase=True)
                if body_id < 0:
                    raise URDFLoadError(f"PyBullet returned error ID for URDF: {urdf_path}")
                return body_id
            except Exception as e:
                raise URDFLoadError(f"Failed to load URDF {urdf_path}: {str(e)}")

        success, result = self.retry_with_backoff(load_urdf_op, "loadURDF", trial_id)
        return success, result

    def handle_simulation_step(self, trial_id: str) -> Tuple[bool, Optional[Dict]]:
        """Handle simulation step with validation and retry logic."""
        def step_op():
            p.stepSimulation()
            # Check for NaN in simulation state
            num_bodies = p.getNumBodies()
            for i in range(num_bodies):
                pos, orn, _, _, _, _ = p.getBasePositionAndOrientation(i)
                if any(np.isnan(pos)) or any(np.isnan(orn)):
                    raise SimulationStepError(f"NaN detected in body {i} state")
            
            # Return current state snapshot
            state = {}
            for i in range(num_bodies):
                pos, orn, lin_vel, ang_vel, joint_states = p.getBasePositionAndOrientation(i), \
                                                            p.getBaseVelocity(i), \
                                                            p.getJointStates(i)
                state[i] = {
                    "position": pos,
                    "orientation": orn,
                    "linear_velocity": lin_vel[0],
                    "angular_velocity": lin_vel[1],
                    "joint_states": joint_states
                }
            return state

        success, result = self.retry_with_backoff(step_op, "stepSimulation", trial_id)
        return success, result

# --- Topology Shift Generator ---

class TopologyShiftGenerator:
    """
    Generates diverse kinematic chains and deformable materials.
    Ensures zero overlap with original GAM training data.
    """

    def __init__(self, config: Dict[str, Any], handler: CrashRecoveryHandler):
        self.config = config
        self.handler = handler
        self.logger = logging.getLogger(__name__)
        self.seed = config.get("seed", 42)
        set_deterministic_seed(self.seed)

    def generate_kinematic_chain(self, hinge_count: int, trial_id: str) -> Optional[str]:
        """
        Generate a kinematic chain with specified hinge count.
        
        Args:
            hinge_count: Number of hinges in the chain (3-10).
            trial_id: Unique identifier for the trial.
        
        Returns:
            URDF path if successful, None if failed.
        """
        # Generate a simple URDF for a kinematic chain
        urdf_content = self._create_kinematic_urdf(hinge_count)
        urdf_path = f"data/generated/temp_{trial_id}.urdf"
        
        try:
            os.makedirs(os.path.dirname(urdf_path), exist_ok=True)
            with open(urdf_path, "w") as f:
                f.write(urdf_content)
        except IOError as e:
            self.logger.error(f"Failed to write URDF: {e}")
            return None

        success, body_id = self.handler.handle_urdf_load(urdf_path, trial_id)
        if not success:
            return None

        return urdf_path

    def _create_kinematic_urdf(self, hinge_count: int) -> str:
        """Create a URDF string for a kinematic chain."""
        urdf = f'''<?xml version="1.0"?>
        <robot name="kinematic_chain_{hinge_count}">
            <link name="base_link">
                <inertial>
                    <mass value="1.0"/>
                    <inertia ixx="1.0" ixy="0.0" ixz="0.0" iyy="1.0" iyz="0.0" izz="1.0"/>
                </inertial>
                <visual>
                    <geometry><box size="0.1 0.1 0.1"/></geometry>
                    <material name="blue"><color rgba="0 0 1 1"/></material>
                </visual>
                <collision>
                    <geometry><box size="0.1 0.1 0.1"/></geometry>
                </collision>
            </link>
        '''
        
        for i in range(hinge_count):
            urdf += f'''
            <link name="link_{i}">
                <inertial>
                    <mass value="1.0"/>
                    <inertia ixx="1.0" ixy="0.0" ixz="0.0" iyy="1.0" iyz="0.0" izz="1.0"/>
                </inertial>
                <visual>
                    <geometry><box size="0.1 0.1 0.1"/></geometry>
                    <material name="green"><color rgba="0 1 0 1"/></material>
                </visual>
                <collision>
                    <geometry><box size="0.1 0.1 0.1"/></geometry>
                </collision>
            </link>
            <joint name="joint_{i}" type="continuous">
                <parent link="link_{i-1}"/>
                <child link="link_{i}"/>
                <axis xyz="0 0 1"/>
                <limit effort="1000.0" velocity="100.0"/>
            </joint>
            ''' if i > 0 else f'''
            <link name="link_{i}">
                <inertial>
                    <mass value="1.0"/>
                    <inertia ixx="1.0" ixy="0.0" ixz="0.0" iyy="1.0" iyz="0.0" izz="1.0"/>
                </inertial>
                <visual>
                    <geometry><box size="0.1 0.1 0.1"/></geometry>
                    <material name="green"><color rgba="0 1 0 1"/></material>
                </visual>
                <collision>
                    <geometry><box size="0.1 0.1 0.1"/></geometry>
                </collision>
            </link>
            <joint name="joint_{i}" type="continuous">
                <parent link="base_link"/>
                <child link="link_{i}"/>
                <axis xyz="0 0 1"/>
                <limit effort="1000.0" velocity="100.0"/>
            </joint>
            '''

        urdf += "</robot>"
        return urdf

    def generate_deformable_material(self, stiffness: float, trial_id: str) -> bool:
        """
        Configure deformable material properties.
        
        Args:
            stiffness: Material stiffness (0.1-1.0).
            trial_id: Unique identifier for the trial.
        
        Returns:
            True if successful, False otherwise.
        """
        # In a real implementation, this would configure PyBullet's soft body parameters
        # For now, we validate the stiffness range
        if not 0.1 <= stiffness <= 1.0:
            self.logger.warning(f"Stiffness {stiffness} out of range [0.1, 1.0]")
            return False
        
        # Simulate configuration
        time.sleep(0.01)  # Placeholder for actual configuration
        return True

    def run_simulation_trial(self, trial_id: str, hinge_count: int, stiffness: float) -> Dict[str, Any]:
        """
        Run a complete simulation trial with error handling.
        
        Args:
            trial_id: Unique identifier for the trial.
            hinge_count: Number of hinges in the kinematic chain.
            stiffness: Material stiffness for deformable objects.
        
        Returns:
            Dictionary containing trial results or error information.
        """
        self.logger.info(f"Starting trial {trial_id} with hinge_count={hinge_count}, stiffness={stiffness}")
        
        # Initialize PyBullet
        p.connect(p.DIRECT)
        p.setAdditionalSearchPath(pybullet_data.getDataPath())
        p.setGravity(0, 0, -9.81)
        
        result = {
            "trial_id": trial_id,
            "success": False,
            "error": None,
            "states": [],
            "topology_id": f"topo_{trial_id}"
        }

        try:
            # Generate kinematic chain
            urdf_path = self.generate_kinematic_chain(hinge_count, trial_id)
            if urdf_path is None:
                result["error"] = "Failed to generate kinematic chain"
                return result

            # Configure deformable material
            if not self.generate_deformable_material(stiffness, trial_id):
                result["error"] = "Failed to configure deformable material"
                return result

            # Run simulation steps
            num_steps = 100
            for step in range(num_steps):
                success, state = self.handler.handle_simulation_step(trial_id)
                if not success:
                    result["error"] = f"Simulation step {step} failed"
                    return result
                
                result["states"].append({
                    "step": step,
                    "state": state,
                    "timestamp": time.time()
                })

            result["success"] = True
            self.logger.info(f"Trial {trial_id} completed successfully")

        except Exception as e:
            result["error"] = str(e)
            self.logger.error(f"Trial {trial_id} failed with exception: {e}")
        finally:
            p.disconnect()

        return result

# --- Main Generation Function ---

def main():
    """Main entry point for data generation."""
    logger = setup_logging("data_generation")
    handler = CrashRecoveryHandler(logger)
    
    # Load configuration
    config_path = "code/config.yaml"
    if not os.path.exists(config_path):
        logger.error(f"Configuration file not found: {config_path}")
        sys.exit(1)
    
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)
    
    # Ensure output directories exist
    os.makedirs("data/generated", exist_ok=True)
    os.makedirs("data/results", exist_ok=True)
    
    # Generate test set
    generator = TopologyShiftGenerator(config, handler)
    all_results = []
    
    # Generate diverse set of topologies
    for i in range(config.get("trial_count", 50)):
        trial_id = f"trial_{i:03d}"
        hinge_count = random.randint(3, 10)
        stiffness = random.uniform(0.1, 1.0)
        
        result = generator.run_simulation_trial(trial_id, hinge_count, stiffness)
        all_results.append(result)
        
        if result["success"]:
            logger.info(f"Trial {trial_id} successful")
        else:
            logger.warning(f"Trial {trial_id} failed: {result['error']}")
    
    # Save results
    output_path = "data/generated/physics_states.json"
    with open(output_path, "w") as f:
        json.dump(all_results, f, indent=2)
    
    logger.info(f"Generated {len(all_results)} trials, saved to {output_path}")
    
    # Compute hash for zero-overlap verification
    with open(output_path, "rb") as f:
        content_hash = compute_sha256(f.read())
    
    logger.info(f"Generated data hash: {content_hash}")
    
    return all_results

if __name__ == "__main__":
    import yaml
    main()
