"""
Minimal test to ensure that the main entry point can be imported without
triggering side‑effects. The heavy Snakemake execution is not run here.
"""
import importlib

def test_import_main():
    mod = importlib.import_module("code.main")
    assert hasattr(mod, "main")