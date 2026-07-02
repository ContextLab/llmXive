"""
Base configuration loader for environment variables and paths.

This module provides a centralized way to manage project configuration,
including environment variable overrides and path resolution.
"""
import os
import json
from pathlib import Path
from typing import Optional, Dict, Any

# Project root is assumed to be the parent of the 'code' directory
# If running from code/, go up one level
_CODE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = _CODE_DIR.parent if _CODE_DIR.name == "code" else _CODE_DIR

# Default directory structure
DEFAULT_DATA_DIR = PROJECT_ROOT / "data"
DEFAULT_DATA_RAW = DEFAULT_DATA_DIR / "raw"
DEFAULT_DATA_PROCESSED = DEFAULT_DATA_DIR / "processed"
DEFAULT_DATA_FIGURES = DEFAULT_DATA_DIR / "figures"
DEFAULT_CONTRACTS_DIR = PROJECT_ROOT / "contracts"
DEFAULT_LOGS_DIR = PROJECT_ROOT / "logs"

# Environment variable prefixes
ENV_PREFIX = "AVIAN_SONG_"

def _get_env_str(key: str, default: str = "") -> str:
    """Get string environment variable with fallback to default."""
    full_key = f"{ENV_PREFIX}{key}"
    return os.getenv(full_key, default)

def _get_env_path(key: str, default: Optional[Path] = None) -> Path:
    """Get path environment variable, resolving relative to project root if needed."""
    val = _get_env_str(key)
    if not val:
        return default or PROJECT_ROOT
    p = Path(val)
    if not p.is_absolute():
        p = PROJECT_ROOT / p
    return p.resolve()

def _get_env_bool(key: str, default: bool = False) -> bool:
    """Get boolean environment variable."""
    val = _get_env_str(key)
    if not val:
        return default
    return val.lower() in ("true", "1", "yes", "on")

class Config:
    """
    Central configuration object for the project.
    
    Loads settings from environment variables prefixed with AVIAN_SONG_.
    If not set, falls back to defaults based on project structure.
    """
    
    def __init__(self):
        # Paths
        self.project_root = _get_env_path("PROJECT_ROOT", PROJECT_ROOT)
        self.data_dir = _get_env_path("DATA_DIR", DEFAULT_DATA_DIR)
        self.data_raw = _get_env_path("DATA_RAW_DIR", DEFAULT_DATA_RAW)
        self.data_processed = _get_env_path("DATA_PROCESSED_DIR", DEFAULT_DATA_PROCESSED)
        self.data_figures = _get_env_path("DATA_FIGURES_DIR", DEFAULT_DATA_FIGURES)
        self.contracts_dir = _get_env_path("CONTRACTS_DIR", DEFAULT_CONTRACTS_DIR)
        self.logs_dir = _get_env_path("LOGS_DIR", DEFAULT_LOGS_DIR)
        
        # Data sources
        self.xeno_canto_api_base = _get_env_str("XENOCANTO_API_BASE", "https://www.xeno-canto.org/api/2")
        self.worldclim_base_url = _get_env_str("WORLDCCLIM_BASE_URL", "https://biogeo.ucdavis.edu/data/worldclim/v2.1")
        
        # Analysis settings
        self.spatial_join_radius_km = float(_get_env_str("SPATIAL_JOIN_RADIUS_KM", "10.0"))
        self.multicollinearity_threshold = float(_get_env_str("MULTICOLLINEARITY_THRESHOLD", "0.8"))
        self.vif_threshold = float(_get_env_str("VIF_THRESHOLD", "5.0"))
        self.p_value_thresholds = [float(x) for x in _get_env_str("P_VALUE_THRESHOLDS", "0.01,0.05,0.10").split(",")]
        
        # Logging
        self.log_level = _get_env_str("LOG_LEVEL", "INFO").upper()
        self.log_to_file = _get_env_bool("LOG_TO_FILE", True)
        self.log_to_console = _get_env_bool("LOG_TO_CONSOLE", True)
        
        # Validation
        self.strict_validation = _get_env_bool("STRICT_VALIDATION", False)
        
        # Ensure directories exist
        self._ensure_dirs()

    def _ensure_dirs(self):
        """Create necessary directories if they don't exist."""
        dirs = [
            self.data_dir,
            self.data_raw,
            self.data_processed,
            self.data_figures,
            self.contracts_dir,
            self.logs_dir
        ]
        for d in dirs:
            d.mkdir(parents=True, exist_ok=True)

    def to_dict(self) -> Dict[str, Any]:
        """Export configuration as a dictionary."""
        exclude = {"project_root"}  # Avoid recursion issues
        return {
            k: str(v) if isinstance(v, Path) else v
            for k, v in self.__dict__.items()
            if not k.startswith("_") and k not in exclude
        }

    def save(self, path: Optional[Path] = None):
        """Save current configuration to a JSON file."""
        if path is None:
            path = self.data_dir / "config_snapshot.json"
        else:
            path = Path(path)
            
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2, default=str)

    @classmethod
    def load(cls, path: Path) -> "Config":
        """Load configuration from a JSON file and override defaults."""
        cfg = cls()
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        for key, value in data.items():
            if hasattr(cfg, key):
                setattr(cfg, key, value)
        
        cfg._ensure_dirs()
        return cfg

# Global instance for convenience
config = Config()

if __name__ == "__main__":
    # Simple test: print current config
    import sys
    print("Current Configuration:")
    print(json.dumps(config.to_dict(), indent=2, default=str))
    print(f"\nProject Root: {config.project_root}")
    print(f"Data Dir: {config.data_dir}")
    print(f"Contracts Dir: {config.contracts_dir}")
    
    # Test saving
    save_path = config.data_dir / "test_config.json"
    config.save(save_path)
    print(f"\nSaved test config to: {save_path}")
    
    # Test loading
    loaded = Config.load(save_path)
    print(f"Loaded config project root: {loaded.project_root}")
    
    # Cleanup
    save_path.unlink()
    print("Test complete.")
