# Random Seed Documentation

All stochastic operations in the project use the following fixed seeds to ensure reproducibility:

- NumPy: `42`
- Python's `random`: `12345`
- Any other libraries (e.g., scikit‑learn) also use the seed `42`.

The seeds are set at the start of each script via `np.random.seed(42)` and `random.seed(12345)`.
