"""
Unified data fetch module.

This module re‑exports the concrete fetch implementations for ACE and NOAA
data.  It exists solely to provide a stable import surface for
``code.main`` and other pipeline stages:

    from code.data.fetch import fetch_ace, fetch_noaa

The heavy‑lifting functions live in ``code.data.fetch_ace`` and
``code.data.fetch_noaa``; they implement streaming downloads, exponential
back‑off, and raise ``ConnectionError`` on any network problem (as required
by the specification).  No additional logic is performed here to avoid
circular imports or unnecessary side‑effects.
"""

# Re‑export the public fetch functions
from .fetch_ace import fetch_ace
from .fetch_noaa import fetch_noaa

__all__ = [
    "fetch_ace",
    "fetch_noaa",
]