"""
Mock SSH Node Generator for CI Unit Tests.

This module provides a deterministic, stateless mock environment to simulate
SSH connections to physical nodes in the mesh network. It allows the
orchestrator and scheduler logic to be tested in CI without requiring
real hardware or network access.

The mock generator simulates:
- Node discovery (list of available nodes with IDs, IP placeholders, and specs)
- SSH connection establishment (mocked context manager)
- Remote command execution (simulating mpstat, tcpdump, and benchmark scripts)
- Node heartbeat responses
- Controlled failure modes (random disconnects, high latency, OOM) for robustness testing

Usage:
    from code.tests.unit.mock_nodes import MockNodeManager

    manager = MockNodeManager(node_count=5)
    with manager.connect("node-001") as conn:
        result = conn.run("mpstat -P ALL 1 1")
        print(result.stdout)
"""

import random
import time
from dataclasses import dataclass
from typing import List, Dict, Optional, Callable, Any
from contextlib import contextmanager
import io
import sys

# Simulated mpstat output template
MPSTAT_TEMPLATE = """Linux 5.15.0-generic (mock-node-{node_id}) 	{timestamp} 	_x86_64_	(8 CPU)

03:45:12 PM     CPU     %usr     %nice      %sys %iowait    %irq   %soft  %steal  %guest  %gnice   %idle
03:45:13 PM     all     15.25      0.00      2.10      0.50      0.00      0.10      0.00      0.00      0.00     82.05
03:45:13 PM       0     18.50      0.00      3.20      0.20      0.00      0.10      0.00      0.00      0.00     78.00
03:45:13 PM       1     12.00      0.00      1.00      0.80      0.00      0.00      0.00      0.00      0.00     86.20
03:45:13 PM       2     22.10      0.00      4.50      0.10      0.00      0.20      0.00      0.00      0.00     73.10
03:45:13 PM       3      5.00      0.00      0.50      1.00      0.00      0.00      0.00      0.00      0.00     93.50
"""

# Simulated tcpdump summary template
TCPDUMP_TEMPLATE = """{count} packets received by filter
0 packets dropped by kernel"""

@dataclass
class MockNodeSpec:
    """Defines the static properties of a simulated node."""
    node_id: str
    ip_address: str
    cpu_cores: int
    ram_gb: int
    is_online: bool = True
    latency_ms: float = 0.0
    should_fail: bool = False
    failure_type: Optional[str] = None  # 'connection', 'timeout', 'oom', 'packet_loss'

class MockSSHConnection:
    """Simulates an active SSH session."""

    def __init__(self, node_spec: MockNodeSpec, config: Dict[str, Any]):
        self.node_spec = node_spec
        self.config = config
        self.is_open = False
        self._fail_counter = 0

    def __enter__(self):
        # Simulate connection delay
        if self.node_spec.should_fail and self.node_spec.failure_type == 'connection':
            raise ConnectionRefusedError(f"Mock connection refused to {self.node_spec.node_id}")
        
        # Simulate network latency
        if self.node_spec.latency_ms > 0:
            time.sleep(self.node_spec.latency_ms / 1000.0)

        self.is_open = True
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.is_open = False
        return False

    def run(self, command: str, timeout: int = 60) -> 'MockResult':
        """Simulates running a command on the remote node."""
        if not self.is_open:
            raise RuntimeError("Connection is not open")

        # Simulate processing time based on command
        if "mpstat" in command:
            delay = 0.1 + (random.random() * 0.05)
        elif "tcpdump" in command:
            delay = 0.2 + (random.random() * 0.1)
        elif "benchmark" in command:
            delay = 1.0 + (random.random() * 0.5)
        else:
            delay = 0.01

        # Simulate latency
        if self.node_spec.latency_ms > 0:
            delay += self.node_spec.latency_ms / 1000.0

        time.sleep(delay)

        # Check for simulated failures
        if self.node_spec.should_fail:
            if self.node_spec.failure_type == 'timeout':
                raise TimeoutError(f"Mock command timed out after {timeout}s")
            if self.node_spec.failure_type == 'oom':
                raise MemoryError(f"Mock OOM on {self.node_spec.node_id}")
            if self.node_spec.failure_type == 'packet_loss':
                # Return partial data or error
                if random.random() < 0.5:
                    raise RuntimeError("Mock packet loss: connection reset")

        return self._generate_result(command)

    def _generate_result(self, command: str) -> 'MockResult':
        """Generates a realistic-looking stdout/stderr based on the command."""
        timestamp = time.strftime("%I:%M:%S %p", time.localtime())
        
        if "mpstat" in command:
            stdout = MPSTAT_TEMPLATE.format(node_id=self.node_spec.node_id.split('-')[-1], timestamp=timestamp)
            stderr = ""
            exit_code = 0
        elif "tcpdump" in command:
            # Simulate packet counts based on "load"
            packet_count = random.randint(100, 5000)
            stdout = TCPDUMP_TEMPLATE.format(count=packet_count)
            stderr = ""
            exit_code = 0
        elif "benchmark" in command:
            # Simulate a benchmark result
            result_value = random.uniform(0.8, 1.2)
            stdout = f"Monte Carlo Integration Result: {result_value:.6f}\nIterations: 1000000\nStatus: Success"
            stderr = ""
            exit_code = 0
        else:
            stdout = f"Mock output for command: {command}"
            stderr = ""
            exit_code = 0

        return MockResult(stdout=stdout, stderr=stderr, exit_code=exit_code)

