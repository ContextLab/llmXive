import os
import json
from pathlib import Path
from typing import Optional, Dict, Any

class Config:
    """
    Base configuration loader for environment variables and paths.
    
    Handles loading project root, data directories, and environment-specific
    settings. Provides a centralized source of truth for file paths used
    throughout the pipeline.
    """
    
    def __init__(self, env_prefix: str = "AVIAN_SONG"):
        self.env_prefix = env_prefix
        self._root: Optional[Path] = None
        self._data_dir: Optional[Path] = None
        self._data_raw: Optional[Path] = None
        self._data_processed: Optional[Path] = None
        self._contracts_dir: Optional[Path] = None
        self._figures_dir: Optional[Path] = None
        self._models_dir: Optional[Path] = None
        
        # Load configuration from environment or defaults
        self._load_from_env()
        self._resolve_paths()
    
    def _load_from_env(self) -> None:
        """Load configuration from environment variables."""
        # Project root (defaults to current working directory if not set)
        root_env = os.getenv(f"{self.env_prefix}_ROOT")
        if root_env:
            self._root = Path(root_env).resolve()
        else:
            # Default to project root based on file location
            self._root = Path(__file__).resolve().parent.parent
        
        # Data directory
        data_env = os.getenv(f"{self.env_prefix}_DATA_DIR")
        if data_env:
            self._data_dir = Path(data_env).resolve()
        else:
            self._data_dir = self._root / "data"
        
        # Data subdirectories
        self._data_raw = self._data_dir / "raw"
        self._data_processed = self._data_dir / "processed"
        
        # Contracts directory
        contracts_env = os.getenv(f"{self.env_prefix}_CONTRACTS_DIR")
        if contracts_env:
            self._contracts_dir = Path(contracts_env).resolve()
        else:
            self._contracts_dir = self._root / "contracts"
        
        # Figures directory
        figures_env = os.getenv(f"{self.env_prefix}_FIGURES_DIR")
        if figures_env:
            self._figures_dir = Path(figures_env).resolve()
        else:
            self._figures_dir = self._root / "figures"
        
        # Models directory
        models_env = os.getenv(f"{self.env_prefix}_MODELS_DIR")
        if models_env:
            self._models_dir = Path(models_env).resolve()
        else:
            self._models_dir = self._root / "data" / "models"
    
    def _resolve_paths(self) -> None:
        """Ensure all directories exist and paths are absolute."""
        # Ensure data directories exist
        self._data_raw.mkdir(parents=True, exist_ok=True)
        self._data_processed.mkdir(parents=True, exist_ok=True)
        self._figures_dir.mkdir(parents=True, exist_ok=True)
        self._models_dir.mkdir(parents=True, exist_ok=True)
        
        # Ensure contracts directory exists (for validation)
        if not self._contracts_dir.exists():
            self._contracts_dir.mkdir(parents=True, exist_ok=True)
    
    @property
    def root(self) -> Path:
        """Return the project root directory."""
        return self._root
    
    @property
    def data_dir(self) -> Path:
        """Return the main data directory."""
        return self._data_dir
    
    @property
    def data_raw(self) -> Path:
        """Return the raw data directory."""
        return self._data_raw
    
    @property
    def data_processed(self) -> Path:
        """Return the processed data directory."""
        return self._data_processed
    
    @property
    def contracts_dir(self) -> Path:
        """Return the contracts directory."""
        return self._contracts_dir
    
    @property
    def figures_dir(self) -> Path:
        """Return the figures directory."""
        return self._figures_dir
    
    @property
    def models_dir(self) -> Path:
        """Return the models directory."""
        return self._models_dir
    
    @property
    def checksums_file(self) -> Path:
        """Return the path to the checksums file."""
        return self._data_dir / "checksums.txt"
    
    def get_path(self, relative_path: str) -> Path:
        """
        Get an absolute path relative to the project root.
        
        Args:
            relative_path: Path relative to project root
        
        Returns:
            Absolute Path object
        """
        return self._root / relative_path
    
    def get_data_path(self, relative_path: str) -> Path:
        """
        Get an absolute path relative to the data directory.
        
        Args:
            relative_path: Path relative to data directory
        
        Returns:
            Absolute Path object
        """
        return self._data_dir / relative_path
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert configuration to a dictionary for logging/debugging.
        
        Returns:
            Dictionary representation of configuration
        """
        return {
            "root": str(self._root),
            "data_dir": str(self._data_dir),
            "data_raw": str(self._data_raw),
            "data_processed": str(self._data_processed),
            "contracts_dir": str(self._contracts_dir),
            "figures_dir": str(self._figures_dir),
            "models_dir": str(self._models_dir),
            "checksums_file": str(self.checksums_file),
        }
    
    def __repr__(self) -> str:
        return f"Config(root={self._root}, data={self._data_dir})"
