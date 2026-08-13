"""
Network Saturation Handler Module (T014b)

Implements the abort logic for network saturation events.
Receives NetworkSaturationException from T014a, terminates remote processes,
verifies termination, logs the failure, and updates the validation status.
"""
from __future__ import annotations

import logging
import time
import os
import json
from dataclasses import dataclass
from enum import Enum
from typing import List, Dict, Any, Optional
from pathlib import Path

import paramiko

from orchestrator.logger import get_logger
from orchestrator.config import get_config

# --- Exceptions ---

class TerminationFailedError(Exception):
    """Raised when remote process termination fails after retries."""
    pass

class NetworkSaturationSignal(Enum):
    """Signal type for network saturation events."""
    NETWORK_SATURATION = "NETWORK_SATURATION"
    TERMINATION_FAILED = "TERMINATION_FAILED"

class NetworkSaturationError(Exception):
    """
    Exception raised to signal the orchestrator to stop the pipeline
    and exclude the run due to network saturation.
    """
    pass

# --- Data Classes ---

@dataclass
class TerminationResult:
    """Result of a remote process termination attempt."""
    node_id: str
    pid: int
    success: bool
    message: str

@dataclass
class NetworkSaturationHandler:
    """
    Handles the abort logic for network saturation events.
    """
    logger: logging.Logger
    config: Dict[str, Any]
    ssh_timeout: int = 10
    termination_retries: int = 3
    termination_delay: float = 1.0
    validation_status_path: Path = Path("code/data/raw/validation_status.json")

    def terminate_remote_process(
        self,
        node_ip: str,
        node_username: str,
        benchmark_pid: int,
        ssh_key_path: Optional[str] = None
    ) -> TerminationResult:
        """
        Terminates the benchmark process on a remote node.

        Args:
            node_ip: IP address of the target node.
            node_username: Username for SSH connection.
            benchmark_pid: Process ID to terminate.
            ssh_key_path: Path to SSH private key (optional).

        Returns:
            TerminationResult with success status and message.
        """
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:
            # Connect to the node
            connect_kwargs = {
                "hostname": node_ip,
                "username": node_username,
                "timeout": self.ssh_timeout
            }
            if ssh_key_path and os.path.exists(ssh_key_path):
                connect_kwargs["key_filename"] = ssh_key_path
            else:
                # Fallback to password or agent if key not provided
                # In production, this should be configured properly
                pass

            client.connect(**connect_kwargs)
            self.logger.debug(f"Connected to {node_ip} to terminate PID {benchmark_pid}")

            # Retry loop for termination
            for attempt in range(1, self.termination_retries + 1):
                try:
                    # First try SIGTERM
                    stdin, stdout, stderr = client.exec_command(f"kill -15 {benchmark_pid}")
                    exit_status = stdout.channel.recv_exit_status()
                    
                    # Wait a moment for graceful termination
                    time.sleep(self.termination_delay)

                    # Check if process is still running
                    stdin_check, stdout_check, stderr_check = client.exec_command(f"ps -p {benchmark_pid}")
                    exit_status_check = stdout_check.channel.recv_exit_status()
                    
                    if exit_status_check != 0:
                        # Process terminated successfully
                        return TerminationResult(
                            node_id=f"{node_username}@{node_ip}",
                            pid=benchmark_pid,
                            success=True,
                            message=f"Process {benchmark_pid} terminated successfully on {node_ip}."
                        )
                    
                    # If still running, try SIGKILL
                    self.logger.warning(f"Process {benchmark_pid} still running on {node_ip}, sending SIGKILL.")
                    stdin_kill, stdout_kill, stderr_kill = client.exec_command(f"kill -9 {benchmark_pid}")
                    exit_status_kill = stdout_kill.channel.recv_exit_status()
                    
                    # Verify termination again
                    time.sleep(self.termination_delay)
                    stdin_final, stdout_final, stderr_final = client.exec_command(f"ps -p {benchmark_pid}")
                    exit_status_final = stdout_final.channel.recv_exit_status()

                    if exit_status_final != 0:
                        return TerminationResult(
                            node_id=f"{node_username}@{node_ip}",
                            pid=benchmark_pid,
                            success=True,
                            message=f"Process {benchmark_pid} forcefully terminated on {node_ip}."
                        )
                    else:
                        raise Exception(f"Process {benchmark_pid} still alive after SIGKILL on {node_ip}.")

                except Exception as e:
                    self.logger.warning(f"Attempt {attempt}/{self.termination_retries} failed on {node_ip}: {str(e)}")
                    if attempt == self.termination_retries:
                        raise
                    time.sleep(self.termination_delay)

            # Should not reach here if retries work, but safety net
            return TerminationResult(
                node_id=f"{node_username}@{node_ip}",
                pid=benchmark_pid,
                success=False,
                message=f"Failed to terminate process {benchmark_pid} on {node_ip} after {self.termination_retries} attempts."
            )

        except paramiko.SSHException as e:
            self.logger.error(f"SSH connection failed for {node_ip}: {str(e)}")
            return TerminationResult(
                node_id=f"{node_username}@{node_ip}",
                pid=benchmark_pid,
                success=False,
                message=f"SSH connection error: {str(e)}"
            )
        except Exception as e:
            self.logger.error(f"Unexpected error during termination on {node_ip}: {str(e)}")
            return TerminationResult(
                node_id=f"{node_username}@{node_ip}",
                pid=benchmark_pid,
                success=False,
                message=f"Unexpected error: {str(e)}"
            )
        finally:
            client.close()

    def handle_saturation_event(
        self,
        node_details: List[Dict[str, Any]],
        benchmark_pids: Dict[str, int],
        run_id: str
    ) -> None:
        """
        Handles the network saturation event by terminating processes and logging.

        Args:
            node_details: List of dicts with 'ip', 'username', 'ssh_key' (optional).
            benchmark_pids: Dict mapping node_id to benchmark_pid.
            run_id: Current run identifier for logging.

        Raises:
            NetworkSaturationError: Always raised to signal abort.
            TerminationFailedError: If any critical termination fails.
        """
        self.logger.critical(f"NETWORK SATURATION DETECTED in run {run_id}. Initiating abort sequence.")
        
        termination_results: List[TerminationResult] = []
        failed_terminations: List[Dict[str, Any]] = []

        for node_info in node_details:
            node_ip = node_info.get("ip")
            node_user = node_info.get("username", "root")
            ssh_key = node_info.get("ssh_key")
            
            # Get PID for this node if available
            pid = benchmark_pids.get(f"{node_user}@{node_ip}")
            
            if pid is None:
                self.logger.warning(f"No PID found for {node_info.get('ip')}, skipping termination.")
                continue

            result = self.terminate_remote_process(
                node_ip=node_ip,
                node_username=node_user,
                benchmark_pid=pid,
                ssh_key_path=ssh_key
            )
            termination_results.append(result)

            if not result.success:
                failed_terminations.append({
                    "node_id": result.node_id,
                    "pid": result.pid,
                    "error": result.message
                })

        # Log summary
        success_count = sum(1 for r in termination_results if r.success)
        total_count = len(termination_results)
        self.logger.info(f"Termination summary: {success_count}/{total_count} processes terminated successfully.")

        # Update validation status file
        self._update_validation_status(run_id, failed_terminations)

        # Raise error to signal orchestrator to stop
        if failed_terminations:
            raise TerminationFailedError(
                f"Failed to terminate processes on {len(failed_terminations)} nodes. "
                f"Details: {failed_terminations}"
            )
        
        raise NetworkSaturationError(
            f"Network saturation detected in run {run_id}. All processes terminated. Run excluded."
        )

    def _update_validation_status(self, run_id: str, failed_terminations: List[Dict[str, Any]]) -> None:
        """
        Updates the validation_status.json file with the saturation event.

        Args:
            run_id: Current run identifier.
            failed_terminations: List of failed termination details.
        """
        status_path = self.validation_status_path
        
        # Ensure directory exists
        status_path.parent.mkdir(parents=True, exist_ok=True)

        # Load existing status or create new
        if status_path.exists():
            try:
                with open(status_path, 'r') as f:
                    status_data = json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                self.logger.error(f"Failed to load validation status file: {e}")
                status_data = {"runs": {}}
        else:
            status_data = {"runs": {}}

        # Initialize run entry if missing
        if run_id not in status_data["runs"]:
            status_data["runs"][run_id] = {
                "status": "excluded",
                "critical_missing": [],
                "non_critical_missing": [],
                "excluded_terms": [],
                "warnings": [],
                "error_code": None,
                "details": {}
            }

        run_entry = status_data["runs"][run_id]
        run_entry["status"] = "excluded"
        run_entry["error_code"] = "NETWORK_SATURATION"
        run_entry["details"]["saturation_event"] = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()),
            "failed_terminations": failed_terminations,
            "reason": "Packet loss exceeded 20% threshold"
        }

        # Write back
        with open(status_path, 'w') as f:
            json.dump(status_data, f, indent=2)
        
        self.logger.info(f"Updated validation status for run {run_id}: excluded due to NETWORK_SATURATION")

