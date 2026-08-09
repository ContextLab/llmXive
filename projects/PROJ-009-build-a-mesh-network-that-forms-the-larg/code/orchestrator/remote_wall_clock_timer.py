"""
Remote Wall-Clock Timer for Mesh Network Benchmarking.

This module implements the capture of wall-clock execution time on remote nodes
via SSH. It is distinct from the benchmark's internal timing and provides
node-level granularity for performance analysis.

Dependencies:
    - paramiko (SSH2 protocol)
    - T013a (node_manager.py) for SSH connection management
"""

from __future__ import annotations

import logging
import time
import socket
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Dict, Optional, Tuple

import paramiko
from paramiko import SSHClient, SSHException, AuthenticationException, SocketTimeout

from orchestrator.node_manager import NodeManager, NodeDiscoveryError
from orchestrator.logger import get_logger

# Configure logger
logger = get_logger(__name__)


class WallClockTimerError(Exception):
    """Base exception for wall-clock timer operations."""
    pass


class RemoteTimerStartError(WallClockTimerError):
    """Raised when starting a remote timer fails."""
    pass


class RemoteTimerStopError(WallClockTimerError):
    """Raised when stopping a remote timer fails."""
    pass


class RemoteTimerReadError(WallClockTimerError):
    """Raised when reading remote timer results fails."""
    pass


@dataclass
class WallClockResult:
    """
    Represents the wall-clock timing result from a remote node.

    Attributes:
        node_id: Unique identifier of the remote node.
        start_time: UTC timestamp when the timer started.
        end_time: UTC timestamp when the timer stopped.
        duration_seconds: Elapsed time in seconds.
        success: Whether the timing operation completed successfully.
        error_message: Optional error description if failed.
    """
    node_id: str
    start_time: datetime
    end_time: datetime
    duration_seconds: float
    success: bool = True
    error_message: Optional[str] = None

    def to_dict(self) -> Dict:
        """Convert result to dictionary for serialization."""
        return {
            "node_id": self.node_id,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "duration_seconds": self.duration_seconds,
            "success": self.success,
            "error_message": self.error_message
        }


@dataclass
class RemoteTimerSession:
    """
    Represents an active timer session on a remote node.

    Attributes:
        node_id: Unique identifier of the remote node.
        session_id: Unique session identifier.
        start_time: UTC timestamp when the timer started.
        ssh_client: The active SSH connection.
        command_id: Optional ID for the remote command tracking.
    """
    node_id: str
    session_id: str
    start_time: datetime
    ssh_client: SSHClient
    command_id: Optional[str] = None


