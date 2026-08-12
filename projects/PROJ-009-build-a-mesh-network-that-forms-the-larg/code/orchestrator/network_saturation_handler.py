"""
network_saturation_handler.py

Implements the abort logic for network saturation events.
Receives NetworkSaturationSignal from instrumentor_remote.py and terminates
remote benchmark processes before raising NetworkSaturationError.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from enum import Enum

import paramiko
from paramiko import SSHClient, AutoAddPolicy, SSHException

from orchestrator.logger import get_logger
from orchestrator.instrumentor_remote import NetworkSaturationSignal

logger = get_logger(__name__)


class TerminationFailedError(Exception):
    """Raised when remote process termination fails after retries."""
    pass


class NetworkSaturationError(Exception):
    """
    Raised to signal the orchestrator that network saturation occurred
    and the current run must be aborted and excluded.
    """
    def __init__(self, message: str, node_ids: List[str]):
        super().__init__(message)
        self.node_ids = node_ids


@dataclass
class TerminationResult:
    """Result of a remote process termination attempt."""
    node_id: str
    success: bool
    message: str
    attempts: int


class NetworkSaturationHandler:
    """
    Handles the abort logic for network saturation events.

    Responsibilities:
    1. Receive NetworkSaturationSignal.
    2. Terminate remote benchmark processes via SSH.
    3. Verify termination with retries.
    4. Raise NetworkSaturationError to abort the pipeline.
    """

    def __init__(self, ssh_clients: Dict[str, SSHClient], timeout_threshold: float = 1.0):
        """
        Initialize the handler.

        Args:
            ssh_clients: Dictionary mapping node_id -> paramiko.SSHClient
            timeout_threshold: Seconds to wait between termination verification retries.
        """
        self.ssh_clients = ssh_clients
        self.timeout_threshold = timeout_threshold
        self.logger = get_logger(__name__)

    def terminate_remote_processes(
        self,
        signal: NetworkSaturationSignal,
        max_retries: int = 3
    ) -> List[TerminationResult]:
        """
        Attempt to terminate the benchmark process on all active nodes.

        Args:
            signal: The NetworkSaturationSignal containing affected node_ids and pids.
            max_retries: Maximum number of retry attempts for termination verification.

        Returns:
            List of TerminationResult objects for each node.

        Raises:
            TerminationFailedError: If any node fails to terminate after max_retries.
        """
        results = []
        failed_nodes = []

        # Extract affected nodes and PIDs from the signal
        # Signal structure assumed to have: node_id, pid, packet_loss_pct
        nodes_to_terminate = signal.affected_nodes

        for node_id, pid in nodes_to_terminate.items():
            client = self.ssh_clients.get(node_id)
            if not client:
                error_msg = f"No SSH client found for node {node_id}"
                self.logger.error(error_msg)
                results.append(TerminationResult(node_id, False, error_msg, 0))
                failed_nodes.append(node_id)
                continue

            success = False
            attempts = 0
            last_error = "No error"

            for attempt in range(1, max_retries + 1):
                attempts = attempt
                try:
                    # Check if process exists
                    stdin, stdout, stderr = client.exec_command(f"ps -p {pid}")
                    stdout.channel.recv_exit_status() # Ensure command completion
                    process_exists = stdout.channel.recv_exit_status() == 0

                    if not process_exists:
                        self.logger.warning(f"Process {pid} on {node_id} already terminated.")
                        success = True
                        break

                    # Attempt SIGKILL
                    self.logger.info(f"Sending SIGKILL to process {pid} on {node_id}")
                    stdin, stdout, stderr = client.exec_command(f"kill -9 {pid}")
                    exit_code = stdout.channel.recv_exit_status()

                    if exit_code != 0:
                        last_error = stderr.read().decode().strip() or f"Exit code: {exit_code}"
                        self.logger.warning(f"Kill command failed on {node_id}: {last_error}")
                        time.sleep(self.timeout_threshold)
                        continue

                    # Verify termination
                    time.sleep(self.timeout_threshold)
                    stdin, stdout, stderr = client.exec_command(f"ps -p {pid}")
                    exit_code = stdout.channel.recv_exit_status()

                    if exit_code != 0:
                        success = True
                        self.logger.info(f"Process {pid} on {node_id} successfully terminated.")
                        break
                    else:
                        last_error = "Process still exists after SIGKILL"
                        self.logger.warning(f"Process {pid} on {node_id} still exists after SIGKILL.")
                        time.sleep(self.timeout_threshold)

                except SSHException as e:
                    last_error = str(e)
                    self.logger.error(f"SSH error during termination on {node_id}: {e}")
                    time.sleep(self.timeout_threshold)
                except Exception as e:
                    last_error = str(e)
                    self.logger.error(f"Unexpected error during termination on {node_id}: {e}")
                    time.sleep(self.timeout_threshold)

            if success:
                results.append(TerminationResult(node_id, True, "Success", attempts))
            else:
                self.logger.error(f"Failed to terminate process {pid} on {node_id} after {attempts} attempts: {last_error}")
                results.append(TerminationResult(node_id, False, last_error, attempts))
                failed_nodes.append(node_id)

        if failed_nodes:
            raise TerminationFailedError(
                f"Failed to terminate processes on nodes: {', '.join(failed_nodes)}"
            )

        return results

    def handle_saturation_event(self, signal: NetworkSaturationSignal) -> None:
        """
        Main entry point for handling a saturation event.

        1. Terminates remote processes.
        2. Logs the failure with error code.
        3. Raises NetworkSaturationError to abort the pipeline.

        Args:
            signal: The NetworkSaturationSignal.

        Raises:
            NetworkSaturationError: Always raised after attempting termination to signal abort.
            TerminationFailedError: If termination fails.
        """
        self.logger.error(
            f"NETWORK_SATURATION detected: Packet loss {signal.packet_loss_pct}% "
            f"on nodes {list(signal.affected_nodes.keys())}"
        )

        try:
            self.terminate_remote_processes(signal)
        except TerminationFailedError as e:
            self.logger.critical(f"Termination failed: {e}")
            # Re-raise to ensure the pipeline knows something went wrong
            raise

        # Log the specific abort code for downstream exclusion logic
        self.logger.error(
            "Aborting run due to network saturation. Error code: NETWORK_SATURATION"
        )

        # Raise the exception to signal the orchestrator to stop the pipeline
        node_ids = list(signal.affected_nodes.keys())
        raise NetworkSaturationError(
            f"Network saturation detected ({signal.packet_loss_pct}% loss). "
            f"Pipeline aborted. Affected nodes: {node_ids}",
            node_ids
        )


def create_handler(ssh_clients: Dict[str, SSHClient], timeout_threshold: float = 1.0) -> NetworkSaturationHandler:
    """Factory function to create a NetworkSaturationHandler."""
    return NetworkSaturationHandler(ssh_clients, timeout_threshold)


def main():
    """
    Standalone test runner for the handler.
    Simulates a signal and attempts to connect to configured nodes.
    """
    import argparse
    import yaml
    from pathlib import Path

    parser = argparse.ArgumentParser(description="Test NetworkSaturationHandler")
    parser.add_argument("--config", type=str, required=True, help="Path to config YAML with node IPs and SSH credentials")
    parser.add_argument("--node", type=str, required=True, help="Node ID to simulate saturation on")
    parser.add_argument("--pid", type=int, required=True, help="PID of the process to kill")
    parser.add_argument("--loss", type=float, default=25.0, help="Simulated packet loss percentage")
    args = parser.parse_args()

    config_path = Path(args.config)
    if not config_path.exists():
        print(f"Error: Config file {config_path} not found.")
        return

    config = yaml.safe_load(config_path.read_text())
    nodes = config.get("nodes", {})
    node_info = nodes.get(args.node)

    if not node_info:
        print(f"Error: Node {args.node} not found in config.")
        return

    # Setup SSH
    client = SSHClient()
    client.set_missing_host_key_policy(AutoAddPolicy())
    try:
        client.connect(
            hostname=node_info["ip"],
            username=node_info["username"],
            password=node_info.get("password", ""),
            key_filename=node_info.get("key_file"),
            timeout=10
        )
    except Exception as e:
        print(f"SSH Connection failed: {e}")
        return

    clients = {args.node: client}

    signal = NetworkSaturationSignal(
        node_id=args.node,
        pid=args.pid,
        packet_loss_pct=args.loss,
        affected_nodes={args.node: args.pid}
    )

    handler = create_handler(clients)

    try:
        handler.handle_saturation_event(signal)
    except NetworkSaturationError as e:
        print(f"Handled Saturation (Expected): {e}")
    except TerminationFailedError as e:
        print(f"Termination Failed (Critical): {e}")
    finally:
        client.close()


if __name__ == "__main__":
    main()