"""
Compatibility wrapper so that ``import generators.synthetic_workflow`` works
in the test suite. It simply re‑exports the implementation from the
canonical location under ``code/generators``.
"""
from code.generators.synthetic_workflow import (
    SyntheticWorkflowGenerator,
    generate_workflows,
)

__all__ = ["SyntheticWorkflowGenerator", "generate_workflows"]
