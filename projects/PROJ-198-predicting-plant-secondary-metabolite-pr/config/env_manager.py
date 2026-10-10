"""
Environment configuration manager for the project.

Provides a singleton ``EnvManager`` that loads variables from a ``.env`` file
(using ``python‑dotenv``) and offers convenient typed accessors.

The public API matches what the test suite expects:

- ``EnvManager`` class with ``get``, ``get_bool``, ``get_int`` methods and
  path properties (data_root, raw_data_path, processed_data_path, figures_path,
  mock_* paths).
- ``get_env_manager()`` function returning a global singleton.
"""

import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

# Global singleton instance – created on first ``get_env_manager`` call.
_env_manager: Optional["EnvManager"] = None


class EnvManager:
    """
    Loads environment variables from a ``.env`` file and provides typed access.
    
    The manager is deliberately lightweight – it does not perform any I/O
    beyond loading the ``.env`` file at initialization. All subsequent
    accesses are pure ``os.getenv`` calls.
    """

    def __init__(self, env_path: Optional[Path] = None):
        """
        Initialise the manager.

        Parameters
        ----------
        env_path: Path | None
            Path to the ``.env`` file. If ``None`` the file ``.env`` in the
            current working directory is used. The file is optional – missing
            files are ignored; only variables already present in the process
            environment will be available.
        """
        if env_path is None:
            env_path = Path.cwd() / ".env"
        self._env_path = env_path
        # Load variables – ``override=True`` ensures values in the file take
        # precedence over existing environment variables (useful for CI).
        load_dotenv(dotenv_path=self._env_path, override=True)

        # Determine CI mode early – many helpers depend on it.
        self.is_ci_mode: bool = self.get_bool("CI_MODE", default=False)

    # ------------------------------------------------------------------
    # Generic getters
    # ------------------------------------------------------------------
    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """
        Retrieve a raw string value from the environment.

        Parameters
        ----------
        key: str
            Environment variable name.
        default: str | None
            Value to return if the variable is missing.

        Returns
        -------
        str | None
        """
        return os.getenv(key, default)

    def get_bool(self, key: str, default: bool = False) -> bool:
        """
        Retrieve a boolean value.

        Accepts typical truthy strings (case‑insensitive):
        ``1``, ``true``, ``yes``, ``on``.

        Parameters
        ----------
        key: str
            Variable name.
        default: bool
            Value to return if the variable is missing or unparsable.

        Returns
        -------
        bool
        """
        val = self.get(key)
        if val is None:
            return default
        return val.strip().lower() in {"1", "true", "yes", "on"}

    def get_int(self, key: str, default: int = 0) -> int:
        """
        Retrieve an integer value.

        Parameters
        ----------
        key: str
            Variable name.
        default: int
            Value to return if conversion fails.

        Returns
        -------
        int
        """
        val = self.get(key)
        try:
            return int(val)
        except (TypeError, ValueError):
            return default

    # ------------------------------------------------------------------
    # Path properties (derived from ``DATA_ROOT`` or defaults)
    # ------------------------------------------------------------------
    @property
    def data_root(self) -> Path:
        """Base data directory (defaults to ``./data``)."""
        return Path(self.get("DATA_ROOT", "data"))

    @property
    def raw_data_path(self) -> Path:
        """Path to raw data (``<data_root>/raw``)."""
        return self.data_root / "raw"

    @property
    def processed_data_path(self) -> Path:
        """Path to processed data (``<data_root>/processed``)."""
        return self.data_root / "processed"

    @property
    def figures_path(self) -> Path:
        """Path to figures (``<project_root>/figures``)."""
        # Figures are not under ``data_root``; they live at the repo root.
        return Path(self.get("FIGURES_ROOT", "figures"))

    # ------------------------------------------------------------------
    # Mock data paths – only relevant when ``CI_MODE`` is true.
    # ------------------------------------------------------------------
    @property
    def mock_genomes_path(self) -> Path:
        """Path to mock genome JSON used in CI mode."""
        return self.raw_data_path / "mock_genomes.json"

    @property
    def mock_metabolites_path(self) -> Path:
        """Path to mock metabolite CSV used in CI mode."""
        return self.raw_data_path / "mock_metabolites.csv"

    @property
    def mock_anti_smash_path(self) -> Path:
        """Path to mock antiSMASH JSON used in CI mode."""
        return self.raw_data_path / "mock_anti_smash.json"

    # ------------------------------------------------------------------
    # Validation helpers
    # ------------------------------------------------------------------
    def validate_required_keys(self) -> bool:
        """
        Ensure that all mandatory API keys are present.

        In CI mode the keys are optional – the pipeline can run with mock data.

        Returns
        -------
        bool
            ``True`` if validation passes, ``False`` otherwise.
        """
        if self.is_ci_mode:
            return True
        required = {"NCBI_API_KEY", "PMDB_API_TOKEN"}
        missing = [k for k in required if not self.get(k)]
        return len(missing) == 0

    # ------------------------------------------------------------------
    # Convenience properties for specific API keys
    # ------------------------------------------------------------------
    @property
    def ncbi_api_key(self) -> Optional[str]:
        return self.get("NCBI_API_KEY")

    @property
    def pmdb_api_token(self) -> Optional[str]:
        return self.get("PMDB_API_TOKEN")


def get_env_manager() -> EnvManager:
    """
    Return the global singleton ``EnvManager`` instance.

    The first call constructs the manager (reading ``.env`` if present);
    subsequent calls return the same object.
    """
    global _env_manager
    if _env_manager is None:
        _env_manager = EnvManager()
    return _env_manager
