"""
Configuration management module.
Handles loading settings from YAML, environment variables, and defaults.
"""
import os
import yaml
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator, ValidationError
from models.species import Species

# Singleton instance
_config_instance: Optional["Config"] = None

class ConfigSettings(BaseModel):
    """Settings for the application."""
    data_path: Path = Field(default=Path("data"))
    raw_data_path: Path = Field(default=Path("data/raw"))
    processed_data_path: Path = Field(default=Path("data/processed"))
    figures_path: Path = Field(default=Path("figures"))
    logs_path: Path = Field(default=Path("logs"))
    model_cache_path: Path = Field(default=Path("model_cache"))
    
    # Thresholds
    genome_size_limit_mb: int = Field(default=500)
    bgc_confidence_threshold: float = Field(default=0.5)
    min_species_count: int = Field(default=5)
    
    # API Keys (placeholders, expected to be overridden by env)
    ncbi_api_key: Optional[str] = None
    pmdb_api_key: Optional[str] = None

    @field_validator('data_path', 'raw_data_path', 'processed_data_path', 'figures_path', 'logs_path', 'model_cache_path', mode='before')
    @classmethod
    def convert_to_path(cls, v):
        if isinstance(v, str):
            return Path(v)
        return v

class Config(BaseModel):
    """Main configuration container."""
    settings: ConfigSettings = Field(default_factory=ConfigSettings)
    species_list: List[Species] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

def load_config(config_path: Optional[Path] = None) -> Config:
    """
    Load configuration from a YAML file.
    
    Args:
        config_path: Path to the YAML config file. Defaults to 'config.yaml' in root.
        
    Returns:
        Config object populated with settings and species.
    """
    global _config_instance
    
    if config_path is None:
        # Check common locations relative to project root
        possible_paths = [
            Path("config.yaml"),
            Path("./config.yaml"),
            Path(os.path.join(os.path.dirname(__file__), "..", "config.yaml"))
        ]
        for p in possible_paths:
            if p.exists():
                config_path = p
                break
        
        if config_path is None:
            # Return default config if file doesn't exist
            return Config()
        
    if not config_path.exists():
        return Config()
        
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
            
        if data is None:
            return Config()
            
        settings_data = data.get('settings', {})
        species_data = data.get('species_list', [])
        
        # Parse settings
        settings = ConfigSettings(**settings_data)
        
        # Parse species list
        species_list = []
        if species_data:
            for sp_data in species_data:
                if sp_data is None:
                    continue
                try:
                    # Assuming Species model has enough fields to be constructed from dict
                    species_list.append(Species(**sp_data))
                except ValidationError as ve:
                    # Log warning but continue loading other species
                    print(f"Warning: Skipping invalid species entry due to validation error: {ve}")
                    continue
                
        _config_instance = Config(settings=settings, species_list=species_list, metadata=data.get('metadata', {}))
        return _config_instance
        
    except ValidationError as e:
        raise ValueError(f"Configuration validation failed: {e}")
    except yaml.YAMLError as ye:
        raise ValueError(f"Failed to parse YAML configuration: {ye}")
    except Exception as e:
        raise RuntimeError(f"Failed to load config from {config_path}: {e}")

def get_config() -> Config:
    """Get the current configuration instance."""
    global _config_instance
    if _config_instance is None:
        _config_instance = load_config()
    return _config_instance

def reset_config() -> None:
    """Reset the configuration singleton to force reload."""
    global _config_instance
    _config_instance = None

def get_species_list() -> List[Species]:
    """Convenience function to get the list of species from config."""
    return get_config().species_list

def get_data_path() -> Path:
    """Convenience function to get the base data path."""
    return get_config().settings.data_path
