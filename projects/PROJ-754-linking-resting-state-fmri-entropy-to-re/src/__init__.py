"""
src package initializer.

This package extends its import path to include the actual source
directory located at ``code/src`` so that commands like
``python -m src.download_data`` resolve to the implementation in
``code/src/download_data.py`` (and similarly for other modules).
"""
import pkgutil
import pathlib

# Ensure this package is a namespace package
__path__ = pkgutil.extend_path(__path__, __name__)

# Append the real source directory to the package search path.
_code_src_dir = pathlib.Path(__file__).resolve().parent / "code" / "src"
if _code_src_dir.is_dir():
    __path__.append(str(_code_src_dir))
