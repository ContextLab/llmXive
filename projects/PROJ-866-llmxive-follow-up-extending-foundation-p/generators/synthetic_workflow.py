"""
Wrapper module that makes the synthetic workflow generator importable
as ``generators.synthetic_workflow`` (used by the test suite).

The actual implementation lives in ``code/generators/synthetic_workflow.py``.
This file simply imports the class and, when executed as a script,
forwards the command‑line interface to the implementation.
"""

from code.generators.synthetic_workflow import (
    SyntheticWorkflowGenerator,
    main as _impl_main,
)

# Export the class at the expected location.
__all__ = ["SyntheticWorkflowGenerator"]

# When run directly (e.g. ``python generators/synthetic_workflow.py``)
# delegate to the implementation's CLI.
if __name__ == "__main__":
    raise SystemExit(_impl_main())