class RemoteWallClockTimer:
    """
    Manages wall-clock timing operations on remote nodes via SSH.

    This class provides methods to start, stop, and read timers on remote nodes.
    It uses the paramiko library to execute timing commands and capture results.

    The timer implementation:
    1. Starts a timer by executing a command that records the start time
    2. Stops the timer by executing a command that records the end time
    3. Calculates the duration based on the difference between start and end times

    Dependencies:
        - T013a (node_manager.py) for node discovery and SSH connections
    """

    def __init__(self, node_manager: NodeManager):
        """
        Initialize the RemoteWallClockTimer.

        Args:
            node_manager: Instance of NodeManager for SSH connections.
        """
        self.node_manager = node_manager
        self._active_sessions: Dict[str, RemoteTimerSession] = {}
        self._logger = logger

    def start_timer(self, node_id: str, task_id: Optional[str] = None) -> RemoteTimerSession:
        """
        Start a wall-clock timer on a remote node.

        Args:
            node_id: Unique identifier of the target node.
            task_id: Optional task identifier for logging.

        Returns:
            RemoteTimerSession object representing the active timer.

        Raises:
            RemoteTimerStartError: If timer start fails.
            NodeDiscoveryError: If node is not found or unreachable.
        """
        try:
            # Get SSH connection from node manager
            ssh_client = self.node_manager.get_ssh_client(node_id)
            if ssh_client is None:
                raise RemoteTimerStartError(f"Failed to get SSH connection for node {node_id}")

            # Generate unique session ID
            session_id = f"{node_id}_{task_id or 'unknown'}_{int(time.time() * 1000)}"

            # Record start time
            start_time = datetime.now(timezone.utc)

            # Execute remote command to record start time
            # We use a simple shell command to record the timestamp
            start_command = f"echo '{session_id}_START' > /tmp/wallclock_{session_id}.txt && date -u +%s.%N"

            try:
                stdin, stdout, stderr = ssh_client.exec_command(start_command, timeout=5)
                exit_code = stdout.channel.recv_exit_status()
                if exit_code != 0:
                    error_output = stderr.read().decode('utf-8', errors='replace')
                    raise RemoteTimerStartError(
                        f"Failed to start timer on {node_id}: {error_output}"
                    )
            except (SSHException, socket.timeout) as e:
                raise RemoteTimerStartError(f"SSH error starting timer on {node_id}: {str(e)}")

            session = RemoteTimerSession(
                node_id=node_id,
                session_id=session_id,
                start_time=start_time,
                ssh_client=ssh_client,
                command_id=session_id
            )

            self._active_sessions[session_id] = session
            self._logger.info(
                f"Started wall-clock timer on node {node_id} for task {task_id}, "
                f"session: {session_id}"
            )

            return session

        except NodeDiscoveryError as e:
            self._logger.error(f"Node discovery failed for {node_id}: {str(e)}")
            raise
        except Exception as e:
            self._logger.error(f"Unexpected error starting timer on {node_id}: {str(e)}")
            raise RemoteTimerStartError(f"Failed to start timer on {node_id}: {str(e)}")

    def stop_timer(self, session: RemoteTimerSession) -> WallClockResult:
        """
        Stop a wall-clock timer on a remote node.

        Args:
            session: The active RemoteTimerSession to stop.

        Returns:
            WallClockResult with timing information.

        Raises:
            RemoteTimerStopError: If timer stop fails.
        """
        node_id = session.node_id
        session_id = session.session_id

        try:
            # Execute remote command to record end time
            end_command = f"echo '{session_id}_END' >> /tmp/wallclock_{session_id}.txt && date -u +%s.%N"

            try:
                stdin, stdout, stderr = session.ssh_client.exec_command(end_command, timeout=5)
                exit_code = stdout.channel.recv_exit_status()
                if exit_code != 0:
                    error_output = stderr.read().decode('utf-8', errors='replace')
                    raise RemoteTimerStopError(
                        f"Failed to stop timer on {node_id}: {error_output}"
                    )
            except (SSHException, socket.timeout) as e:
                raise RemoteTimerStopError(f"SSH error stopping timer on {node_id}: {str(e)}")

            # Record end time
            end_time = datetime.now(timezone.utc)

            # Calculate duration
            duration_seconds = (end_time - session.start_time).total_seconds()

            result = WallClockResult(
                node_id=node_id,
                start_time=session.start_time,
                end_time=end_time,
                duration_seconds=duration_seconds,
                success=True
            )

            # Clean up session
            if session_id in self._active_sessions:
                del self._active_sessions[session_id]

            self._logger.info(
                f"Stopped wall-clock timer on node {node_id}, "
                f"duration: {duration_seconds:.3f}s, session: {session_id}"
            )

            return result

        except Exception as e:
            self._logger.error(f"Unexpected error stopping timer on {node_id}: {str(e)}")
            # Mark session as failed but don't remove from active sessions yet
            return WallClockResult(
                node_id=node_id,
                start_time=session.start_time,
                end_time=datetime.now(timezone.utc),
                duration_seconds=0.0,
                success=False,
                error_message=str(e)
            )

    def stop_all_timers(self) -> List[WallClockResult]:
        """
        Stop all active timers and return results.

        Returns:
            List of WallClockResult objects for all stopped timers.
        """
        results = []
        sessions_to_stop = list(self._active_sessions.values())

        for session in sessions_to_stop:
            result = self.stop_timer(session)
            results.append(result)

        return results

    def read_timer_file(self, node_id: str, session_id: str) -> Tuple[Optional[float], Optional[float]]:
        """
        Read the timer file from remote node to get precise timestamps.

        This method reads the remote file created during start/stop to get
        the actual system timestamps from the remote node.

        Args:
            node_id: Unique identifier of the target node.
            session_id: The session identifier.

        Returns:
            Tuple of (start_timestamp, end_timestamp) in seconds since epoch,
            or (None, None) if file not found or error occurred.
        """
        try:
            ssh_client = self.node_manager.get_ssh_client(node_id)
            if ssh_client is None:
                raise RemoteTimerReadError(f"Failed to get SSH connection for node {node_id}")

            # Read the remote file
            read_command = f"cat /tmp/wallclock_{session_id}.txt 2>/dev/null || echo 'FILE_NOT_FOUND'"

            try:
                stdin, stdout, stderr = ssh_client.exec_command(read_command, timeout=5)
                output = stdout.read().decode('utf-8', errors='replace').strip()
                exit_code = stdout.channel.recv_exit_status()

                if exit_code != 0 or "FILE_NOT_FOUND" in output:
                    self._logger.warning(f"Timer file not found on {node_id} for session {session_id}")
                    return None, None

                # Parse the output
                lines = output.split('\n')
                start_ts = None
                end_ts = None

                for line in lines:
                    if '_START' in line and len(line.split()) > 1:
                        try:
                            start_ts = float(line.split()[-1])
                        except ValueError:
                            continue
                    elif '_END' in line and len(line.split()) > 1:
                        try:
                            end_ts = float(line.split()[-1])
                        except ValueError:
                            continue

                return start_ts, end_ts

            except (SSHException, socket.timeout) as e:
                raise RemoteTimerReadError(f"SSH error reading timer file on {node_id}: {str(e)}")

        except Exception as e:
            self._logger.error(f"Error reading timer file on {node_id}: {str(e)}")
            return None, None

    def cleanup_remote_files(self, node_id: str, session_id: str) -> bool:
        """
        Clean up remote timer files after reading.

        Args:
            node_id: Unique identifier of the target node.
            session_id: The session identifier.

        Returns:
            True if cleanup successful, False otherwise.
        """
        try:
            ssh_client = self.node_manager.get_ssh_client(node_id)
            if ssh_client is None:
                return False

            cleanup_command = f"rm -f /tmp/wallclock_{session_id}.txt"

            try:
                stdin, stdout, stderr = ssh_client.exec_command(cleanup_command, timeout=5)
                exit_code = stdout.channel.recv_exit_status()
                return exit_code == 0
            except (SSHException, socket.timeout):
                return False

        except Exception as e:
            self._logger.warning(f"Failed to cleanup remote files on {node_id}: {str(e)}")
            return False


