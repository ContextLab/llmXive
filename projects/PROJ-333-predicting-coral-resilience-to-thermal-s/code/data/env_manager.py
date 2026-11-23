import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass

from utils import setup_logger, handle_critical_error

@dataclass
class NCBIConfig:
    """Configuration for NCBI access."""
    email: Optional[str] = None
    api_key: Optional[str] = None
    tool_name: str = "llmXive-coral-resilience"

def load_env_file(path: Optional[Path] = None) -> Dict[str, str]:
    """Loads environment variables from a .env file if it exists."""
    env_vars = {}
    if path is None:
        path = Path(os.getcwd()) / ".env"
    
    if path.exists():
        with open(path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip()
    return env_vars

def get_ncbi_config() -> NCBIConfig:
    """Creates an NCBIConfig object from environment variables."""
    env_vars = load_env_file()
    return NCBIConfig(
        email=env_vars.get("NCBI_EMAIL"),
        api_key=env_vars.get("NCBI_API_KEY")
    )

def get_entrez_headers(config: NCBIConfig) -> Dict[str, str]:
    """Generates headers for NCBI Entrez requests."""
    headers = {
        "User-Agent": f"{config.tool_name} (Python)"
    }
    if config.email:
        headers["From"] = config.email
    return headers

def is_ftp_access_available() -> bool:
    """Checks if FTP access is available."""
    import socket
    try:
        socket.create_connection(("ftp.ncbi.nlm.nih.gov", 21), timeout=5)
        return True
    except (socket.timeout, socket.gaierror):
        return False

def get_ftp_base_url() -> str:
    """Returns the base FTP URL for NCBI."""
    return "ftp://ftp.ncbi.nlm.nih.gov"

def ensure_ncbi_access(logger: Optional[logging.Logger] = None) -> None:
    """Ensures NCBI access is available, raising error if not."""
    if logger is None:
        logger = setup_logger("env_manager")
    
    if not is_ftp_access_available():
        logger.error("Cannot reach NCBI FTP server. Check internet connection or proxy settings.")
        raise RuntimeError("NCBI FTP access unavailable")
    
    logger.info("NCBI FTP access confirmed")

def main():
    """Main entry point for environment management checks."""
    logger = setup_logger("env_manager")
    try:
        ensure_ncbi_access(logger)
        config = get_ncbi_config()
        logger.info(f"NCBI Config loaded: email={config.email is not None}, has_key={config.api_key is not None}")
    except Exception as e:
        handle_critical_error(logger, "Failed to initialize NCBI environment", e)

if __name__ == "__main__":
    main()
