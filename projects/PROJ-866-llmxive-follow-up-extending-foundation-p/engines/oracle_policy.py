"""
Compatibility shim for legacy imports.

The execution engine ``code.services.executor_full`` historically imported
``OraclePolicyEngine`` from a top‑level ``engines.oracle_policy`` module.
In the current project layout the implementation lives in
``code.engines.oracle_policy``.  This thin wrapper re‑exports the class so
that existing import statements continue to work without modification.
"""

from code.engines.oracle_policy import OraclePolicyEngine  # re-export

__all__ = ["OraclePolicyEngine"]