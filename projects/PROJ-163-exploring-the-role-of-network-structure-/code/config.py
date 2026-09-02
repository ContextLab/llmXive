import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass, field

from qiskit_ibm_runtime import QiskitRuntimeService

logger = logging.getLogger(__name__)

@dataclass
class IBMQuantumConfig:
    """Configuration container for IBM Quantum Runtime settings."""
    channel: str = "ibm_cloud"
    token: Optional[str] = None
    url: str = "https://auth.quantum-computing.ibm.com/api"
    instance: Optional[str] = None
    default_backend: Optional[str] = None
    timeout: int = 120

    def __post_init__(self):
        if not self.token and not os.getenv("QISKIT_IBM_TOKEN"):
            logger.warning(
                "IBM Quantum token not found in config or QISKIT_IBM_TOKEN env var. "
                "Authentication will fail unless a valid token is provided."
            )

    def get_token(self) -> Optional[str]:
        """Retrieve token from config or environment."""
        return self.token or os.getenv("QISKIT_IBM_TOKEN")

    def get_url(self) -> str:
        """Retrieve URL from config or environment."""
        return self.url or os.getenv("QISKIT_IBM_URL", self.url)

    def get_instance(self) -> Optional[str]:
        """Retrieve instance (hub/group/project) from config or environment."""
        return self.instance or os.getenv("QISKIT_IBM_INSTANCE")

def load_config(config_path: Optional[Path] = None) -> IBMQuantumConfig:
    """
    Load IBM Quantum configuration from a YAML/JSON file or environment variables.
    
    Priority:
    1. Explicit config file (if provided)
    2. Environment variables (QISKIT_IBM_TOKEN, QISKIT_IBM_URL, etc.)
    3. Default values
    
    Args:
        config_path: Optional path to a configuration file (YAML or JSON).
        
    Returns:
        IBMQuantumConfig instance populated with settings.
    """
    token = os.getenv("QISKIT_IBM_TOKEN")
    url = os.getenv("QISKIT_IBM_URL")
    instance = os.getenv("QISKIT_IBM_INSTANCE")
    default_backend = os.getenv("QISKIT_IBM_DEFAULT_BACKEND")
    channel = os.getenv("QISKIT_IBM_CHANNEL", "ibm_cloud")
    timeout = int(os.getenv("QISKIT_IBM_TIMEOUT", "120"))

    # If a config file is provided, attempt to load it (optional extension)
    if config_path and config_path.exists():
        try:
            import json
            import yaml
            
            with open(config_path, "r") as f:
                if config_path.suffix in [".yaml", ".yml"]:
                    file_config = yaml.safe_load(f)
                elif config_path.suffix == ".json":
                    file_config = json.load(f)
                else:
                    file_config = {}
            
            # Override env vars with file config if present
            token = token or file_config.get("token")
            url = url or file_config.get("url")
            instance = instance or file_config.get("instance")
            default_backend = default_backend or file_config.get("default_backend")
            channel = channel or file_config.get("channel", "ibm_cloud")
            timeout = timeout or file_config.get("timeout", 120)
            
            logger.info(f"Loaded configuration from {config_path}")
        except Exception as e:
            logger.warning(f"Failed to load config file {config_path}: {e}")

    return IBMQuantumConfig(
        channel=channel,
        token=token,
        url=url,
        instance=instance,
        default_backend=default_backend,
        timeout=timeout
    )

def setup_ibm_runtime(config: Optional[IBMQuantumConfig] = None) -> QiskitRuntimeService:
    """
    Initialize and return the QiskitRuntimeService using the provided or loaded config.
    
    Args:
        config: Optional pre-loaded config. If None, loads from environment/file.
        
    Returns:
        Authenticated QiskitRuntimeService instance.
        
    Raises:
        RuntimeError: If authentication fails or no valid token is found.
    """
    if config is None:
        config = load_config()

    token = config.get_token()
    if not token:
        raise RuntimeError(
            "IBM Quantum token is missing. Set QISKIT_IBM_TOKEN environment variable "
            "or provide it in the configuration file."
        )

    try:
        service = QiskitRuntimeService(
            channel=config.channel,
            token=token,
            url=config.get_url(),
            instance=config.get_instance()
        )
        logger.info("Successfully authenticated with IBM Quantum Runtime.")
        return service
    except Exception as e:
        logger.error(f"Failed to authenticate with IBM Quantum Runtime: {e}")
        raise RuntimeError(f"IBM Quantum Runtime authentication failed: {e}") from e

def main():
    """CLI entry point to test configuration loading and service connection."""
    logging.basicConfig(level=logging.INFO)
    
    logger.info("Testing IBM Quantum Configuration Management...")
    
    try:
        config = load_config()
        logger.info(f"Loaded Config: Channel={config.channel}, URL={config.get_url()}")
        logger.info(f"Token present: {bool(config.get_token())}")
        logger.info(f"Default Backend: {config.default_backend}")
        
        # Attempt to connect if token is present
        if config.get_token():
            service = setup_ibm_runtime(config)
            backends = service.backends()
            logger.info(f"Successfully connected. Found {len(backends)} backends.")
            if config.default_backend:
                logger.info(f"Default backend '{config.default_backend}' is available: "
                            f"{service.backend(config.default_backend) is not None}")
        else:
            logger.warning("No token found. Skipping runtime connection test.")
            
    except RuntimeError as e:
        logger.error(f"Configuration/Connection Error: {e}")
        return 1
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        return 1
        
    return 0

if __name__ == "__main__":
    exit(main())