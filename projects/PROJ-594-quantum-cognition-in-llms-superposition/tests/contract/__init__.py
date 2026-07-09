"""
Contract tests for PROJ-594: Quantum Cognition in LLMs.

This package contains schema validation and contract tests that ensure
all system outputs adhere to the defined interfaces and data structures.
These tests verify that:
- Baseline metrics JSON follows the expected schema
- Quantum model outputs match the complex-valued adapter contract
- Statistical analysis reports contain required fields (p-value, effect size, etc.)
- All outputs maintain FR-006 framing (associational, not causal claims)

Contract tests run independently of implementation details and validate
the system's adherence to specifications.
"""

__version__ = "0.1.0"
__all__ = []