# --- Factory and Main ---

def create_handler(config: Optional[Dict[str, Any]] = None) -> NetworkSaturationHandler:
    """Factory function to create a NetworkSaturationHandler instance."""
    logger = get_logger(__name__)
    cfg = config or get_config()
    return NetworkSaturationHandler(
        logger=logger,
        config=cfg,
        ssh_timeout=cfg.get("ssh_timeout", 10),
        termination_retries=cfg.get("termination_retries", 3),
        termination_delay=cfg.get("termination_delay", 1.0)
    )

def main():
    """
    Main entry point for testing the handler directly.
    Expects environment variables or config file for node details.
    """
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="Network Saturation Handler")
    parser.add_argument("--run-id", type=str, required=True, help="Run ID for logging")
    parser.add_argument("--nodes", type=str, required=True, help="JSON string of node details")
    parser.add_argument("--pids", type=str, required=True, help="JSON string of node->pid mapping")
    
    args = parser.parse_args()

    try:
        node_details = json.loads(args.nodes)
        benchmark_pids = json.loads(args.pids)
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON arguments: {e}", file=sys.stderr)
        sys.exit(1)

    handler = create_handler()
    
    try:
        handler.handle_saturation_event(
            node_details=node_details,
            benchmark_pids=benchmark_pids,
            run_id=args.run_id
        )
    except NetworkSaturationError as e:
        print(f"Network saturation handled: {e}")
        sys.exit(0) # Normal exit after handling
    except TerminationFailedError as e:
        print(f"Termination failed: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(2)

if __name__ == "__main__":
    main()
