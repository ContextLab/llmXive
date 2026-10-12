"""Thin wrapper that re‑exports the OPID router implementation.

The real implementation lives in ``code/agent/opid_router.py``.  This
wrapper simply imports the public symbols so that they are available under
the ``src.agent`` namespace.
"""

from importlib import import_module

_router_mod = import_module('code.agent.opid_router')
OPIDRouter = _router_mod.OPIDRouter
OPIDRouterConfig = _router_mod.OPIDRouterConfig
main = _router_mod.main
