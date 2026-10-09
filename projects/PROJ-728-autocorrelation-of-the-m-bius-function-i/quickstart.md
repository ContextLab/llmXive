# Quickstart: Autocorrelation of the Möbius Function in Short Intervals

## Project Layout

```text
.
├── code/ # Source code
│ ├── __init__.py
│ ├── main.py # Master orchestration script (to be implemented)
│ ├── sieve.py # Linear‑time Möbius sieve
│ ├── autocorrelation.py # Autocorrelation computation
│ ├── permutation.py # Block‑permutation generator
│ └── viz.py # Heat‑map visualisation
├── data/
│ ├── raw/
│ │ └── mobius_array.npy # Generated μ(n) for 1 ≤ n ≤ 10⁷
│ └── processed/
│ └── autocorrelation_stats.csv
├── outputs/
│ └── figures/
│ ├── heatmap_L1000.png
│ ├── heatmap_L10000.png
│ └── heatmap_L100000.png
├── tests/
│ ├── unit/
│ │ ├── test_sieve.py
│ │ └── test_autocorrelation.py
│ └── integration/
│ └── test_full_pipeline.py
├── requirements.txt # Pinned Python dependencies
├── quickstart.md # ← You are reading it
└── README.md # Project overview
```

## Prerequisites

- Python **3.11** or newer
- `pip` package manager
- At least **500 MiB** of free disk space

## Installation

1. **Clone the repository** and `cd` into the project root.
2. **Create a virtual environment** and activate it:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```
3. **Install the exact, pinned dependencies**:
 ```bash
 pip install -r requirements.txt
 ```
 The `requirements.txt` file pins each package to a specific version, ensuring reproducible builds.

## Running the Demo

The project provides a lightweight demo that runs the full pipeline on a tiny subset of the data (so it finishes in seconds). [UNRESOLVED-CLAIM: c_40cd14f0 — status=not_enough_info] Execute it with:

```bash
python -m code.main --demo
```

This command will:

1. Generate the Möbius sequence for a reduced `N` and store it under `data/raw/mobius_array.npy`.
2. Compute autocorrelation for a single short interval.
3. Perform a tiny permutation test.
4. Produce a single heat‑map figure in `outputs/figures/`.

The demo verifies that the end‑to‑end workflow is functional without requiring the full 10⁷‑element computation. [UNRESOLVED-CLAIM: c_aa8ce985 — status=not_enough_info]

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
 # Expected output: Unique values: [-1  0  1] [UNRESOLVED-CLAIM: c_df9a0d85 — status=not_enough_info]
 ```
- **Run the test suite**:
 ```bash
 pytest tests/unit/
 pytest tests/integration/
 ```

## Troubleshooting

- **Memory errors** – Ensure the array is stored as `int8` (the code uses this dtype by default).
- **Long runtimes** – The full pipeline can take several hours on modest hardware; use the `--demo` flag for quick checks. [UNRESOLVED-CLAIM: c_9678100a — status=not_enough_info]
- **Zero p‑values** – If an observed autocorrelation is more extreme than all permutations, the p‑value is reported as the reciprocal of the number of permutations to avoid reporting an absolute zero.
