"""
Wrapper for the actual CLI implementation located in ``code/src/cli/main.py``.
This file allows ``python -m src.cli.main`` to work from the project root
without needing to modify the PYTHONPATH. All public symbols from the real
implementation are re‑exported.
"""
import importlib.util
import pathlib
import sys

# Resolve the path to the real implementation inside ``code/src/cli/main.py``.
_CURRENT_DIR = pathlib.Path(__file__).resolve().parent
_PROJECT_ROOT = _CURRENT_DIR.parent.parent  # two levels up from src/cli
_REAL_IMPL_PATH = _PROJECT_ROOT / "code" / "src" / "cli" / "main.py"

if not _REAL_IMPL_PATH.is_file():
    raise FileNotFoundError(f"Real CLI implementation not found at {_REAL_IMPL_PATH}")

# Load the real module under a temporary name.
spec = importlib.util.spec_from_file_location("code_src_cli_main", str(_REAL_IMPL_PATH))
real_module = importlib.util.module_from_spec(spec)
sys.modules["code_src_cli_main"] = real_module
spec.loader.exec_module(real_module)

# Re‑export the public API expected by the rest of the project.
build_parser = real_module.build_parser
main = real_module.main

# Preserve other helper functions that may be imported elsewhere.
_helpers = [
    "_load_service",
    "_run_service",
    "_cmd_extract_topology",
    "_cmd_calc_vdos",
    "_cmd_ingest_kappa",
    "_cmd_aggregate",
    "_cmd_analyze",
    "_cmd_run",
]
for _name in _helpers:
    if hasattr(real_module, _name):
        globals()[_name] = getattr(real_module, _name)
