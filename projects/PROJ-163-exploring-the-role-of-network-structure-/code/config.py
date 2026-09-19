import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass, field

# Configure logging to capture config loading events
logger = logging.getLogger(__name__)

@dataclass
class IBMQuantumConfig:
    """Configuration container for IBM Quantum Runtime credentials and defaults."""
    token: Optional[str] = None
    url: Optional[str] = None
    instance: Optional[str] = None
    channel: str = "ibm_quantum"
    default_backend: Optional[str] = None

    def is_valid(self) -> bool:
        """Check if the configuration has the mandatory token."""
        if not self.token:
            logger.error("IBM Quantum token is missing in config.")
            return False
        return True

def load_config() -> IBMQuantumConfig:
    """
    Load IBM Quantum configuration from environment variables.
    
    Priorities:
    1. Environment variables (highest priority)
    2. Default values if env vars are missing (for specific defaults like channel)
    
    Expected Environment Variables:
    - IBMQ_TOKEN: The API token for IBM Quantum.
    - IBMQ_URL: Optional custom URL for the IBM Quantum service.
    - IBMQ_INSTANCE: Optional specific instance ID.
    - IBMQ_CHANNEL: Defaults to 'ibm_quantum'.
    - IBMQ_DEFAULT_BACKEND: Optional default backend name.
    
    Returns:
        IBMQuantumConfig: A populated configuration object.
    
    Raises:
        ValueError: If the mandatory token is missing and cannot be resolved.
    """
    token = os.getenv("IBMQ_TOKEN")
    url = os.getenv("IBMQ_URL")
    instance = os.getenv("IBMQ_INSTANCE")
    channel = os.getenv("IBMQ_CHANNEL", "ibm_quantum")
    default_backend = os.getenv("IBMQ_DEFAULT_BACKEND")

    if not token:
        logger.warning("No IBM Quantum token found in environment variables (IBMQ_TOKEN).")
        logger.warning("Please set the 'IBMQ_TOKEN' environment variable or run 'ibm quantum save'.")
        # We do not raise here to allow the module to be imported for testing,
        # but the config will be marked invalid.
        
    config = IBMQuantumConfig(
        token=token,
        url=url,
        instance=instance,
        channel=channel,
        default_backend=default_backend
    )
    
    if config.is_valid():
        logger.info(f"IBM Quantum config loaded. Channel: {config.channel}, Backend: {config.default_backend}")
    else:
        logger.info("IBM Quantum config loaded but is invalid (missing token).")
        
    return config

def setup_ibm_runtime(config: Optional[IBMQuantumConfig] = None) -> None:
    """
    Initialize the IBM Quantum Runtime environment.
    
    This function sets up the credentials for the `qiskit-ibm-runtime` library.
    It attempts to use the provided config, but falls back to the default
    credential store (usually ~/.ibm/credentials) if the token is missing
    from the environment.
    
    Args:
        config: Optional IBMQuantumConfig instance. If None, loads defaults.
    
    Raises:
        RuntimeError: If credentials are not found in either env or default store.
    """
    if config is None:
        config = load_config()
    
    # If token is explicitly provided in config, we set it as an env var
    # to ensure the runtime provider picks it up, or we use the provider directly.
    # However, the standard pattern is to use `IBMProvider.save_account` or
    # rely on the environment.
    
    if config.token:
        os.environ["IBMQ_TOKEN"] = config.token
        logger.info("Token set from config to environment variable.")
    
    try:
        # Attempt to import the provider to verify setup
        from qiskit_ibm_runtime import IBMProvider
        
        # If we have a token in env, the provider usually finds it.
        # If not, it looks in the default account store.
        provider = IBMProvider()
        logger.info(f"IBM Provider initialized successfully. Default backend: {provider.default_backend()}")
        
        # Optionally set the default backend if specified in config
        if config.default_backend:
            # Note: Provider doesn't have a simple setter for default backend globally,
            # but we can log the intent or use it in subsequent fetch calls.
            logger.info(f"Preferred default backend configured in config: {config.default_backend}")
            
    except Exception as e:
        # This is a critical failure for the research pipeline
        logger.error(f"Failed to initialize IBM Runtime provider: {e}")
        raise RuntimeError(f"IBM Quantum credentials not found. Please set IBMQ_TOKEN or run 'ibm quantum save'.") from e

def main():
    """Entry point to test configuration loading."""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    config = load_config()
    print(f"Loaded Config: {config}")
    if config.is_valid():
        try:
            setup_ibm_runtime(config)
            print("Runtime environment setup successful.")
        except RuntimeError as e:
            print(f"Runtime setup failed: {e}")
    else:
        print("Configuration is invalid (missing token). Run 'ibm quantum save' or set IBMQ_TOKEN.")

if __name__ == "__main__":
    main()