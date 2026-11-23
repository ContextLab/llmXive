"""
Top‑level ``engines`` package.

The integration tests import ``engines.full_context`` and
``engines.compressed_context`` directly.  The real implementations live
under ``code/engines``; this wrapper simply re‑exports them so that
imports succeed without duplicating code.
"""
# Re‑export everything from the actual implementation modules.
from code.engines.full_context import *  # noqa: F403,F401
from code.engines.compressed_context import *  # noqa: F403,F401
