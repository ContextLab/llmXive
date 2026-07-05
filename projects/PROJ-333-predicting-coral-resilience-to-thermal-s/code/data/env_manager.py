"""
Environment variable management for NCBI API keys and external service credentials.

This module handles:
1. Loading credentials from environment variables
2. Fallback to .env file if available
3. Validation of required credentials
4. Direct URL access configuration (no API key required for NCBI FTP)

Note: NCBI FTP access (ftp://ftp-trace.ncbi.nlm.nih.gov/...) does NOT require an API key.
API keys are only needed for programmatic access to NCBI Entrez/EFetch services.
"""
import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass

# Try to import python-dotenv, but make it optional
try:
    from dotenv import load_dotenv
    HAS_DOTENV = True
except ImportError:
    HAS_DOTENV = False
    load_dotenv = None

from utils import setup_logger, handle_critical_error

logger = setup_logger(__name__)


@dataclass
class NCBIConfig:
    """Configuration container for NCBI access settings."""
    api_key: Optional[str] = None
    email: Optional[str] = None
    tool_name: str = "llmXive-coral-resilience"
    max_retries: int = 3
    timeout_seconds: int = 60
    use_direct_ftp: bool = True
    ftp_base_url: str = "ftp://ftp-trace.ncbi.nlm.nih.gov/sra/sra-instant/reads/ByStudy/sra/"
    
    def validate(self) -> bool:
        """Validate configuration. Returns True if valid, False otherwise."""
        if self.use_direct_ftp:
            logger.info("Using direct FTP access (no API key required)")
            return True
        
        if not self.api_key:
            logger.warning("No API key provided. Some NCBI services may be rate-limited.")
            return True  # Still valid, just limited
        
        if not self.email:
            logger.warning("No email provided for NCBI Entrez requests.")
            return True
        
        return True


def load_env_file(env_path: Optional[Path] = None) -> bool:
    """
    Load environment variables from a .env file if it exists.
    
    Args:
        env_path: Path to .env file. If None, searches in current directory and parent.
    
    Returns:
        True if .env was loaded, False if not found or error.
    """
    if not HAS_DOTENV:
        logger.warning("python-dotenv not installed. Skipping .env file loading.")
        return False
    
    if env_path is None:
        # Search for .env in current directory and project root
        possible_paths = [
            Path(".env"),
            Path("../.env"),
            Path("../../.env"),
        ]
        
        for p in possible_paths:
            if p.exists():
                env_path = p
                break
        else:
            logger.debug("No .env file found in standard locations")
            return False
    
    if env_path.exists():
        try:
            load_dotenv(env_path)
            logger.info(f"Loaded environment variables from {env_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to load .env file: {e}")
            return False
    
    return False


def get_ncbi_config() -> NCBIConfig:
    """
    Build NCBI configuration from environment variables.
    
    Environment variables checked:
    - NCBI_API_KEY: Optional API key for Entrez services
    - NCBI_EMAIL: Email for NCBI Entrez requests (recommended)
    - NCBI_TOOL_NAME: Tool name for NCBI Entrez requests
    - USE_DIRECT_FTP: Whether to use direct FTP (default: True)
    
    Returns:
        NCBIConfig object with loaded settings.
    """
    # Load .env file if available
    load_env_file()
    
    api_key = os.getenv("NCBI_API_KEY")
    email = os.getenv("NCBI_EMAIL")
    tool_name = os.getenv("NCBI_TOOL_NAME", "llmXive-coral-resilience")
    use_direct_ftp = os.getenv("USE_DIRECT_FTP", "true").lower() in ("true", "1", "yes")
    ftp_base_url = os.getenv(
        "NCBI_FTP_BASE_URL", 
        "ftp://ftp-trace.ncbi.nlm.nih.gov/sra/sra-instant/reads/ByStudy/sra/"
    )
    
    config = NCBIConfig(
        api_key=api_key,
        email=email,
        tool_name=tool_name,
        use_direct_ftp=use_direct_ftp,
        ftp_base_url=ftp_base_url
    )
    
    config.validate()
    return config


def get_entrez_headers(config: Optional[NCBIConfig] = None) -> Dict[str, str]:
    """
    Get HTTP headers for NCBI Entrez API requests.
    
    Args:
        config: NCBIConfig object. If None, loads default config.
    
    Returns:
        Dictionary of headers for use with requests library.
    """
    if config is None:
        config = get_ncbi_config()
    
    headers = {
        "User-Agent": f"{config.tool_name} (Python script)",
    }
    
    if config.email:
        headers["X-NCBI-Email"] = config.email
    
    if config.api_key:
        headers["X-NCBI-APIKey"] = config.api_key
    
    return headers


def is_ftp_access_available() -> bool:
    """
    Check if direct FTP access to NCBI is available.
    
    Returns:
        True if FTP access is configured, False otherwise.
    """
    config = get_ncbi_config()
    return config.use_direct_ftp


def get_ftp_base_url() -> str:
    """
    Get the base URL for NCBI SRA FTP access.
    
    Returns:
        Base FTP URL string.
    """
    config = get_ncbi_config()
    return config.ftp_base_url


def ensure_ncbi_access() -> bool:
    """
    Ensure that NCBI access is configured properly.
    
    Returns:
        True if access is available (either via FTP or API key), False otherwise.
    """
    config = get_ncbi_config()
    
    if config.use_direct_ftp:
        logger.info("Direct FTP access is enabled for NCBI SRA data")
        return True
    
    if config.api_key:
        logger.info("NCBI API key is configured for Entrez services")
        return True
    
    logger.warning("No NCBI access method configured. Using direct FTP by default.")
    return True  # Default to FTP if nothing else is configured


def main():
    """Main entry point for testing environment configuration."""
    logger.info("Testing NCBI environment configuration...")
    
    config = get_ncbi_config()
    
    print(f"NCBI Configuration:")
    print(f"  API Key: {'Present' if config.api_key else 'Not set'}")
    print(f"  Email: {'Present' if config.email else 'Not set'}")
    print(f"  Tool Name: {config.tool_name}")
    print(f"  Use Direct FTP: {config.use_direct_ftp}")
    print(f"  FTP Base URL: {config.ftp_base_url}")
    
    if ensure_ncbi_access():
        print("\n✓ NCBI access is properly configured")
        return 0
    else:
        print("\n✗ NCBI access configuration failed")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
