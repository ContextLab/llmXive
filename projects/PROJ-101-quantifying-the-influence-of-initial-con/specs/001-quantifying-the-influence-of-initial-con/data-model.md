# Data Model: Quantifying the Influence of Initial Conditions on Chaotic Systems

## Overview
All artifacts live under `data/`. Raw trajectories are immutable; processed results are derived and version‑checked via SHA‑256 checksums recorded in `state/manifest.yaml`.

## Directory Layout
```
data/
├── raw/
│   └── trajectories_N{N}_sigma{sigma}_trial{t}.npz
├── processed/
│   ├── ftle_results.json            # Aggregated FTLE entries (ftle_results.schema.yaml)
│   ├── baseline_{N}.json            # Clean baseline per dimension (baseline.schema.yaml)
│   ├── regression_results.json      # Mixed‑effects / Tobit regression output (regression_results.schema.yaml)
│   ├── results.json                 # Bundled outputs (results.schema.yaml)
│   └── plots/
│       ├── convergence.png
│       ├── bias_scaling.png
│       └── dimension_scaling.png
└── artifacts/
    └── manifest.yaml                # Checksums & metadata
```

## Entity Definitions

| Entity | Source | Format | Schema |
|--------|--------|--------|--------|
| **Trajectory** | `code/simulation/generator.py` | NumPy `.npz` (arrays `time`, `state`, `noise`, dict `params`) | `contracts/trajectory.schema.yaml` |
| **FTLE Result (single)** | `code/analysis/ftle.py` | JSON (list of objects) | `contracts/ftle_result.schema.yaml` |
| **FTLE Results (aggregated)** | `code/analysis/ftle.py` (aggregation step) | JSON (object) | `contracts/ftle_results.schema.yaml` |
| **Baseline** | `code/analysis/baseline.py` | JSON (single object) | `contracts/baseline.schema.yaml` |
| **Regression Results** | `code/analysis/regression.py` | JSON (mixed‑effects + Tobit) | `contracts/regression_results.schema.yaml` |
| **Results Bundle** | Pipeline end‑stage | JSON (combines FTLE, regression, escape probabilities) | `contracts/results.schema.yaml` |
| **Plots** | `code/analysis/plotting.py` | PNG | – (visual artifact) |

## Data Flow
1. **Generation** → `data/raw/*.npz`.  
2. **Baseline Validation** reads clean raw file → writes `baseline_{N}.json`.  
3. **FTLE Computation** reads each raw file → appends entries to `ftle_results.json` (single‑entry) and aggregates them into `ftle_results.json` (object) validated against `ftle_results.schema.yaml`.  
4. **Statistical Analysis** consumes `ftle_results.json` + `baseline_{N}.json` → writes `regression_results.json` (validated against `regression_results.schema.yaml`).  
5. **Bundling** creates `results.json` containing FTLE trials, regression output, and escape probabilities; validated against `results.schema.yaml`.  
6. **Visualization** consumes `regression_results.json` → writes PNGs.  
7. **Manifest** computes SHA‑256 for every file in `data/` and stores them under `state/artifacts/manifest.yaml`.  

## Integrity & Hygiene
- **Immutability**: Raw `.npz` files are never overwritten.  
- **Checksums**: Generated automatically after each pipeline stage; CI fails if a checksum mismatch is detected.  
- **Versioning**: `state/projects/PROJ-101-quantifying-the-influence-of-initial-con.yaml` records the git commit hash and the artifact hash map.  
- **Reproducibility**: All random seeds are stored in each trajectory’s metadata (`params.seed`).  

---

