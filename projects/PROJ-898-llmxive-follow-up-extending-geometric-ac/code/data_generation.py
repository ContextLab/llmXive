import json
import logging
import os
import signal
import sys
import time
import math
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
import pybullet as p
import numpy as np

# Import from project utilities
from utils import setup_logging, set_deterministic_seed, compute_sha256
from config import load_config, TopologyConfig, ExperimentConfig

# -----------------------------------------------------------------------------
# Custom Exceptions
# -----------------------------------------------------------------------------
class PhysicsSimulationError(Exception):
    """Base exception for physics simulation failures."""
    pass

class URDFLoadError(PhysicsSimulationError):
    """Raised when loading a URDF file fails (e.g., p.loadURDF returns -1)."""
    def __init__(self, message: str, urdf_path: str):
        super().__init__(f"Failed to load URDF '{urdf_path}': {message}")
        self.urdf_path = urdf_path

class SimulationStepError(PhysicsSimulationError):
    """Raised when a simulation step produces invalid results (e.g., NaN)."""
    def __init__(self, message: str, step_data: Dict[str, Any]):
        super().__init__(f"Simulation step failed: {message}")
        self.step_data = step_data

class TimeoutError(PhysicsSimulationError):
    """Raised when a simulation exceeds the allowed time limit."""
    pass

# -----------------------------------------------------------------------------
# Data Classes
# -----------------------------------------------------------------------------
@dataclass
class RecoveryResult:
    """Result of a crash recovery attempt."""
    success: bool
    retry_count: int
    error_log: List[str]
    skipped_trial: bool

# -----------------------------------------------------------------------------
# Error Handler
# -----------------------------------------------------------------------------
class CrashRecoveryHandler:
    """
    Handles specific failure modes in PyBullet simulation:
    1. URDF Load Failures (p.loadURDF returns -1)
    2. Simulation Step NaNs
    
    Recovery Mechanism:
    - Retry with exponential backoff.
    - Log errors to data/results/errors.log.
    - Skip trial if max retries exceeded.
    """
    def __init__(self, logger: logging.Logger, max_retries: int = 3, base_delay: float = 1.0):
        self.logger = logger
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.error_log_path = "data/results/errors.log"
        self._ensure_error_log_dir()

    def _ensure_error_log_dir(self):
        """Ensure the directory for error logs exists."""
        dir_path = os.path.dirname(self.error_log_path)
        if dir_path and not os.path.exists(dir_path):
            os.makedirs(dir_path, exist_ok=True)

    def _log_error(self, message: str, details: Optional[Dict[str, Any]] = None):
        """Log error to both logger and file."""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] ERROR: {message}"
        if details:
            log_entry += f" | Details: {details}"
        
        self.logger.error(log_entry)
        
        with open(self.error_log_path, "a", encoding="utf-8") as f:
            f.write(log_entry + "\n")

    def load_urdf_with_recovery(self, urdf_path: str, base_position: List[float], 
                                base_orientation: List[float]) -> Tuple[int, bool]:
        """
        Attempt to load a URDF with retry logic.
        Returns (body_id, success). If body_id is -1 and success is False, the load failed.
        """
        for attempt in range(self.max_retries):
            try:
                # PyBullet returns -1 on failure
                body_id = p.loadURDF(urdf_path, basePosition=base_position, 
                                     baseOrientation=base_orientation)
                
                if body_id == -1:
                    error_msg = f"PyBullet returned -1 for URDF load: {urdf_path}"
                    self._log_error(error_msg, {"attempt": attempt + 1, "urdf": urdf_path})
                    if attempt < self.max_retries - 1:
                        delay = self.base_delay * (2 ** attempt)
                        self.logger.warning(f"Retrying in {delay}s...")
                        time.sleep(delay)
                        continue
                    else:
                        return -1, False
                
                return body_id, True

            except Exception as e:
                self._log_error(f"Exception during URDF load: {str(e)}", 
                                {"attempt": attempt + 1, "urdf": urdf_path})
                if attempt < self.max_retries - 1:
                    delay = self.base_delay * (2 ** attempt)
                    time.sleep(delay)
                else:
                    return -1, False
        
        return -1, False

    def validate_simulation_step(self, state: Dict[str, Any]) -> bool:
        """
        Check if simulation step results contain NaN or Inf values.
        Returns True if valid, False otherwise.
        """
        valid = True
        for key, value in state.items():
            if isinstance(value, (float, int, np.number)):
                if math.isnan(value) or math.isinf(value):
                    valid = False
                    break
            elif isinstance(value, (list, np.ndarray)):
                arr = np.array(value)
                if np.any(np.isnan(arr)) or np.any(np.isinf(arr)):
                    valid = False
                    break
            
            if not valid:
                self._log_error(f"NaN/Inf detected in simulation state: {key} = {value}", state)
                break
        
        return valid

    def recover_from_step_error(self, step_data: Dict[str, Any]) -> RecoveryResult:
        """
        Attempt to recover from a simulation step error (NaN/Inf).
        In this context, recovery usually means resetting the simulation or skipping the step.
        Here we implement a 'skip trial' strategy for simplicity in the generation loop.
        """
        self._log_error("Simulation step produced invalid data. Skipping trial.", step_data)
        return RecoveryResult(
            success=False,
            retry_count=0,
            error_log=[f"NaN/Inf in step data: {list(step_data.keys())}"],
            skipped_trial=True
        )

