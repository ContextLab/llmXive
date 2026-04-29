"""Pre-CI checks (T114). Each module exits non-zero on failure.

Used by .github/workflows/llmxive-real-call-tests.yml to fail fast
before any real LLM call is issued, saving daily quota.
"""
