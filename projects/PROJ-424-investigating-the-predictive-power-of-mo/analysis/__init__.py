"""
Top‑level ``analysis`` package.

This lightweight wrapper forwards imports to the actual implementation
located under ``code/analysis``.  It exists solely so that test suites
(which import ``analysis.diffusion`` and ``analysis.msd``) resolve
correctly without altering the original project structure.
"""
