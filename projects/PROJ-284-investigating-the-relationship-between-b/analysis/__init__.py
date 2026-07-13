"""
Top‑level shim package that forwards calls to the real implementation
located under ``code.analysis``.  This allows the existing ``code/main.py``
script (which imports ``analysis.correlation_main_runner``) to function
without altering the original package layout.
"""
