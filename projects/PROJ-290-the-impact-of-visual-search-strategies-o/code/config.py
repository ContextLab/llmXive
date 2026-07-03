import os
from pathlib import Path
from typing import Any, Dict, Optional
import yaml

class Config:
    """
    Configuration manager for the project.
    Loads defaults and overrides from environment variables.
    """

    # Default paths relative to project root
    _DEFAULTS: Dict[str, Any] = {
        "data_root": "data",
        "data_raw": "data/raw",
        "data_processed": "data/processed",
        "results_root": "results",
        "results_figures": "results/figures",
        "results_reports": "results/reports",
        "state_root": "state",
        "code_root": "code",
        "tests_root": "tests",
        "logs_root": "logs",
        "log_level": "INFO",
        "hf_cache_dir": None,  # Defaults to HuggingFace default
    }

    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or Path.cwd()
        self._values: Dict[str, Any] = {}
        self._load_defaults()
        self._load_env_overrides()

    def _load_defaults(self):
        """Load default configuration values."""
        self._values = self._DEFAULTS.copy()

    def _load_env_overrides(self):
        """Override defaults with environment variables."""
        env_prefix = "LLMXIVE_"
        for key in self._values:
            env_key = f"{env_prefix}{key.upper()}"
            if env_key in os.environ:
                val = os.environ[env_key]
                # Simple type coercion
                if val.lower() in ("true", "1", "yes"):
                    self._values[key] = True
                elif val.lower() in ("false", "0", "no"):
                    self._values[key] = False
                elif val.isdigit():
                    self._values[key] = int(val)
                else:
                    self._values[key] = val

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value."""
        return self._values.get(key, default)

    def get_path(self, key: str, relative: bool = True) -> Path:
        """Get a configuration value as a Path object."""
        val = self._values.get(key)
        if val is None:
            return self.project_root / key
        p = Path(val)
        if not p.is_absolute():
            p = self.project_root / p
        return p.resolve()

    def to_dict(self) -> Dict[str, Any]:
        """Return configuration as a dictionary."""
        return self._values.copy()

    def save(self, path: Path):
        """Save configuration to a YAML file."""
        with open(path, "w") as f:
            yaml.dump(self._values, f)

    @classmethod
    def load(cls, path: Path) -> "Config":
        """Load configuration from a YAML file."""
        cfg = cls()
        if path.exists():
            with open(path, "r") as f:
                overrides = yaml.safe_load(f)
            if overrides:
                cfg._values.update(overrides)
        return cfg

_CONFIG_INSTANCE: Optional[Config] = None

def get_config(project_root: Optional[Path] = None) -> Config:
    """
    Get the singleton configuration instance.
    Creates it if it doesn't exist.
    """
    global _CONFIG_INSTANCE
    if _CONFIG_INSTANCE is None:
        _CONFIG_INSTANCE = Config(project_root)
    return _CONFIG_INSTANCE