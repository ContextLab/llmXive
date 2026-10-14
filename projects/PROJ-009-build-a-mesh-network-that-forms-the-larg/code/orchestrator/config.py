"""
Configuration manager for the mesh network supercomputer.
Provides both the original Config dataclass (used by runtime code) and
a ConfigManager class (used by unit tests) together with a simple
ConfigError exception and convenience loader.
"""
import os
import yaml
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional

# ----------------------------------------------------------------------
# Original Config dataclass (kept for backward compatibility)
# ----------------------------------------------------------------------
@dataclass
class Config:
    """Holds all project configuration for runtime code."""
    project_root: Path
    node_list_path: Path
    granularity_settings: Dict[str, int]
    ci_timeout_seconds: int
    max_retries: int
    ssh_key_path: Optional[Path]
    log_level: str = "INFO"
    data_dir: Path = field(default_factory=lambda: Path("data"))

    @classmethod
    def load(cls, config_path: Optional[Path] = None) -> 'Config':
        """Load configuration from a YAML file or defaults."""
        if config_path is None:
            config_path = Path("config.yaml")

        if not config_path.exists():
            return cls(
                project_root=Path.cwd(),
                node_list_path=Path("nodes.yaml"),
                granularity_settings={
                    "fine": 100,
                    "medium": 1000,
                    "coarse": 10000
                },
                ci_timeout_seconds=21600,
                max_retries=3,
                ssh_key_path=Path("~/.ssh/id_rsa").expanduser(),
                log_level="INFO",
                data_dir=Path("data")
            )

        with open(config_path, 'r') as f:
            data = yaml.safe_load(f) or {}

        base_dir = config_path.parent if config_path.is_absolute() else Path.cwd()

        project_root = Path(data.get('project_root', '.'))
        if not project_root.is_absolute():
            project_root = base_dir / project_root

        node_list_path = Path(data.get('node_list_path', 'nodes.yaml'))
        if not node_list_path.is_absolute():
            node_list_path = base_dir / node_list_path

        data_dir = Path(data.get('data_dir', 'data'))
        if not data_dir.is_absolute():
            data_dir = base_dir / data_dir

        ssh_key_path = data.get('ssh_key_path')
        if ssh_key_path:
            ssh_key_path = Path(ssh_key_path).expanduser()
            if not ssh_key_path.is_absolute():
                ssh_key_path = base_dir / ssh_key_path

        return cls(
            project_root=project_root,
            node_list_path=node_list_path,
            granularity_settings=data.get('granularity_settings', {
                "fine": 100,
                "medium": 1000,
                "coarse": 10000
            }),
            ci_timeout_seconds=data.get('ci_timeout_seconds', 21600),
            max_retries=data.get('max_retries', 3),
            ssh_key_path=ssh_key_path,
            log_level=data.get('log_level', 'INFO'),
            data_dir=data_dir
        )

def get_config() -> Config:
    """Global accessor for configuration."""
    return Config.load()

def save_config(config: Config, path: Optional[Path] = None) -> None:
    """Save the current configuration to a YAML file."""
    if path is None:
        path = Path("config.yaml")
    data = {
        'project_root': str(config.project_root),
        'node_list_path': str(config.node_list_path),
        'granularity_settings': config.granularity_settings,
        'ci_timeout_seconds': config.ci_timeout_seconds,
        'max_retries': config.max_retries,
        'ssh_key_path': str(config.ssh_key_path) if config.ssh_key_path else None,
        'log_level': config.log_level,
        'data_dir': str(config.data_dir)
    }
    with open(path, 'w') as f:
        yaml.dump(data, f, default_flow_style=False)

# ----------------------------------------------------------------------
# Test‑oriented configuration manager
# ----------------------------------------------------------------------
class ConfigError(Exception):
    """Raised for any configuration validation problem."""
    pass

class ConfigManager:
    """
    Loads a YAML configuration file and provides convenient accessor methods
    used by the unit‑test suite.
    """

    def __init__(self, config_path: str):
        self.path = Path(config_path)
        if not self.path.exists():
            raise ConfigError("Configuration file not found")
        try:
            with open(self.path, 'r') as f:
                self._data = yaml.safe_load(f) or {}
        except Exception as exc:
            raise ConfigError(f"Failed to parse YAML: {exc}") from exc

        self._validate()

    # ------------------------------------------------------------------
    # Validation helpers
    # ------------------------------------------------------------------
    def _validate(self) -> None:
        # Nodes
        nodes = self._data.get('nodes')
        if not nodes:
            raise ConfigError("No nodes configured")
        for idx, node in enumerate(nodes):
            if 'id' not in node:
                raise ConfigError(f"Node at index {idx} missing required 'id'")
            if 'host' not in node:
                raise ConfigError(f"Node at index {idx} missing required 'host'")

        # Granularity
        gran = self._data.get('granularity')
        if not gran:
            raise ConfigError("Missing granularity settings")
        for key in ('fine', 'medium', 'coarse'):
            if key not in gran:
                raise ConfigError(f"Missing granularity key '{key}'")
            if not isinstance(gran[key], int) or gran[key] <= 0:
                raise ConfigError("Granularity values must be positive integers")

        # CI timeout
        ci = self._data.get('ci_timeout')
        if not ci or 'seconds' not in ci:
            raise ConfigError("Missing 'ci_timeout.seconds'")
        if not isinstance(ci['seconds'], (int, float)) or ci['seconds'] <= 0:
            raise ConfigError("CI timeout must be a positive number")

        # Pipeline timeout
        pl = self._data.get('pipeline_timeout')
        if not pl or 'seconds' not in pl:
            raise ConfigError("Missing 'pipeline_timeout.seconds'")
        if not isinstance(pl['seconds'], (int, float)) or pl['seconds'] <= 0:
            raise ConfigError("Pipeline timeout must be a positive number")

        # Node count range
        ncr = self._data.get('node_count_range')
        if not ncr:
            raise ConfigError("Missing node_count_range")
        for key in ('min', 'max', 'step'):
            if key not in ncr:
                raise ConfigError(f"node_count_range missing '{key}'")
            if not isinstance(ncr[key], int) or ncr[key] <= 0:
                raise ConfigError(f"node_count_range.{key} must be a positive integer")

        # Paths
        paths = self._data.get('paths')
        if not paths:
            raise ConfigError("Missing paths configuration")
        for key in ('raw_data', 'processed_data', 'figures'):
            if key not in paths:
                raise ConfigError(f"paths missing '{key}'")

    # ------------------------------------------------------------------
    # Public accessor methods used by the test suite
    # ------------------------------------------------------------------
    def get_nodes(self) -> List[Dict[str, Any]]:
        return self._data['nodes']

    def get_granularity_settings(self) -> Dict[str, int]:
        return self._data['granularity']

    def get_ci_timeout(self) -> int:
        return int(self._data['ci_timeout']['seconds'])

    def get_pipeline_timeout(self) -> int:
        return int(self._data['pipeline_timeout']['seconds'])

    def get_node_count_range(self) -> Dict[str, int]:
        return self._data['node_count_range']

    def get_raw_data_path(self) -> str:
        return self._data['paths']['raw_data']

    def get_processed_data_path(self) -> str:
        return self._data['paths']['processed_data']

    def get_figures_path(self) -> str:
        return self._data['paths']['figures']

def load_config(config_path: str) -> ConfigManager:
    """Convenient function used by tests."""
    return ConfigManager(config_path)
