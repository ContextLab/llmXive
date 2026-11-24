"""
Top‑level ``generators`` package.

The test suite imports ``generators.synthetic_workflow`` directly.
This package re‑exports the implementation that lives under
``code/generators`` to keep a single source of truth.
"""
# Re‑export the public symbols from the implementation module.
from code.generators.synthetic_workflow import SyntheticWorkflowGenerator  # noqa: F401
