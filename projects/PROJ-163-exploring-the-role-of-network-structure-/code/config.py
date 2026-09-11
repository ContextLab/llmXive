"""
Environment configuration management for IBM Quantum access.
Loads API tokens and default settings from environment variables.
"""
import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass, field

from qiskit_ibm_runtime import QiskitRuntimeService

logger = logging.getLogger(__name__)

@dataclass
class IBMQuantumConfig:
    """Configuration container for IBM Quantum Runtime access."""
    channel: str = "ibm_quantum"
    token: Optional[str] = None
    url: Optional[str] = None
    instance: Optional[str] = None
    proxies: Optional[Dict[str, Any]] = None
    verify: bool = True

    def __post_init__(self):
        """Validate that a token is present if channel is ibm_quantum."""
        if self.channel == "ibm_quantum" and not self.token:
            raise ValueError(
                "IBM Quantum token is missing. "
                "Set the IBMQ_TOKEN environment variable or provide 'token' explicitly."
            )

def load_config() -> IBMQuantumConfig:
    """
    Load IBM Quantum configuration from environment variables.

    Environment variables read:
        - IBMQ_TOKEN: The IBM Quantum API token (required).
        - IBMQ_CHANNEL: Service channel type (default: "ibm_quantum").
        - IBMQ_URL: Custom URL for the service (optional).
        - IBMQ_INSTANCE: Hub/Group/Project instance string (optional).
        - IBMQ_VERIFY: Boolean to verify SSL certificates (default: True).

    Returns:
        IBMQuantumConfig: Populated configuration object.
    """
    token = os.getenv("IBMQ_TOKEN")
    channel = os.getenv("IBMQ_CHANNEL", "ibm_quantum")
    url = os.getenv("IBMQ_URL")
    instance = os.getenv("IBMQ_INSTANCE")
    verify_str = os.getenv("IBMQ_VERIFY", "true").lower()
    verify = verify_str in ("true", "1", "yes")

    config = IBMQuantumConfig(
        channel=channel,
        token=token,
        url=url,
        instance=instance,
        verify=verify
    )

    logger.info(
        "Loaded IBM Quantum config: channel=%s, token_set=%s, url=%s, instance=%s",
        config.channel,
        "True" if config.token else "False",
        config.url,
        config.instance
    )

    return config

def setup_ibm_runtime(config: Optional[IBMQuantumConfig] = None) -> QiskitRuntimeService:
    """
    Initialize and return a QiskitRuntimeService instance.

    Args:
        config: Optional pre-loaded configuration. If None, loads from env.

    Returns:
        QiskitRuntimeService: Active service instance.

    Raises:
        ValueError: If token is missing or authentication fails.
        RuntimeError: If service initialization fails unexpectedly.
    """
    if config is None:
        config = load_config()

    try:
        logger.info("Initializing QiskitRuntimeService...")
        service = QiskitRuntimeService(
            channel=config.channel,
            token=config.token,
            url=config.url,
            instance=config.instance,
            verify=config.verify
        )
        logger.info("Successfully connected to IBM Quantum Runtime.")
        return service
    except Exception as e:
        logger.error("Failed to initialize QiskitRuntimeService: %s", str(e))
        raise RuntimeError(f"Service initialization failed: {e}") from e

def main():
    """
    Entry point for testing configuration loading.
    Prints the loaded configuration details to stdout.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    try:
        config = load_config()
        print("Configuration loaded successfully:")
        print(f"  Channel: {config.channel}")
        print(f"  Token present: {'Yes' if config.token else 'No'}")
        print(f"  URL: {config.url or 'Default'}")
        print(f"  Instance: {config.instance or 'Default'}")
        print(f"  Verify SSL: {config.verify}")

        # Attempt to connect to validate the token
        service = setup_ibm_runtime(config)
        backends = service.backends()
        print(f"\nConnected! Found {len(backends)} accessible backends.")
        if backends:
            print(f"First backend: {backends[0].name}")

    except ValueError as e:
        print(f"Configuration Error: {e}")
        print("Please set the IBMQ_TOKEN environment variable.")
        exit(1)
    except RuntimeError as e:
        print(f"Connection Error: {e}")
        exit(1)

if __name__ == "__main__":
    main()
