"""
Network Saturation Handler Module (T014b)

Implements the abort logic for network saturation events.
Receives NetworkSaturationSignal from T014a, terminates remote benchmark processes,
verifies termination, and raises NetworkSaturationError to stop the pipeline.
"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from enum import Enum
from typing import List, Dict, Any, Optional

import paramiko
from paramiko import SSHClient, AutoAddPolicy, SSHException

from orchestrator.logger import get_logger
from orchestrator.models import PhysicalNode

# Configure logger
logger = get_logger(__name__)


class TerminationFailedError(Exception):
    """Raised when remote process termination fails after retries."""
    pass


class NetworkSaturationSignal:
    """
    Signal object received from T014a (RemoteInstrumentor).
    Contains the necessary context to abort the current run.
    """
    def __init__(
        self,
        node_ids: List[str],
        benchmark_pids: Dict[str, int],
        run_id: str,
        packet_loss_rate: float
    ):
        self.node_ids = node_ids
        self.benchmark_pids = benchmark_pids  # Dict: node_id -> pid
        self.run_id = run_id
        self.packet_loss_rate = packet_loss_rate

    def __repr__(self):
        return (f"NetworkSaturationSignal(run_id={self.run_id}, "
                f"nodes={self.node_ids}, loss_rate={self.packet_loss_rate:.2%})")


class NetworkSaturationError(Exception):
    """
    Raised to signal the orchestrator (T017, T015b) to stop the pipeline
    and exclude the current run due to network saturation.
    """
    def __init__(self, message: str, run_id: str, signal: NetworkSaturationSignal):
        super().__init__(message)
        self.run_id = run_id
        self.signal = signal
        self.error_code = "NETWORK_SATURATION"


@dataclass
class TerminationResult:
    """Result of attempting to terminate a process on a node."""
    node_id: str
    pid: int
    success: bool
    message: str
    attempts: int


class NetworkSaturationHandler:
    """
    Handles the abort logic for network saturation events.
    Responsible for terminating remote processes and verifying their death.
    """

    def __init__(self, ssh_config: Optional[Dict[str, Any]] = None):
        """
        Initialize the handler.
        
        Args:
            ssh_config: Optional dictionary with 'username', 'password', 'key_filename', 
                        'timeout' for SSH connections.
        """
        self.ssh_config = ssh_config or {
            'username': 'root',
            'timeout': 10
        }
        self.logger = logger

    def _create_ssh_client(self, node_id: str) -> SSHClient:
        """Establish an SSH connection to the target node."""
        client = SSHClient()
        client.set_missing_host_key_policy(AutoAddPolicy())
        
        # Determine host from node_id (assuming node_id is IP or resolvable hostname)
        host = node_id
        
        try:
            client.connect(
                hostname=host,
                username=self.ssh_config.get('username', 'root'),
                password=self.ssh_config.get('password'),
                key_filename=self.ssh_config.get('key_filename'),
                timeout=self.ssh_config.get('timeout', 10)
            )
            self.logger.debug(f"SSH connected to {host}")
            return client
        except Exception as e:
            self.logger.error(f"SSH connection failed for {host}: {e}")
            raise

    def _terminate_process(self, client: SSHClient, pid: int, node_id: str) -> bool:
        """
        Attempt to kill a process by PID on the remote node.
        
        Args:
            client: Active SSHClient instance.
            pid: Process ID to kill.
            node_id: Identifier of the node (for logging).
            
        Returns:
            True if process was successfully killed, False otherwise.
        """
        try:
            # Send SIGKILL immediately for fast termination
            cmd = f"kill -9 {pid}"
            self.logger.info(f"Sending SIGKILL to PID {pid} on {node_id}")
            
            stdin, stdout, stderr = client.exec_command(cmd)
            exit_status = stdout.channel.recv_exit_status()
            
            if exit_status == 0:
                self.logger.info(f"Successfully sent kill signal to PID {pid} on {node_id}")
                return True
            else:
                error_msg = stderr.read().decode('utf-8', errors='ignore').strip()
                self.logger.warning(f"Kill command returned non-zero for PID {pid} on {node_id}: {error_msg}")
                return False
        except Exception as e:
            self.logger.error(f"Error executing kill command on {node_id}: {e}")
            return False

    def _verify_termination(self, client: SSHClient, pid: int, node_id: str) -> bool:
        """
        Verify that the process is no longer running.
        
        Args:
            client: Active SSHClient instance.
            pid: Process ID to check.
            node_id: Identifier of the node.
            
        Returns:
            True if process is confirmed dead, False if still running.
        """
        try:
            # Check if process exists
            cmd = f"ps -p {pid} > /dev/null 2>&1; echo $?"
            stdin, stdout, stderr = client.exec_command(cmd)
            exit_code_str = stdout.read().decode('utf-8', errors='ignore').strip()
            
            # Exit code 0 means process exists, 1 means it doesn't
            try:
                exit_code = int(exit_code_str)
                if exit_code != 0:
                    self.logger.info(f"Verified PID {pid} is terminated on {node_id}")
                    return True
                else:
                    self.logger.warning(f"PID {pid} still running on {node_id}")
                    return False
            except ValueError:
                self.logger.warning(f"Could not parse exit code for PID check on {node_id}: {exit_code_str}")
                return False
        except Exception as e:
            self.logger.error(f"Error verifying termination on {node_id}: {e}")
            return False

    def handle_signal(self, signal: NetworkSaturationSignal) -> List[TerminationResult]:
        """
        Main entry point to handle a NetworkSaturationSignal.
        
        This method performs the following actions:
        1. Iterates through all affected nodes.
        2. Attempts to terminate the benchmark process (SIGKILL).
        3. Verifies termination with retries (up to 3 attempts, 1s delay).
        4. Logs failures and raises NetworkSaturationError if any termination fails.
        
        Args:
            signal: The NetworkSaturationSignal containing node IDs and PIDs.
            
        Returns:
            List of TerminationResult objects.
            
        Raises:
            NetworkSaturationError: Always raised after handling to signal the orchestrator
                                   to abort the pipeline, unless all were successfully handled.
        """
        self.logger.error(f"Handling NetworkSaturationSignal: {signal}")
        results = []
        any_failed = False

        for node_id in signal.node_ids:
            pid = signal.benchmark_pids.get(node_id)
            if pid is None:
                self.logger.warning(f"No PID found for {node_id} in signal. Skipping termination.")
                results.append(TerminationResult(
                    node_id=node_id,
                    pid=0,
                    success=True,
                    message="No PID found",
                    attempts=0
                ))
                continue

            result = self._terminate_and_verify(node_id, pid)
            results.append(result)
            if not result.success:
                any_failed = True

        # Log summary
        success_count = sum(1 for r in results if r.success)
        total_count = len([r for r in results if r.pid > 0])
        self.logger.info(f"Termination summary: {success_count}/{total_count} processes terminated.")

        # ALWAYS raise NetworkSaturationError to signal the orchestrator to stop the pipeline
        # as per spec requirement: "Raise NetworkSaturationError exception to signal the orchestrator"
        if any_failed:
            raise NetworkSaturationError(
                f"Failed to terminate benchmark processes on {total_count - success_count} nodes.",
                run_id=signal.run_id,
                signal=signal
            )
        else:
            # Even if successful, we must raise the error to abort the run
            raise NetworkSaturationError(
                f"Network saturation detected (loss={signal.packet_loss_rate:.2%}). Aborting run {signal.run_id}.",
                run_id=signal.run_id,
                signal=signal
            )

    def _terminate_and_verify(self, node_id: str, pid: int) -> TerminationResult:
        """
        Attempt to terminate and verify a single process with retries.
        
        Args:
            node_id: Target node ID.
            pid: Process ID.
            
        Returns:
            TerminationResult.
        """
        client = None
        max_retries = 3
        delay = 1.0
        success = False
        last_error = "Unknown"

        try:
            client = self._create_ssh_client(node_id)
            
            for attempt in range(1, max_retries + 1):
                if attempt > 1:
                    self.logger.info(f"Retry {attempt}/{max_retries} for PID {pid} on {node_id}")
                    time.sleep(delay)

                # 1. Terminate
                if not self._terminate_process(client, pid, node_id):
                    last_error = "Kill command failed"
                    continue
                
                # 2. Verify
                if self._verify_termination(client, pid, node_id):
                    success = True
                    last_error = "Success"
                    break
                else:
                    last_error = "Process still running after kill"
                    continue

        except SSHException as e:
            last_error = f"SSH Error: {e}"
        except Exception as e:
            last_error = f"Unexpected Error: {e}"
        finally:
            if client:
                try:
                    client.close()
                except:
                    pass

        if success:
            return TerminationResult(
                node_id=node_id,
                pid=pid,
                success=True,
                message="Process terminated and verified",
                attempts=attempt
            )
        else:
            return TerminationResult(
                node_id=node_id,
                pid=pid,
                success=False,
                message=f"Failed after {max_retries} attempts: {last_error}",
                attempts=max_retries
            )


def create_handler(ssh_config: Optional[Dict[str, Any]] = None) -> NetworkSaturationHandler:
    """Factory function to create a NetworkSaturationHandler instance."""
    return NetworkSaturationHandler(ssh_config=ssh_config)


def main():
    """
    CLI entry point for testing the handler.
    Simulates receiving a signal and attempting to abort.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Test Network Saturation Handler")
    parser.add_argument("--node", type=str, required=True, help="Target node IP/hostname")
    parser.add_argument("--pid", type=int, required=True, help="PID to kill")
    parser.add_argument("--run-id", type=str, default="test-run", help="Run ID")
    parser.add_argument("--loss", type=float, default=0.25, help="Packet loss rate (e.g., 0.25)")
    parser.add_argument("--username", type=str, default="root", help="SSH username")
    parser.add_argument("--password", type=str, default=None, help="SSH password")
    
    args = parser.parse_args()
    
    signal = NetworkSaturationSignal(
        node_ids=[args.node],
        benchmark_pids={args.node: args.pid},
        run_id=args.run_id,
        packet_loss_rate=args.loss
    )
    
    handler = create_handler({
        'username': args.username,
        'password': args.password
    })
    
    try:
        handler.handle_signal(signal)
    except NetworkSaturationError as e:
        print(f"NetworkSaturationError raised as expected: {e}")
        print(f"Run ID: {e.run_id}")
        print(f"Error Code: {e.error_code}")
        return 0
    except Exception as e:
        print(f"Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
