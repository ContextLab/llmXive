# Quickstart: Autocorrelation of the Möbius Function in Short Intervals

## Prerequisites
- Python **3.11** or newer
- `git`, ≥ 1 GB free disk, internet for package install.

## Installation
```bash
git clone
cd autocorr-mobius
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
```

## Running the Demo

The project provides a lightweight demo that runs the full pipeline on a tiny subset of the data (so it finishes in seconds). Execute it with:

```bash
python -m code.main --demo
```

This command will:

1. Generate the Möbius sequence for a reduced `N` and store it under `data/raw/mobius_array.npy`.
2. Compute autocorrelation for a single short interval.
3. Produce a single heat‑map figure in `outputs/figures/`.

The demo verifies that the end‑to‑end workflow is functional without requiring the full 10⁷‑element computation. [UNRESOLVED-CLAIM: c_bd96198c — status=not_enough_info]

## Running the Full Pipeline

To run the complete analysis (the full 10⁷‑element sieve, all interval lengths, full permutation set, and all visualisations), simply omit the `--demo` flag:

```bash
python -m code.main
```

## Verification

After a successful run you can:

- **Check the generated Möbius array**:
 ```bash
 python -c "import numpy as np; a = np.load('data/raw/mobius_array.npy'); print('Unique values:', np.unique(a))"
 # Expected output: Unique values: [-1  0  1] [UNRESOLVED-CLAIM: c_3c1dd1f9 — status=not_enough_info]
 ```
- **Run the test suite**:
 ```bash
 pytest tests/unit/
 pytest tests/integration/
 ```

## Troubleshooting
- **Memory errors** – Ensure the array is stored as `int8` (the code uses this dtype by default).
- **Long runtimes** – The full pipeline can take several hours on modest hardware; use the `--demo` flag for quick checks.
- **Zero p‑values** – If an observed autocorrelation is more extreme than all permutations, the p‑value is reported as the reciprocal of the number of permutations to avoid reporting an absolute zero.