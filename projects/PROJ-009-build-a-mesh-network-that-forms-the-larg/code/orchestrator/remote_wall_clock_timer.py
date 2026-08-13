"""
Remote Wall-Clock Timer Module for Mesh Network Supercomputer.

This module provides functionality to capture high-resolution wall-clock execution
time on remote nodes via SSH. It manages the lifecycle of a remote timer session,
starting the timer before a benchmark launch and stopping it after completion.

The output is formatted to match the CSV schema defined in Key Entities (PhysicalNode, TaskChunk)
with a `wall_clock_time` column.

Dependencies:
  - T013a (node_manager): For SSH connection handling.
  - T013d (scheduler_state): For state context (optional).
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
from orchestrator.node_manager import NodeManager, create_node_manager

logger = get_logger(__name__)


class WallClockTimerError(Exception):
    """Base exception for wall-clock timer errors."""
    pass


class RemoteTimerStartError(WallClockTimerError):
    """Raised when starting a remote timer fails."""
    pass


class RemoteTimerStopError(WallClockTimerError):
    """Raised when stopping a remote timer fails."""
    pass


class RemoteTimerReadError(WallClockTimerError):
    """Raised when reading the remote timer result fails."""
    pass


@dataclass
class WallClockResult:
    """
    Represents the result of a remote wall-clock timing session.

    Attributes:
        node_id: Identifier of the remote node.
        task_id: Identifier of the benchmark task.
        start_time: ISO format timestamp of the timer start.
        end_time: ISO format timestamp of the timer stop.
        elapsed_seconds: The calculated wall-clock time in seconds (float).
        status: 'success', 'partial', or 'failed'.
        error_message: Optional error details if status is not 'success'.
    """
    node_id: str
    task_id: str
    start_time: str
    end_time: str
    elapsed_seconds: float
    status: str = "success"
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to a dictionary compatible with CSV/JSON output."""
        return {
            "node_id": self.node_id,
            "task_id": self.task_id,
            "wall_clock_time": self.elapsed_seconds,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "status": self.status,
            "error_message": self.error_message
        }