# -----------------------------------------------------------------------------
# Topology Shift Generator (Simplified for T011 context)
# -----------------------------------------------------------------------------
class TopologyShiftGenerator:
    """
    Generates diverse kinematic chains and deformable objects.
    This implementation focuses on the error handling logic required by T011.
    """
    def __init__(self, config: ExperimentConfig, handler: CrashRecoveryHandler):
        self.config = config
        self.handler = handler
        self.logger = logging.getLogger(__name__)

    def generate_trial(self, trial_id: int) -> Optional[Dict[str, Any]]:
        """
        Generate a single trial. Returns None if the trial was skipped due to unrecoverable errors.
        """
        set_deterministic_seed(self.config.seed + trial_id)
        
        # Simulated URDF paths (in a real scenario, these would be real paths)
        # For the purpose of T011 implementation, we assume we are iterating over a list of URDFs
        # and handling the case where loadURDF fails or simulation breaks.
        
        # Placeholder URDFs for demonstration of error handling logic
        # In a real run, these would be populated from a dataset or generated dynamically
        urdf_candidates = [
            "data/raw/simple_cube.urdf", 
            "data/raw/chain_5_links.urdf",
            "data/raw/deformable_sphere.urdf"
        ]
        
        selected_urdf = urdf_candidates[trial_id % len(urdf_candidates)]
        base_pos = [0.0, 0.0, 0.5]
        base_orient = [0.0, 0.0, 0.0, 1.0]

        # 1. Attempt URDF Load with Recovery
        body_id, load_success = self.handler.load_urdf_with_recovery(
            selected_urdf, base_pos, base_orient
        )

        if not load_success:
            self.logger.warning(f"Trial {trial_id} skipped: URDF load failed after retries.")
            return None

        try:
            # 2. Run Simulation Steps with Validation
            physics_state = []
            steps = 10 # Reduced for demo
            
            for step in range(steps):
                p.stepSimulation()
                time.sleep(0.01)

                # Extract state
                pos, orn, _, _ = p.getBasePositionAndOrientation(body_id)
                state = {
                    "position": pos,
                    "orientation": orn,
                    "timestamp": step * 0.01
                }

                # 3. Validate Step (Check for NaN)
                if not self.handler.validate_simulation_step(state):
                    recovery = self.handler.recover_from_step_error(state)
                    if recovery.skipped_trial:
                        return None
                    # If recovery logic allowed continuing, we would proceed here

                physics_state.append(state)

            return {
                "trial_id": trial_id,
                "topology_id": f"topo_{trial_id}",
                "physics_state": physics_state,
                "success": True
            }

        except Exception as e:
            self.handler._log_error(f"Unexpected error in trial {trial_id}: {str(e)}")
            return None

        finally:
            # Cleanup
            if body_id != -1:
                p.removeBody(body_id)

# -----------------------------------------------------------------------------
# Main Entry Point
# -----------------------------------------------------------------------------
def main():
    """
    Main entry point for data generation with error handling.
    """
    # Setup
    logger = setup_logging()
    config = load_config()
    handler = CrashRecoveryHandler(logger, max_retries=3)
    
    generator = TopologyShiftGenerator(config, handler)
    
    results = []
    successful_trials = 0
    skipped_trials = 0

    logger.info(f"Starting generation for {config.trial_count} trials...")

    for i in range(config.trial_count):
        result = generator.generate_trial(i)
        if result:
            results.append(result)
            successful_trials += 1
        else:
            skipped_trials += 1

    logger.info(f"Generation complete. Success: {successful_trials}, Skipped: {skipped_trials}")
    
    # Save results (placeholder path, actual path depends on T009-serialize)
    output_path = "data/generated/physics_states.json"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Results saved to {output_path}")
    logger.info(f"Error log available at {handler.error_log_path}")

if __name__ == "__main__":
    main()
