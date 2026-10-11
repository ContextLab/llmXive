"""Code the platform gives to every research project.

``llmxive_toolkit`` (the package in this directory) is importable from any
project's analysis code. It is NOT part of ``llmxive``: a project sees this
directory on its path and nothing else of the platform.
"""

from pathlib import Path

#: Directory to put on a project's import path.
TOOLKIT_PATH = Path(__file__).resolve().parent

#: The importable name. A project file or folder with this name is a COPY.
TOOLKIT_NAME = "llmxive_toolkit"


def is_toolkit_copy(rel: str) -> bool:
    """Whether a project-relative path would create the project's own toolkit.

    ``llmxive_toolkit/…`` or ``llmxive_toolkit.py`` at any depth: anywhere on a
    project's import path it would be imported in place of the platform's.
    """
    parts = str(rel).replace("\\", "/").split("/")
    return TOOLKIT_NAME in parts[:-1] or parts[-1] in {TOOLKIT_NAME, f"{TOOLKIT_NAME}.py"}


__all__ = ["TOOLKIT_NAME", "TOOLKIT_PATH", "is_toolkit_copy"]
