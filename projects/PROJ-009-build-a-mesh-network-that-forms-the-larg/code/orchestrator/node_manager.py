from __future__ import annotations

import logging
import threading
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any, Dict, Generator, List, Optional

import paramiko

from orchestrator.config import ProjectConfig, load_config
from orchestrator.logger import get_logger
from orchestrator.models import NodeStatus, PhysicalNode

# Constants for connection management
DEFAULT_HEARTBEAT_INTERVAL = 30.0  # seconds
DEFAULT_TIMEOUT = 5.0  # seconds for connection/operations
DEFAULT_MAX_RETRIES = 3
HEARTBEAT_CMD = "echo 'heartbeat'"

@dataclass
class SSHConnection:
    """Wrapper for a single active SSH client connection."""
    client: paramiko.SSHClient
    node_id: str
    last_heartbeat: float = field(default_factory=time.time)
    last_used: float = field(default_factory=time.time)
    is_healthy: bool = True
    lock: threading.Lock = field(default_factory=threading.Lock)

    def mark_used(self) -> None:
        self.last_used = time.time()

    def check_heartbeat(self, timeout: float = DEFAULT_TIMEOUT) -> bool:
        """
        Execute a simple command to verify the connection is alive.
        Returns True if successful, False otherwise.
        """
        try:
            with self.lock:
                stdin, stdout, stderr = self.client.exec_command(
                    HEARTBEAT_CMD, timeout=timeout
                )
                exit_status = stdout.channel.recv_exit_status()
                if exit_status == 0:
                    self.last_heartbeat = time.time()
                    self.is_healthy = True
                    return True
                else:
                    self.is_healthy = False
                    return False
        except (paramiko.SSHException, OSError, TimeoutError) as e:
            logging.getLogger(__name__).warning(
                f"Heartbeat failed for {self.node_id}: {e}"
            )
            self.is_healthy = False
            return False

