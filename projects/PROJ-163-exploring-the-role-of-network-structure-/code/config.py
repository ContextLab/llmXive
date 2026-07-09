"""
Environment configuration management for IBM Quantum API access.

Handles loading of API tokens and default settings from environment variables
and optional local configuration files.
"""
import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any

# Initialize logger for this module
logger = logging.getLogger(__name__)

class IBMQuantumConfig:
    """
    Configuration manager for IBM Quantum Runtime access.
    
    Attributes:
        token (str): IBM Quantum API token.
        instance (str): IBM Quantum Hub/Group/Project string.
        channel (str): Channel type ('ibm_quantum' or 'ibm_cloud').
        url (str): Custom URL for IBM Quantum service (optional).
        timeout (int): Default timeout in seconds for API calls.
        max_retries (int): Maximum number of retry attempts for failed requests.
    """
    
    def __init__(
        self,
        token: Optional[str] = None,
        instance: Optional[str] = None,
        channel: str = "ibm_quantum",
        url: Optional[str] = None,
        timeout: int = 60,
        max_retries: int = 3
    ):
        self.token = token
        self.instance = instance
        self.channel = channel
        self.url = url
        self.timeout = timeout
        self.max_retries = max_retries
        self._validated = False

    def validate(self) -> bool:
        """
        Validates that the configuration contains a valid token.
        
        Returns:
            bool: True if configuration is valid, False otherwise.
        """
        if not self.token:
            logger.warning("IBM Quantum API token is missing.")
            return False
        
        # Basic token format validation (IBM tokens are typically long alphanumeric strings)
        if len(self.token) < 20:
            logger.warning("IBM Quantum API token appears to be invalid (too short).")
            return False
        
        self._validated = True
        logger.info("IBM Quantum configuration validated successfully.")
        return True

    @classmethod
    def from_env(
        cls,
        token_var: str = "IBM_QUANTUM_TOKEN",
        instance_var: str = "IBM_QUANTUM_INSTANCE",
        url_var: str = "IBM_QUANTUM_URL",
        timeout_var: str = "IBM_QUANTUM_TIMEOUT",
        retries_var: str = "IBM_QUANTUM_MAX_RETRIES"
    ) -> "IBMQuantumConfig":
        """
        Creates an IBMQuantumConfig instance from environment variables.
        
        Args:
            token_var: Name of the environment variable for the API token.
            instance_var: Name of the environment variable for the hub/group/project.
            url_var: Name of the environment variable for the custom URL.
            timeout_var: Name of the environment variable for the timeout.
            retries_var: Name of the environment variable for max retries.
        
        Returns:
            IBMQuantumConfig: Configuration instance populated from environment.
        """
        token = os.getenv(token_var)
        instance = os.getenv(instance_var)
        url = os.getenv(url_var)
        
        try:
            timeout = int(os.getenv(timeout_var, "60"))
        except ValueError:
            logger.warning(f"Invalid {timeout_var}, using default 60s.")
            timeout = 60
        
        try:
            max_retries = int(os.getenv(retries_var, "3"))
        except ValueError:
            logger.warning(f"Invalid {retries_var}, using default 3.")
            max_retries = 3

        return cls(
            token=token,
            instance=instance,
            channel="ibm_quantum",
            url=url,
            timeout=timeout,
            max_retries=max_retries
        )

    @classmethod
    def from_file(cls, config_path: Path) -> "IBMQuantumConfig":
        """
        Creates an IBMQuantumConfig instance from a YAML configuration file.
        
        Args:
            config_path: Path to the YAML configuration file.
        
        Returns:
            IBMQuantumConfig: Configuration instance populated from file.
        
        Raises:
            FileNotFoundError: If the configuration file does not exist.
            ValueError: If the file contains invalid YAML or missing required keys.
        """
        import yaml

        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        with open(config_path, 'r', encoding='utf-8') as f:
            try:
                data = yaml.safe_load(f)
            except yaml.YAMLError as e:
                raise ValueError(f"Invalid YAML in configuration file: {e}")

        if not isinstance(data, dict):
            raise ValueError("Configuration file must contain a YAML dictionary.")

        token = data.get("token")
        instance = data.get("instance")
        url = data.get("url")
        
        timeout = data.get("timeout", 60)
        max_retries = data.get("max_retries", 3)

        if not isinstance(timeout, int):
            try:
                timeout = int(timeout)
            except (ValueError, TypeError):
                logger.warning("Invalid timeout value in config, using default 60.")
                timeout = 60

        if not isinstance(max_retries, int):
            try:
                max_retries = int(max_retries)
            except (ValueError, TypeError):
                logger.warning("Invalid max_retries value in config, using default 3.")
                max_retries = 3

        return cls(
            token=token,
            instance=instance,
            channel="ibm_quantum",
            url=url,
            timeout=timeout,
            max_retries=max_retries
        )

    def get_runtime_credentials(self) -> Dict[str, Any]:
        """
        Returns credentials dictionary compatible with qiskit-ibm-runtime.
        
        Returns:
            Dict[str, Any]: Dictionary containing token, instance, channel, and url.
        """
        creds = {
            "channel": self.channel,
            "token": self.token,
        }
        if self.instance:
            creds["instance"] = self.instance
        if self.url:
            creds["url"] = self.url
        return creds

