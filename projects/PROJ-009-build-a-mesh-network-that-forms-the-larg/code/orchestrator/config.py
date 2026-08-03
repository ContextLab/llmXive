"""
Configuration manager for the mesh network supercomputer.
Loads node lists, granularity settings, and CI timeouts.
"""
import os
import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field

@dataclass
class Config:
    """Holds all project configuration."""
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

        # Resolve relative to project root if a file exists, otherwise use defaults
        if not config_path.exists():
            # Return a default config if no file exists
            return cls(
                project_root=Path.cwd(),
                node_list_path=Path("nodes.yaml"),
                granularity_settings={
                    "fine": 100,
                    "medium": 1000,
                    "coarse": 10000
                },
                ci_timeout_seconds=21600,  # 6 hours
                max_retries=3,
                ssh_key_path=Path("~/.ssh/id_rsa").expanduser(),
                log_level="INFO",
                data_dir=Path("data")
            )

        with open(config_path, 'r') as f:
            data = yaml.safe_load(f)

        if data is None:
            # Handle empty YAML file
            data = {}

        # Resolve paths relative to the config file location if provided
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
    """Global accessor for configuration.
    
    Returns:
        Config: The loaded or default configuration instance.
    """
    return Config.load()

def save_config(config: Config, path: Optional[Path] = None) -> None:
    """Save the current configuration to a YAML file.
    
    Args:
        config: The Config instance to save.
        path: Optional path to save to. Defaults to 'config.yaml'.
    """
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