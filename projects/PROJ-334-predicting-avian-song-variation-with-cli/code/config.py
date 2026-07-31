import os
import json
from pathlib import Path
from typing import Optional, Dict, Any

class Config:
    """
    Base configuration loader for environment variables and paths.
    
    Loads project paths, data directories, and optional settings from:
    1. Environment variables (highest priority)
    2. .env file (if present)
    3. Hardcoded defaults
    """
    
    def __init__(self, env_file: Optional[Path] = None):
        self.project_root = Path(os.getenv("PROJECT_ROOT", Path(__file__).parent.parent))
        self.data_dir = self.project_root / "data"
        self.code_dir = self.project_root / "code"
        self.tests_dir = self.project_root / "tests"
        self.contracts_dir = self.project_root / "contracts"
        self.figures_dir = self.project_root / "figures"
        
        # Data subdirectories
        self.raw_data_dir = self.data_dir / "raw"
        self.processed_data_dir = self.data_dir / "processed"
        self.models_dir = self.data_dir / "models"
        
        # File paths
        self.checksums_file = self.data_dir / "checksums.txt"
        self.env_file = env_file or self.project_root / ".env"
        
        # API Keys and URLs (from env or defaults)
        self.xeno_canto_base_url = os.getenv(
            "XENO_CANTO_BASE_URL", 
            "https://www.xeno-canto.org/api/2/recordings"
        )
        self.worldclim_base_url = os.getenv(
            "WORLDCCLIM_BASE_URL",
            "https://www.worldclim.org/data/v2.1"
        )
        
        # Load .env if it exists (simple parsing, no external deps)
        if self.env_file.exists():
            self._load_env_file(self.env_file)
        
        # Override with explicit env vars (already loaded by os.getenv, but ensures consistency)
        self._apply_env_overrides()
        
        # Ensure directories exist
        self._ensure_directories()

    def _load_env_file(self, path: Path) -> None:
        """Simple .env file parser."""
        if not path.exists():
            return
        
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, value = line.split("=", 1)
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")
                    # Only set if not already in os.environ (env vars take precedence)
                    if key not in os.environ:
                        os.environ[key] = value

    def _apply_env_overrides(self) -> None:
        """Apply environment variable overrides to config attributes."""
        # Directory overrides
        if "PROJECT_ROOT" in os.environ:
            self.project_root = Path(os.environ["PROJECT_ROOT"])
            self.data_dir = self.project_root / "data"
            self.code_dir = self.project_root / "code"
            self.tests_dir = self.project_root / "tests"
            self.contracts_dir = self.project_root / "contracts"
            self.figures_dir = self.project_root / "figures"
            self.raw_data_dir = self.data_dir / "raw"
            self.processed_data_dir = self.data_dir / "processed"
            self.models_dir = self.data_dir / "models"
            self.checksums_file = self.data_dir / "checksums.txt"

        if "DATA_DIR" in os.environ:
            self.data_dir = Path(os.environ["DATA_DIR"])
            self.raw_data_dir = self.data_dir / "raw"
            self.processed_data_dir = self.data_dir / "processed"
            self.models_dir = self.data_dir / "models"
            self.checksums_file = self.data_dir / "checksums.txt"

        # API URL overrides
        if "XENO_CANTO_BASE_URL" in os.environ:
            self.xeno_canto_base_url = os.environ["XENO_CANTO_BASE_URL"]
        if "WORLDCCLIM_BASE_URL" in os.environ:
            self.worldclim_base_url = os.environ["WORLDCCLIM_BASE_URL"]

    def _ensure_directories(self) -> None:
        """Create all required directories if they don't exist."""
        dirs = [
            self.data_dir,
            self.code_dir,
            self.tests_dir,
            self.contracts_dir,
            self.figures_dir,
            self.raw_data_dir,
            self.processed_data_dir,
            self.models_dir,
        ]
        for d in dirs:
            d.mkdir(parents=True, exist_ok=True)

    def get(self, key: str, default: Optional[Any] = None) -> Any:
        """
        Get a configuration value by key.
        
        Supports dotted notation for nested access if needed in the future.
        Currently maps directly to object attributes or environment variables.
        """
        # Check object attributes first
        if hasattr(self, key):
            return getattr(self, key)
        
        # Fall back to environment variable
        return os.getenv(key, default)

    def to_dict(self) -> Dict[str, Any]:
        """Export configuration as a dictionary."""
        return {
            "project_root": str(self.project_root),
            "data_dir": str(self.data_dir),
            "code_dir": str(self.code_dir),
            "tests_dir": str(self.tests_dir),
            "contracts_dir": str(self.contracts_dir),
            "figures_dir": str(self.figures_dir),
            "raw_data_dir": str(self.raw_data_dir),
            "processed_data_dir": str(self.processed_data_dir),
            "models_dir": str(self.models_dir),
            "checksums_file": str(self.checksums_file),
            "xeno_canto_base_url": self.xeno_canto_base_url,
            "worldclim_base_url": self.worldclim_base_url,
        }

    def __repr__(self) -> str:
        return f"Config(project_root={self.project_root})"

    def __str__(self) -> str:
        return json.dumps(self.to_dict(), indent=2)