"""
Configuration management for the dipole‑moment prediction project.

This module loads environment variables (optionally from a ``.env`` file)
and provides a :class:`Config` dataclass that can be imported throughout
the code‑base.

The implementation avoids a hard dependency on ``python-dotenv`` – if the
package is available it will be used; otherwise a very small fallback
parser reads ``.env`` manually.
"""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any


def _load_dotenv() -> None:
    """
    Load environment variables from a ``.env`` file located in the project
    root (the directory that contains the ``code`` package).  If the
    optional ``python-dotenv`` package is installed it will be used;
    otherwise a minimal manual parser is applied.
    """
    # The project root is the parent directory of this ``config.py`` file's
    # ``code`` folder.
    project_root = Path(__file__).resolve().parents[1]
    env_path = project_root / ".env"

    if not env_path.is_file():
        return  # Nothing to load

    try:
        # Prefer the robust implementation from python‑dotenv if available.
        from dotenv import load_dotenv  # type: ignore

        load_dotenv(dotenv_path=env_path)
    except Exception:
        # Fallback: simple line‑by‑line parsing (ignores export statements,
        # comments and quoted values).
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('\'"')
            os.environ.setdefault(key, value)


# Load the .env file as soon as this module is imported.
_load_dotenv()


@dataclass(frozen=True)
class Config:
    """
    Immutable configuration container.  All values are read from the
    environment with sensible defaults.
    """

    # General settings
    random_seed: int = int(os.getenv("RANDOM_SEED", "42"))
    data_root: Path = Path(os.getenv("DATA_ROOT", "data"))
    checkpoint_dir: Path = Path(os.getenv("CHECKPOINT_DIR", str(data_root / "checkpoints")))
    log_level: str = os.getenv("LOG_LEVEL", "INFO")

    # Resource constraints
    cpu_cores: int = int(os.getenv("CPU_CORES", "2"))
    pipeline_time_limit: int = int(os.getenv("PIPELINE_TIME_LIMIT", "21600"))  # seconds (6 h)

    # Helper properties
    @property
    def raw_data_dir(self) -> Path:
        """Directory for raw downloaded data."""
        return self.data_root / "raw"

    @property
    def processed_data_dir(self) -> Path:
        """Directory for processed feature files."""
        return self.data_root / "processed"

    @property
    def results_dir(self) -> Path:
        """Directory where result artefacts such as metrics and figures are stored."""
        return Path("results")

    def as_dict(self) -> dict[str, Any]:
        """Return a plain dictionary representation (useful for logging)."""
        return {
            "random_seed": self.random_seed,
            "data_root": str(self.data_root),
            "checkpoint_dir": str(self.checkpoint_dir),
            "log_level": self.log_level,
            "cpu_cores": self.cpu_cores,
            "pipeline_time_limit": self.pipeline_time_limit,
        }


# Export a singleton for convenient import ``from config import cfg``.
cfg = Config()

__all__ = ["Config", "cfg"]