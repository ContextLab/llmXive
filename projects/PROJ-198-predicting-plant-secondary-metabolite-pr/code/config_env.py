"""
Environment configuration management.
Loads settings from .env file and provides access to API keys and paths.
"""
import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any, Set

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)

class EnvConfig(BaseSettings):
    """
    Pydantic model for environment variables.
    """
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # API Keys
    ncbi_api_key: Optional[str] = Field(None, description="NCBI API Key")
    metabolights_api_key: Optional[str] = Field(None, description="MetaboLights API Key")

    # Paths
    data_raw_path: Path = Field(Path("data/raw"), description="Path to raw data directory")
    data_processed_path: Path = Field(Path("data/processed"), description="Path to processed data directory")
    data_interim_path: Path = Field(Path("data/interim"), description="Path to interim data directory")
    logs_path: Path = Field(Path("code/logs"), description="Path to logs directory")
    figures_path: Path = Field(Path("figures"), description="Path to figures directory")
    phylogeny_path: Path = Field(Path("data/raw/phylogeny/tree.newick"), description="Path to phylogeny tree file")

    # Configuration
    max_genome_size_mb: int = Field(500, description="Maximum genome size to download in MB")
    antismash_timeout: int = Field(3600, description="AntiSMASH timeout in seconds")
    log_level: str = Field("INFO", description="Logging level")

    @field_validator('data_raw_path', 'data_processed_path', 'data_interim_path', 'logs_path', 'figures_path', 'phylogeny_path')
    @classmethod
    def validate_paths(cls, v: Path) -> Path:
        """Ensure paths are absolute if relative, or resolve them relative to project root."""
        # Assuming project root is two levels up from code/
        # This logic might need adjustment based on execution context
        return v.resolve()

def load_environment() -> EnvConfig:
    """
    Load environment configuration from .env file.
    """
    try:
        config = EnvConfig()
        logger.info("Environment configuration loaded successfully.")
        return config
    except Exception as e:
        logger.error(f"Failed to load environment configuration: {e}")
        raise

def ensure_directories(config: EnvConfig) -> None:
    """
    Ensure all required directories exist.
    """
    directories = [
        config.data_raw_path,
        config.data_processed_path,
        config.data_interim_path,
        config.logs_path,
        config.figures_path,
        config.phylogeny_path.parent
    ]
    
    for directory in directories:
        try:
            directory.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Ensured directory exists: {directory}")
        except Exception as e:
            logger.error(f"Failed to create directory {directory}: {e}")
            raise

def get_api_key(service: str) -> Optional[str]:
    """
    Retrieve an API key for a specific service.
    
    Args:
        service: Name of the service (e.g., 'ncbi', 'metabolights')
        
    Returns:
        The API key string or None if not set.
    """
    config = load_environment()
    
    if service.lower() == 'ncbi':
        return config.ncbi_api_key
    elif service.lower() == 'metabolights':
        return config.metabolights_api_key
    else:
        logger.warning(f"Unknown service requested for API key: {service}")
        return None

def get_data_path(subdir: Optional[str] = None) -> Path:
    """
    Get the path to the data directory, optionally with a subdirectory.
    
    Args:
        subdir: Optional subdirectory name.
        
    Returns:
        Path object.
    """
    config = load_environment()
    base_path = config.data_processed_path
    
    if subdir:
        return base_path / subdir
    return base_path

def get_logs_path() -> Path:
    """
    Get the path to the logs directory.
    
    Returns:
        Path object.
    """
    config = load_environment()
    return config.logs_path

def get_figures_path() -> Path:
    """
    Get the path to the figures directory.
    
    Returns:
        Path object.
    """
    config = load_environment()
    return config.figures_path

def validate_required_env_vars(required_vars: Set[str]) -> bool:
    """
    Validate that required environment variables are set.
    
    Args:
        required_vars: Set of variable names to check.
        
    Returns:
        True if all required vars are present, False otherwise.
    """
    config = load_environment()
    missing = []
    
    # Map variable names to config attributes
    var_map = {
        'NCBI_API_KEY': 'ncbi_api_key',
        'METABOLIGHTS_API_KEY': 'metabolights_api_key',
        'DATA_RAW_PATH': 'data_raw_path',
        'DATA_PROCESSED_PATH': 'data_processed_path',
        'LOGS_PATH': 'logs_path',
        'FIGURES_PATH': 'figures_path'
    }
    
    for var in required_vars:
        attr = var_map.get(var)
        if attr and getattr(config, attr) is None:
            missing.append(var)
        
    if missing:
        logger.error(f"Missing required environment variables: {missing}")
        return False
    
    return True

def create_env_file_template() -> None:
    """
    Create a template .env.example file if it doesn't exist.
    """
    project_root = Path(__file__).parent.parent
    env_example_path = project_root / "code" / ".env.example"
    
    if env_example_path.exists():
        return
    
    template = """# Environment Variables for Plant Secondary Metabolite Prediction Pipeline
# Copy this file to .env and fill in your specific values.
# This file is gitignored. Do not commit real secrets.

# --- API Keys (Optional, only if specific services require authentication) ---
# NCBI API Key (Optional, increases rate limits for Entrez queries)
# Get one from: https://www.ncbi.nlm.nih.gov/account/
NCBI_API_KEY=

# MetaboLights API Key (Optional, for restricted datasets)
# Check documentation at: https://www.ebi.ac.uk/metabolights/
METABOLIGHTS_API_KEY=

# --- Local Paths ---
# Root directory for raw data downloads (FASTA, GFF, etc.)
DATA_RAW_PATH=data/raw

# Root directory for processed data (aligned matrices, features)
DATA_PROCESSED_PATH=data/processed

# Root directory for interim data (PCA features, temporary files)
DATA_INTERIM_PATH=data/interim

# Directory for log files
LOGS_PATH=code/logs

# Directory for generated figures/plots
FIGURES_PATH=figures

# Path to the phylogeny tree file (Newick format)
PHYLOGENY_PATH=data/raw/phylogeny/tree.newick

# --- Configuration ---
# Maximum genome size to download (in MB)
MAX_GENOME_SIZE_MB=500

# AntiSMASH timeout in seconds
ANITSMASH_TIMEOUT=3600

# Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
LOG_LEVEL=INFO
"""
    with open(env_example_path, 'w', encoding='utf-8') as f:
        f.write(template)
    
    logger.info(f"Created .env.example template at {env_example_path}")

def get_env_config() -> EnvConfig:
    """
    Get the environment configuration.
    
    Returns:
        EnvConfig instance.
    """
    return load_environment()