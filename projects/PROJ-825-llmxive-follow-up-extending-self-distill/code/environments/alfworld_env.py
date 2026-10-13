"""
ALFWorld Environment Wrapper.

Implements T008 requirements: verifies that the ``alfworld`` package is installed,
constructs a real ALFWorld environment, and forwards ``reset`` and ``step`` calls
to the underlying environment. No synthetic fallback is provided – any import
or instantiation error is raised immediately.
"""
# Verify that the ALFWorld package is installed at import time.
try:
    import alfworld  # noqa: F401
except ImportError as e:
    raise RuntimeError(
        "ALFWorld is not installed. Please install it via `pip install alfworld`."
    ) from e

from typing import Any, Dict, Optional, Tuple, List

class ALFWorldWrapper:
    """
    Wrapper for the ALFWorld environment.

    The wrapper lazily creates an ``AlfredTWEnv`` (the standard ALFWorld
    environment class) using the provided ``task_type`` and any additional
    configuration supplied via ``config``. All interactions are delegated
    directly to the underlying environment instance.
    """

    def __init__(self, task_type: str = "pick_and_place", config: Optional[Dict] = None):
        """
        Args:
            task_type: The ALFWorld task type (e.g. ``pick_and_place``).
            config: Optional dictionary of additional keyword arguments passed
                to the underlying ``AlfredTWEnv`` constructor (e.g. ``seed``,
                ``max_steps``). If omitted, defaults are used.
        """
        self.task_type = task_type
        self.config = config or {}
        self.env: Any = None
        self._initialized = False

    # ------------------------------------------------------------------ #
    # Public API expected by the training loop / tests
    # ------------------------------------------------------------------ #
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

        # The real ALFWorld environment returns a tuple (observation, info).
        # We forward that directly.
        observation, info = self.env.reset()
        return observation, info

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

        observation, reward, done, info = self.env.step(action)
        return observation, reward, done, info

    # ------------------------------------------------------------------ #
    # Internal helpers
    # ------------------------------------------------------------------ #
    def _initialize_env(self) -> None:
        """
        Lazily instantiate the underlying ALFWorld environment.

        The ALFWorld package provides the ``AlfredTWEnv`` class. If the class
        cannot be imported (e.g. due to version incompatibility), a clear
        ``RuntimeError`` is raised – there is no silent fallback.
        """
        try:
            # The canonical class name in the alfworld package.
            from alfworld import AlfredTWEnv
        except Exception as e:
            raise RuntimeError(
                "Failed to import AlfredTWEnv from the alfworld package. "
                "Ensure you have a compatible version installed."
            ) from e

        # Merge the task_type with any user‑provided configuration.
        init_kwargs = {"task_type": self.task_type, **self.config}
        self.env = AlfredTWEnv(**init_kwargs)
        self._initialized = True

    def close(self) -> None:
        """
        Close the environment and release resources.
        """
        if self._initialized and hasattr(self.env, "close"):
            self.env.close()
        self._initialized = False

__all__ = ["ALFWorldWrapper"]
