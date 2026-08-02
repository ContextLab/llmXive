"""
Configuration Manager for the Mesh Network Supercomputer.

Loads and validates YAML configuration files for:
- Node lists (PhysicalNode definitions)
- Granularity settings (task chunk sizes)
- Network parameters (latency, bandwidth thresholds, etc.)
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from orchestrator.models import PhysicalNode


@dataclass
class NetworkConfig:
    """Network parameters for the mesh supercomputer."""
    default_latency_ms: float = 0.0
    default_bandwidth_mbps: float = 1000.0
    packet_loss_threshold: float = 0.02  # 2%
    heartbeat_timeout_seconds: float = 30.0
    max_retries: int = 3
    ssh_port: int = 22
    ssh_timeout_seconds: float = 10.0


@dataclass
class GranularityConfig:
    """Settings for task chunk granularity."""
    fine_chunk_size: int = 100
    medium_chunk_size: int = 1000
    coarse_chunk_size: int = 10000
    default_granularity: str = "medium"  # "fine", "medium", "coarse"

    def get_chunk_size(self, granularity: Optional[str] = None) -> int:
        """Get chunk size for a specific granularity level."""
        level = granularity or self.default_granularity
        if level == "fine":
            return self.fine_chunk_size
        elif level == "medium":
            return self.medium_chunk_size
        elif level == "coarse":
            return self.coarse_chunk_size
        else:
            raise ValueError(f"Unknown granularity level: {level}")


@dataclass
class OrchestratorConfig:
    """Main orchestrator configuration."""
    run_id: str = "default_run"
    data_dir: str = "data"
    log_dir: str = "data/raw"
    output_dir: str = "data/processed"
    max_concurrent_nodes: int = 10
    hard_timeout_hours: float = 6.0  # FR-007
    straggler_timeout_multiplier: float = 2.0  # 2x median task time


@dataclass
class ProjectConfig:
    """Complete project configuration."""
    nodes: List[PhysicalNode] = field(default_factory=list)
    network: NetworkConfig = field(default_factory=NetworkConfig)
    granularity: GranularityConfig = field(default_factory=GranularityConfig)
    orchestrator: OrchestratorConfig = field(default_factory=OrchestratorConfig)

    def get_node(self, node_id: str) -> Optional[PhysicalNode]:
        """Get a specific node by ID."""
        for node in self.nodes:
            if node.node_id == node_id:
                return node
        return None

    def get_available_nodes(self) -> List[PhysicalNode]:
        """Get all nodes that are currently available."""
        return [node for node in self.nodes if node.status.value == "available"]


class ConfigManager:
    """
    Manages loading and validation of YAML configuration files.

    Expected YAML structure:
    ```yaml
    nodes:
      - node_id: "node-001"
        hostname: "192.168.1.10"
        username: "researcher"
        hardware_spec:
          cpu_cores: 8
          memory_gb: 32
          gpu: "NVIDIA A100"
        status: "available"

    network:
      default_latency_ms: 5.0
      default_bandwidth_mbps: 1000.0
      packet_loss_threshold: 0.02

    granularity:
      fine_chunk_size: 100
      medium_chunk_size: 1000
      coarse_chunk_size: 10000
      default_granularity: "medium"

    orchestrator:
      run_id: "experiment-001"
      data_dir: "data"
      max_concurrent_nodes: 10
      hard_timeout_hours: 6.0
    ```
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the ConfigManager.

        Args:
            config_path: Path to the YAML configuration file.
                        If None, attempts to load from default locations.
        """
        self.config_path = config_path
        self._config: Optional[ProjectConfig] = None

    def load(self, config_path: Optional[str] = None) -> ProjectConfig:
        """
        Load and parse the configuration file.

        Args:
            config_path: Optional override for the config file path.

        Returns:
            ProjectConfig: The validated configuration object.

        Raises:
            FileNotFoundError: If the config file does not exist.
            ValueError: If the configuration is invalid.
        """
        path = config_path or self.config_path

        if path is None:
            # Try default locations
            default_paths = [
                "config/mesh_config.yaml",
                "config/config.yaml",
                "mesh_config.yaml",
                "config.yaml"
            ]
            for default in default_paths:
                if os.path.exists(default):
                    path = default
                    break

        if path is None or not os.path.exists(path):
            raise FileNotFoundError(
                f"Configuration file not found. "
                f"Expected at: {self.config_path} or default locations."
            )

        with open(path, "r", encoding="utf-8") as f:
            raw_config = yaml.safe_load(f)

        if raw_config is None:
            raise ValueError("Configuration file is empty or invalid YAML.")

        self._config = self._parse_config(raw_config)
        return self._config

    def _parse_config(self, raw: Dict[str, Any]) -> ProjectConfig:
        """Parse raw dictionary into strongly-typed config objects."""
        # Parse nodes
        nodes = []
        if "nodes" in raw:
            for node_data in raw["nodes"]:
                # Ensure hardware_spec is a dict
                hardware = node_data.get("hardware_spec", {})
                if isinstance(hardware, dict):
                    node = PhysicalNode(
                        node_id=node_data["node_id"],
                        hostname=node_data.get("hostname", "localhost"),
                        username=node_data.get("username", "root"),
                        hardware_spec=hardware,
                        status=node_data.get("status", "available")
                    )
                    nodes.append(node)

        # Parse network config
        network_raw = raw.get("network", {})
        network = NetworkConfig(
            default_latency_ms=network_raw.get("default_latency_ms", 0.0),
            default_bandwidth_mbps=network_raw.get("default_bandwidth_mbps", 1000.0),
            packet_loss_threshold=network_raw.get("packet_loss_threshold", 0.02),
            heartbeat_timeout_seconds=network_raw.get("heartbeat_timeout_seconds", 30.0),
            max_retries=network_raw.get("max_retries", 3),
            ssh_port=network_raw.get("ssh_port", 22),
            ssh_timeout_seconds=network_raw.get("ssh_timeout_seconds", 10.0)
        )

        # Parse granularity config
        granularity_raw = raw.get("granularity", {})
        granularity = GranularityConfig(
            fine_chunk_size=granularity_raw.get("fine_chunk_size", 100),
            medium_chunk_size=granularity_raw.get("medium_chunk_size", 1000),
            coarse_chunk_size=granularity_raw.get("coarse_chunk_size", 10000),
            default_granularity=granularity_raw.get("default_granularity", "medium")
        )

        # Parse orchestrator config
        orchestrator_raw = raw.get("orchestrator", {})
        orchestrator = OrchestratorConfig(
            run_id=orchestrator_raw.get("run_id", "default_run"),
            data_dir=orchestrator_raw.get("data_dir", "data"),
            log_dir=orchestrator_raw.get("log_dir", "data/raw"),
            output_dir=orchestrator_raw.get("output_dir", "data/processed"),
            max_concurrent_nodes=orchestrator_raw.get("max_concurrent_nodes", 10),
            hard_timeout_hours=orchestrator_raw.get("hard_timeout_hours", 6.0),
            straggler_timeout_multiplier=orchestrator_raw.get(
                "straggler_timeout_multiplier", 2.0
            )
        )

        return ProjectConfig(
            nodes=nodes,
            network=network,
            granularity=granularity,
            orchestrator=orchestrator
        )

    def get_config(self) -> ProjectConfig:
        """
        Get the loaded configuration.

        Returns:
            ProjectConfig: The current configuration.

        Raises:
            RuntimeError: If configuration has not been loaded yet.
        """
        if self._config is None:
            raise RuntimeError("Configuration not loaded. Call load() first.")
        return self._config

    def reload(self) -> ProjectConfig:
        """Reload the configuration from the file."""
        return self.load(self.config_path)


def load_config(config_path: Optional[str] = None) -> ProjectConfig:
    """
    Convenience function to load configuration.

    Args:
        config_path: Path to the YAML configuration file.

    Returns:
        ProjectConfig: The loaded and validated configuration.
    """
    manager = ConfigManager(config_path)
    return manager.load()
