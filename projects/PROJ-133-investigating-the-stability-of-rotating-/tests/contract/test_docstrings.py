"""Contract test ensuring every public object has a non‑empty docstring."""

import importlib
import pkgutil
import inspect
import pathlib

def _public_objects(module):
    """Yield public functions and classes from *module*."""
    for name, obj in inspect.getmembers(module):
        if name.startswith("_"):
            continue
        if inspect.isfunction(obj) or inspect.isclass(obj):
            yield name, obj

def test_all_public_objects_have_docstrings():
    """Assert that each public object in the ``code`` package has a docstring."""
    root = pathlib.Path(__file__).parents[2] / "code"
    for _, module_name, _ in pkgutil.iter_modules([str(root)]):
        full_name = f"code.{module_name}"
        mod = importlib.import_module(full_name)
        for name, obj in _public_objects(mod):
            assert inspect.getdoc(obj), f"{full_name}.{name} is missing a docstring"
