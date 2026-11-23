import os
import json
from pathlib import Path
from typing import Any, Dict, Optional, List
from dataclasses import dataclass, field
from .logging_config import get_logger, fail_loudly

@dataclass
class ProjectConfig:
    """Project configuration container."""
    project_root: Path
    data_dir: Path
    code_dir: Path
    tests_dir: Path
    docs_dir: Path
    state_dir: Path
    processed_data_dir: Path
    raw_data_dir: Path
    
    # Feature extraction settings
    max_frames_per_clip: int = 100
    frame_subsampling_rate: int = 1
    temporal_chunk_size: int = 50
    
    # Physics simulation settings
    gravity: float = 9.81
    simulation_steps: int = 100
    collision_threshold: float = 0.01
    
    # Data fetch settings
    fetch_retries: int = 3
    fetch_base_delay: float = 2.0
    fetch_max_delay: float = 30.0
    
    # Labeling settings
    confidence_threshold: float = 0.9
    correlation_threshold: float = 0.1
    
    def __post_init__(self):
        """Ensure all paths are Path objects and exist."""
        self.project_root = Path(self.project_root)
        self.data_dir = Path(self.data_dir)
        self.code_dir = Path(self.code_dir)
        self.tests_dir = Path(self.tests_dir)
        self.docs_dir = Path(self.docs_dir)
        self.state_dir = Path(self.state_dir)
        self.processed_data_dir = Path(self.processed_data_dir)
        self.raw_data_dir = Path(self.raw_data_dir)
        
        # Create directories if they don't exist
        for path in [self.data_dir, self.code_dir, self.tests_dir, 
                    self.docs_dir, self.state_dir, 
                    self.processed_data_dir, self.raw_data_dir]:
            path.mkdir(parents=True, exist_ok=True)

def load_env_config(env_file: Optional[str] = None) -> Dict[str, Any]:
    """
    Load configuration from environment variables or a file.
    
    Args:
        env_file: Optional path to environment file.
    
    Returns:
        Dictionary of configuration values.
    """
    config = {}
    
    # Try to load from file
    if env_file and Path(env_file).exists():
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    config[key.strip()] = value.strip()
    
    # Override with environment variables
    for key in list(config.keys()):
        env_value = os.getenv(key)
        if env_value is not None:
            config[key] = env_value
    
    return config

def initialize_project_config(config_file: Optional[str] = None) -> ProjectConfig:
    """
    Initialize project configuration from file or defaults.
    
    Args:
        config_file: Optional path to configuration file.
    
    Returns:
        Initialized ProjectConfig instance.
    """
    logger = get_logger('config')
    
    # Default paths
    project_root = Path.cwd()
    config_data = {
        'data_dir': 'data',
        'code_dir': 'code',
        'tests_dir': 'tests',
        'docs_dir': 'docs',
        'state_dir': 'state',
        'processed_data_dir': 'data/processed',
        'raw_data_dir': 'data/raw',
    }
    
    # Load from file if exists
    if config_file and Path(config_file).exists():
        with open(config_file, 'r') as f:
            file_config = json.load(f)
            config_data.update(file_config)
    
    # Override with environment variables
    env_config = load_env_config()
    config_data.update(env_config)
    
    try:
        config = ProjectConfig(
            project_root=project_root,
            data_dir=project_root / config_data['data_dir'],
            code_dir=project_root / config_data['code_dir'],
            tests_dir=project_root / config_data['tests_dir'],
            docs_dir=project_root / config_data['docs_dir'],
            state_dir=project_root / config_data['state_dir'],
            processed_data_dir=project_root / config_data['processed_data_dir'],
            raw_data_dir=project_root / config_data['raw_data_dir'],
        )
        
        logger.info(f"Project configuration initialized at {project_root}")
        return config
    except Exception as e:
        fail_loudly(f"Failed to initialize project configuration: {e}")

def initialize_checksums_file(checksums_file: Optional[str] = None) -> Path:
    """
    Initialize the checksums file if it doesn't exist.
    
    Args:
        checksums_file: Optional path to checksums file.
    
    Returns:
        Path to the checksums file.
    """
    if checksums_file is None:
        checksums_file = 'data/.checksums.json'
    
    checksums_path = Path(checksums_file)
    checksums_path.parent.mkdir(parents=True, exist_ok=True)
    
    if not checksums_path.exists():
        with open(checksums_path, 'w') as f:
            json.dump({}, f, indent=2)
        get_logger('config').info(f"Initialized checksums file at {checksums_path}")
    
    return checksums_path

def update_checksums(checksums_file: str, artifact_path: str, checksum: str) -> None:
    """
    Update the checksums file with a new artifact checksum.
    
    Args:
        checksums_file: Path to checksums file.
        artifact_path: Path to the artifact.
        checksum: SHA-256 checksum of the artifact.
    """
    checksums_path = Path(checksums_file)
    
    with open(checksums_path, 'r') as f:
        checksums = json.load(f)
    
    checksums[artifact_path] = checksum
    
    with open(checksums_path, 'w') as f:
        json.dump(checksums, f, indent=2)
    
    get_logger('config').info(f"Updated checksum for {artifact_path}")

def verify_checksums(checksums_file: str) -> bool:
    """
    Verify all checksums in the checksums file.
    
    Args:
        checksums_file: Path to checksums file.
    
    Returns:
        True if all checksums are valid, False otherwise.
    """
    import hashlib
    
    checksums_path = Path(checksums_file)
    if not checksums_path.exists():
        get_logger('config').warning("Checksums file does not exist")
        return False
    
    with open(checksums_path, 'r') as f:
        checksums = json.load(f)
    
    all_valid = True
    for artifact_path, expected_checksum in checksums.items():
        artifact_full_path = Path(artifact_path)
        if not artifact_full_path.exists():
            get_logger('config').error(f"Artifact not found: {artifact_path}")
            all_valid = False
            continue
        
        with open(artifact_full_path, 'rb') as f:
            actual_checksum = hashlib.sha256(f.read()).hexdigest()
        
        if actual_checksum != expected_checksum:
            get_logger('config').error(
                f"Checksum mismatch for {artifact_path}: "
                f"expected {expected_checksum}, got {actual_checksum}"
            )
            all_valid = False
        else:
            get_logger('config').debug(f"Checksum verified for {artifact_path}")
    
    return all_valid

def get_config(config_key: str, default: Any = None) -> Any:
    """
    Get a configuration value from environment or defaults.
    
    Args:
        config_key: The configuration key.
        default: Default value if key is not found.
    
    Returns:
        The configuration value.
    """
    value = os.getenv(config_key)
    if value is not None:
        # Try to convert to appropriate type
        if value.lower() in ('true', 'false'):
            return value.lower() == 'true'
        try:
            return int(value)
        except ValueError:
            try:
                return float(value)
            except ValueError:
                return value
    return default