def create_remote_wall_clock_timer(node_manager: NodeManager) -> RemoteWallClockTimer:
    """
    Factory function to create a RemoteWallClockTimer instance.

    Args:
        node_manager: Instance of NodeManager for SSH connections.

    Returns:
        Configured RemoteWallClockTimer instance.
    """
    return RemoteWallClockTimer(node_manager)


def main():
    """
    Main entry point for testing the remote wall-clock timer.

    This function demonstrates the usage of the RemoteWallClockTimer class
    by starting and stopping timers on discovered nodes.
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    try:
        # Create node manager
        from orchestrator.node_manager import create_node_manager
        node_manager = create_node_manager()

        # Discover nodes (using mock nodes for testing if no real nodes available)
        # In production, this would use real node IPs
        node_ips = ["127.0.0.1"]  # Default to localhost for testing

        logger.info(f"Discovering nodes: {node_ips}")
        nodes = node_manager.discover_nodes(node_ips)

        if not nodes:
            logger.warning("No nodes discovered, using mock node for testing")
            # Fallback to mock node if discovery fails
            from tests.unit.mock_nodes import MockNodeManager
            mock_manager = MockNodeManager()
            node_manager = mock_manager
            nodes = mock_manager.discover_nodes(["mock_node"])

        # Create timer
        timer = create_remote_wall_clock_timer(node_manager)

        # Test timer on first available node
        if nodes:
            node_id = nodes[0].node_id if hasattr(nodes[0], 'node_id') else str(nodes[0])
            logger.info(f"Testing wall-clock timer on node: {node_id}")

            # Start timer
            session = timer.start_timer(node_id, task_id="test_task_001")

            # Simulate some work (in real scenario, this would be the benchmark)
            logger.info("Simulating benchmark work...")
            time.sleep(2)  # Simulate 2 seconds of work

            # Stop timer
            result = timer.stop_timer(session)

            logger.info(f"Timer result: {result.to_dict()}")

            # Clean up
            if result.success:
                timer.cleanup_remote_files(node_id, session.session_id)

        else:
            logger.error("No nodes available for testing")

    except Exception as e:
        logger.error(f"Error in main: {str(e)}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
