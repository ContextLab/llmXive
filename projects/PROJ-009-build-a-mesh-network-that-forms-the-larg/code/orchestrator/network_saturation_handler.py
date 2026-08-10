"""
network_saturation_handler.py

Handles the abort logic for network saturation events.
Receives NETWORK_SATURATION_SIGNAL from T014a (RemoteInstrumentor) and
executes the termination of benchmark processes on active nodes.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from enum import Enum

import paramiko

from orchestrator.logger import get_logger
from orchestrator.models import ExecutionRun, TaskStatus, PhysicalNode
from orchestrator.config import get_config

logger = get_logger(__name__)


class TerminationFailedError(Exception):
    """Raised when remote process termination fails after retries."""
    pass


class NetworkSaturationSignal(Enum):
    """Signal type for network saturation events."""
    TRIGGERED = "NETWORK_SATURATION"


@dataclass
class TerminationResult:
    """Result of a termination attempt on a specific node."""
    node_id: str
    success: bool
    message: str
    pid: int
    attempts: int


class NetworkSaturationHandler:
    """
    Handles the abort logic for network saturation.
    
    Responsibilities:
    1. Receive NETWORK_SATURATION_SIGNAL from T014a.
    2. Terminate remote benchmark processes (SIGKILL).
    3. Verify termination via polling (ps -p <pid>).
    4. Update central scheduler state.
    5. Log failure if termination fails.
    """

    def __init__(self, node_manager: Any, scheduler_state: Any):
        """
        Initialize the handler.
        
        Args:
            node_manager: Instance of orchestrator.node_manager.NodeManager 
                          (provides SSH connections).
            scheduler_state: Instance of orchestrator.completion_feedback.CompletionFeedbackManager
                             or similar state manager to update task status.
        """
        self.node_manager = node_manager
        self.scheduler_state = scheduler_state
        self.logger = get_logger(__name__)
        self.max_retries = 3
        self.retry_delay = 1.0  # seconds

    def handle_saturation_signal(
        self, 
        signal: NetworkSaturationSignal, 
        active_tasks: Dict[str, Dict[str, Any]]
    ) -> List[TerminationResult]:
        """
        Process the network saturation signal and terminate active tasks.
        
        Args:
            signal: The NetworkSaturationSignal (must be TRIGGERED).
            active_tasks: Dict mapping node_id -> { 'task_id': str, 'pid': int, 'ssh_client': paramiko.SSHClient }
        
        Returns:
            List of TerminationResult objects for each node.
        
        Raises:
            ValueError: If signal is not TRIGGERED.
        """
        if signal != NetworkSaturationSignal.TRIGGERED:
            raise ValueError(f"Invalid signal type: {signal}. Expected TRIGGERED.")
        
        self.logger.error("NETWORK_SATURATION_SIGNAL received. Initiating abort sequence.")
        
        results = []
        
        for node_id, task_info in active_tasks.items():
            task_id = task_info.get('task_id')
            pid = task_info.get('pid')
            ssh_client = task_info.get('ssh_client')
            
            if not all([task_id, pid, ssh_client]):
                self.logger.error(f"Missing task info for node {node_id}: {task_info}")
                results.append(TerminationResult(
                    node_id=node_id,
                    success=False,
                    message="Missing task info (task_id, pid, or ssh_client)",
                    pid=pid or -1,
                    attempts=0
                ))
                continue
            
            result = self._terminate_process_on_node(ssh_client, node_id, task_id, pid)
            results.append(result)
            
            if result.success:
                self.logger.info(f"Successfully terminated task {task_id} (PID {pid}) on node {node_id}")
                self._update_scheduler_state(task_id, "ABORTED_NETWORK_SATURATION")
            else:
                self.logger.error(f"Failed to terminate task {task_id} (PID {pid}) on node {node_id}: {result.message}")
                # Log failure with error code as per spec
                self.logger.error(f"FAILURE_LOG: NetworkSaturationAbortFailed on node {node_id} for task {task_id}. Error code: NETWORK_SATURATION")
                # Initiate abort sequence for the run (update state to aborted)
                self._update_scheduler_state(task_id, "ABORTED_NETWORK_SATURATION")

        return results

    def _terminate_process_on_node(
        self, 
        ssh_client: paramiko.SSHClient, 
        node_id: str, 
        task_id: str, 
        pid: int
    ) -> TerminationResult:
        """
        Attempt to kill a process on a remote node with retries.
        
        Args:
            ssh_client: Active paramiko SSHClient connection.
            node_id: Identifier of the remote node.
            task_id: Identifier of the task being terminated.
            pid: Process ID to kill.
        
        Returns:
            TerminationResult indicating success/failure.
        """
        attempts = 0
        last_error = None
        
        for attempt in range(self.max_retries):
            attempts += 1
            try:
                # Send SIGKILL
                kill_cmd = f"kill -9 {pid}"
                self.logger.debug(f"Sending SIGKILL to PID {pid} on node {node_id}")
                
                stdin, stdout, stderr = ssh_client.exec_command(kill_cmd)
                exit_status = stdout.channel.recv_exit_status()
                
                if exit_status != 0:
                    error_msg = stderr.read().decode('utf-8', errors='ignore').strip()
                    self.logger.warning(f"Kill command failed on node {node_id} (attempt {attempt+1}): {error_msg}")
                    last_error = error_msg
                    time.sleep(self.retry_delay)
                    continue
                
                # Verify termination
                if self._verify_termination(ssh_client, node_id, pid):
                    return TerminationResult(
                        node_id=node_id,
                        success=True,
                        message="Process terminated and verified",
                        pid=pid,
                        attempts=attempts
                    )
                else:
                    self.logger.warning(f"Process {pid} still running on node {node_id} after kill (attempt {attempt+1})")
                    last_error = "Process verification failed"
                    time.sleep(self.retry_delay)
                    
            except Exception as e:
                self.logger.exception(f"Exception during termination on node {node_id} (attempt {attempt+1}): {e}")
                last_error = str(e)
                time.sleep(self.retry_delay)

        # All retries exhausted
        return TerminationResult(
            node_id=node_id,
            success=False,
            message=f"Termination failed after {self.max_retries} attempts. Last error: {last_error}",
            pid=pid,
            attempts=attempts
        )

    def _verify_termination(self, ssh_client: paramiko.SSHClient, node_id: str, pid: int) -> bool:
        """
        Poll the remote process list to confirm the process is gone.
        
        Args:
            ssh_client: Active paramiko SSHClient connection.
            node_id: Identifier of the remote node.
            pid: Process ID to check.
        
        Returns:
            True if process is not found (success), False otherwise.
        """
        try:
            check_cmd = f"ps -p {pid} > /dev/null 2>&1"
            stdin, stdout, stderr = ssh_client.exec_command(check_cmd)
            exit_status = stdout.channel.recv_exit_status()
            
            # Exit status 0 means process exists, 1 means not found
            if exit_status == 0:
                return False
            return True
        except Exception as e:
            self.logger.warning(f"Failed to verify process {pid} on node {node_id}: {e}")
            # Assume failure if we can't check
            return False

    def _update_scheduler_state(self, task_id: str, status: str) -> None:
        """
        Update the central scheduler state for the terminated task.
        
        Args:
            task_id: Identifier of the task.
            status: New status string (e.g., "ABORTED_NETWORK_SATURATION").
        """
        try:
            if hasattr(self.scheduler_state, 'update_task_status'):
                self.scheduler_state.update_task_status(task_id, status)
            elif hasattr(self.scheduler_state, 'update_scheduler_state'):
                # Fallback to T013b interface
                self.scheduler_state.update_scheduler_state(task_id, status)
            else:
                self.logger.warning(f"Scheduler state object {type(self.scheduler_state)} lacks expected update methods.")
            self.logger.info(f"Updated state for task {task_id} to {status}")
        except Exception as e:
            self.logger.exception(f"Failed to update scheduler state for task {task_id}: {e}")


def create_handler(node_manager: Any, scheduler_state: Any) -> NetworkSaturationHandler:
    """Factory function to create a NetworkSaturationHandler."""
    return NetworkSaturationHandler(node_manager, scheduler_state)


def main():
    """
    CLI entry point for testing the handler logic.
    This script demonstrates the signal handling flow but requires 
    a real node_manager and scheduler_state to function fully.
    """
    import sys
    import argparse

    parser = argparse.ArgumentParser(description="Test Network Saturation Handler")
    parser.add_argument("--node-ip", type=str, help="IP of a test node")
    parser.add_argument("--pid", type=int, help="PID of a test process to kill")
    args = parser.parse_args()

    if not args.node_ip or not args.pid:
        print("Usage: python network_saturation_handler.py --node-ip <ip> --pid <pid>")
        sys.exit(1)

    # In a real scenario, we would initialize NodeManager and CompletionFeedbackManager here.
    # For this CLI, we simulate the signal flow.
    print(f"Simulating signal for node {args.node_ip}, PID {args.pid}")
    
    # Note: Actual execution requires real SSH connections which are not set up in this CLI context.
    # The logic is contained in the class methods above.
    print("Handler logic defined in NetworkSaturationHandler class.")
    print("To run fully, instantiate with real NodeManager and CompletionFeedbackManager instances.")


if __name__ == "__main__":
    main()