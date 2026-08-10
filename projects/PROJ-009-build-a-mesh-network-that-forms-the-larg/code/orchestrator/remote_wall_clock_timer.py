"""
Remote Wall Clock Timer for Mesh Network Supercomputer.

This module implements precise wall-clock time capture on remote nodes
via SSH, distinct from the benchmark's internal timing. It handles
start/stop signals and reads the elapsed time from remote execution.
"""

from __future__ import annotations

import logging
import time
import socket
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple, Any
import paramiko

from orchestrator.logger import get_logger
from orchestrator.node_manager import NodeDiscoveryError

logger = get_logger(__name__)


class WallClockTimerError(Exception):
    """Base exception for wall clock timer errors."""
    pass


class RemoteTimerStartError(WallClockTimerError):
    """Raised when starting a remote timer fails."""
    pass


class RemoteTimerStopError(WallClockTimerError):
    """Raised when stopping a remote timer fails."""
    pass


class RemoteTimerReadError(WallClockTimerError):
    """Raised when reading the timer result fails."""
    pass


@dataclass
class WallClockResult:
    """Result of a remote wall clock timing session."""
    node_ip: str
    start_time: datetime
    end_time: datetime
    duration_seconds: float
    success: bool
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_ip": self.node_ip,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "duration_seconds": self.duration_seconds,
            "success": self.success,
            "error_message": self.error_message
        }


@dataclass
class RemoteTimerSession:
    """
    Represents a single timing session on a remote node.
    Stores the SSH connection and timing metadata.
    """
    node_ip: str
    ssh_client: Optional[paramiko.SSHClient] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration_seconds: float = 0.0
    is_active: bool = False
    remote_pid: Optional[int] = None  # Optional: track a specific process if needed

class RemoteWallClockTimer:
    """
    Manages wall-clock timing on remote nodes via SSH.

    This class handles the start/stop lifecycle of timing sessions
    on remote machines, ensuring that the time measured is the
    actual wall-clock time experienced by the node, independent
    of the orchestrator's clock skew.
    """

    def __init__(self, timeout: float = 10.0):
        """
        Initialize the RemoteWallClockTimer.

        Args:
            timeout: SSH command timeout in seconds.
        """
        self.timeout = timeout
        self.sessions: Dict[str, RemoteTimerSession] = {}
        self.logger = get_logger(__name__)

    def _connect(self, node_ip: str, username: str = "root", password: str = "", key_filename: Optional[str] = None) -> paramiko.SSHClient:
        """
        Establish an SSH connection to a remote node.

        Args:
            node_ip: IP address of the remote node.
            username: SSH username.
            password: SSH password.
            key_filename: Path to SSH private key.

        Returns:
            paramiko.SSHClient instance.

        Raises:
            RemoteTimerStartError: If connection fails.
        """
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            if key_filename:
                client.connect(
                    node_ip,
                    username=username,
                    key_filename=key_filename,
                    timeout=self.timeout,
                    allow_agent=False,
                    look_for_keys=False
                )
            else:
                client.connect(
                    node_ip,
                    username=username,
                    password=password,
                    timeout=self.timeout
                )
            self.logger.debug(f"SSH connection established to {node_ip}")
            return client
        except (socket.timeout, paramiko.AuthenticationException, paramiko.SSHException) as e:
            raise RemoteTimerStartError(f"Failed to connect to {node_ip}: {e}")

    def start_timer(self, node_ip: str, username: str = "root", password: str = "", key_filename: Optional[str] = None) -> WallClockResult:
        """
        Start a wall-clock timer on a remote node.

        This executes a remote command to capture the precise start time
        on the node's local clock.

        Args:
            node_ip: IP address of the remote node.
            username: SSH username.
            password: SSH password.
            key_filename: Path to SSH private key.

        Returns:
            WallClockResult indicating success and start time.

        Raises:
            RemoteTimerStartError: If the timer cannot be started.
        """
        if node_ip in self.sessions and self.sessions[node_ip].is_active:
            self.logger.warning(f"Timer already active for {node_ip}")
            return self._get_session_result(node_ip, False, "Timer already active")

        try:
            client = self._connect(node_ip, username, password, key_filename)
        except RemoteTimerStartError as e:
            return WallClockResult(
                node_ip=node_ip,
                start_time=datetime.now(timezone.utc),
                end_time=datetime.now(timezone.utc),
                duration_seconds=0.0,
                success=False,
                error_message=str(e)
            )

        # Command to get precise local time on remote node
        # Using 'date +%s.%N' for nanosecond precision if available, fallback to seconds
        remote_cmd = "date +%s.%N 2>/dev/null || date +%s"

        try:
            stdin, stdout, stderr = client.exec_command(remote_cmd, timeout=self.timeout)
            exit_status = stdout.channel.recv_exit_status()
            
            if exit_status != 0:
                error_msg = stderr.read().decode('utf-8', errors='ignore').strip()
                raise RemoteTimerStartError(f"Remote command failed with status {exit_status}: {error_msg}")

            raw_time = stdout.read().decode('utf-8', errors='ignore').strip()
            
            # Parse the time string
            try:
                timestamp = float(raw_time)
            except ValueError:
                raise RemoteTimerReadError(f"Invalid timestamp format from {node_ip}: {raw_time}")

            # Convert to UTC datetime
            start_dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)

            session = RemoteTimerSession(
                node_ip=node_ip,
                ssh_client=client,
                start_time=start_dt,
                is_active=True
            )
            self.sessions[node_ip] = session

            self.logger.info(f"Remote timer started on {node_ip} at {start_dt.isoformat()}")
            
            return WallClockResult(
                node_ip=node_ip,
                start_time=start_dt,
                end_time=start_dt,
                duration_seconds=0.0,
                success=True
            )

        except Exception as e:
            client.close()
            raise RemoteTimerStartError(f"Failed to execute start command on {node_ip}: {e}")

    def stop_timer(self, node_ip: str) -> WallClockResult:
        """
        Stop a wall-clock timer on a remote node and calculate duration.

        This executes a remote command to capture the stop time and
        calculates the elapsed duration based on the node's local clock.

        Args:
            node_ip: IP address of the remote node.

        Returns:
            WallClockResult containing the duration and end time.

        Raises:
            RemoteTimerStopError: If the timer cannot be stopped or read.
        """
        if node_ip not in self.sessions:
            raise RemoteTimerStopError(f"No active session found for {node_ip}")

        session = self.sessions[node_ip]
        if not session.is_active:
            raise RemoteTimerStopError(f"Timer for {node_ip} is not active")

        if session.ssh_client is None:
            raise RemoteTimerStopError(f"SSH connection lost for {node_ip}")

        remote_cmd = "date +%s.%N 2>/dev/null || date +%s"

        try:
            stdin, stdout, stderr = session.ssh_client.exec_command(remote_cmd, timeout=self.timeout)
            exit_status = stdout.channel.recv_exit_status()

            if exit_status != 0:
                error_msg = stderr.read().decode('utf-8', errors='ignore').strip()
                raise RemoteTimerStopError(f"Remote stop command failed: {error_msg}")

            raw_time = stdout.read().decode('utf-8', errors='ignore').strip()
            
            try:
                timestamp = float(raw_time)
            except ValueError:
                raise RemoteTimerReadError(f"Invalid timestamp format from {node_ip}: {raw_time}")

            end_dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)
            session.end_time = end_dt

            # Calculate duration in seconds
            duration = end_dt.timestamp() - session.start_time.timestamp()
            session.duration_seconds = duration
            session.is_active = False

            self.logger.info(f"Remote timer stopped on {node_ip}. Duration: {duration:.4f}s")

            return WallClockResult(
                node_ip=node_ip,
                start_time=session.start_time,
                end_time=end_dt,
                duration_seconds=duration,
                success=True
            )

        except Exception as e:
            raise RemoteTimerStopError(f"Failed to stop timer on {node_ip}: {e}")

    def get_result(self, node_ip: str) -> WallClockResult:
        """
        Retrieve the result of a completed timing session.

        Args:
            node_ip: IP address of the remote node.

        Returns:
            WallClockResult.

        Raises:
            RemoteTimerReadError: If no session exists or session is still active.
        """
        if node_ip not in self.sessions:
            raise RemoteTimerReadError(f"No session found for {node_ip}")

        session = self.sessions[node_ip]
        if session.is_active:
            raise RemoteTimerReadError(f"Session for {node_ip} is still active. Call stop_timer first.")

        if session.ssh_client:
            session.ssh_client.close()

        return WallClockResult(
            node_ip=node_ip,
            start_time=session.start_time,
            end_time=session.end_time,
            duration_seconds=session.duration_seconds,
            success=True
        )

    def close_all(self):
        """Close all active SSH connections."""
        for node_ip, session in self.sessions.items():
            if session.ssh_client:
                try:
                    session.ssh_client.close()
                    self.logger.debug(f"Closed SSH connection to {node_ip}")
                except Exception as e:
                    self.logger.warning(f"Error closing connection to {node_ip}: {e}")
        self.sessions.clear()


