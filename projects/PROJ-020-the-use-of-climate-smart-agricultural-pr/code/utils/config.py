import os
import sys
from pathlib import Path
from typing import List, Optional, Set

class ConfigError(Exception):
    """Exception raised for configuration errors."""
    pass

class Config:
    """
    Centralized configuration manager for the project.
    Loads defaults but prioritizes environment variables for:
    - Target countries (comma-separated ISO codes)
    - Target years (comma-separated integers, inclusive range)
    - Data directory path
    - Maximum RAM limit in GB
    """
    def __init__(self):
        # Default values (overridden by env vars if present)
        self._target_countries: List[str] = self._parse_env_countries()
        self._target_years: List[int] = self._parse_env_years()
        self._data_dir: Path = self._parse_env_data_dir()
        self._max_ram_gb: int = self._parse_env_ram()

    def _parse_env_countries(self) -> List[str]:
        """Parse TARGET_COUNTRIES env var or return defaults."""
        default = ["KEN", "IND", "VNM"]
        env_val = os.getenv("TARGET_COUNTRIES")
        if env_val:
            return [c.strip().upper() for c in env_val.split(",") if c.strip()]
        return default

    def _parse_env_years(self) -> List[int]:
        """
        Parse TARGET_YEARS env var or return defaults.
        Supports comma-separated years (e.g., "2015,2020,2023")
        or range syntax (e.g., "2015-2023").
        """
        default = list(range(2015, 2024))  # 2015-2023 inclusive
        env_val = os.getenv("TARGET_YEARS")
        if not env_val:
            return default

        years = []
        parts = [p.strip() for p in env_val.split(",") if p.strip()]
        for part in parts:
            if "-" in part:
                try:
                    start, end = part.split("-")
                    years.extend(range(int(start), int(end) + 1))
                except ValueError:
                    raise ConfigError(f"Invalid year range format: {part}")
            else:
                try:
                    years.append(int(part))
                except ValueError:
                    raise ConfigError(f"Invalid year value: {part}")

        return sorted(list(set(years))) if years else default

    def _parse_env_data_dir(self) -> Path:
        """Parse DATA_DIR env var or return default."""
        default = Path("data")
        env_val = os.getenv("DATA_DIR")
        if env_val:
            return Path(env_val)
        return default

    def _parse_env_ram(self) -> int:
        """Parse MAX_RAM_GB env var or return default."""
        default = 7
        env_val = os.getenv("MAX_RAM_GB")
        if env_val:
            try:
                return int(env_val)
            except ValueError:
                raise ConfigError(f"Invalid MAX_RAM_GB value: {env_val}")
        return default

    def set_target_countries(self, countries: List[str]):
        """Override target countries programmatically."""
        self._target_countries = [c.upper() for c in countries]

    def set_target_years(self, years: List[int]):
        """Override target years programmatically."""
        self._target_years = sorted(list(set(years)))

    def set_data_dir(self, path: Path):
        """Override data directory programmatically."""
        self._data_dir = Path(path)

    def set_max_ram_gb(self, gb: int):
        """Override max RAM limit programmatically."""
        self._max_ram_gb = gb

    @property
    def target_countries(self) -> List[str]:
        return self._target_countries

    @property
    def target_years(self) -> List[int]:
        return self._target_years

    @property
    def data_dir(self) -> Path:
        return self._data_dir

    @property
    def max_ram_gb(self) -> int:
        return self._max_ram_gb

# Singleton instance
_config = Config()

def get_config() -> Config:
    """Return the singleton Config instance."""
    return _config

def reset_config():
    """Reset configuration to current environment variables."""
    global _config
    _config = Config()

def get_target_countries() -> List[str]:
    """Get target countries from config (supports env var override)."""
    return _config.target_countries

def get_target_years() -> List[int]:
    """Get target years from config (supports env var override)."""
    return _config.target_years

def get_data_dir() -> Path:
    """Get data directory from config (supports env var override)."""
    return _config.data_dir

def get_raw_data_dir() -> Path:
    """Get raw data directory path."""
    return _config.data_dir / "raw"

def get_processed_data_dir() -> Path:
    """Get processed data directory path."""
    return _config.data_dir / "processed"

def get_state_dir() -> Path:
    """Get state/checksums directory path."""
    return _config.data_dir / "state"

def get_max_ram_gb() -> int:
    """Get maximum RAM limit in GB."""
    return _config.max_ram_gb

def get_memory_limit_bytes() -> int:
    """Get maximum RAM limit in bytes."""
    return _config.max_ram_gb * 1024 * 1024 * 1024