"""
Environment configuration management for IBM Quantum API access.

This module handles loading, validating, and providing access to:
- IBM Quantum API tokens
- Default backend configurations
- Rate-limiting parameters

Environment variables used:
- IBM_QUANTUM_TOKEN: The API token for IBM Quantum services
- IBM_QUANTUM_INSTANCE: (Optional) The cloud instance ID for IBM Cloud
- IBM_QUANTUM_URL: (Optional) Custom API URL for private clouds
"""
import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass, field
from qiskit_ibm_runtime import QiskitRuntimeService
from qiskit_ibm_runtime.exceptions import IBMInputValueError, IBMRuntimeError

# Configure logging for this module
logger = logging.getLogger(__name__)

@dataclass
class IBMQuantumConfig:
    """
    Configuration container for IBM Quantum access.
    
    Attributes:
        token: The API token for authentication.
        instance: Optional cloud instance ID.
        url: Optional custom API URL.
        channel: The channel type ('ibm_quantum' or 'ibm_cloud').
        timeout_seconds: Default timeout for API calls (default: 120).
        max_retries: Maximum number of retry attempts (default: 3).
        backoff_factor: Exponential backoff multiplier (default: 2).
    """
    token: str
    instance: Optional[str] = None
    url: Optional[str] = None
    channel: str = "ibm_quantum"
    timeout_seconds: int = 120
    max_retries: int = 3
    backoff_factor: int = 2

    def __post_init__(self):
        """Validate configuration after initialization."""
        if not self.token or not self.token.strip():
            raise ValueError("IBM Quantum token cannot be empty.")
        if self.channel not in ("ibm_quantum", "ibm_cloud"):
            raise ValueError(f"Invalid channel: {self.channel}. Must be 'ibm_quantum' or 'ibm_cloud'.")

def load_config() -> IBMQuantumConfig:
    """
    Load IBM Quantum configuration from environment variables.
    
    Reads the following environment variables:
    - IBM_QUANTUM_TOKEN (Required)
    - IBM_QUANTUM_INSTANCE (Optional)
    - IBM_QUANTUM_URL (Optional)
    - IBM_QUANTUM_CHANNEL (Optional, default: 'ibm_quantum')
    - IBM_QUANTUM_TIMEOUT (Optional, default: 120)
    
    Returns:
        IBMQuantumConfig: A validated configuration object.
        
    Raises:
        ValueError: If required environment variables are missing or invalid.
        RuntimeError: If the token format is invalid.
    """
    token = os.getenv("IBM_QUANTUM_TOKEN")
    if not token:
        raise RuntimeError(
            "IBM Quantum token not found. Set the IBM_QUANTUM_TOKEN "
            "environment variable. Example: export IBM_QUANTUM_TOKEN='your_token'"
        )

    token = token.strip()
    # Basic validation: IBM Quantum tokens are typically 64-character hex strings
    if len(token) < 32:
        logger.warning("IBM Quantum token appears unusually short. Proceeding anyway.")

    instance = os.getenv("IBM_QUANTUM_INSTANCE")
    url = os.getenv("IBM_QUANTUM_URL")
    channel = os.getenv("IBM_QUANTUM_CHANNEL", "ibm_quantum")
    
    try:
        timeout_seconds = int(os.getenv("IBM_QUANTUM_TIMEOUT", "120"))
        max_retries = int(os.getenv("IBM_QUANTUM_MAX_RETRIES", "3"))
        backoff_factor = int(os.getenv("IBM_QUANTUM_BACKOFF_FACTOR", "2"))
    except ValueError as e:
        raise ValueError(f"Invalid numeric configuration value: {e}")

    config = IBMQuantumConfig(
        token=token,
        instance=instance,
        url=url,
        channel=channel,
        timeout_seconds=timeout_seconds,
        max_retries=max_retries,
        backoff_factor=backoff_factor
    )
    
    logger.info(
        f"Loaded IBM Quantum config: channel={config.channel}, "
        f"timeout={config.timeout_seconds}s, retries={config.max_retries}"
    )
    
    return config

def setup_ibm_runtime(config: Optional[IBMQuantumConfig] = None) -> QiskitRuntimeService:
    """
    Initialize and return a QiskitRuntimeService instance using the provided config.
    
    This function authenticates with the IBM Quantum service using the configuration.
    It handles authentication errors and logs the status of the connection.
    
    Args:
        config: Optional IBMQuantumConfig instance. If None, loads from environment.
        
    Returns:
        QiskitRuntimeService: An authenticated service instance.
        
    Raises:
        RuntimeError: If authentication fails or configuration is invalid.
    """
    if config is None:
        config = load_config()

    try:
        # Authenticate with IBM Quantum
        service = QiskitRuntimeService(
            channel=config.channel,
            token=config.token,
            instance=config.instance,
            url=config.url
        )
        
        # Verify the service is connected by listing backends (lightweight check)
        try:
            backend_count = len(service.backends())
            logger.info(f"Successfully authenticated. Found {backend_count} backends.")
        except Exception as e:
            logger.warning(f"Service authenticated but could not list backends: {e}")
        
        return service

    except IBMInputValueError as e:
        logger.error(f"Invalid IBM Quantum configuration: {e}")
        raise RuntimeError(f"Configuration error: {e}") from e
    except IBMRuntimeError as e:
        logger.error(f"IBM Runtime error during authentication: {e}")
        raise RuntimeError(f"Runtime error: {e}") from e
    except Exception as e:
        logger.error(f"Unexpected error during IBM Quantum authentication: {e}")
        raise RuntimeError(f"Authentication failed: {e}") from e

def main():
    """
    Entry point for testing configuration loading and service setup.
    
    This function attempts to load the configuration and authenticate with
    the IBM Quantum service. It prints the status and available backends.
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    try:
        logger.info("Starting IBM Quantum configuration check...")
        config = load_config()
        logger.info("Configuration loaded successfully.")
        
        logger.info("Initializing QiskitRuntimeService...")
        service = setup_ibm_runtime(config)
        
        # List available backends
        backends = service.backends()
        logger.info(f"Available backends ({len(backends)}):")
        for backend in backends:
            logger.info(f"  - {backend.name}")
            
        print(f"\nSuccess! Connected to {len(backends)} backends.")
        
    except RuntimeError as e:
        logger.error(f"Failed to setup IBM Quantum service: {e}")
        print(f"Error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print(f"Unexpected error: {e}")
        return 1
        
    return 0

if __name__ == "__main__":
    exit(main())
