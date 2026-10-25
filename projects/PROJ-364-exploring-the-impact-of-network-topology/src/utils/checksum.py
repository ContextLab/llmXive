"""
Compatibility wrapper for checksum utilities.

The original implementation lives in ``code/src/utils/checksum.py``.
This module re‑exports the public API so that imports from
``src.utils.checksum`` (used by the existing unit tests) work correctly.
"""
import importlib
import sys
from pathlib import Path

# Resolve the location of the original module relative to this file.
# The original module is at ``code/src/utils/checksum.py``.
_original_path = Path(__file__).resolve().parents[2] / "code" / "src" / "utils" / "checksum.py"
_module_name = "code_src_utils_checksum"

# Load the original module only once.
if _module_name not in sys.modules:
    spec = importlib.util.spec_from_file_location(_module_name, _original_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[_module_name] = module
    spec.loader.exec_module(module)  # type: ignore
else:
    module = sys.modules[_module_name]

# Re‑export the public symbols expected by the tests.
__all__ = [
    "calculate_sha256",
    "compute_file_sha256",
    "compute_string_sha256",
    "compute_file_checksum",
    "verify_file_checksum",
    "generate_checksum_manifest",
    "load_checksum_manifest",
    "verify_manifest",
]

calculate_sha256 = module.calculate_sha256
compute_file_sha256 = module.compute_file_sha256
compute_string_sha256 = module.compute_string_sha256
compute_file_checksum = module.compute_file_checksum
verify_file_checksum = module.verify_file_checksum
generate_checksum_manifest = module.generate_checksum_manifest
load_checksum_manifest = module.load_checksum_manifest
verify_manifest = module.verify_manifest
