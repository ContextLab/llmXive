import os
import json
import time
import logging
import threading
from typing import Dict, List, Any, Optional, Tuple
import math

from src.config import POSE_DEV_TOLERANCE_CM, ORIENT_DEV_TOLERANCE_DEG

# Custom Exceptions
class ConnectionError(Exception):
    """Raised when robot connection fails."""
    pass

class SimulationFailureError(Exception):
    """Raised when simulation execution fails."""
    pass

class ExecutionTimeoutError(Exception):
    """Raised when task execution exceeds timeout."""
    pass

class ValidationFailedError(Exception):
    """Raised when validation metrics do not meet thresholds."""
    pass

# Data Classes
class ExecutionOutcome:
    def __init__(
        self,
        task_id: str,
        success: bool,
        failure_mode: Optional[str] = None,
        timestamp: Optional[float] = None
    ):
        self.task_id = task_id
        self.success = success
        self.failure_mode = failure_mode
        self.timestamp = timestamp if timestamp is not None else time.time()

        # Validate against schema constraints
        if not self.success and self.failure_mode is None:
            raise ValueError("failure_mode must be set if success is False")
        
        valid_modes = [
            "Planner Infeasibility", 
            "Controller Execution Failure", 
            "Hardware Error", 
            "Timeout"
        ]
        if self.failure_mode and self.failure_mode not in valid_modes:
            raise ValueError(f"Invalid failure_mode: {self.failure_mode}. Must be one of {valid_modes}")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "success": self.success,
            "failure_mode": self.failure_mode,
            "timestamp": self.timestamp
        }

class RobotController:
    """
    Simulates or interfaces with a physical robot controller.
    For this implementation, we assume a mock interface that returns
    pose and orientation telemetry.
    """
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._connected = False
        self._logger = logging.getLogger(__name__)

    def connect(self) -> bool:
        """
        Establish connection to the robot.
        In a real deployment, this would handle ROS bridge or hardware handshake.
        """
        # Simulate connection logic
        # If real hardware is required and unavailable, this should raise ConnectionError
        # For the purpose of this task, we simulate a successful connection
        self._connected = True
        self._logger.info("RobotController connected.")
        return True

    def disconnect(self):
        self._connected = False
        self._logger.info("RobotController disconnected.")

    def send_command(self, cmd: Dict[str, Any]) -> bool:
        if not self._connected:
            raise ConnectionError("Cannot send command: Robot not connected.")
        # Simulate command transmission
        self._logger.debug(f"Sending command: {cmd}")
        return True

    def get_current_pose(self) -> Tuple[float, float, float, float, float, float]:
        """
        Returns (x, y, z, roll, pitch, yaw) in meters and radians.
        In a real system, this reads from the robot's state estimator.
        """
        if not self._connected:
            raise ConnectionError("Cannot get pose: Robot not connected.")
        # Placeholder: In real usage, this would fetch from hardware
        # Returning a mock current state for the logic demonstration
        return (0.0, 0.0, 0.0, 0.0, 0.0, 0.0)

    def check_completion(
        self, 
        target_pose: Dict[str, float], 
        current_pose: Tuple[float, float, float, float, float, float]
    ) -> bool:
        """
        Checks if the robot has reached the target pose within tolerances.
        
        Args:
            target_pose: Dict with 'x', 'y', 'z', 'roll', 'pitch', 'yaw'
            current_pose: Tuple (x, y, z, roll, pitch, yaw)
        
        Returns:
            True if within tolerance, False otherwise.
        """
        cx, cy, cz, cr, cp, cyaw = current_pose
        
        tx = target_pose.get('x', 0.0)
        ty = target_pose.get('y', 0.0)
        tz = target_pose.get('z', 0.0)
        tr = target_pose.get('roll', 0.0)
        tp = target_pose.get('pitch', 0.0)
        tyaw = target_pose.get('yaw', 0.0)

        # Calculate deviations
        # Position deviation in cm
        pos_dev_m = math.sqrt(
            (cx - tx)**2 + 
            (cy - ty)**2 + 
            (cz - tz)**2
        )
        pos_dev_cm = pos_dev_m * 100.0

        # Orientation deviation in degrees
        # Normalize angles to [-pi, pi]
        def normalize_angle(angle):
            while angle > math.pi:
                angle -= 2 * math.pi
            while angle < -math.pi:
                angle += 2 * math.pi
            return angle

        diff_roll = normalize_angle(cr - tr)
        diff_pitch = normalize_angle(cp - tp)
        diff_yaw = normalize_angle(cyaw - tyaw)
        
        orient_dev_rad = math.sqrt(
            diff_roll**2 + 
            diff_pitch**2 + 
            diff_yaw**2
        )
        orient_dev_deg = math.degrees(orient_dev_rad)

        # Check against tolerances defined in config
        if pos_dev_cm <= POSE_DEV_TOLERANCE_CM and orient_dev_deg <= ORIENT_DEV_TOLERANCE_DEG:
            return True
        
        return False

