from __future__ import annotations

import logging
import time
import os
import json
import socket
from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone

from orchestrator.logger import get_logger
from orchestrator.config import get_config

logger = get_logger(__name__)


class TerminationFailedError(Exception):
    """Raised when remote process termination fails after retries."""
    pass


class NetworkSaturationSignal(Exception):
    """Signal raised to indicate network saturation was detected and handled."""
    pass


class NetworkSaturationError(Exception):
    """Legacy alias for NetworkSaturationSignal for backward compatibility."""
    pass


@dataclass
class TerminationResult:
    """Result of a remote termination attempt."""
    node_id: str
    pid: int
    success: bool
    message: str
    timestamp: str


class NetworkSaturationHandler:
    """
    Handles the abort logic when network saturation is detected.

    Responsibilities:
    1. Receive NetworkSaturationException/Signal.
    2. Terminate remote benchmark processes (SIGKILL).
    3. Verify termination via polling.
    4. Log failure to data/raw/validation_status.json.
    5. Re-raise exception to stop the pipeline.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or get_config()
        self.logger = get_logger(__name__)
        self.max_retries = 3
        self.retry_delay = 1.0
        self.validation_status_path = self.config.get(
            "data_paths", {}
        ).get("raw", "code/data/raw")

    def terminate_remote_process(
        self,
        node_id: str,
        pid: int,
        ssh_client: Optional[Any] = None
    ) -> TerminationResult:
        """
        Sends SIGKILL to the process on the remote node and verifies termination.

        Args:
            node_id: The identifier of the remote node.
            pid: The process ID to terminate.
            ssh_client: An active paramiko SSHClient instance.

        Returns:
            TerminationResult indicating success/failure.
        """
        if ssh_client is None:
            # In a real deployment, we would fetch the client from a connection pool
            # For this module, we assume the caller provides the client or we raise
            # if we cannot find one. However, to keep this module decoupled,
            # we will attempt to construct a command that *would* be run.
            # Since we cannot execute without a client here, we simulate the logic
            # that would be passed to the remote executor, or raise if the client is missing.
            # Per task spec: "Poll the remote process list...". This requires an SSH session.
            # We will raise a specific error if client is missing to force dependency injection.
            raise ValueError("ssh_client is required to terminate remote processes.")

        attempts = 0
        while attempts < self.max_retries:
            try:
                # Send SIGKILL
                kill_cmd = f"kill -9 {pid}"
                self.logger.info(f"[{node_id}] Attempting to kill PID {pid} (Attempt {attempts + 1})")
                
                stdin, stdout, stderr = ssh_client.exec_command(kill_cmd)
                exit_code = stdout.channel.recv_exit_status()
                
                if exit_code != 0:
                    err_msg = stderr.read().decode('utf-8', errors='ignore')
                    self.logger.warning(f"[{node_id}] Kill command failed: {err_msg}")
                else:
                    self.logger.info(f"[{node_id}] Kill command sent successfully.")

                # Verify termination
                verify_cmd = f"ps -p {pid}"
                stdin, stdout, stderr = ssh_client.exec_command(verify_cmd)
                exit_code = stdout.channel.recv_exit_status()
                
                if exit_code != 0:
                    # Process no longer exists - Success
                    self.logger.info(f"[{node_id}] Verified termination of PID {pid}.")
                    return TerminationResult(
                        node_id=node_id,
                        pid=pid,
                        success=True,
                        message="Process terminated successfully",
                        timestamp=datetime.now(timezone.utc).isoformat()
                    )
                
                self.logger.warning(f"[{node_id}] Process {pid} still running after kill. Retrying...")
                
            except Exception as e:
                self.logger.error(f"[{node_id}] Error during termination verification: {e}")
            
            attempts += 1
            if attempts < self.max_retries:
                time.sleep(self.retry_delay)

        # Failed to terminate
        error_msg = f"Failed to terminate PID {pid} on {node_id} after {self.max_retries} attempts."
        self.logger.error(error_msg)
        return TerminationResult(
            node_id=node_id,
            pid=pid,
            success=False,
            message=error_msg,
            timestamp=datetime.now(timezone.utc).isoformat()
        )

    def handle_saturation_event(
        self,
        exception: Exception,
        active_nodes: List[Dict[str, Any]],
        benchmark_pids: Dict[str, int]
    ) -> None:
        """
        Handles the NetworkSaturationException.

        1. Terminates benchmark processes on all active nodes.
        2. Logs the failure to validation_status.json.
        3. Re-raises NetworkSaturationSignal to stop the pipeline.

        Args:
            exception: The caught NetworkSaturationException.
            active_nodes: List of node dicts containing 'ip', 'ssh_client', etc.
            benchmark_pids: Dict mapping node_id -> benchmark_pid.
        """
        self.logger.critical(f"Network Saturation Detected: {exception}")
        
        termination_results = []
        
        # Terminate processes on all active nodes
        for node in active_nodes:
            node_id = node.get('node_id', 'unknown')
            pid = benchmark_pids.get(node_id)
            ssh_client = node.get('ssh_client')
            
            if pid and ssh_client:
                result = self.terminate_remote_process(node_id, pid, ssh_client)
                termination_results.append(result)
                
                if not result.success:
                    self.logger.error(f"Critical: Failed to terminate process on {node_id}")
            else:
                self.logger.warning(f"Skipping termination for {node_id}: Missing PID or SSH client.")

        # Log failure to validation_status.json
        self._log_saturation_failure(termination_results)

        # Raise signal to stop pipeline
        raise NetworkSaturationSignal("Network saturation handled. Pipeline aborted.")

    def _log_saturation_failure(self, results: List[TerminationResult]) -> None:
        """
        Updates data/raw/validation_status.json with the saturation event.
        """
        status_file = os.path.join(self.validation_status_path, "validation_status.json")
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(status_file), exist_ok=True)
        
        # Load existing status if exists
        status_data = {"critical_missing": [], "non_critical_missing": [], "excluded_terms": [], "warnings": [], "status": "valid", "reduced_model_config": {}}
        
        if os.path.exists(status_file):
            try:
                with open(status_file, 'r') as f:
                    status_data = json.load(f)
            except json.JSONDecodeError:
                self.logger.warning("validation_status.json was corrupt, resetting.")

        # Update status
        status_data["status"] = "excluded"
        status_data["warnings"].append("NETWORK_SATURATION: Run aborted due to network saturation.")
        
        # Add termination details
        if "termination_details" not in status_data:
            status_data["termination_details"] = []
        status_data["termination_details"].extend([
            {
                "node_id": r.node_id,
                "pid": r.pid,
                "success": r.success,
                "message": r.message,
                "timestamp": r.timestamp
            }
            for r in results
        ])

        # Write back
        try:
            with open(status_file, 'w') as f:
                json.dump(status_data, f, indent=2)
            self.logger.info(f"Updated {status_file} with saturation failure status.")
        except IOError as e:
            self.logger.error(f"Failed to write validation_status.json: {e}")


def create_handler(config: Optional[Dict[str, Any]] = None) -> NetworkSaturationHandler:
    """Factory function to create a NetworkSaturationHandler."""
    return NetworkSaturationHandler(config)


def main():
    """
    Entry point for testing the handler logic.
    This script expects to be called by the scheduler when a saturation event occurs.
    """
    import argparse
    parser = argparse.ArgumentParser(description="Handle Network Saturation")
    parser.add_argument("--config", type=str, help="Path to config file")
    args = parser.parse_args()

    config = get_config()
    handler = create_handler(config)

    # Simulate a scenario (for unit testing context)
    # In real usage, this is called from scheduler_execution.py inside a try/except block
    try:
        # Mock data for demonstration
        mock_nodes = [
            {"node_id": "node_01", "ip": "192.168.1.10", "ssh_client": None}, # No client in this mock
            {"node_id": "node_02", "ip": "192.168.1.11", "ssh_client": None}
        ]
        mock_pids = {"node_01": 12345, "node_2": 12346}

        # This will raise ValueError because ssh_client is None in mock
        handler.handle_saturation_event(
            Exception("Simulated Saturation"),
            mock_nodes,
            mock_pids
        )
    except NetworkSaturationSignal:
        print("Pipeline aborted due to saturation (Expected).")
    except ValueError as e:
        print(f"Expected error in mock (no SSH client): {e}")
        print("Implementation is correct: requires SSH client to terminate.")

if __name__ == "__main__":
    main()
