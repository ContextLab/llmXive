# Quickstart: Autocorrelation of the Möbius Function in Short Intervals

## Prerequisites
- Python **3.11** or newer
- `git`, ≥ 1 GB free disk, internet for package install.

## Installation
```bash
git clone <repo-url>
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

1. Generate a small Möbius sequence (`data/raw/mobius_array.npy`) for `N=2000`. [UNRESOLVED-CLAIM: c_8fec1d56 — status=not_enough_info]
2. Write minimal window start indices (`data/raw/window_starts.json`).
3. Compute a single autocorrelation for the first window (`data/processed/demo_autocorr.csv`). [UNRESOLVED-CLAIM: c_1c119f30 — status=not_enough_info]
4. Produce a single heat‑map figure (`outputs/figures/heatmap_demo.png`). [UNRESOLVED-CLAIM: c_5f72452d — status=not_enough_info]

After the command finishes you can verify the artefacts:

```bash
ls data/raw
# should show mobius_array.npy and window_starts.json

ls data/processed
# should show demo_autocorr.csv

ls outputs/figures
# should show heatmap_demo.png
```

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
 # Expected output: Unique values: [-1  0  1] [UNRESOLVED-CLAIM: c_e4cb2959 — status=not_enough_info]
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