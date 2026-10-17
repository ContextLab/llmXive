"""
Wrapper for the full‑context execution engine.

This module makes ``engines.full_context`` importable while delegating
all functionality to the implementation in ``code.engines.full_context``.
"""
from code.engines.full_context import (  # noqa: F401
    run_engine,
    build_parser,
    main,
)
