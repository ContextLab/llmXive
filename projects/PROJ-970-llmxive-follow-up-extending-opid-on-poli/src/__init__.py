"""Top-level package for the OPID routing complexity analysis project.

This package aggregates the main sub‑packages so that they can be imported
directly via ``import src``. The sub‑packages are also exposed as attributes
of this package for convenience.
"""

# Export sub‑packages for convenient top‑level imports.
# Importing sub‑packages lazily to avoid side‑effects during package import.
from importlib import import_module

def _load_submodule(name: str):
    return import_module(f'src.{name}')

environment = _load_submodule('environment')
agent = _load_submodule('agent')
simulation = _load_submodule('simulation')
analysis = _load_submodule('analysis')
utils = _load_submodule('utils')

__all__ = [
    "environment",
    "agent",
    "simulation",
    "analysis",
    "utils",
]
