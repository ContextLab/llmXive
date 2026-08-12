"""
Remote Wall Clock Timer Module for US1.

Implements high-resolution wall-clock timing on remote nodes via SSH.
Captures start and stop timestamps relative to the remote node's clock,
calculates elapsed time, and formats the output for the CSV schema
required by Key Entities (PhysicalNode, TaskChunk).
"""
from __future__ import annotations

import logging
import time
import socket
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List

import paramiko

from orchestrator.logger import get_logger
from orchestrator.node_manager import NodeState

logger = get_logger(__name__)


class WallClockTimerError(Exception):
    """Base exception for wall-clock timer errors."""
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
    Container for wall-clock timing results.
    Matches the CSV schema columns: node_id, wall_clock_time.
    """
    node_id: str
    wall_clock_time: float  # Elapsed seconds (float)
    start_time_utc: Optional[datetime] = None
    stop_time_utc: Optional[datetime] = None
    status: str = "success"
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for CSV serialization."""
        return {
            "node_id": self.node_id,
            "wall_clock_time": self.wall_clock_time,
            "status": self.status,
            "error_message": self.error_message,
            # Optional metadata for debugging
            "start_time_utc": self.start_time_utc.isoformat() if self.start_time_utc else None,
            "stop_time_utc": self.stop_time_utc.isoformat() if self.stop_time_utc else None
        }


@dataclass
class RemoteTimerSession:
    """
    Manages the state of a timer session on a specific node.
    Tracks the SSH connection and the start time reference.
    """
    node_id: str
    ssh_client: paramiko.SSHClient
    start_time: Optional[datetime] = None
    stop_time: Optional[datetime] = None
    elapsed_seconds: Optional[float] = None
    is_active: bool = False


class RemoteWallClockTimer:
    """
    Handles remote wall-clock timing operations via SSH.
    Uses a high-precision command on the remote side to ensure
    accurate measurement of the benchmark execution window.
    """

    def __init__(self, ssh_client: paramiko.SSHClient, node_id: str):
        """
        Initialize the timer for a specific node.

        Args:
            ssh_client: An active, authenticated paramiko SSHClient.
            node_id: Unique identifier for the remote node.
        """
        self.ssh_client = ssh_client
        self.node_id = node_id
        self.session: Optional[RemoteTimerSession] = None
        self.logger = get_logger(__name__)

    def start_timer(self) -> RemoteTimerSession:
        """
        Start the high-resolution timer on the remote node.

        Executes `date +%s.%N` to capture nanosecond precision start time.
        Stores the result in the session.

        Returns:
            RemoteTimerSession: The active session object.

        Raises:
            RemoteTimerStartError: If the command fails or output is invalid.
        """
        try:
            self.logger.info(f"[{self.node_id}] Starting remote wall-clock timer...")
            
            # Command to get current time with nanosecond precision
            # Fallback to seconds if nanoseconds not available on older systems
            cmd = "date +%s.%N"
            
            stdin, stdout, stderr = self.ssh_client.exec_command(cmd)
            exit_status = stdout.channel.recv_exit_status()
            error_output = stderr.read().decode('utf-8')

            if exit_status != 0:
                raise RemoteTimerStartError(
                    f"Failed to start timer on {self.node_id}: {error_output}"
                )

            output = stdout.read().decode('utf-8').strip()
            
            # Parse the float time
            try:
                start_float = float(output)
            except ValueError:
                raise RemoteTimerReadError(
                    f"Invalid time format from {self.node_id}: '{output}'"
                )

            # Create a datetime object for UTC logging (approximate for nanosecond precision)
            # We use the float seconds since epoch to create a datetime
            start_dt = datetime.fromtimestamp(start_float, tz=timezone.utc)

            self.session = RemoteTimerSession(
                node_id=self.node_id,
                ssh_client=self.ssh_client,
                start_time=start_dt,
                is_active=True
            )

            self.logger.info(f"[{self.node_id}] Timer started at {start_dt.isoformat()}")
            return self.session

        except Exception as e:
            self.logger.error(f"[{self.node_id}] Error starting timer: {str(e)}")
            raise RemoteTimerStartError(f"Timer start failed: {str(e)}") from e

    def stop_timer(self, session: Optional[RemoteTimerSession] = None) -> float:
        """
        Stop the timer and calculate elapsed time.

        Args:
            session: The active session returned by start_timer().
                   If None, uses the internal session.

        Returns:
            float: Elapsed time in seconds.

        Raises:
            RemoteTimerStopError: If stopping fails or no active session exists.
            RemoteTimerReadError: If the stop time cannot be read.
        """
        if session is None:
            session = self.session

        if not session or not session.is_active:
            raise RemoteTimerStopError(
                f"No active timer session for {self.node_id}"
            )

        try:
            self.logger.info(f"[{self.node_id}] Stopping remote wall-clock timer...")
            
            cmd = "date +%s.%N"
            stdin, stdout, stderr = self.ssh_client.exec_command(cmd)
            exit_status = stdout.channel.recv_exit_status()
            error_output = stderr.read().decode('utf-8')

            if exit_status != 0:
                raise RemoteTimerStopError(
                    f"Failed to stop timer on {self.node_id}: {error_output}"
                )

            output = stdout.read().decode('utf-8').strip()
            
            try:
                stop_float = float(output)
            except ValueError:
                raise RemoteTimerReadError(
                    f"Invalid time format from {self.node_id}: '{output}'"
                )

            stop_dt = datetime.fromtimestamp(stop_float, tz=timezone.utc)
            elapsed = stop_float - float(session.start_time.timestamp())

            session.stop_time = stop_dt
            session.elapsed_seconds = elapsed
            session.is_active = False

            self.logger.info(f"[{self.node_id}] Timer stopped. Elapsed: {elapsed:.6f} seconds")
            return elapsed

        except Exception as e:
            self.logger.error(f"[{self.node_id}] Error stopping timer: {str(e)}")
            raise RemoteTimerStopError(f"Timer stop failed: {str(e)}") from e

    def get_result(self, session: Optional[RemoteTimerSession] = None) -> WallClockResult:
        """
        Retrieve the final result object formatted for the CSV schema.

        Args:
            session: The session to finalize.

        Returns:
            WallClockResult: The result object with node_id and wall_clock_time.
        """
        if not session:
            session = self.session

        if not session or session.elapsed_seconds is None:
            return WallClockResult(
                node_id=self.node_id,
                wall_clock_time=0.0,
                status="error",
                error_message="Session not completed or no elapsed time recorded."
            )

        return WallClockResult(
            node_id=self.node_id,
            wall_clock_time=session.elapsed_seconds,
            start_time_utc=session.start_time,
            stop_time_utc=session.stop_time,
            status="success"
        )


