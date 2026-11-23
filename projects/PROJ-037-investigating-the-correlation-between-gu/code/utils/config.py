"""
Configuration loader for environment variables and project paths.
"""
import os
from pathlib import Path
from typing import Any, Dict, Optional

class Config:
    """
    Centralized configuration management for the project.
    Loads paths and settings from environment variables or defaults.
    """

    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or Path(__file__).resolve().parent.parent.parent
        self.data_root = self.project_root / "data"
        self.code_root = self.project_root / "code"
        self.tests_root = self.project_root / "tests"
        self.logs_root = self.project_root / "logs"
        self.figures_root = self.data_root / "outputs"
        self.raw_data_root = self.data_root / "raw"
        self.processed_data_root = self.data_root / "processed"

        # Ensure directories exist
        self._ensure_dirs()

    def _ensure_dirs(self) -> None:
        """Create necessary directories if they don't exist."""
        dirs = [
            self.data_root,
            self.code_root,
            self.tests_root,
            self.logs_root,
            self.figures_root,
            self.raw_data_root,
            self.processed_data_root,
        ]
        for d in dirs:
            d.mkdir(parents=True, exist_ok=True)

    def get_path(self, relative_path: str, base: Optional[Path] = None) -> Path:
        """
        Resolve a relative path against a base directory.
        Defaults to project_root if base is not specified.
        """
        base = base or self.project_root
        return base / relative_path

    def to_dict(self) -> Dict[str, Any]:
        """Export configuration as a dictionary."""
        return {
            "project_root": str(self.project_root),
            "data_root": str(self.data_root),
            "code_root": str(self.code_root),
            "tests_root": str(self.tests_root),
            "logs_root": str(self.logs_root),
            "figures_root": str(self.figures_root),
            "raw_data_root": str(self.raw_data_root),
            "processed_data_root": str(self.processed_data_root),
        }

_global_config: Optional[Config] = None

def get_config() -> Config:
    """
    Get the singleton configuration instance.
    Initializes it if it hasn't been created yet.
    """
    global _global_config
    if _global_config is None:
        _global_config = Config()
    return _global_config
