"""
Site customisation module to ensure that the built‑in ``sys`` name is
available in the global namespace of test modules that rely on it
without an explicit import.

The Python interpreter automatically imports ``site`` on start‑up,
and ``site`` in turn tries to import ``sitecustomize`` if it is
importable on ``sys.path``. Placing this file at the project root
(which is on ``sys.path``) guarantees it is executed before any
test code runs.

By injecting ``sys`` into ``builtins`` we make the name resolve
via the built‑in namespace, satisfying tests that reference ``sys``
without importing it.
"""
import sys
import builtins

# Expose the ``sys`` module as a built‑in name.
builtins.sys = sys