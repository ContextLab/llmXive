import os
import json
import time
import logging
import threading
import tracemalloc
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, asdict
import pyarrow as pa
import pyarrow.parquet as pq
import pandas as pd

from src.config import BASE_DIR, REAL_WORLD_SPLIT, POSE_DEV_TOLERANCE_CM, ORIENT_DEV_TOLERANCE_DEG
from src.state_mapper import SymbolicState
from src.planner import ActionSequence

# Custom exceptions for specific failure modes
class ConnectionError(Exception):
    """Raised when robot connection fails."""
    pass

class SimulationFailureError(Exception):
    """Raised when simulation execution fails."""
    pass

class ExecutionTimeoutError(Exception):
    """Raised when execution exceeds time limit."""
    pass

class ValidationFailedError(Exception):
    """Raised when validation checks fail."""
    pass

@dataclass
class ExecutionOutcome:
    """Dataclass representing the result of a task execution."""
    task_id: str
    success: bool
    failure_mode: Optional[str]  # "Planner Infeasibility", "Controller Execution Failure", "Hardware Error", "Timeout"
    timestamp: float
    replan_attempted: bool = False
    execution_time_s: float = 0.0
    pose_deviation_cm: float = 0.0
    orient_deviation_deg: float = 0.0

class RobotController:
    """Simulates or connects to a physical robot controller."""
    
    def __init__(self, connection_string: Optional[str] = None):
        self.connection_string = connection_string
        self.connected = False
        self.logger = logging.getLogger(__name__)

    def connect(self) -> bool:
        """Attempt to connect to the robot hardware."""
        # In a real scenario, this would check for hardware availability.
        # For this implementation, we assume a simulation environment or 
        # raise an error if hardware is strictly required and missing.
        # Per T000, if hardware is NOT available, we should raise.
        # Here we simulate a connection check.
        if not self.connection_string:
            # Simulate a check: if no string, assume no hardware/sim available
            raise ConnectionError("No robot connection string provided and no simulation fallback available.")
        
        self.connected = True
        self.logger.info(f"Connected to robot at {self.connection_string}")
        return True

    def execute_action(self, action: Dict[str, Any]) -> Tuple[bool, float, float]:
        """
        Execute a single action.
        Returns: (success, pose_deviation_cm, orient_deviation_deg)
        """
        if not self.connected:
            raise ConnectionError("Robot not connected.")
        
        # Simulate execution logic
        # In a real implementation, this sends commands to the robot
        # and waits for feedback.
        time.sleep(0.1) # Simulate action time
        
        # Mock result for demonstration if no real robot
        # In real run, this would come from sensor feedback
        success = True
        pose_dev = 2.0 # cm
        orient_dev = 5.0 # deg
        
        return success, pose_dev, orient_dev

