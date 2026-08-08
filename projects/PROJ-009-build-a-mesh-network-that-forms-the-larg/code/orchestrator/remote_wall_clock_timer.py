"""
Remote Wall-Clock Timer Module

Captures wall-clock execution time on remote nodes via SSH.
This is distinct from the benchmark's internal timing, providing
node-level wall-clock metrics for the mesh network supercomputer.

Dependencies:
    - T013a (node_manager): For SSH connection management.
    - T004 (config): For timeout configurations.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Dict, Optional, Tuple
from enum import Enum

import paramiko

from orchestrator.node_manager import NodeManager, NodeDiscoveryError
from orchestrator.logger import get_logger
from orchestrator.config import get_config

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
    """Raised when reading the elapsed time fails."""
    pass


@dataclass
class WallClockResult:
    """
    Result of a remote wall-clock timing operation.

    Attributes:
        node_id: Identifier of the remote node.
        start_time_utc: UTC timestamp when the timer started.
        stop_time_utc: UTC timestamp when the timer stopped.
        elapsed_seconds: Measured wall-clock duration in seconds.
        success: Boolean indicating if the operation completed successfully.
        error_message: Optional error description if failed.
    """
    node_id: str
    start_time_utc: datetime
    stop_time_utc: Optional[datetime] = None
    elapsed_seconds: Optional[float] = None
    success: bool = False
    error_message: Optional[str] = None

    def to_dict(self) -> Dict:
        """Convert result to dictionary for serialization."""
        return {
            "node_id": self.node_id,
            "start_time_utc": self.start_time_utc.isoformat() if self.start_time_utc else None,
            "stop_time_utc": self.stop_time_utc.isoformat() if self.stop_time_utc else None,
            "elapsed_seconds": self.elapsed_seconds,
            "success": self.success,
            "error_message": self.error_message
        }


@dataclass
class RemoteTimerSession:
    """
    Manages a timing session on a specific remote node.

    This class handles the SSH commands required to start, stop, and
    read a high-resolution wall-clock timer on the remote host.
    """
    node_id: str
    manager: NodeManager
    _ssh_client: Optional[paramiko.SSHClient] = None
    _start_command: Optional[str] = None
    _stop_command: Optional[str] = None
    _read_command: Optional[str] = None
    _session_active: bool = False
    _start_time_utc: Optional[datetime] = None

    def __post_init__(self):
        # Define remote commands using `date` for high-resolution timestamps
        # We use a unique session ID to avoid conflicts if multiple timers run
        self._session_id = f"timer_{self.node_id}_{int(time.time())}"
        self._start_command = f"echo '{self._session_id}:START' > /tmp/{self._session_id}.timer && date +%s.%N"
        self._stop_command = f"echo '{self._session_id}:STOP' >> /tmp/{self._session_id}.timer && date +%s.%N"
        self._read_command = f"cat /tmp/{self._session_id}.timer && rm -f /tmp/{self._session_id}.timer"

    def _ensure_connection(self) -> paramiko.SSHClient:
        """Ensure an SSH connection is active."""
        if self._ssh_client is None or not self._ssh_client.get_transport().is_active():
            # Attempt to reconnect using the manager's node info
            node_info = self.manager.get_node_info(self.node_id)
            if not node_info:
                raise RemoteTimerStartError(f"Node {self.node_id} not found in manager.")
            
            logger.info(f"Establishing SSH connection to {self.node_id} for timing.")
            self._ssh_client = paramiko.SSHClient()
            self._ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            try:
                self._ssh_client.connect(
                    hostname=node_info.ip_address,
                    username=node_info.username,
                    key_filename=node_info.ssh_key_path,
                    timeout=get_config().ssh_timeout_seconds
                )
            except Exception as e:
                raise RemoteTimerStartError(f"Failed to connect to {self.node_id}: {e}")
        return self._ssh_client

    def start_timer(self) -> datetime:
        """
        Start the remote wall-clock timer.
        
        Returns:
            datetime: The UTC timestamp when the timer was started locally.
        
        Raises:
            RemoteTimerStartError: If the start command fails.
        """
        if self._session_active:
            logger.warning(f"Timer for {self.node_id} is already active.")
            return self._start_time_utc

        client = self._ensure_connection()
        self._start_time_utc = datetime.now(timezone.utc)
        
        try:
            stdin, stdout, stderr = client.exec_command(self._start_command)
            exit_status = stdout.channel.recv_exit_status()
            
            if exit_status != 0:
                error_output = stderr.read().decode('utf-8', errors='replace')
                raise RemoteTimerStartError(f"Remote start command failed on {self.node_id}: {error_output}")
            
            # Optional: Verify the file was created remotely
            logger.debug(f"Started timer on {self.node_id} at {self._start_time_utc}")
            self._session_active = True
            return self._start_time_utc

        except Exception as e:
            self._session_active = False
            raise RemoteTimerStartError(f"Exception starting timer on {self.node_id}: {e}")

    def stop_timer(self) -> datetime:
        """
        Stop the remote wall-clock timer.
        
        Returns:
            datetime: The UTC timestamp when the timer was stopped locally.
        
        Raises:
            RemoteTimerStopError: If the stop command fails.
        """
        if not self._session_active:
            raise RemoteTimerStopError(f"Timer for {self.node_id} is not active.")

        client = self._ensure_connection()
        stop_time_utc = datetime.now(timezone.utc)
        
        try:
            stdin, stdout, stderr = client.exec_command(self._stop_command)
            exit_status = stdout.channel.recv_exit_status()
            
            if exit_status != 0:
                error_output = stderr.read().decode('utf-8', errors='replace')
                raise RemoteTimerStopError(f"Remote stop command failed on {self.node_id}: {error_output}")
            
            logger.debug(f"Stopped timer on {self.node_id} at {stop_time_utc}")
            self._session_active = False
            return stop_time_utc

        except Exception as e:
            self._session_active = False
            raise RemoteTimerStopError(f"Exception stopping timer on {self.node_id}: {e}")

    def get_elapsed_time(self) -> float:
        """
        Retrieve the elapsed time from the remote timer.
        
        This method reads the start and stop timestamps written by the
        remote commands and calculates the difference.
        
        Returns:
            float: Elapsed time in seconds.
        
        Raises:
            RemoteTimerReadError: If reading or parsing the time fails.
        """
        if self._session_active:
            logger.warning(f"Timer for {self.node_id} is still active. Stopping automatically to read.")
            try:
                self.stop_timer()
            except RemoteTimerStopError:
                pass # Continue to try and read partial data or fail

        client = self._ensure_connection()
        
        try:
            stdin, stdout, stderr = client.exec_command(self._read_command)
            exit_status = stdout.channel.recv_exit_status()
            
            if exit_status != 0:
                error_output = stderr.read().decode('utf-8', errors='replace')
                raise RemoteTimerReadError(f"Remote read command failed on {self.node_id}: {error_output}")
            
            output = stdout.read().decode('utf-8', errors='replace').strip()
            
            # Parse output: "START\n<timestamp>\nSTOP\n<timestamp>"
            lines = [line for line in output.split('\n') if line.strip()]
            if len(lines) < 2:
                raise RemoteTimerReadError(f"Insufficient data from {self.node_id}: {output}")
            
            # The first line is the marker, the second is the timestamp
            # Actually, our command writes marker then timestamp on separate lines
            # Command: echo '...:START' > file && date
            # So file contains: "ID:START\n<timestamp>"
            # Stop command: echo '...:STOP' >> file && date
            # So file contains: "ID:START\n<timestamp_start>\nID:STOP\n<timestamp_end>"
            
            if len(lines) < 4:
                # Maybe only start was recorded
                raise RemoteTimerReadError(f"Incomplete timing data on {self.node_id}: {lines}")

            # Extract timestamps (second and fourth lines usually, or parse carefully)
            # Format: ID:START\n<ts1>\nID:STOP\n<ts2>
            # We need to find the numeric timestamps
            timestamps = []
            for line in lines:
                if ':' in line:
                    # Marker line, skip or parse ID
                    continue
                try:
                    timestamps.append(float(line))
                except ValueError:
                    # Skip non-numeric lines if any
                    continue

            if len(timestamps) < 2:
                raise RemoteTimerReadError(f"Could not parse timestamps from {self.node_id}: {timestamps}")

            start_ts = timestamps[0]
            stop_ts = timestamps[1]
            
            elapsed = stop_ts - start_ts
            if elapsed < 0:
                raise RemoteTimerReadError(f"Negative elapsed time on {self.node_id}: {elapsed}")
            
            logger.info(f"Remote wall-clock time for {self.node_id}: {elapsed:.6f}s")
            return elapsed

        except Exception as e:
            raise RemoteTimerReadError(f"Exception reading timer on {self.node_id}: {e}")

    def close(self):
        """Close the SSH connection."""
        if self._ssh_client:
            self._ssh_client.close()
            self._ssh_client = None
            logger.debug(f"Closed SSH connection to {self.node_id}")


class RemoteWallClockTimer:
    """
    High-level interface for managing wall-clock timers across multiple nodes.
    """
    def __init__(self, node_manager: NodeManager):
        self.manager = node_manager
        self.sessions: Dict[str, RemoteTimerSession] = {}

    def create_session(self, node_id: str) -> RemoteTimerSession:
        """Create a new timing session for a specific node."""
        if node_id in self.sessions:
            logger.warning(f"Session for {node_id} already exists, closing previous.")
            self.sessions[node_id].close()
        
        session = RemoteTimerSession(node_id=node_id, manager=self.manager)
        self.sessions[node_id] = session
        return session

    def start_all(self, node_ids: List[str]) -> Dict[str, WallClockResult]:
        """
        Start timers on all specified nodes.
        
        Args:
            node_ids: List of node identifiers to start timers on.
        
        Returns:
            Dictionary mapping node_id to WallClockResult.
        """
        results = {}
        for node_id in node_ids:
            try:
                session = self.create_session(node_id)
                start_time = session.start_timer()
                results[node_id] = WallClockResult(
                    node_id=node_id,
                    start_time_utc=start_time,
                    success=True
                )
            except Exception as e:
                logger.error(f"Failed to start timer on {node_id}: {e}")
                results[node_id] = WallClockResult(
                    node_id=node_id,
                    start_time_utc=datetime.now(timezone.utc),
                    success=False,
                    error_message=str(e)
                )
        return results

    def stop_all(self, node_ids: List[str]) -> Dict[str, WallClockResult]:
        """
        Stop timers on all specified nodes.
        
        Args:
            node_ids: List of node identifiers to stop timers on.
        
        Returns:
            Dictionary mapping node_id to WallClockResult.
        """
        results = {}
        for node_id in node_ids:
            if node_id not in self.sessions:
                results[node_id] = WallClockResult(
                    node_id=node_id,
                    start_time_utc=None,
                    success=False,
                    error_message="No active session"
                )
                continue
            
            try:
                session = self.sessions[node_id]
                stop_time = session.stop_timer()
                results[node_id] = WallClockResult(
                    node_id=node_id,
                    start_time_utc=session._start_time_utc,
                    stop_time_utc=stop_time,
                    success=True
                )
            except Exception as e:
                logger.error(f"Failed to stop timer on {node_id}: {e}")
                results[node_id] = WallClockResult(
                    node_id=node_id,
                    start_time_utc=session._start_time_utc,
                    success=False,
                    error_message=str(e)
                )
        return results

    def read_all(self, node_ids: List[str]) -> Dict[str, WallClockResult]:
        """
        Read elapsed times from all specified nodes.
        
        Args:
            node_ids: List of node identifiers to read from.
        
        Returns:
            Dictionary mapping node_id to WallClockResult with elapsed_seconds.
        """
        results = {}
        for node_id in node_ids:
            if node_id not in self.sessions:
                results[node_id] = WallClockResult(
                    node_id=node_id,
                    success=False,
                    error_message="No active session"
                )
                continue

            try:
                session = self.sessions[node_id]
                elapsed = session.get_elapsed_time()
                results[node_id] = WallClockResult(
                    node_id=node_id,
                    start_time_utc=session._start_time_utc,
                    elapsed_seconds=elapsed,
                    success=True
                )
            except Exception as e:
                logger.error(f"Failed to read timer on {node_id}: {e}")
                results[node_id] = WallClockResult(
                    node_id=node_id,
                    start_time_utc=session._start_time_utc,
                    success=False,
                    error_message=str(e)
                )
        return results

    def run_timing_session(self, node_ids: List[str], task_duration_seconds: float = 10.0) -> Dict[str, WallClockResult]:
        """
        Convenience method to start, wait, stop, and read timers.
        
        Args:
            node_ids: List of nodes to time.
            task_duration_seconds: How long to wait between start and stop.
        
        Returns:
            Dictionary of results with elapsed times.
        """
        logger.info(f"Starting wall-clock timing session for {len(node_ids)} nodes.")
        self.start_all(node_ids)
        logger.info(f"Waiting for {task_duration_seconds}s to simulate task execution...")
        time.sleep(task_duration_seconds)
        self.stop_all(node_ids)
        return self.read_all(node_ids)

    def cleanup(self):
        """Close all active sessions."""
        for node_id, session in self.sessions.items():
            session.close()
        self.sessions.clear()


def main():
    """
    CLI entry point for testing the remote wall clock timer.
    Requires a config file with node definitions.
    """
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Test Remote Wall Clock Timer")
    parser.add_argument("--config", type=str, default="config/orchestrator.yaml", help="Path to config file")
    parser.add_argument("--nodes", type=str, nargs="+", help="Specific node IDs to test")
    parser.add_argument("--duration", type=float, default=5.0, help="Duration to wait between start/stop")
    args = parser.parse_args()

    config = get_config(args.config)
    node_manager = NodeManager(config)
    
    # If specific nodes provided, use them; otherwise use all discovered
    target_nodes = args.nodes if args.nodes else [n.id for n in node_manager.nodes]

    if not target_nodes:
        print("No nodes found.")
        return 1

    timer = RemoteWallClockTimer(node_manager)
    try:
        results = timer.run_timing_session(target_nodes, args.duration)
        
        print("\n--- Wall Clock Timing Results ---")
        for node_id, res in results.items():
            if res.success:
                print(f"Node {node_id}: {res.elapsed_seconds:.6f} seconds")
            else:
                print(f"Node {node_id}: FAILED - {res.error_message}")
        
        # Save results to a JSON file for downstream consumption
        output_path = "data/processed/wall_clock_test_results.json"
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            json.dump({k: v.to_dict() for k, v in results.items()}, f, indent=2)
        print(f"\nResults saved to {output_path}")
        
    finally:
        timer.cleanup()

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