class MockResult:
    """Simulates the result of a remote command execution."""
    def __init__(self, stdout: str, stderr: str, exit_code: int):
        self.stdout = stdout
        self.stderr = stderr
        self.exit_code = exit_code

class MockNodeManager:
    """
    Mock implementation of the Node Manager for unit testing.
    
    This class replaces the real SSH-based node manager to allow CI tests
    to run without network dependencies. It generates a pool of mock nodes
    and manages simulated connections.
    """

    def __init__(self, node_count: int = 5, seed: int = 42):
        self.seed = seed
        random.seed(seed)
        self.nodes: List[MockNodeSpec] = []
        self._generate_nodes(node_count)

    def _generate_nodes(self, count: int):
        """Generates a list of mock node specifications."""
        for i in range(count):
            node_id = f"node-{i:03d}"
            # Randomize specs slightly to simulate heterogeneity
            cores = random.choice([4, 8, 12, 16])
            ram = random.choice([8, 16, 32, 64])
            
            # 10% chance of being offline or having issues
            is_online = random.random() > 0.1
            should_fail = random.random() < 0.05
            failure_type = None
            if should_fail:
                failure_type = random.choice(['connection', 'timeout', 'oom', 'packet_loss'])

            node = MockNodeSpec(
                node_id=node_id,
                ip_address=f"192.168.1.{100 + i}",
                cpu_cores=cores,
                ram_gb=ram,
                is_online=is_online,
                latency_ms=random.uniform(1, 50) if is_online else 0,
                should_fail=should_fail,
                failure_type=failure_type
            )
            self.nodes.append(node)

    def discover_nodes(self) -> List[MockNodeSpec]:
        """Returns the list of available nodes."""
        return [n for n in self.nodes if n.is_online]

    @contextmanager
    def connect(self, node_id: str):
        """
        Context manager to simulate an SSH connection to a specific node.
        
        Args:
            node_id: The ID of the node to connect to (e.g., 'node-001').
        
        Yields:
            MockSSHConnection: A simulated SSH connection object.
        
        Raises:
            ValueError: If the node_id is not found.
            ConnectionRefusedError: If the node is offline or configured to fail.
        """
        target_node = next((n for n in self.nodes if n.node_id == node_id), None)
        if not target_node:
            raise ValueError(f"Node {node_id} not found in mock registry")
        
        if not target_node.is_online:
            raise ConnectionRefusedError(f"Node {node_id} is offline")

        conn = MockSSHConnection(target_node, {})
        yield conn

    def get_node_stats(self, node_id: str) -> Dict[str, Any]:
        """
        Retrieves static stats for a node without establishing a connection.
        Useful for pre-flight checks.
        """
        node = next((n for n in self.nodes if n.node_id == node_id), None)
        if not node:
            raise ValueError(f"Node {node_id} not found")
        
        return {
            "node_id": node.node_id,
            "cpu_cores": node.cpu_cores,
            "ram_gb": node.ram_gb,
            "is_online": node.is_online
        }

    def set_failure_mode(self, node_id: str, fail: bool, mode: Optional[str] = None):
        """
        Programmatically sets a node to simulate a failure.
        
        Args:
            node_id: The ID of the node.
            fail: True to enable failure mode.
            mode: The type of failure ('connection', 'timeout', 'oom', 'packet_loss').
        """
        node = next((n for n in self.nodes if n.node_id == node_id), None)
        if node:
            node.should_fail = fail
            if mode:
                node.failure_type = mode