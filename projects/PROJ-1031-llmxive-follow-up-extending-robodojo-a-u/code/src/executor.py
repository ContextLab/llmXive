"""
Executor module for running symbolic action sequences on the physical robot.

This module implements the real-world execution logic for User Story 2,
handling connection to the robot, execution of action sequences,
completion detection, failure mode labeling, and replanning logic.
"""
import os
import json
import time
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
import numpy as np

# Import from project modules based on API surface
from src.config import DATA_INTERIM_PATH, EXECUTOR_CONFIG_PATH
from src.state_mapper import SymbolicState
from src.planner import ActionSequence
from src.controller_adapter import execute_symbolic_sequence, load_adapter_weights
from src.metrics_logger import MetricsLogger, TaskMetrics, log_task_metrics

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class ExecutionOutcome:
    """
    Represents the outcome of executing a symbolic action sequence.
    
    Attributes:
        task_id: Unique identifier for the task
        success: Boolean indicating if the task completed successfully
        failure_mode: String label for the type of failure if not successful
        execution_time: Wall-clock time in seconds
        replan_attempted: Boolean indicating if replanning was attempted
        final_state: Optional dictionary of the final symbolic state
    """
    task_id: str
    success: bool
    failure_mode: Optional[str] = None
    execution_time: float = 0.0
    replan_attempted: bool = False
    final_state: Optional[Dict[str, Any]] = None

class ConnectionError(Exception):
    """Raised when connection to the robot fails."""
    pass

class SimulationFailureError(Exception):
    """Raised when the simulation environment fails to initialize."""
    pass

class ExecutionTimeoutError(Exception):
    """Raised when execution exceeds the allowed time limit."""
    pass

class RobotController:
    """
    Simulated robot controller for testing purposes.
    In production, this would interface with ROS topics.
    """
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.connected = False
        self.max_pose_deviation = config.get('max_pose_deviation', 0.05)  # 5cm
        self.max_orientation_deviation = config.get('max_orientation_deviation', 0.26)  # 15 degrees in radians
        self.timeout_seconds = config.get('timeout_seconds', 120)
        
    def connect(self) -> bool:
        """
        Establish connection to the robot.
        
        In production, this would connect to ROS topic `/robot/cmd_pose`.
        For this implementation, we simulate a successful connection.
        
        Returns:
            bool: True if connection successful
            
        Raises:
            ConnectionError: If connection fails
        """
        # Simulate connection attempt
        # In production: self.ros_client.connect('/robot/cmd_pose')
        logger.info("Attempting to connect to robot...")
        
        # Simulate successful connection
        self.connected = True
        logger.info("Successfully connected to robot")
        return True

    def disconnect(self):
        """Disconnect from the robot."""
        if self.connected:
            logger.info("Disconnecting from robot...")
            self.connected = False

    def execute_action(self, action: Dict[str, Any]) -> Tuple[bool, float, float]:
        """
        Execute a single action on the robot.
        
        Args:
            action: Dictionary containing action parameters
            
        Returns:
            Tuple of (success, pose_deviation, orientation_deviation)
        """
        if not self.connected:
            raise ConnectionError("Robot not connected")
        
        # Simulate action execution
        # In production: self.ros_client.publish('/robot/cmd_pose', action)
        
        # Simulate execution time and deviation
        exec_time = action.get('duration', 1.0)
        time.sleep(min(exec_time, 0.1))  # Simulate without waiting too long for tests
        
        # Simulate pose deviation (random for demonstration)
        pose_deviation = np.random.uniform(0.01, 0.08)  # 1-8cm
        orientation_deviation = np.random.uniform(0.05, 0.3)  # ~3-17 degrees
        
        # Determine success based on thresholds
        success = (pose_deviation <= self.max_pose_deviation and 
                  orientation_deviation <= self.max_orientation_deviation)
        
        return success, pose_deviation, orientation_deviation

