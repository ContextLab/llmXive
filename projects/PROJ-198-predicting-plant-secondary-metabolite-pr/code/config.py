"""
Configuration loader for the llmXive plant metabolite project.

Manages species lists, thresholds, and data paths using a YAML configuration file.
"""
import os
import yaml
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator, ValidationError
from models.species import Species


class ConfigSettings(BaseModel):
    """Settings derived from the configuration file."""
    data_root: Path = Field(..., description="Root directory for data storage")
    raw_dir: Path = Field(..., description="Directory for raw downloaded data")
    processed_dir: Path = Field(..., description="Directory for processed data")
    interim_dir: Path = Field(..., description="Directory for intermediate data")
    figures_dir: Path = Field(..., description="Directory for output figures")
    
    # Thresholds
    max_genome_size_mb: float = Field(500.0, description="Max genome size in MB to download")
    antismash_confidence: float = Field(0.3, description="Default antiSMASH confidence threshold")
    min_species_count: int = Field(5, description="Minimum species count for valid analysis")
    
    # Timeouts
    download_timeout: int = Field(300, description="Timeout for network requests in seconds")
    
    # Paths relative to data_root
    phylogeny_path: Path = Field(..., description="Path to phylogeny Newick file relative to data_root")
    mibig_ontology_path: Path = Field(..., description="Path to MIBiG ontology JSON relative to data_root")

    @field_validator('data_root', 'raw_dir', 'processed_dir', 'interim_dir', 'figures_dir', 'phylogeny_path', 'mibig_ontology_path')
    @classmethod
    def ensure_path(cls, v):
        if isinstance(v, str):
            return Path(v)
        return v
    
    @field_validator('max_genome_size_mb', 'antismash_confidence')
    @classmethod
    def ensure_positive(cls, v):
        if v <= 0:
            raise ValueError(f"{cls.__name__} requires positive values for {v}")
        return v


class Config(BaseModel):
    """Main configuration container."""
    settings: ConfigSettings
    species_list: List[Dict[str, Any]] = Field(default_factory=list)
    
    @property
    def species_objects(self) -> List[Species]:
        """Convert raw species dicts into Pydantic Species models."""
        species = []
        for s in self.species_list:
            try:
                species.append(Species(**s))
            except ValidationError as e:
                # Log warning but skip invalid entries if possible, or raise depending on strictness
                print(f"Warning: Skipping invalid species entry {s}: {e}")
        return species

_CONFIG: Optional[Config] = None


def load_config(config_path: Optional[str] = None) -> Config:
    """
    Load configuration from a YAML file.
    
    Args:
        config_path: Path to the config file. Defaults to 'config.yaml' in project root.
        
    Returns:
        Config object with validated settings and species list.
        
    Raises:
        FileNotFoundError: If config file does not exist.
        ValidationError: If config contents do not match schema.
    """
    global _CONFIG
    
    if _CONFIG is not None:
        return _CONFIG
        
    if config_path is None:
        # Default to project root config.yaml
        config_path = Path.cwd() / "config.yaml"
        
    if not Path(config_path).exists():
        raise FileNotFoundError(f"Configuration file not found at {config_path}")
        
    with open(config_path, 'r', encoding='utf-8') as f:
        raw_data = yaml.safe_load(f)
        
    if not isinstance(raw_data, dict):
        raise ValueError("Configuration file must be a valid YAML dictionary.")
        
    # Ensure directory structure exists if paths are provided
    # We do this after validation to ensure paths are valid
    if 'settings' in raw_data:
        data_root = raw_data['settings'].get('data_root')
        if data_root:
            base = Path(data_root)
            if not base.exists():
                base.mkdir(parents=True, exist_ok=True)
            
            # Create subdirectories if defined
            for subdir in ['raw', 'processed', 'interim', 'figures']:
                path = base / subdir
                if not path.exists():
                    path.mkdir(parents=True, exist_ok=True)
    
    config = Config(**raw_data)
    _CONFIG = config
    return config


def get_config() -> Config:
    """
    Get the global configuration instance.
    Raises FileNotFoundError if not yet loaded.
    """
    if _CONFIG is None:
        raise RuntimeError("Configuration not loaded. Call load_config() first.")
    return _CONFIG


def reset_config() -> None:
    """Reset the global configuration (useful for testing)."""
    global _CONFIG
    _CONFIG = None

def get_species_list() -> List[Species]:
    """Convenience wrapper to get the list of Species models."""
    return get_config().species_objects


def get_data_path(relative_path: str) -> Path:
    """
    Construct a full path relative to the configured data root.
    
    Args:
        relative_path: Path relative to the data root.
        
    Returns:
        Absolute Path object.
    """
    return get_config().settings.data_root / relative_path