def create_remote_wall_clock_timer(timeout: float = 10.0) -> RemoteWallClockTimer:
    """Factory function to create a RemoteWallClockTimer instance."""
    return RemoteWallClockTimer(timeout=timeout)


def main():
    """
    CLI entry point for testing remote wall clock timing.
    Usage: python -m orchestrator.remote_wall_clock_timer --nodes 192.168.1.10,192.168.1.11
    """
    import argparse

    parser = argparse.ArgumentParser(description="Remote Wall Clock Timer Test")
    parser.add_argument("--nodes", type=str, required=True, help="Comma-separated list of node IPs")
    parser.add_argument("--username", type=str, default="root", help="SSH username")
    parser.add_argument("--password", type=str, default="", help="SSH password")
    parser.add_argument("--duration", type=float, default=5.0, help="Simulated workload duration in seconds")
    parser.add_argument("--key", type=str, default=None, help="Path to SSH private key")

    args = parser.parse_args()

    nodes = [n.strip() for n in args.nodes.split(",")]
    timer = create_remote_wall_clock_timer()

    try:
        # Start timers
        for node in nodes:
            result = timer.start_timer(node, username=args.username, password=args.password, key_filename=args.key)
            if not result.success:
                logger.error(f"Failed to start timer on {node}: {result.error_message}")
            else:
                logger.info(f"Started timer on {node}")

        # Simulate workload (local sleep)
        logger.info(f"Simulating workload for {args.duration} seconds...")
        time.sleep(args.duration)

        # Stop timers
        for node in nodes:
            result = timer.stop_timer(node)
            if result.success:
                logger.info(f"Stopped timer on {node}. Duration: {result.duration_seconds:.4f}s")
            else:
                logger.error(f"Failed to stop timer on {node}: {result.error_message}")

        # Print results
        print("\n--- Wall Clock Timing Results ---")
        for node in nodes:
            try:
                res = timer.get_result(node)
                print(f"Node: {res.node_ip} | Duration: {res.duration_seconds:.4f}s | Success: {res.success}")
            except RemoteTimerReadError as e:
                print(f"Node: {node} | Error: {e}")

    finally:
        timer.close_all()


if __name__ == "__main__":
    main()