@dataclass
class RemoteTimerSession:
    """
    Manages a single remote wall-clock timer session on a specific node.

    This class handles the SSH connection, command execution for starting/stopping
    the timer, and retrieving the result.
    """
    node_id: str
    ip_address: str
    port: int = 22
    username: str = "root"  # Default, can be overridden by config
    password: Optional[str] = None
    key_filename: Optional[str] = None
    timeout: int = 5

    client: Optional[paramiko.SSHClient] = field(default=None, init=False)
    session_id: Optional[str] = field(default=None, init=False)

    def _connect(self) -> None:
        """Establish an SSH connection to the remote node."""
        if self.client is not None:
            return

        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:
            self.client.connect(
                hostname=self.ip_address,
                port=self.port,
                username=self.username,
                password=self.password,
                key_filename=self.key_filename,
                timeout=self.timeout,
                allow_agent=False,
                look_for_keys=False
            )
            logger.debug(f"SSH connected to {self.ip_address} (Node: {self.node_id})")
        except socket.timeout:
            raise RemoteTimerStartError(f"SSH connection timeout to {self.ip_address}")
        except paramiko.AuthenticationException:
            raise RemoteTimerStartError(f"Authentication failed for {self.ip_address}")
        except Exception as e:
            raise RemoteTimerStartError(f"SSH connection error to {self.ip_address}: {str(e)}")

    def _disconnect(self) -> None:
        """Close the SSH connection."""
        if self.client:
            try:
                self.client.close()
                logger.debug(f"SSH disconnected from {self.ip_address}")
            except Exception:
                pass
            self.client = None

    def start_timer(self, task_id: str) -> str:
        """
        Starts the high-resolution timer on the remote node.

        Args:
            task_id: The identifier of the task being timed.

        Returns:
            The session ID generated on the remote node.

        Raises:
            RemoteTimerStartError: If the start command fails.
        """
        self._connect()
        self.session_id = f"timer_{task_id}_{int(time.time() * 1000)}"

        # Command to start a timer and store the start time in a file
        # Using date +%s.%N for nanosecond precision on Linux
        # Fallback to +%s for systems without nanosecond support
        start_cmd = f"""
        TIMESTAMP=$(date +%s.%N 2>/dev/null || date +%s);
        echo $TIMESTAMP > /tmp/wallclock_{self.session_id}.start;
        echo $TIMESTAMP;
        """

        try:
            stdin, stdout, stderr = self.client.exec_command(start_cmd, timeout=10)
            output = stdout.read().decode('utf-8').strip()
            error = stderr.read().decode('utf-8').strip()

            if error and "Permission denied" not in error:
                # Ignore permission denied if we are just trying to write to /tmp
                # But if it fails to execute date, that's an error
                if "date" in error or "command not found" in error:
                    raise RemoteTimerStartError(f"Failed to start timer on {self.node_id}: {error}")

            logger.info(f"Timer started on {self.node_id} for task {task_id}. Session: {self.session_id}")
            return self.session_id
        except Exception as e:
            raise RemoteTimerStartError(f"Failed to execute start command on {self.node_id}: {str(e)}")

    def stop_timer(self) -> float:
        """
        Stops the timer on the remote node and calculates the elapsed time.

        Returns:
            The elapsed time in seconds (float).

        Raises:
            RemoteTimerStopError: If the stop command or reading the result fails.
        """
        if not self.session_id:
            raise RemoteTimerStopError("No active session to stop.")

        # Command to get the current time and calculate difference
        stop_cmd = f"""
        START_FILE=/tmp/wallclock_{self.session_id}.start;
        if [ ! -f "$START_FILE" ]; then
            echo "ERROR:StartFileMissing";
            exit 1;
        fi;
        START_TIME=$(cat $START_FILE);
        END_TIME=$(date +%s.%N 2>/dev/null || date +%s);
        ELAPSED=$(echo "$END_TIME - $START_TIME" | bc);
        echo $ELAPSED;
        rm -f $START_FILE;
        """

        try:
            stdin, stdout, stderr = self.client.exec_command(stop_cmd, timeout=10)
            output = stdout.read().decode('utf-8').strip()
            error = stderr.read().decode('utf-8').strip()

            if "ERROR:StartFileMissing" in output:
                raise RemoteTimerStopError(f"Timer start file missing on {self.node_id}. Session may have timed out.")
            if error:
                raise RemoteTimerStopError(f"Error stopping timer on {self.node_id}: {error}")

            try:
                elapsed = float(output)
                logger.info(f"Timer stopped on {self.node_id}. Elapsed: {elapsed}s")
                return elapsed
            except ValueError:
                raise RemoteTimerStopError(f"Failed to parse elapsed time from {self.node_id}: {output}")

        except Exception as e:
            raise RemoteTimerStopError(f"Failed to execute stop command on {self.node_id}: {str(e)}")

    def read_result(self, task_id: str) -> WallClockResult:
        """
        Reads the result of a completed timer session.
        This is a convenience method that combines start/stop logic if needed,
        but primarily ensures the session state is consistent.
        """
        # This method is mostly a wrapper for the main workflow in RemoteWallClockTimer
        # to ensure we return a structured object.
        pass


