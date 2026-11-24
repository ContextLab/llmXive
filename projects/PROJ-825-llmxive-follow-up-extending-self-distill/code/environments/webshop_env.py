"""
WebShop Environment Wrapper.

Implements T008 requirements: verifies that the ``webshop`` package is installed,
constructs a real WebShop environment, and forwards ``reset`` and ``step`` calls
to the underlying environment. No synthetic fallback is provided – any import
or instantiation error is raised immediately.
"""
# Verify that the WebShop package is installed at import time.
try:
    import webshop  # noqa: F401
except ImportError as e:
    raise RuntimeError(
        "WebShop is not installed. Please install it via `pip install webshop`."
    ) from e

from typing import Any, Dict, Optional, Tuple, List

class WebShopWrapper:
    """
    Wrapper for the WebShop environment.

    The wrapper lazily creates a ``WebShopEnv`` (the standard WebShop
    environment class) using the optional ``config`` dictionary. All
    interactions are delegated directly to the underlying environment.
    """

    def __init__(self, config: Optional[Dict] = None):
        """
        Args:
            config: Optional dictionary of keyword arguments passed to the
                underlying ``WebShopEnv`` constructor (e.g. ``seed``,
                ``max_steps``). If omitted, defaults are used.
        """
        self.config = config or {}
        self.env: Any = None
        self._initialized = False

    def reset(self) -> Tuple[str, Dict]:
        """
        Reset the environment and return the initial observation and an info dict.

        Returns:
            observation: The initial textual observation.
            info: Additional information about the reset (contains at least a
                ``status`` field).
        """
        if not self._initialized:
            self._initialize_env()

        # Forward the reset call to the real WebShop environment.
        return self.env.reset()

    def step(self, action: str) -> Tuple[str, float, bool, Dict]:
        """
        Take a step in the environment.

        Args:
            action: The textual action to execute.

        Returns:
            observation: The next observation string.
            reward: Float reward for the step.
            done: Boolean indicating episode termination.
            info: Additional step information.
        """
        if not self._initialized:
            self._initialize_env()

        # Forward the step call to the real WebShop environment.
        return self.env.step(action)

    def _initialize_env(self) -> None:
        """
        Lazily instantiate the underlying WebShop environment.

        The WebShop package provides the ``WebShopEnv`` class. If the class
        cannot be imported, a clear ``RuntimeError`` is raised.
        """
        try:
            from webshop import WebShopEnv
        except Exception as e:
            raise RuntimeError(
                "Failed to import WebShopEnv from the webshop package. "
                "Ensure you have a compatible version installed."
            ) from e

        self.env = WebShopEnv(**self.config)
        self._initialized = True

    def close(self) -> None:
        """
        Close the environment and release resources.
        """
        if self._initialized and hasattr(self.env, "close"):
            self.env.close()
        self._initialized = False

__all__ = ["WebShopWrapper"]
