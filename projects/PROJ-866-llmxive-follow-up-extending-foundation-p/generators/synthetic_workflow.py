"""
generators.synthetic_workflow
-----------------------------

Thin wrapper that re‑exports the implementation located under ``code/generators``.
This allows the test suite (which imports ``generators.synthetic_workflow``) to
locate the class without duplicating code.
"""

from code.generators.synthetic_workflow import SyntheticWorkflowGenerator  # noqa: F401
