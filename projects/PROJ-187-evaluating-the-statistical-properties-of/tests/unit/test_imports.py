"""Regression test to ensure that the imported ``sdv`` and ``rdt`` packages
are the ones installed in the environment (site‑packages) and not local
shadow modules.
"""
import importlib
import os
from pathlib import Path

import pytest

def _is_site_package(module):
    return "site-packages" in getattr(module, "__file__", "")

def test_sdv_and_rdt_imported_from_site_packages():
    # Import via the trainer's safe import helper to ensure path hygiene
    from src.models.trainer import _import_sdv

    sdv = _import_sdv()
    rdt = importlib.import_module("rdt")

    assert _is_site_package(sdv), f"sdv imported from unexpected location: {sdv.__file__}"
    assert _is_site_package(rdt), f"rdt imported from unexpected location: {rdt.__file__}"

    # Ensure no local ``sdv`` or ``rdt`` packages exist under the project root
    project_root = Path(os.getenv("PROJECT_ROOT", Path.cwd()))
    for pkg_name in ("sdv", "rdt"):
        local_path = project_root / pkg_name
        assert not local_path.is_dir(), f"Local shadow package found: {local_path}"
