"""Thin wrapper that re‑exports the OPID injector implementation.

The real implementation lives in ``code/agent/opid_injector.py``.
"""

from importlib import import_module

_injector_mod = import_module('code.agent.opid_injector')
OPIDInjector = _injector_mod.OPIDInjector
OPIDInjectorConfig = _injector_mod.OPIDInjectorConfig
main = _injector_mod.main