class NodeManager:
    """
    Manages a pool of SSH connections to physical nodes.
    Handles connection pooling, heartbeat monitoring, and timeout logic.
    """

    def __init__(
        self,
        config: Optional[ProjectConfig] = None,
        heartbeat_interval: float = DEFAULT_HEARTBEAT_INTERVAL,
        connection_timeout: float = DEFAULT_TIMEOUT,
    ):
        self.logger = get_logger(__name__)
        self.config = config or load_config()
        self.heartbeat_interval = heartbeat_interval
        self.connection_timeout = connection_timeout

        # Pool of active connections: node_id -> SSHConnection
        self._pool: Dict[str, SSHConnection] = {}
        self._lock = threading.Lock()
        self._heartbeat_thread: Optional[threading.Thread] = None
        self._stop_heartbeat = threading.Event()

    def _create_connection(self, node: PhysicalNode) -> SSHConnection:
        """Establish a new SSH connection to a node."""
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:
            client.connect(
                hostname=node.host,
                port=node.port,
                username=node.username,
                password=node.password, # In production, use keys
                key_filename=node.ssh_key_path,
                timeout=self.connection_timeout,
                allow_agent=False,
                look_for_keys=False,
            )
            self.logger.info(f"Successfully connected to node {node.node_id}")
            return SSHConnection(
                client=client,
                node_id=node.node_id,
            )
        except paramiko.AuthenticationException:
            self.logger.error(f"Authentication failed for node {node.node_id}")
            raise
        except paramiko.SSHException as e:
            self.logger.error(f"SSH error connecting to node {node.node_id}: {e}")
            raise
        except OSError as e:
            self.logger.error(f"Network error connecting to node {node.node_id}: {e}")
            raise

    def get_connection(self, node: PhysicalNode) -> SSHConnection:
        """
        Retrieve an existing healthy connection or create a new one.
        Thread-safe.
        """
        with self._lock:
            if node.node_id in self._pool:
                conn = self._pool[node.node_id]
                if conn.is_healthy:
                    conn.mark_used()
                    return conn
                else:
                    # Connection is unhealthy, close and remove
                    self.logger.warning(
                        f"Closing unhealthy connection for {node.node_id} before re-creating."
                    )
                    try:
                        conn.client.close()
                    except Exception:
                        pass
                    del self._pool[node.node_id]

            # Create new connection
            try:
                conn = self._create_connection(node)
                self._pool[node.node_id] = conn
                return conn
            except Exception as e:
                self.logger.error(f"Failed to create connection for {node.node_id}: {e}")
                raise

    def release_connection(self, node_id: str) -> None:
        """
        Return a connection to the pool.
        In a simple pool, we just keep it alive unless explicitly closed.
        """
        with self._lock:
            if node_id in self._pool:
                self._pool[node_id].mark_used()

    def close_connection(self, node_id: str) -> None:
        """Explicitly close and remove a connection from the pool."""
        with self._lock:
            if node_id in self._pool:
                conn = self._pool[node_id]
                try:
                    conn.client.close()
                    self.logger.info(f"Closed connection for {node_id}")
                except Exception as e:
                    self.logger.warning(f"Error closing connection for {node_id}: {e}")
                finally:
                    del self._pool[node_id]

    def close_all(self) -> None:
        """Close all connections in the pool."""
        with self._lock:
            for node_id in list(self._pool.keys()):
                self.close_connection(node_id)

    def start_heartbeat_monitor(self) -> None:
        """Start the background thread that monitors connection health."""
        if self._heartbeat_thread is not None and self._heartbeat_thread.is_alive():
            return

        self._stop_heartbeat.clear()
        self._heartbeat_thread = threading.Thread(
            target=self._heartbeat_loop, daemon=True
        )
        self._heartbeat_thread.start()
        self.logger.info("Heartbeat monitor started")

    def stop_heartbeat_monitor(self) -> None:
        """Stop the background heartbeat monitor."""
        self._stop_heartbeat.set()
        if self._heartbeat_thread is not None:
            self._heartbeat_thread.join(timeout=self.heartbeat_interval + 5)
            self.logger.info("Heartbeat monitor stopped")

    def _heartbeat_loop(self) -> None:
        """Background loop to check heartbeats on all pooled connections."""
        while not self._stop_heartbeat.is_set():
            try:
                with self._lock:
                    nodes_to_check = list(self._pool.keys())
                
                for node_id in nodes_to_check:
                    if self._stop_heartbeat.is_set():
                        break
                    
                    conn = self._pool.get(node_id)
                    if conn:
                        # Check if enough time has passed since last heartbeat
                        if time.time() - conn.last_heartbeat >= self.heartbeat_interval:
                            is_healthy = conn.check_heartbeat(timeout=self.connection_timeout)
                            if not is_healthy:
                                self.logger.warning(
                                    f"Node {node_id} failed heartbeat. Marking unhealthy."
                                )
                                # Optional: remove from pool if we want to force reconnect on next use
                                # self.close_connection(node_id) 
            except Exception as e:
                self.logger.error(f"Error in heartbeat loop: {e}")
            
            # Sleep in small increments to allow quick shutdown
            for _ in range(int(self.heartbeat_interval)):
                if self._stop_heartbeat.is_set():
                    break
                time.sleep(1)

    @contextmanager
    def get_connection_context(self, node: PhysicalNode) -> Generator[paramiko.SSHClient, None, None]:
        """
        Context manager to get a connection and ensure it is released (or kept in pool) properly.
        Yields the raw paramiko.SSHClient for the caller to execute commands.
        """
        conn = self.get_connection(node)
        try:
            yield conn.client
            self.release_connection(node.node_id)
        except Exception as e:
            self.logger.error(f"Error using connection for {node.node_id}: {e}")
            conn.is_healthy = False
            raise

    def execute_command(
        self,
        node: PhysicalNode,
        command: str,
        timeout: Optional[float] = None,
    ) -> tuple[int, str, str]:
        """
        Execute a command on a node and return (exit_code, stdout, stderr).
        Handles connection lifecycle.
        """
        if timeout is None:
            timeout = self.connection_timeout * 2 # Default command timeout

        conn = self.get_connection(node)
        try:
            with conn.lock:
                stdin, stdout, stderr = conn.client.exec_command(
                    command, timeout=timeout
                )
                exit_status = stdout.channel.recv_exit_status()
                out = stdout.read().decode("utf-8", errors="replace")
                err = stderr.read().decode("utf-8", errors="replace")
                conn.mark_used()
                return exit_status, out, err
        except (paramiko.SSHException, OSError, TimeoutError) as e:
            self.logger.error(f"Command execution failed on {node.node_id}: {e}")
            conn.is_healthy = False
            raise
        finally:
            self.release_connection(node.node_id)

    def is_node_available(self, node: PhysicalNode) -> bool:
        """Check if a node is currently available (healthy connection exists)."""
        with self._lock:
            if node.node_id not in self._pool:
                return False
            return self._pool[node.node_id].is_healthy

    def __enter__(self) -> "NodeManager":
        self.start_heartbeat_monitor()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.stop_heartbeat_monitor()
        self.close_all()

def create_node_manager(
    config_path: Optional[str] = None,
    heartbeat_interval: float = DEFAULT_HEARTBEAT_INTERVAL,
) -> NodeManager:
    """
    Factory function to create a NodeManager instance.
    """
    config = load_config(config_path) if config_path else load_config()
    return NodeManager(
        config=config,
        heartbeat_interval=heartbeat_interval,
    )
