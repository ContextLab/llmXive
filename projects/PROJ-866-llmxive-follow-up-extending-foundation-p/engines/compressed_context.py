"""
Wrapper for the compressed‑context execution engine.

This module makes ``engines.compressed_context`` importable while
delegating all functionality to the implementation in
``code.engines.compressed_context``.
"""
from code.engines.compressed_context import (  # noqa: F401
    run_engine,
    build_parser,
    main,
)