def create_remote_wall_clock_timer(ssh_client: paramiko.SSHClient, node_id: str) -> RemoteWallClockTimer:
    """
    Factory function to create a RemoteWallClockTimer instance.

    Args:
        ssh_client: Active SSH client.
        node_id: Target node identifier.

    Returns:
        RemoteWallClockTimer: Configured timer instance.
    """
    return RemoteWallClockTimer(ssh_client, node_id)


def main():
    """
    CLI entry point for testing the remote wall clock timer.
    Requires a valid SSH config or command-line arguments to connect.
    """
    import argparse

    parser = argparse.ArgumentParser(description="Test Remote Wall Clock Timer")
    parser.add_argument("--host", required=True, help="Remote host IP/hostname")
    parser.add_argument("--user", required=True, help="SSH username")
    parser.add_argument("--key", help="Path to private key")
    parser.add_argument("--password", help="SSH password (if no key)")
    parser.add_argument("--node-id", default="test-node", help="Node identifier for logging")

    args = parser.parse_args()

    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        if args.key:
            client.connect(args.host, username=args.user, key_filename=args.key)
        else:
            client.connect(args.host, username=args.user, password=args.password)

        timer = create_remote_wall_clock_timer(client, args.node_id)
        
        print(f"Starting timer on {args.host}...")
        timer.start_timer()
        
        # Simulate work (or run a real benchmark command here)
        print("Simulating work (sleep 2s)...")
        time.sleep(2)
        
        print("Stopping timer...")
        timer.stop_timer()
        
        result = timer.get_result()
        print(f"Result: {result.to_dict()}")
        
        client.close()

    except Exception as e:
        logger.error(f"CLI execution failed: {e}")
        raise


if __name__ == "__main__":
    main()
