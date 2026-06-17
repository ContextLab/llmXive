# Random Seeds

All stochastic operations in the pipeline use the following fixed seeds:

- NumPy: ``42``
- Python ``random``: ``12345``
- Scikit‑learn (if used): ``0``

The seeds are set in `code/__init__.py` and documented in
`docs/reproducibility/seed_verification.md`.
