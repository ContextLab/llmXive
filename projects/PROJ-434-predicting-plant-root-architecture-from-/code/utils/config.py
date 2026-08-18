import os
from pathlib import Path
from typing import Optional, Dict, Any
import warnings

try:
    from dotenv import load_dotenv
except ImportError:
    warnings.warn("python-dotenv not installed. Install it via 'pip install python-dotenv' to enable .env support.")
    load_dotenv = None

class Config:
    """
    Centralized configuration manager for the project.
    Handles loading environment variables from .env files and providing
    typed access to configuration values.
    """

    def __init__(self, env_path: Optional[Path] = None):
        """
        Initialize the Config instance.

        Args:
            env_path: Path to the .env file. If None, looks for .env in the
                      project root or current working directory.
        """
        self._env_path = env_path
        self._loaded = False
        self._values: Dict[str, str] = {}

    def load(self) -> None:
        """
        Load environment variables from the .env file.
        This method should be called once at application startup.
        """
        if self._loaded:
            return

        if load_dotenv is None:
            # If dotenv is not installed, rely solely on system env vars
            self._loaded = True
            return

        if self._env_path:
            if not self._env_path.exists():
                warnings.warn(f"Environment file not found: {self._env_path}")
            else:
                load_dotenv(self._env_path)
        else:
            # Default behavior: look for .env in current directory or project root
            current_dir = Path.cwd()
            project_root = current_dir.parent if current_dir.name == "code" else current_dir
            env_file = project_root / ".env"

            if env_file.exists():
                load_dotenv(env_file)
            else:
                # Fallback to current directory
                load_dotenv()

        self._loaded = True

    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """
        Get an environment variable value.

        Args:
            key: The environment variable name.
            default: Default value if the variable is not set.

        Returns:
            The value of the environment variable or the default.
        """
        self.load()
        return os.getenv(key, default)

    def get_int(self, key: str, default: Optional[int] = None) -> Optional[int]:
        """
        Get an environment variable as an integer.

        Args:
            key: The environment variable name.
            default: Default value if the variable is not set or invalid.

        Returns:
            The integer value or the default.
        """
        value = self.get(key)
        if value is None:
            return default
        try:
            return int(value)
        except ValueError:
            warnings.warn(f"Cannot convert {key} to int: {value}")
            return default

    def get_float(self, key: str, default: Optional[float] = None) -> Optional[float]:
        """
        Get an environment variable as a float.

        Args:
            key: The environment variable name.
            default: Default value if the variable is not set or invalid.

        Returns:
            The float value or the default.
        """
        value = self.get(key)
        if value is None:
            return default
        try:
            return float(value)
        except ValueError:
            warnings.warn(f"Cannot convert {key} to float: {value}")
            return default

    def get_bool(self, key: str, default: Optional[bool] = None) -> Optional[bool]:
        """
        Get an environment variable as a boolean.

        Args:
            key: The environment variable name.
            default: Default value if the variable is not set or invalid.

        Returns:
            The boolean value or the default.
        """
        value = self.get(key)
        if value is None:
            return default
        if value.lower() in ('true', '1', 'yes', 'on'):
            return True
        elif value.lower() in ('false', '0', 'no', 'off'):
            return False
        else:
            warnings.warn(f"Cannot convert {key} to bool: {value}")
            return default

    def require(self, key: str) -> str:
        """
        Get a required environment variable, raising an error if not set.

        Args:
            key: The environment variable name.

        Returns:
            The value of the environment variable.

        Raises:
            ValueError: If the environment variable is not set.
        """
        value = self.get(key)
        if value is None:
            raise ValueError(f"Required environment variable '{key}' is not set")
        return value

    def to_dict(self) -> Dict[str, str]:
        """
        Get all loaded environment variables as a dictionary.

        Returns:
            A dictionary of environment variable names and values.
        """
        self.load()
        return dict(os.environ)


# Global config instance
_config = Config()


def load_environment(env_path: Optional[Path] = None) -> None:
    """
    Load environment variables from the .env file using the global config.

    Args:
        env_path: Optional path to the .env file.
    """
    _config._env_path = env_path
    _config.load()


def get_env(key: str, default: Optional[str] = None) -> Optional[str]:
    """
    Get an environment variable value using the global config.

    Args:
        key: The environment variable name.
        default: Default value if the variable is not set.

    Returns:
        The value of the environment variable or the default.
    """
    return _config.get(key, default)
