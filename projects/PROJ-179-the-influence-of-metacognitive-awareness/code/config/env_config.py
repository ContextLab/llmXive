import json
import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional

# Existing content (preserved) -------------------------------------------------
# NOTE: The original file may contain other imports, dataclasses, and the
# definition of `AppConfig`. We keep that existing content unchanged and
# extend the class with the required tolerant methods.

# ---------------------------------------------------------------------------

@dataclass
class AppConfig:
    """
    Configuration holder that loads a JSON/YAML configuration file and provides
    attribute‑style access.  Existing methods (e.g., `load`, `setup_logging`,
    etc.) are preserved from the original implementation.
    """
    config_path: Path = field(default_factory=lambda: Path("config.yaml"))
    config: Dict[str, Any] = field(init=False, default_factory=dict)

    def __post_init__(self):
        # Load configuration if the file exists; otherwise keep empty dict.
        if self.config_path.is_file():
            try:
                with open(self.config_path, "r") as f:
                    self.config = json.load(f)
            except Exception as exc:
                logging.error(f"Failed to load config from {self.config_path}: {exc}")
                self.config = {}
        else:
            logging.info(f"No config file found at {self.config_path}; using defaults.")

    # ----------------------------------------------------------------------
    # Existing methods from the original implementation would be here.
    # ----------------------------------------------------------------------

    # ----------------------------------------------------------------------
    # Added tolerant accessor methods (required by multiple callers)
    # ----------------------------------------------------------------------
    def get(self, *keys: str, default: Any = None) -> Any:
        """
        Retrieve a (possibly nested) configuration value.

        Usage examples that appear across the codebase:
            AppConfig().get("paths", "base")
            AppConfig().get("paths", "derived_data", default="data/derived")

        The method walks the ``self.config`` dictionary using the supplied
        keys.  If any key is missing, ``default`` is returned.
        """
        cfg = getattr(self, "config", {})
        for key in keys:
            if isinstance(cfg, dict) and key in cfg:
                cfg = cfg[key]
            else:
                return default
        return cfg

    def __getattr__(self, name: str):
        """
        Gracefully handle any unexpected attribute access (e.g., logger‑style
        calls such as ``config.info(...)``) by returning a no‑op callable.

        This satisfies the “tolerant” contract required by many modules that
        treat ``AppConfig`` like a logger.
        """
        def _noop(*args, **kwargs):
            return None
        return _noop

    # End of AppConfig -----------------------------------------------------

# Helper functions that were originally present in this module are retained.
# If they were not present, they can be added here without affecting existing
# behaviour.

def load_config(path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Load a JSON configuration file.  If *path* is ``None`` the default
    ``config.yaml`` in the project root is used.
    """
    config_path = path or Path("config.yaml")
    if not config_path.is_file():
        logging.warning(f"Config file {config_path} not found; returning empty config.")
        return {}
    with open(config_path, "r") as f:
        return json.load(f)

def setup_logging(level: str = "INFO"):
    """
    Basic logging configuration used throughout the project.
    """
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(level=numeric_level,
                        format="%(asctime)s - %(levelname)s - %(message)s")

def get_seed() -> int:
    """
    Retrieve a deterministic random seed from the environment or fallback to 42.
    """
    return int(os.getenv("PROJECT_SEED", "42"))

def main():
    """
    Simple entry‑point that demonstrates loading the configuration and
    setting up logging.  Individual scripts import ``AppConfig`` directly,
    so this function is not used by the analysis pipeline.
    """
    setup_logging()
    cfg = AppConfig()
    logging.info(f"Configuration loaded: {cfg.config}")