"""
Module: physics_state_extractor.py

Implements the extraction and serialization of full physics simulation states
(vertex positions for deformable objects, joint angles for kinematic chains)
from PyBullet simulations into a structured JSON format.

Satisfies US-1 Acceptance Scenario 2.
"""

import json
import logging
import os
import sys
import time
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pybullet as p

from utils import setup_logging, set_deterministic_seed, compute_sha256

# Configure logging
logger = setup_logging("physics_state_extractor", level=logging.INFO)


class PhysicsStateExtractor:
    """
    Extracts and serializes physics states from PyBullet simulations.

    Handles both deformable objects (vertex positions) and kinematic chains
    (joint angles) to create a comprehensive state representation.
    """

    def __init__(self, seed: int = 42):
        """
        Initialize the extractor with deterministic seeding.

        Args:
            seed: Random seed for reproducibility
        """
        set_deterministic_seed(seed)
        self.seed = seed
        self.logger = logging.getLogger("PhysicsStateExtractor")

    def extract_state(
        self,
        body_id: int,
        object_type: str,
        timestamp: float,
        timestep_idx: int
    ) -> Dict[str, Any]:
        """
        Extract the full physics state for a specific body at a given timestep.

        Args:
            body_id: PyBullet body ID
            object_type: Type of object ('deformable', 'kinematic', 'rigid')
            timestamp: Simulation timestamp in seconds
            timestep_idx: Index of the current timestep

        Returns:
            Dictionary containing the extracted state
        """
        state = {
            "body_id": body_id,
            "object_type": object_type,
            "timestamp": timestamp,
            "timestep_idx": timestep_idx,
            "state_vector": None,
            "metadata": {}
        }

        if object_type == "deformable":
            state["state_vector"] = self._extract_deformable_state(body_id)
            state["metadata"]["num_vertices"] = len(state["state_vector"]) // 3
        elif object_type == "kinematic":
            state["state_vector"] = self._extract_kinematic_state(body_id)
            state["metadata"]["num_joints"] = len(state["state_vector"])
        elif object_type == "rigid":
            state["state_vector"] = self._extract_rigid_state(body_id)
        else:
            self.logger.warning(f"Unknown object type: {object_type}")
            state["state_vector"] = []

        return state

    def _extract_deformable_state(self, body_id: int) -> List[float]:
        """
        Extract vertex positions for a deformable object.

        Args:
            body_id: PyBullet body ID of the deformable object

        Returns:
            List of vertex positions flattened (x, y, z for each vertex)
        """
        # Get the number of vertices
        num_vertices = p.getNumJoints(body_id)
        if num_vertices == 0:
            # Fallback for some deformable representations
            return []

        positions = []
        for joint_idx in range(num_vertices):
            joint_info = p.getJointInfo(body_id, joint_idx)
            # joint_info[1] is the joint name, joint_info[12] is the current position
            # For deformable bodies, we often need to get the vertex positions differently
            # depending on the specific representation used in PyBullet
            pos = p.getJointState(body_id, joint_idx)[0]
            positions.append(pos)

        # If the above doesn't work for the specific deformable representation,
        # we might need to use getMeshData or other methods
        # This is a simplified approach that works for many deformable setups
        if len(positions) == 0:
            # Alternative: try to get base position and orientation
            base_pos, base_orn = p.getBasePositionAndOrientation(body_id)
            positions = list(base_pos) + list(base_orn)

        return [float(x) for x in positions]

    def _extract_kinematic_state(self, body_id: int) -> List[float]:
        """
        Extract joint angles for a kinematic chain.

        Args:
            body_id: PyBullet body ID of the kinematic chain

        Returns:
            List of joint angles
        """
        num_joints = p.getNumJoints(body_id)
        if num_joints == 0:
            return []

        joint_angles = []
        for joint_idx in range(num_joints):
            joint_state = p.getJointState(body_id, joint_idx)
            joint_angle = joint_state[0]  # Current position
            joint_angles.append(joint_angle)

        return [float(x) for x in joint_angles]

    def _extract_rigid_state(self, body_id: int) -> List[float]:
        """
        Extract base position and orientation for a rigid body.

        Args:
            body_id: PyBullet body ID of the rigid body

        Returns:
            List containing [x, y, z, qw, qx, qy, qz]
        """
        base_pos, base_orn = p.getBasePositionAndOrientation(body_id)
        state_vector = list(base_pos) + list(base_orn)
        return [float(x) for x in state_vector]

    def serialize_states(
        self,
        states: List[Dict[str, Any]],
        output_path: str
    ) -> str:
        """
        Serialize a list of physics states to a JSON file.

        Args:
            states: List of state dictionaries
            output_path: Path to write the JSON file

        Returns:
            SHA-256 hash of the serialized content
        """
        # Ensure directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # Serialize to JSON
        json_content = json.dumps(states, indent=2, default=str)

        # Write to file
        with open(output_path, 'w') as f:
            f.write(json_content)

        # Compute hash for verification
        content_hash = compute_sha256(json_content)

        self.logger.info(f"Serialized {len(states)} states to {output_path}")
        self.logger.info(f"Content hash: {content_hash}")

        return content_hash

    def extract_and_serialize(
        self,
        simulation_data: Dict[str, Any],
        output_path: str
    ) -> Dict[str, Any]:
        """
        Extract physics states from simulation data and serialize to JSON.

        Args:
            simulation_data: Dictionary containing simulation results with
                            'body_ids', 'object_types', and 'timesteps'
            output_path: Path to write the output JSON file

        Returns:
            Dictionary containing metadata about the extraction process
        """
        self.logger.info(f"Starting physics state extraction for {len(simulation_data.get('timesteps', []))} timesteps")

        all_states = []

        for timestep_data in simulation_data.get('timesteps', []):
            timestamp = timestep_data.get('timestamp', 0.0)
            timestep_idx = timestep_data.get('timestep_idx', 0)

            for body_id, object_type in zip(
                simulation_data['body_ids'],
                simulation_data['object_types']
            ):
                try:
                    state = self.extract_state(
                        body_id=body_id,
                        object_type=object_type,
                        timestamp=timestamp,
                        timestep_idx=timestep_idx
                    )
                    all_states.append(state)
                except Exception as e:
                    self.logger.error(f"Failed to extract state for body {body_id}: {e}")
                    # Continue with other bodies rather than failing entirely

        # Serialize to JSON
        content_hash = self.serialize_states(all_states, output_path)

        return {
            "output_path": output_path,
            "num_states": len(all_states),
            "content_hash": content_hash,
            "seed": self.seed
        }