def load_config(config_file: Optional[Path] = None) -> IBMQuantumConfig:
    """
    Loads IBM Quantum configuration, prioritizing file then environment.
    
    Args:
        config_file: Optional path to a YAML configuration file.
                    If not provided, looks for 'config.yaml' in the project root.
    
    Returns:
        IBMQuantumConfig: The loaded configuration instance.
    """
    if config_file is None:
        # Default location: project root / config.yaml
        config_file = Path.cwd() / "config.yaml"
    
    # Try loading from file first
    if config_file.exists():
        try:
            logger.info(f"Loading configuration from {config_file}")
            return IBMQuantumConfig.from_file(config_file)
        except Exception as e:
            logger.warning(f"Failed to load config from file {config_file}: {e}. Falling back to environment.")
    
    # Fallback to environment variables
    logger.info("Loading configuration from environment variables.")
    return IBMQuantumConfig.from_env()

def setup_ibm_runtime(config: Optional[IBMQuantumConfig] = None) -> None:
    """
    Configures the IBM Quantum Runtime environment using the provided or loaded config.
    
    This function sets up the environment for use with `qiskit-ibm-runtime`.
    
    Args:
        config: Optional IBMQuantumConfig instance. If None, loads from file/env.
    """
    if config is None:
        config = load_config()
    
    if not config.validate():
        raise RuntimeError("IBM Quantum configuration is invalid. "
                           "Please set the IBM_QUANTUM_TOKEN environment variable "
                           "or provide a valid config.yaml file.")
    
    # Set environment variables for qiskit-ibm-runtime if not already set
    if not os.getenv("IBM_QUANTUM_TOKEN"):
        os.environ["IBM_QUANTUM_TOKEN"] = config.token
    
    if config.instance and not os.getenv("IBM_QUANTUM_INSTANCE"):
        os.environ["IBM_QUANTUM_INSTANCE"] = config.instance
    
    if config.url and not os.getenv("IBM_QUANTUM_URL"):
        os.environ["IBM_QUANTUM_URL"] = config.url

    logger.info("IBM Quantum Runtime environment configured successfully.")

def main():
    """
    CLI entry point to test configuration loading and validation.
    """
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="Test IBM Quantum configuration loading.")
    parser.add_argument("--config", type=str, help="Path to YAML config file")
    parser.add_argument("--validate", action="store_true", help="Validate the loaded config")
    
    args = parser.parse_args()
    
    try:
        config_path = Path(args.config) if args.config else None
        config = load_config(config_path)
        
        print(f"Configuration loaded:")
        print(f"  Token (masked): {config.token[:8]}...{config.token[-4:] if config.token else 'None'}")
        print(f"  Instance: {config.instance or 'Not set'}")
        print(f"  Channel: {config.channel}")
        print(f"  URL: {config.url or 'Default'}")
        print(f"  Timeout: {config.timeout}s")
        print(f"  Max Retries: {config.max_retries}")
        
        if args.validate or True: # Always validate to demonstrate
            if config.validate():
                print("\nValidation: SUCCESS")
                sys.exit(0)
            else:
                print("\nValidation: FAILED")
                sys.exit(1)
                
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
