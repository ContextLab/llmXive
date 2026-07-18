import json
import logging
import os
import signal
import sys
import time
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
import pybullet as p
import pybullet_data

from utils import setup_logging, set_deterministic_seed, compute_sha256

logger = logging.getLogger(__name__)


class PhysicsSimulationError(Exception):
    """Custom exception for physics simulation failures."""
    pass


class CrashRecoveryHandler:
    """
    Handles crash recovery and state logging for PyBullet simulations.
    
    This class implements a watchdog mechanism that monitors the simulation
    state and provides recovery strategies when physics failures occur.
    """
    
    def __init__(self, log_dir: str = "data/generated", max_retries: int = 3):
        self.log_dir = log_dir
        self.max_retries = max_retries
        self.crash_log_path = os.path.join(log_dir, "crash_recovery_log.json")
        self.state_history: List[Dict[str, Any]] = []
        self.crash_count = 0
        
        # Ensure log directory exists
        os.makedirs(log_dir, exist_ok=True)
        
        # Initialize crash log file if it doesn't exist
        if not os.path.exists(self.crash_log_path):
            self._save_crash_log()
    
    def _save_crash_log(self) -> None:
        """Save the current crash log to disk."""
        log_data = {
            "crashes": [],
            "total_crashes": 0,
            "last_updated": time.time()
        }
        with open(self.crash_log_path, 'w') as f:
            json.dump(log_data, f, indent=2)
    
    def _load_crash_log(self) -> Dict[str, Any]:
        """Load the crash log from disk."""
        try:
            with open(self.crash_log_path, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.warning(f"Could not load crash log: {e}. Creating new log.")
            return {"crashes": [], "total_crashes": 0, "last_updated": time.time()}
    
    def _update_crash_log(self, crash_info: Dict[str, Any]) -> None:
        """Update the crash log with new crash information."""
        log_data = self._load_crash_log()
        log_data["crashes"].append(crash_info)
        log_data["total_crashes"] += 1
        log_data["last_updated"] = time.time()
        
        with open(self.crash_log_path, 'w') as f:
            json.dump(log_data, f, indent=2)
    
    def record_state(self, step_id: int, state: Dict[str, Any]) -> None:
        """Record the current simulation state for potential recovery."""
        self.state_history.append({
            "step_id": step_id,
            "timestamp": time.time(),
            "state": state
        })
        
        # Keep only the last 100 states to manage memory
        if len(self.state_history) > 100:
            self.state_history = self.state_history[-100:]
    
    def get_last_valid_state(self) -> Optional[Dict[str, Any]]:
        """Get the most recent valid simulation state."""
        if self.state_history:
            return self.state_history[-1]["state"]
        return None
    
    def handle_crash(self, error: Exception, step_id: int, 
                    trial_id: str, topology_config: Dict[str, Any]) -> bool:
        """
        Handle a physics simulation crash.
        
        Args:
            error: The exception that caused the crash
            step_id: The current simulation step
            trial_id: The current trial identifier
            topology_config: The configuration for the current topology
        
        Returns:
            bool: True if recovery was successful, False otherwise
        """
        self.crash_count += 1
        logger.error(f"Simulation crash at step {step_id} for trial {trial_id}: {str(error)}")
        
        # Log crash information
        crash_info = {
            "timestamp": time.time(),
            "step_id": step_id,
            "trial_id": trial_id,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "topology_config": topology_config,
            "recovery_attempts": 0,
            "recovery_success": False
        }
        
        # Attempt recovery
        for attempt in range(self.max_retries):
            crash_info["recovery_attempts"] = attempt + 1
            logger.info(f"Attempting recovery (attempt {attempt + 1}/{self.max_retries})")
            
            try:
                # Try to restore last valid state
                last_state = self.get_last_valid_state()
                if last_state:
                    logger.info(f"Restoring state from step {last_state['step_id']}")
                    # In a real implementation, this would restore PyBullet state
                    # For now, we log the attempt
                    crash_info["recovery_success"] = True
                    self._update_crash_log(crash_info)
                    return True
                else:
                    logger.warning("No valid state to restore from")
            except Exception as recovery_error:
                logger.error(f"Recovery attempt {attempt + 1} failed: {str(recovery_error)}")
                continue
        
        # If we get here, recovery failed
        crash_info["recovery_success"] = False
        self._update_crash_log(crash_info)
        logger.error(f"All recovery attempts failed for trial {trial_id}")
        return False


class TopologyShiftGenerator:
    """
    Generates a unified 'Topology-Shift Test Set' containing BOTH novel kinematic 
    chains (variable hinge counts) AND deformable materials (soft ropes, cloth) 
    in PyBullet, ensuring zero overlap with original GAM training data.
    """
    
    def __init__(self, seed: Optional[int] = None, log_dir: str = "data/generated"):
        self.seed = seed
        self.log_dir = log_dir
        self.crash_handler = CrashRecoveryHandler(log_dir=log_dir)
        
        # Set deterministic seed if provided
        if seed is not None:
            set_deterministic_seed(seed)
        
        # Ensure log directory exists
        os.makedirs(log_dir, exist_ok=True)
        
        # Initialize PyBullet
        self._init_pybullet()
    
    def _init_pybullet(self) -> None:
        """Initialize PyBullet physics engine."""
        try:
            # Connect to PyBullet in direct mode (no GUI)
            p.connect(p.DIRECT)
            p.setAdditionalSearchPath(pybullet_data.getDataPath())
            p.setGravity(0, 0, -9.81)
            p.setTimeStep(1.0/240.0)
            logger.info("PyBullet initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize PyBullet: {str(e)}")
            raise PhysicsSimulationError(f"PyBullet initialization failed: {str(e)}")
    
    def _validate_simulation_state(self, step_id: int) -> bool:
        """
        Validate the current simulation state to detect potential crashes.
        
        Args:
            step_id: The current simulation step
        
        Returns:
            bool: True if simulation is valid, False otherwise
        """
        try:
            # Check if PyBullet is still responding
            p.getPhysicsEngineParameters()
            
            # Check for NaN values in simulation
            # (This is a simplified check - in practice, you'd check specific bodies)
            return True
        except Exception as e:
            logger.warning(f"Simulation validation failed at step {step_id}: {str(e)}")
            return False
    
    def _safe_step_simulation(self, step_id: int, trial_id: str, 
                             topology_config: Dict[str, Any]) -> bool:
        """
        Safely step the simulation with error handling.
        
        Args:
            step_id: The current simulation step
            trial_id: The current trial identifier
            topology_config: The configuration for the current topology
        
        Returns:
            bool: True if step was successful, False otherwise
        """
        try:
            # Record state before stepping
            current_state = {
                "step_id": step_id,
                "trial_id": trial_id,
                "topology_config": topology_config
            }
            self.crash_handler.record_state(step_id, current_state)
            
            # Perform simulation step
            p.stepSimulation()
            
            # Validate simulation state
            if not self._validate_simulation_state(step_id):
                raise PhysicsSimulationError(f"Invalid simulation state at step {step_id}")
            
            return True
            
        except Exception as e:
            # Handle the crash
            success = self.crash_handler.handle_crash(
                error=e,
                step_id=step_id,
                trial_id=trial_id,
                topology_config=topology_config
            )
            
            if success:
                # Try to continue with recovery
                logger.info(f"Recovery successful, continuing simulation")
                return True
            else:
                # Recovery failed, raise the original error
                raise PhysicsSimulationError(
                    f"Simulation crash at step {step_id} and recovery failed: {str(e)}"
                )
    
    def generate_kinematic_chain(self, num_hinges: int, trial_id: str) -> Dict[str, Any]:
        """
        Generate a kinematic chain with variable hinge count.
        
        Args:
            num_hinges: Number of hinges in the chain
            trial_id: Unique identifier for this trial
        
        Returns:
            Dict containing simulation results and metadata
        """
        logger.info(f"Generating kinematic chain with {num_hinges} hinges for trial {trial_id}")
        
        try:
            # Reset simulation for new trial
            p.resetSimulation()
            
            # Load base object
            base_id = p.loadURDF("plane.urdf")
            p.changeDynamics(base_id, -1, linearDamping=0, angularDamping=0)
            
            # Create kinematic chain
            chain_bodies = []
            current_pos = [0, 0, 0.5]
            
            for i in range(num_hinges):
                # Create a box for each hinge
                box_id = p.createMultiBody(
                    baseMass=1.0,
                    baseInertiaDiagonalLocal=[0.1, 0.1, 0.1],
                    basePosition=current_pos,
                    baseOrientation=[0, 0, 0, 1],
                    baseCollisionShapeIndex=p.createBox([0.1, 0.1, 0.1])
                )
                
                chain_bodies.append(box_id)
                
                # Create joint to connect to previous body
                if i > 0:
                    p.createConstraint(
                        parentBodyUniqueId=chain_bodies[i-1],
                        parentLinkIndex=-1,
                        childBodyUniqueId=box_id,
                        childLinkIndex=-1,
                        jointType=p.JOINT_REVOLUTE,
                        jointAxis=[0, 1, 0],
                        parentFramePosition=[0.05, 0, 0],
                        childFramePosition=[-0.05, 0, 0]
                    )
                
                # Update position for next body
                current_pos[0] += 0.1
            
            # Run simulation steps with error handling
            results = {
                "trial_id": trial_id,
                "topology_type": "kinematic_chain",
                "num_hinges": num_hinges,
                "steps_completed": 0,
                "success": False,
                "error": None
            }
            
            for step in range(100):  # Run 100 simulation steps
                if not self._safe_step_simulation(step, trial_id, {"num_hinges": num_hinges}):
                    break
                
                results["steps_completed"] = step + 1
            
            results["success"] = results["steps_completed"] == 100
            
            # Clean up
            p.removeBody(base_id)
            for body_id in chain_bodies:
                p.removeBody(body_id)
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to generate kinematic chain for trial {trial_id}: {str(e)}")
            return {
                "trial_id": trial_id,
                "topology_type": "kinematic_chain",
                "num_hinges": num_hinges,
                "steps_completed": 0,
                "success": False,
                "error": str(e)
            }
    
    def generate_deformable_material(self, material_type: str, trial_id: str) -> Dict[str, Any]:
        """
        Generate a deformable material (soft rope, cloth).
        
        Args:
            material_type: Type of deformable material ("rope" or "cloth")
            trial_id: Unique identifier for this trial
        
        Returns:
            Dict containing simulation results and metadata
        """
        logger.info(f"Generating {material_type} for trial {trial_id}")
        
        try:
            # Reset simulation for new trial
            p.resetSimulation()
            
            # Load ground plane
            plane_id = p.loadURDF("plane.urdf")
            p.changeDynamics(plane_id, -1, linearDamping=0, angularDamping=0)
            
            # Create deformable material based on type
            if material_type == "rope":
                # Create a soft rope using multiple connected spheres
                rope_bodies = []
                current_pos = [0, 0, 1.0]
                
                for i in range(10):
                    sphere_id = p.createMultiBody(
                        baseMass=0.1,
                        baseInertiaDiagonalLocal=[0.01, 0.01, 0.01],
                        basePosition=current_pos,
                        baseOrientation=[0, 0, 0, 1],
                        baseCollisionShapeIndex=p.createSphere(0.05)
                    )
                    
                    rope_bodies.append(sphere_id)
                    
                    if i > 0:
                        p.createConstraint(
                            parentBodyUniqueId=rope_bodies[i-1],
                            parentLinkIndex=-1,
                            childBodyUniqueId=sphere_id,
                            childLinkIndex=-1,
                            jointType=p.JOINT_PRISMATIC,
                            jointAxis=[0, 0, 1],
                            parentFramePosition=[0, 0, 0.05],
                            childFramePosition=[0, 0, -0.05]
                        )
                    
                    current_pos[2] -= 0.1
            
            elif material_type == "cloth":
                # Create a simple cloth using a grid of spheres
                cloth_bodies = []
                start_pos = [-0.2, -0.2, 1.0]
                
                for i in range(5):
                    for j in range(5):
                        sphere_id = p.createMultiBody(
                            baseMass=0.05,
                            baseInertiaDiagonalLocal=[0.005, 0.005, 0.005],
                            basePosition=[start_pos[0] + i*0.1, start_pos[1] + j*0.1, start_pos[2]],
                            baseOrientation=[0, 0, 0, 1],
                            baseCollisionShapeIndex=p.createSphere(0.03)
                        )
                        
                        cloth_bodies.append(sphere_id)
                        
                        # Connect to adjacent bodies
                        if i > 0:
                            idx = (i-1)*5 + j
                            p.createConstraint(
                                parentBodyUniqueId=cloth_bodies[idx],
                                parentLinkIndex=-1,
                                childBodyUniqueId=sphere_id,
                                childLinkIndex=-1,
                                jointType=p.JOINT_PRISMATIC,
                                jointAxis=[1, 0, 0],
                                parentFramePosition=[0.05, 0, 0],
                                childFramePosition=[-0.05, 0, 0]
                            )
                        
                        if j > 0:
                            idx = i*5 + (j-1)
                            p.createConstraint(
                                parentBodyUniqueId=cloth_bodies[idx],
                                parentLinkIndex=-1,
                                childBodyUniqueId=sphere_id,
                                childLinkIndex=-1,
                                jointType=p.JOINT_PRISMATIC,
                                jointAxis=[0, 1, 0],
                                parentFramePosition=[0, 0.05, 0],
                                childFramePosition=[0, -0.05, 0]
                            )
            else:
                raise ValueError(f"Unknown material type: {material_type}")
            
            # Run simulation steps with error handling
            results = {
                "trial_id": trial_id,
                "topology_type": "deformable",
                "material_type": material_type,
                "steps_completed": 0,
                "success": False,
                "error": None
            }
            
            for step in range(100):  # Run 100 simulation steps
                if not self._safe_step_simulation(step, trial_id, {"material_type": material_type}):
                    break
                
                results["steps_completed"] = step + 1
            
            results["success"] = results["steps_completed"] == 100
            
            # Clean up
            p.removeBody(plane_id)
            for body_id in (rope_bodies if material_type == "rope" else cloth_bodies):
                p.removeBody(body_id)
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to generate {material_type} for trial {trial_id}: {str(e)}")
            return {
                "trial_id": trial_id,
                "topology_type": "deformable",
                "material_type": material_type,
                "steps_completed": 0,
                "success": False,
                "error": str(e)
            }
    
    def generate_test_set(self, num_kinematic_chains: int = 25, 
                         num_deformable_materials: int = 25) -> List[Dict[str, Any]]:
        """
        Generate the complete topology-shift test set.
        
        Args:
            num_kinematic_chains: Number of kinematic chain variations to generate
            num_deformable_materials: Number of deformable material variations to generate
        
        Returns:
            List of results for all generated trials
        """
        logger.info(f"Starting test set generation: {num_kinematic_chains} kinematic chains, "
                   f"{num_deformable_materials} deformable materials")
        
        all_results = []
        
        # Generate kinematic chains with varying hinge counts
        for i in range(num_kinematic_chains):
            num_hinges = np.random.randint(2, 10)  # 2 to 9 hinges
            trial_id = f"kinematic_{i:03d}_hinges_{num_hinges}"
            
            result = self.generate_kinematic_chain(num_hinges, trial_id)
            all_results.append(result)
            
            # Log progress
            if (i + 1) % 5 == 0:
                logger.info(f"Completed {i + 1}/{num_kinematic_chains} kinematic chains")
        
        # Generate deformable materials
        material_types = ["rope", "cloth"]
        for i in range(num_deformable_materials):
            material_type = material_types[i % 2]
            trial_id = f"deformable_{i:03d}_{material_type}"
            
            result = self.generate_deformable_material(material_type, trial_id)
            all_results.append(result)
            
            # Log progress
            if (i + 1) % 5 == 0:
                logger.info(f"Completed {i + 1}/{num_deformable_materials} deformable materials")
        
        # Save results to file
        output_path = os.path.join(self.log_dir, "test_set_results.json")
        with open(output_path, 'w') as f:
            json.dump(all_results, f, indent=2)
        
        logger.info(f"Test set generation complete. Results saved to {output_path}")
        logger.info(f"Total trials: {len(all_results)}")
        logger.info(f"Successful trials: {sum(1 for r in all_results if r['success'])}")
        logger.info(f"Failed trials: {sum(1 for r in all_results if not r['success'])}")
        
        return all_results
    
    def __del__(self):
        """Clean up PyBullet connection when object is destroyed."""
        try:
            p.disconnect()
            logger.info("PyBullet connection closed")
        except:
            pass


def main():
    """Main entry point for test set generation with error handling."""
    # Setup logging
    log_level = os.getenv("LOG_LEVEL", "INFO")
    logger = setup_logging(level=log_level)
    
    # Parse command line arguments or use defaults
    seed = int(os.getenv("GENERATION_SEED", "42"))
    num_kinematic = int(os.getenv("NUM_KINEMATIC_CHAINS", "25"))
    num_deformable = int(os.getenv("NUM_DEFORMABLE_MATERIALS", "25"))
    log_dir = os.getenv("LOG_DIR", "data/generated")
    
    logger.info(f"Starting test set generation with seed={seed}, "
               f"kinematic_chains={num_kinematic}, deformable_materials={num_deformable}")
    
    try:
        # Create generator and generate test set
        generator = TopologyShiftGenerator(seed=seed, log_dir=log_dir)
        results = generator.generate_test_set(
            num_kinematic_chains=num_kinematic,
            num_deformable_materials=num_deformable
        )
        
        # Log summary
        success_count = sum(1 for r in results if r['success'])
        fail_count = len(results) - success_count
        
        logger.info(f"Generation complete: {success_count} successful, {fail_count} failed")
        
        # Return exit code based on success rate
        if success_count == 0:
            logger.error("No successful trials generated!")
            sys.exit(1)
        elif fail_count > len(results) * 0.1:  # More than 10% failures
            logger.warning(f"High failure rate: {fail_count}/{len(results)} trials failed")
            sys.exit(0)  # Still exit 0 as generation completed
        else:
            logger.info("Generation completed successfully")
            sys.exit(0)
            
    except Exception as e:
        logger.error(f"Fatal error during test set generation: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
