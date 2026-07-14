"""
Site customization module for the project.

Previously this file attempted to modify import behavior in a way that caused
failures when importing standard‑library modules such as ``importlib`` and
third‑party packages like ``numpy`` and ``pandas``. The problematic logic has
been removed to ensure a clean interpreter startup.

This module intentionally does nothing; it only exists so that Python's
automatic ``sitecustomize`` import succeeds without side‑effects.
"""
# No operation needed – the presence of this file satisfies Python's
# ``sitecustomize`` import mechanism while keeping the import system
# untouched.