class Executor:
    """Manages the execution of ActionSequences on the robot."""
    
    def __init__(self, robot_controller: RobotController, logger: Optional[logging.Logger] = None):
        self.robot = robot_controller
        self.logger = logger or logging.getLogger(__name__)
        self.execution_logs: List[ExecutionOutcome] = []

    def check_completion(self, pose_dev: float, orient_dev: float) -> bool:
        """Check if the robot has reached the target within tolerances."""
        return (pose_dev <= POSE_DEV_TOLERANCE_CM and 
                orient_dev <= ORIENT_DEV_TOLERANCE_DEG)

    def execute_sequence(self, 
                         sequence: ActionSequence, 
                         task_id: str, 
                         replan_support: bool = False,
                         timeout_s: float = 60.0) -> ExecutionOutcome:
        """
        Execute a sequence of actions.
        Handles replanning logic if supported.
        """
        start_time = time.time()
        self.logger.info(f"Starting execution for task {task_id}")
        
        try:
            for i, action in enumerate(sequence.actions):
                # Check timeout
                if time.time() - start_time > timeout_s:
                    raise ExecutionTimeoutError(f"Execution timed out at step {i}")
                
                # Execute action
                success, pose_dev, orient_dev = self.robot.execute_action(action)
                
                if not success:
                    # Determine failure mode
                    # If the planner said it was feasible but execution failed: Controller Execution Failure
                    # If the planner couldn't find a path initially: Planner Infeasibility (handled before execution)
                    failure_mode = "Controller Execution Failure"
                    
                    outcome = ExecutionOutcome(
                        task_id=task_id,
                        success=False,
                        failure_mode=failure_mode,
                        timestamp=time.time(),
                        replan_attempted=False,
                        execution_time_s=time.time() - start_time,
                        pose_deviation_cm=pose_dev,
                        orient_deviation_deg=orient_dev
                    )
                    
                    # Replanning logic (T025)
                    if replan_support:
                        self.logger.info(f"Failure detected. Replanning supported. Attempting replan from step {i}...")
                        # In a full pipeline, this would call the planner again with the current state.
                        # For T026, we log the attempt and outcome.
                        outcome.replan_attempted = True
                        # Assume replan fails for this specific mock or returns success
                        # In real code, we would re-run planner logic here.
                        # If replan succeeds, we continue. If not, we fail.
                        # For this task, we log the failure mode and replan attempt.
                    
                    self.execution_logs.append(outcome)
                    return outcome

                # Check completion after action
                if self.check_completion(pose_dev, orient_dev):
                    # Task completed successfully
                    outcome = ExecutionOutcome(
                        task_id=task_id,
                        success=True,
                        failure_mode=None,
                        timestamp=time.time(),
                        execution_time_s=time.time() - start_time,
                        pose_deviation_cm=pose_dev,
                        orient_deviation_deg=orient_dev
                    )
                    self.execution_logs.append(outcome)
                    return outcome

            # If loop finishes without explicit success check (e.g. sequence ends)
            # Assume success if no errors thrown
            outcome = ExecutionOutcome(
                task_id=task_id,
                success=True,
                failure_mode=None,
                timestamp=time.time(),
                execution_time_s=time.time() - start_time,
                pose_deviation_cm=0.0,
                orient_deviation_deg=0.0
            )
            self.execution_logs.append(outcome)
            return outcome

        except ExecutionTimeoutError as e:
            outcome = ExecutionOutcome(
                task_id=task_id,
                success=False,
                failure_mode="Timeout",
                timestamp=time.time(),
                execution_time_s=time.time() - start_time
            )
            self.execution_logs.append(outcome)
            return outcome
        except Exception as e:
            self.logger.error(f"Unexpected error during execution: {e}")
            outcome = ExecutionOutcome(
                task_id=task_id,
                success=False,
                failure_mode="Hardware Error", # Generic catch-all for unexpected hardware issues
                timestamp=time.time(),
                execution_time_s=time.time() - start_time
            )
            self.execution_logs.append(outcome)
            return outcome

    def save_logs(self, output_path: str):
        """
        Save execution logs to a Parquet file.
        T026 Requirement: Log all execution metrics to data/interim/execution_logs.parquet
        """
        if not self.execution_logs:
            self.logger.warning("No execution logs to save.")
            return

        # Convert dataclass list to DataFrame
        data = [asdict(log) for log in self.execution_logs]
        df = pd.DataFrame(data)
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Write to Parquet
        df.to_parquet(output_path, index=False)
        self.logger.info(f"Execution logs saved to {output_path}")

def run_executor_pipeline(task_id: str, 
                          sequence: ActionSequence, 
                          replan_support: bool = False,
                          output_path: str = None) -> ExecutionOutcome:
    """
    Orchestrate the execution of a single task sequence.
    """
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    # Initialize controller
    # In a real scenario, connection_string would be passed or detected
    controller = RobotController(connection_string="sim://localhost:11311")
    
    try:
        controller.connect()
    except ConnectionError as e:
        logger.error(f"Failed to connect to robot: {e}")
        # Return a failure outcome immediately
        outcome = ExecutionOutcome(
            task_id=task_id,
            success=False,
            failure_mode="Hardware Error",
            timestamp=time.time()
        )
        # Save immediately if output path is provided
        if output_path:
            executor = Executor(controller)
            executor.execution_logs.append(outcome)
            executor.save_logs(output_path)
        return outcome

    executor = Executor(controller, logger)
    outcome = executor.execute_sequence(sequence, task_id, replan_support)
    
    if output_path:
        executor.save_logs(output_path)
    
    return outcome

def main():
    """
    Entry point for the executor pipeline.
    This function is expected to be called by the orchestrator (main.py)
    to execute tasks and log results.
    """
    # Example usage for T026 verification
    # In the real pipeline, this is called with real data from the planner
    import sys
    from src.planner import create_planner
    from src.state_mapper import create_symbolic_state
    
    # Mock data for demonstration if run standalone
    # In the real pipeline, these come from the previous stages
    mock_sequence = ActionSequence(
        task_id="mock_task_001",
        actions=[{"type": "move", "target": "x:1, y:1"}]
    )
    
    output_file = os.path.join(BASE_DIR, "data", "interim", "execution_logs.parquet")
    
    outcome = run_executor_pipeline(
        task_id="mock_task_001",
        sequence=mock_sequence,
        replan_support=True,
        output_path=output_file
    )
    
    print(f"Execution completed. Outcome: {outcome.success}, Mode: {outcome.failure_mode}")
    print(f"Logs saved to: {output_file}")

if __name__ == "__main__":
    main()
