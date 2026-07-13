"""
Wrapper module exposing the ``main`` entry‑point from the real implementation
located in ``code.analysis.correlation_main_runner``.  The original script
expects a top‑level ``analysis`` package; this file provides that thin
indirection.
"""
import logging
from code.analysis.correlation_main_runner import main as _real_main

logger = logging.getLogger(__name__)

def main() -> None:
    """
    Forward the call to the actual runner implementation.
    """
    logger.info("Invoking real correlation_main_runner")
    _real_main()