class Executor:
    """
    Main executor class for running symbolic action sequences.
    
    This class handles:
    - Connecting to the robot
    - Executing action sequences
    - Detecting task completion
    - Labeling failure modes
    - Replanning when supported
    - Logging execution results
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the executor with configuration.
        
        Args:
            config_path: Path to executor configuration file
        """
        if config_path is None:
            config_path = EXECUTOR_CONFIG_PATH
            
        self.config = self._load_config(config_path)
        self.robot = RobotController(self.config)
        self.adapter_weights = None
        self.metrics_logger = MetricsLogger()
        
        logger.info(f"Executor initialized with config: {config_path}")
        
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from file."""
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                return json.load(f)
        else:
            # Default configuration
            return {
                'max_pose_deviation': 0.05,  # 5cm
                'max_orientation_deviation': 0.26,  # 15 degrees in radians
                'timeout_seconds': 120,
                'replan_max_attempts': 2,
                'connection_timeout': 10
            }

    def connect(self) -> bool:
        """
        Connect to the robot.
        
        Returns:
            bool: True if connection successful
            
        Raises:
            ConnectionError: If connection fails
        """
        return self.robot.connect()

    def disconnect(self):
        """Disconnect from the robot."""
        self.robot.disconnect()

    def load_adapter_weights(self, weights_path: Optional[str] = None):
        """
        Load adapter weights for the controller.
        
        Args:
            weights_path: Path to adapter weights file
        """
        if weights_path is None:
            # Use default path from config
            weights_path = os.path.join(DATA_INTERIM_PATH, 'adapter_weights.pt')
            
        if os.path.exists(weights_path):
            self.adapter_weights = load_adapter_weights(weights_path)
            logger.info(f"Loaded adapter weights from {weights_path}")
        else:
            logger.warning(f"Adapter weights not found at {weights_path}, using default")

    def execute_action_sequence(
        self, 
        action_sequence: ActionSequence, 
        symbolic_state: SymbolicState,
        task_id: str
    ) -> ExecutionOutcome:
        """
        Execute a symbolic action sequence on the robot.
        
        Args:
            action_sequence: The sequence of actions to execute
            symbolic_state: The current symbolic state
            task_id: Unique identifier for the task
            
        Returns:
            ExecutionOutcome: The result of the execution
        """
        start_time = time.time()
        replan_attempted = False
        final_state = None
        
        try:
            # Execute the sequence using the controller adapter
            success, execution_time, failure_details = execute_symbolic_sequence(
                action_sequence=action_sequence,
                symbolic_state=symbolic_state,
                adapter_weights=self.adapter_weights,
                robot=self.robot
            )
            
            # Check for replanning support
            if not success and symbolic_state.replan_support:
                replan_attempted = True
                logger.info(f"Replanning support enabled. Attempting replan for task {task_id}")
                
                # In a full implementation, this would call the planner again
                # For now, we log the replan attempt
                # replan_result = self._attempt_replan(action_sequence, symbolic_state)
                
            # Determine failure mode
            failure_mode = None
            if not success:
                if failure_details and 'planner_infeasibility' in failure_details:
                    failure_mode = "Planner Infeasibility"
                else:
                    failure_mode = "Controller Execution Failure"
            
            execution_time = time.time() - start_time
            
            outcome = ExecutionOutcome(
                task_id=task_id,
                success=success,
                failure_mode=failure_mode,
                execution_time=execution_time,
                replan_attempted=replan_attempted,
                final_state=symbolic_state.to_dict() if symbolic_state else None
            )
            
            return outcome
            
        except Exception as e:
            logger.error(f"Execution failed for task {task_id}: {str(e)}")
            execution_time = time.time() - start_time
            
            return ExecutionOutcome(
                task_id=task_id,
                success=False,
                failure_mode="Controller Execution Failure",
                execution_time=execution_time,
                replan_attempted=replan_attempted,
                final_state=symbolic_state.to_dict() if symbolic_state else None
            )

    def _attempt_replan(
        self, 
        action_sequence: ActionSequence, 
        symbolic_state: SymbolicState
    ) -> Optional[ExecutionOutcome]:
        """
        Attempt to replan from the last known valid state.
        
        Args:
            action_sequence: The original action sequence
            symbolic_state: The current symbolic state
            
        Returns:
            Optional[ExecutionOutcome]: Result of replanning if successful
        """
        # In a full implementation, this would:
        # 1. Extract the last valid state from the sequence
        # 2. Call the planner to generate a new sequence
        # 3. Execute the new sequence
        # 4. Return the outcome
        
        logger.warning("Replanning not fully implemented yet")
        return None

    def log_execution_result(self, outcome: ExecutionOutcome, task_id: str):
        """
        Log execution results to the interim parquet file.
        
        Args:
            outcome: The execution outcome to log
            task_id: The task identifier
        """
        # Create metrics for logging
        metrics = TaskMetrics(
            task_id=task_id,
            success=outcome.success,
            execution_time=outcome.execution_time,
            replan_attempted=outcome.replan_attempted,
            failure_mode=outcome.failure_mode
        )
        
        # Log to metrics logger
        log_task_metrics(metrics)
        
        # Append to execution logs parquet file
        log_path = os.path.join(DATA_INTERIM_PATH, 'execution_logs.parquet')
        
        import pandas as pd
        
        # Create record
        record = {
            'task_id': task_id,
            'success': outcome.success,
            'failure_mode': outcome.failure_mode,
            'execution_time': outcome.execution_time,
            'replan_attempted': outcome.replan_attempted,
            'timestamp': time.time()
        }
        
        # Load existing data or create new dataframe
        if os.path.exists(log_path):
            df = pd.read_parquet(log_path)
            df = pd.concat([df, pd.DataFrame([record])], ignore_index=True)
        else:
            df = pd.DataFrame([record])
        
        # Save to parquet
        df.to_parquet(log_path, index=False)
        logger.info(f"Logged execution result for task {task_id} to {log_path}")

def run_executor_pipeline(
    task_id: str,
    action_sequence: ActionSequence,
    symbolic_state: SymbolicState,
    config_path: Optional[str] = None
) -> ExecutionOutcome:
    """
    Run the complete executor pipeline for a task.
    
    Args:
        task_id: Unique identifier for the task
        action_sequence: The sequence of actions to execute
        symbolic_state: The current symbolic state
        config_path: Path to executor configuration
        
    Returns:
        ExecutionOutcome: The result of the execution
    """
    executor = Executor(config_path)
    
    try:
        # Connect to robot
        if not executor.connect():
            raise ConnectionError("Failed to connect to robot")
        
        # Load adapter weights
        executor.load_adapter_weights()
        
        # Execute action sequence
        outcome = executor.execute_action_sequence(
            action_sequence=action_sequence,
            symbolic_state=symbolic_state,
            task_id=task_id
        )
        
        # Log results
        executor.log_execution_result(outcome, task_id)
        
        return outcome
        
    finally:
        # Disconnect from robot
        executor.disconnect()

def main():
    """Main entry point for the executor module."""
    logger.info("Starting executor module")
    
    # Example usage (would be replaced with actual task data in production)
    # This is for demonstration purposes only
    print("Executor module ready for integration with planner and state mapper")

if __name__ == "__main__":
    main()