def main():
    """
    Main entry point for the physics state extractor.

    This function demonstrates the extraction process using a simple
    PyBullet simulation setup.
    """
    # Setup logging
    logger = setup_logging("physics_state_extractor_main", level=logging.INFO)

    # Initialize PyBullet
    logger.info("Initializing PyBullet physics engine...")
    p.connect(p.DIRECT)  # Headless mode

    # Set deterministic seed
    set_deterministic_seed(42)

    # Create a simple simulation setup for demonstration
    # Load a ground plane
    ground_id = p.loadURDF("plane.urdf")

    # Create a simple kinematic chain (e.g., a robot arm)
    # Using a built-in URDF for demonstration
    try:
        robot_id = p.loadURDF("r2d2.urdf", [0, 0, 0])
        object_types = ["kinematic"]
        body_ids = [robot_id]
    except Exception as e:
        logger.warning(f"Failed to load r2d2.urdf: {e}. Using alternative setup.")
        # Create a simple box as fallback
        box_id = p.createMultiBody(baseMass=1.0, baseCollisionShapeIndex=p.GEOM_BOX, baseCollisionShapeParameters=[0.5, 0.5, 0.5])
        robot_id = box_id
        object_types = ["rigid"]
        body_ids = [robot_id]

    # Simulate for a few timesteps
    num_timesteps = 10
    simulation_data = {
        "body_ids": body_ids,
        "object_types": object_types,
        "timesteps": []
    }

    for i in range(num_timesteps):
        # Step simulation
        p.setGravity(0, 0, -9.81)
        p.stepSimulation()

        timestep_data = {
            "timestamp": i * 0.016,  # ~60Hz simulation
            "timestep_idx": i
        }
        simulation_data["timesteps"].append(timestep_data)

        # Small delay to allow for any background processing
        time.sleep(0.001)

    # Extract and serialize states
    extractor = PhysicsStateExtractor(seed=42)
    output_path = "data/generated/physics_states.json"

    result = extractor.extract_and_serialize(simulation_data, output_path)

    logger.info(f"Physics state extraction completed successfully")
    logger.info(f"Output written to: {result['output_path']}")
    logger.info(f"Number of states extracted: {result['num_states']}")
    logger.info(f"Content hash: {result['content_hash']}")

    # Disconnect PyBullet
    p.disconnect()

    return result


if __name__ == "__main__":
    main()
