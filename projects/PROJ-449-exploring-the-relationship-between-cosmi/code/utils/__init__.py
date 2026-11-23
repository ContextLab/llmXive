"""Utilities package for the cosmic ray analysis pipeline.

NOTE: This package previously did `from code.utils.config import CONFIG`
unconditionally, which broke every entry point (ImportError) because the
current revision of ``code/utils/config.py`` no longer exports a module
level ``CONFIG`` symbol. Importing config symbols eagerly from the
package __init__ is removed so that ``code.utils.logging`` (and every
downstream stage) can be imported regardless of the config module's
current public surface. Modules that need configuration values should
import them directly from ``code.utils.config``.
"""
try:
    # Preserve backwards compatibility for any consumer that does
    # `from code.utils import CONFIG`, without making it a hard import.
    from code.utils.config import CONFIG  # noqa: F401
except ImportError:
    CONFIG = None  # type: ignore
