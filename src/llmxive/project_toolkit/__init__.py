"""Code the platform gives to every research project.

``llmxive_toolkit`` (the package in this directory) is importable from any
project's analysis code. It is NOT part of ``llmxive``: a project sees this
directory on its path and nothing else of the platform.
"""

from pathlib import Path

#: Directory to put on a project's import path.
TOOLKIT_PATH = Path(__file__).resolve().parent

__all__ = ["TOOLKIT_PATH"]