class Executor:
    """
    Orchestrates the execution of an ActionSequence on the physical robot.
    Implements task completion detection and outcome recording.
    """
    def __init__(self, controller: RobotController):
        self.controller = controller
        self._logger = logging.getLogger(__name__)
        self._outcome_log: List[ExecutionOutcome] = []

    def execute_sequence(
        self, 
        action_sequence: List[Dict[str, Any]], 
        task_id: str,
        timeout_s: int = 60
    ) -> List[ExecutionOutcome]:
        """
        Executes a sequence of symbolic actions.
        
        Args:
            action_sequence: List of actions, each containing a 'target_pose' dict.
            task_id: Identifier for the current task.
            timeout_s: Maximum time allowed for the whole sequence.
        
        Returns:
            List of ExecutionOutcome objects.
        """
        if not self.controller._connected:
            try:
                self.controller.connect()
            except Exception as e:
                self._logger.error(f"Failed to connect to robot: {e}")
                raise ConnectionError("Robot connection failed.") from e

        outcomes = []
        start_time = time.time()

        for idx, action in enumerate(action_sequence):
            if time.time() - start_time > timeout_s:
                self._logger.warning(f"Task {task_id} timed out during action {idx}")
                outcome = ExecutionOutcome(
                    task_id=task_id,
                    success=False,
                    failure_mode="Timeout",
                    timestamp=time.time()
                )
                outcomes.append(outcome)
                break

            target_pose = action.get('target_pose')
            if not target_pose:
                self._logger.error(f"Action {idx} missing target_pose")
                outcome = ExecutionOutcome(
                    task_id=task_id,
                    success=False,
                    failure_mode="Controller Execution Failure",
                    timestamp=time.time()
                )
                outcomes.append(outcome)
                continue

            # Send command
            self.controller.send_command({'action': 'move_to', 'target': target_pose})
            
            # Poll for completion
            # In a real system, this would be a blocking wait or callback loop
            # Here we simulate a check
            current_pose = self.controller.get_current_pose()
            
            # Simulate a delay or check loop
            # For this implementation, we assume the robot moves and we check immediately
            # In a real scenario, we would loop until success or timeout
            is_complete = self.controller.check_completion(target_pose, current_pose)
            
            if is_complete:
                self._logger.info(f"Action {idx} completed successfully.")
                # If this is the last action, the task is successful
                if idx == len(action_sequence) - 1:
                    outcome = ExecutionOutcome(
                        task_id=task_id,
                        success=True,
                        timestamp=time.time()
                    )
                    outcomes.append(outcome)
            else:
                # If not complete, we might retry or fail depending on policy
                # For this task, we record a failure if the target is not reached within the step
                self._logger.warning(f"Action {idx} failed to reach target pose.")
                outcome = ExecutionOutcome(
                    task_id=task_id,
                    success=False,
                    failure_mode="Controller Execution Failure",
                    timestamp=time.time()
                )
                outcomes.append(outcome)
                break # Stop execution on first failure for this simplified logic

        self._outcome_log.extend(outcomes)
        return outcomes

    def get_outcomes(self) -> List[ExecutionOutcome]:
        return self._outcome_log

def run_executor_pipeline(
    action_sequences: List[List[Dict[str, Any]]], 
    task_ids: List[str]
) -> List[ExecutionOutcome]:
    """
    Runs the executor pipeline on a list of action sequences.
    """
    controller = RobotController()
    executor = Executor(controller)
    all_outcomes = []

    for seq, tid in zip(action_sequences, task_ids):
        outcomes = executor.execute_sequence(seq, tid)
        all_outcomes.extend(outcomes)

    return all_outcomes

def main():
    """
    Entry point for the executor script.
    """
    logging.basicConfig(level=logging.INFO)
    
    # Example usage
    controller = RobotController()
    try:
        controller.connect()
        executor = Executor(controller)
        
        # Mock action sequence for demonstration
        mock_actions = [
            {
                "action_id": "move_1",
                "target_pose": {
                    "x": 0.5, "y": 0.0, "z": 0.0,
                    "roll": 0.0, "pitch": 0.0, "yaw": 0.0
                }
            }
        ]
        
        outcomes = executor.execute_sequence(mock_actions, "TASK-001", timeout_s=10)
        for o in outcomes:
            print(json.dumps(o.to_dict(), indent=2))
            
    except ConnectionError as e:
        logging.error(f"Execution failed: {e}")
    finally:
        controller.disconnect()

if __name__ == "__main__":
    main()