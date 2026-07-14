# This placeholder test ensures the repository has at least one test file.
# Real tests are defined in other modules; this file simply verifies that
# the project can be imported without syntax errors.
import importlib

def test_imports():
    modules = [
        "config",
        "logging_config",
        "00_generate_synthetic_data",
    ]
    for mod in modules:
        importlib.import_module(mod)