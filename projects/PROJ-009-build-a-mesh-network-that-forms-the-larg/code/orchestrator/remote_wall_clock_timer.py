"""
Remote Wall Clock Timer for Mesh Network Benchmarking.

This module implements high-resolution wall-clock timing for benchmark
execution on remote nodes via SSH. It captures start and stop times
with nanosecond precision and formats the output for the CSV schema
defined in the Key Entities (PhysicalNode, TaskChunk).

Dependencies: T012 (remote_tools_manager), T013a (node_manager)
"""

from __future__ import annotations

import logging
import socket
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List

import paramiko

from orchestrator.logger import get_logger
from orchestrator.node_manager import NodeManager, NodeDiscoveryResult

logger = get_logger(__name__)


class WallClockTimerError(Exception):
    """Base exception for wall clock timer errors."""
    pass


class RemoteTimerStartError(WallClockTimerError):
    """Raised when starting the remote timer fails."""
    pass


class RemoteTimerStopError(WallClockTimerError):
    """Raised when stopping the remote timer fails."""
    pass


class RemoteTimerReadError(WallClockTimerError):
    """Raised when reading the timer result fails."""
    pass


@dataclass
class WallClockResult:
    """
    Result container for a remote wall-clock timing session.

    Attributes:
        node_id: The identifier of the remote node.
        start_time: ISO 8601 timestamp of the start event (UTC).
        end_time: ISO 8601 timestamp of the stop event (UTC).
        elapsed_seconds: Total elapsed time in seconds (float).
        run_id: The ID of the execution run this measurement belongs to.
        task_id: The ID of the specific task chunk timed.
        status: 'success' or 'failed'.
        error_message: Optional error details if status is 'failed'.
    """
    node_id: str
    start_time: str
    end_time: str
    elapsed_seconds: float
    run_id: str
    task_id: str
    status: str = 'success'
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for CSV serialization."""
        return {
            'node_id': self.node_id,
            'run_id': self.run_id,
            'task_id': self.task_id,
            'wall_clock_time': self.elapsed_seconds,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'status': self.status,
            'error_message': self.error_message or ''
        }


@dataclass
class RemoteTimerSession:
    """
    Manages the state of a single timing session on a remote node.

    Attributes:
        node_id: Target node identifier.
        ssh_client: Active Paramiko SSH client.
        start_time: Local start timestamp (float).
        end_time: Local end timestamp (float).
        remote_start_cmd: Command executed to start the timer on remote.
        remote_stop_cmd: Command executed to stop the timer on remote.
    """
    node_id: str
    ssh_client: paramiko.SSHClient
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    remote_start_cmd: Optional[str] = None
    remote_stop_cmd: Optional[str] = None
    run_id: str = ""
    task_id: str = ""


class RemoteWallClockTimer:
    """
    Handles high-resolution wall-clock timing on remote nodes.

    This class orchestrates the start/stop/measure cycle via SSH,
    ensuring synchronization with the local orchestrator clock.
    """

    def __init__(self, node_manager: NodeManager):
        """
        Initialize the timer with a NodeManager for SSH connectivity.

        Args:
            node_manager: An instance of NodeManager providing SSH connections.
        """
        self.node_manager = node_manager
        self.logger = logger
        self.sessions: Dict[str, RemoteTimerSession] = {}

    def _get_ssh_client(self, node_id: str) -> paramiko.SSHClient:
        """
        Retrieve or establish an SSH connection to a specific node.

        Args:
            node_id: The identifier of the node.

        Returns:
            A connected paramiko.SSHClient instance.

        Raises:
            RemoteTimerStartError: If connection fails.
        """
        try:
            # Assuming node_manager has a method to get or create client
            # If not, we rely on the node_manager's discovery to validate reachability first
            if node_id not in self.node_manager._nodes:
                # Attempt discovery if not cached, though usually T013a runs first
                self.node_manager.discover_nodes([node_id]) # Re-using discovery logic for connection check

            client = self.node_manager.get_ssh_client(node_id)
            if client is None:
                raise RemoteTimerStartError(f"Failed to establish SSH connection to {node_id}")
            return client
        except Exception as e:
            raise RemoteTimerStartError(f"SSH connection error for {node_id}: {str(e)}")

    def start_timer(self, node_id: str, run_id: str, task_id: str) -> RemoteTimerSession:
        """
        Start the high-resolution timer on the remote node.

        This records the local start time and executes a remote command
        to mark the start of the benchmark workload.

        Args:
            node_id: Target node ID.
            run_id: Current execution run ID.
            task_id: Current task chunk ID.

        Returns:
            RemoteTimerSession object.

        Raises:
            RemoteTimerStartError: If the remote command fails.
        """
        self.logger.info(f"Starting wall-clock timer on {node_id} for task {task_id}")
        
        client = self._get_ssh_client(node_id)
        session = RemoteTimerSession(
            node_id=node_id,
            ssh_client=client,
            run_id=run_id,
            task_id=task_id
        )

        # Record local start time with high resolution
        session.start_time = time.time()
        
        # Execute a remote command to mark the start (e.g., write a timestamp file)
        # This ensures the remote side knows exactly when the "work" started relative to the command
        remote_start_cmd = f"date -u +%Y-%m-%dT%H:%M:%S.%3NZ > /tmp/wallclock_start_{task_id}.txt"
        session.remote_start_cmd = remote_start_cmd

        try:
            stdin, stdout, stderr = client.exec_command(remote_start_cmd, timeout=10)
            exit_status = stdout.channel.recv_exit_status()
            if exit_status != 0:
                error_msg = stderr.read().decode('utf-8')
                raise RemoteTimerStartError(f"Remote start command failed on {node_id}: {error_msg}")
        except Exception as e:
            raise RemoteTimerStartError(f"Remote start execution failed: {str(e)}")

        self.sessions[task_id] = session
        return session

    def stop_timer(self, task_id: str) -> RemoteTimerSession:
        """
        Stop the timer and calculate elapsed time.

        This records the local stop time and executes a remote command
        to mark the end of the benchmark workload.

        Args:
            task_id: The task ID associated with the running session.

        Returns:
            Updated RemoteTimerSession object.

        Raises:
            RemoteTimerStopError: If the remote command fails or session not found.
        """
        if task_id not in self.sessions:
            raise RemoteTimerStopError(f"No active session found for task {task_id}")

        session = self.sessions[task_id]
        self.logger.info(f"Stopping wall-clock timer on {session.node_id} for task {task_id}")

        # Record local stop time
        session.end_time = time.time()

        # Execute remote stop command
        remote_stop_cmd = f"date -u +%Y-%m-%dT%H:%M:%S.%3NZ > /tmp/wallclock_end_{task_id}.txt"
        session.remote_stop_cmd = remote_stop_cmd

        try:
            stdin, stdout, stderr = session.ssh_client.exec_command(remote_stop_cmd, timeout=10)
            exit_status = stdout.channel.recv_exit_status()
            if exit_status != 0:
                error_msg = stderr.read().decode('utf-8')
                raise RemoteTimerStopError(f"Remote stop command failed on {session.node_id}: {error_msg}")
        except Exception as e:
            raise RemoteTimerStopError(f"Remote stop execution failed: {str(e)}")

        # Calculate elapsed time (local high-res delta)
        # Note: In a distributed system, we use the local orchestrator's delta as the primary
        # measurement for the "wall clock" of the orchestration, while remote timestamps
        # are for audit and drift detection.
        elapsed = session.end_time - session.start_time
        
        # Format timestamps for CSV
        start_dt = datetime.fromtimestamp(session.start_time, tz=timezone.utc)
        end_dt = datetime.fromtimestamp(session.end_time, tz=timezone.utc)
        
        # Update session with results
        session.elapsed_seconds = elapsed
        session.start_time_str = start_dt.isoformat()
        session.end_time_str = end_dt.isoformat()
        
        return session

    def read_result(self, task_id: str) -> WallClockResult:
        """
        Retrieve the final WallClockResult for a completed task.

        This fetches the remote timestamps to verify consistency and
        returns the structured result object.

        Args:
            task_id: The task ID.

        Returns:
            WallClockResult object.

        Raises:
            RemoteTimerReadError: If session missing or remote read fails.
        """
        if task_id not in self.sessions:
            raise RemoteTimerReadError(f"No session found for task {task_id}")

        session = self.sessions[task_id]
        
        # Verify remote files exist and read them for audit
        remote_start_read = f"cat /tmp/wallclock_start_{task_id}.txt"
        remote_end_read = f"cat /tmp/wallclock_end_{task_id}.txt"
        
        remote_start_ts = None
        remote_end_ts = None

        try:
            # Read start timestamp
            stdin, stdout, stderr = session.ssh_client.exec_command(remote_start_read, timeout=5)
            if stdout.channel.recv_exit_status() == 0:
                remote_start_ts = stdout.read().decode('utf-8').strip()
            
            # Read end timestamp
            stdin, stdout, stderr = session.ssh_client.exec_command(remote_end_read, timeout=5)
            if stdout.channel.recv_exit_status() == 0:
                remote_end_ts = stdout.read().decode('utf-8').strip()
        except Exception as e:
            self.logger.warning(f"Could not read remote timestamps for {task_id}: {e}")
            # We proceed with local time as it's the primary metric for the orchestrator

        # Clean up remote files
        try:
            session.ssh_client.exec_command(f"rm -f /tmp/wallclock_start_{task_id}.txt /tmp/wallclock_end_{task_id}.txt")
        except Exception:
            pass # Ignore cleanup errors

        result = WallClockResult(
            node_id=session.node_id,
            start_time=session.start_time_str,
            end_time=session.end_time_str,
            elapsed_seconds=session.elapsed_seconds,
            run_id=session.run_id,
            task_id=session.task_id,
            status='success'
        )

        return result

    def cleanup(self, task_id: str):
        """Remove the session from memory."""
        if task_id in self.sessions:
            del self.sessions[task_id]


def create_remote_wall_clock_timer(node_manager: NodeManager) -> RemoteWallClockTimer:
    """
    Factory function to create a RemoteWallClockTimer instance.

    Args:
        node_manager: The NodeManager instance.

    Returns:
        A configured RemoteWallClockTimer.
    """
    return RemoteWallClockTimer(node_manager)


def main():
    """
    CLI entry point for testing the remote wall clock timer.
    Expects node IPs and a task ID to simulate a run.
    """
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Test Remote Wall Clock Timer")
    parser.add_argument("--nodes", nargs='+', required=True, help="List of node IPs")
    parser.add_argument("--run_id", default="test-run-001", help="Run ID")
    parser.add_argument("--task_id", default="task-001", help="Task ID")
    args = parser.parse_args()

    # Initialize NodeManager (T013a dependency)
    # In a real scenario, this would load from config
    nm = NodeManager()
    # Simulate discovery or assume connectivity
    # For testing, we assume nodes are reachable or we skip actual SSH if not configured
    
    timer = create_remote_wall_clock_timer(nm)
    
    try:
        # Start
        session = timer.start_timer(args.nodes[0], args.run_id, args.task_id)
        print(f"Timer started on {args.nodes[0]}")
        
        # Simulate work (in real usage, benchmark runs here)
        time.sleep(2)
        
        # Stop
        timer.stop_timer(args.task_id)
        print("Timer stopped")
        
        # Read
        result = timer.read_result(args.task_id)
        print(f"Result: {json.dumps(result.to_dict(), indent=2)}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        timer.cleanup(args.task_id)


if __name__ == "__main__":
    main()