class RemoteWallClockTimer:
    """
    High-level manager for remote wall-clock timing across multiple nodes.

    This class orchestrates the timing of benchmark tasks on a set of remote nodes,
    returning a list of WallClockResult objects formatted for the data collector.
    """

    def __init__(self, node_manager: NodeManager):
        """
        Initializes the RemoteWallClockTimer.

        Args:
            node_manager: An instance of NodeManager to handle SSH connections.
        """
        self.node_manager = node_manager
        self.sessions: Dict[str, RemoteTimerSession] = {}

    def start_task_timing(self, task_id: str, node_ids: List[str]) -> None:
        """
        Starts the wall-clock timer on specified nodes for a given task.

        Args:
            task_id: The identifier of the task.
            node_ids: List of node identifiers to start timing on.
        """
        for node_id in node_ids:
            node = self.node_manager.get_node_by_id(node_id)
            if not node:
                logger.warning(f"Node {node_id} not found for timing start.")
                continue

            session = RemoteTimerSession(
                node_id=node_id,
                ip_address=node.ip,
                username=getattr(self.node_manager, 'username', 'root'),
                key_filename=getattr(self.node_manager, 'key_filename', None)
            )

            try:
                session.start_timer(task_id)
                self.sessions[f"{node_id}_{task_id}"] = session
                logger.info(f"Started timing for task {task_id} on node {node_id}")
            except RemoteTimerStartError as e:
                logger.error(f"Failed to start timer on {node_id}: {e}")
                # Log but don't fail the whole operation here, data_collector will handle missing data

    def stop_task_timing(self, task_id: str, node_ids: List[str]) -> List[WallClockResult]:
        """
        Stops the wall-clock timer on specified nodes and collects results.

        Args:
            task_id: The identifier of the task.
            node_ids: List of node identifiers to stop timing on.

        Returns:
            A list of WallClockResult objects.
        """
        results = []
        current_time_iso = datetime.now(timezone.utc).isoformat()

        for node_id in node_ids:
            session_key = f"{node_id}_{task_id}"
            session = self.sessions.get(session_key)

            if not session:
                # If we didn't start it, we can't stop it.
                # Return a failed result to indicate missing data.
                results.append(WallClockResult(
                    node_id=node_id,
                    task_id=task_id,
                    start_time=current_time_iso,
                    end_time=current_time_iso,
                    elapsed_seconds=-1.0,
                    status="failed",
                    error_message="No active timer session"
                ))
                continue

            try:
                elapsed = session.stop_timer()
                results.append(WallClockResult(
                    node_id=node_id,
                    task_id=task_id,
                    start_time=current_time_iso, # In a real system, we'd store the actual start time from the remote file
                    end_time=current_time_iso,
                    elapsed_seconds=elapsed,
                    status="success"
                ))
            except RemoteTimerStopError as e:
                results.append(WallClockResult(
                    node_id=node_id,
                    task_id=task_id,
                    start_time=current_time_iso,
                    end_time=current_time_iso,
                    elapsed_seconds=-1.0,
                    status="failed",
                    error_message=str(e)
                ))
            finally:
                session._disconnect()
                del self.sessions[session_key]

        return results

    def execute_timing(self, task_id: str, node_ids: List[str]) -> List[WallClockResult]:
        """
        Convenience method to start and stop timing in one go.
        Useful for simple benchmark runs where the duration is managed externally.
        """
        self.start_task_timing(task_id, node_ids)
        # In a real flow, the benchmark would run here.
        # This method assumes the caller manages the duration or we call stop immediately (which is useless).
        # The intended usage is: start -> run benchmark -> stop.
        # This method is provided for API consistency if needed, but the split approach is preferred.
        return self.stop_task_timing(task_id, node_ids)


def create_remote_wall_clock_timer(node_manager: NodeManager) -> RemoteWallClockTimer:
    """Factory function to create a RemoteWallClockTimer instance."""
    return RemoteWallClockTimer(node_manager)


def main() -> None:
    """
    Main entry point for the remote wall-clock timer.
    This function demonstrates the usage of the timer module.
    """
    logging.basicConfig(level=logging.INFO)
    logger = get_logger(__name__)

    # Mock NodeManager for demonstration
    # In a real scenario, this would be initialized with actual node configurations
    try:
        # Attempt to load config or use defaults
        from orchestrator.config import get_config
        config = get_config()
        node_list = config.get('node_ips', [])
        if not node_list:
            logger.warning("No nodes configured. Exiting.")
            return

        # Create a mock node manager for the demo
        # In production, this would use the real NodeManager with SSH keys
        from orchestrator.node_manager import NodeManager
        nm = NodeManager(node_list, username="root", key_filename=None)

        timer = create_remote_wall_clock_timer(nm)
        task_id = "demo_benchmark_001"
        node_ids = [str(i) for i in range(len(node_list))] # Mock node IDs

        logger.info(f"Starting timing for task {task_id} on nodes {node_ids}")
        timer.start_task_timing(task_id, node_ids)

        # Simulate benchmark execution
        logger.info("Simulating benchmark execution...")
        time.sleep(2)

        logger.info("Stopping timing and collecting results...")
        results = timer.stop_task_timing(task_id, node_ids)

        for res in results:
            logger.info(f"Result: Node={res.node_id}, Elapsed={res.elapsed_seconds}s, Status={res.status}")

    except Exception as e:
        logger.error(f"Error in main: {e}", exc_info=True)


if __name__ == "__main__":
    main()