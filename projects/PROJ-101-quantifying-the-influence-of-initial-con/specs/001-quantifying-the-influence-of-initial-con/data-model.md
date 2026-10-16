# Data Model: Quantifying the Influence of Initial Conditions on Chaotic Systems

## Overview
All artifacts reside under `data/`. Raw trajectories are immutable; processed results are derived and validated against JSON schemas located in `specs/.../contracts/`. Checksums are recorded in `state/artifacts/manifest.yaml`.

## Directory Layout
```
data/
├── raw/
│   └── trajectories_N{N}_sigma{sigma}_trial{t}.npz
├── processed/
│   ├── ftle_results.json            # Aggregated FTLE entries (ftle_results.schema.yaml)
│   ├── baseline_{N}.json            # Clean baseline per dimension (baseline.schema.yaml)
│   ├── regression_results.json      # Mixed‑effects + Tobit output (regression_results.schema.yaml)
│   ├── results.json                 # Bundle of all outputs (results.schema.yaml)
│   └── plots/
│       ├── convergence.png
│       ├── bias_scaling.png
│       └── dimension_scaling.png
└── artifacts/
    └── manifest.yaml                # SHA‑256 checksums & metadata (platform‑owned)
```

## Entity Definitions

| Entity | Produced by | Format | Schema |
|--------|-------------|--------|--------|
| **Trajectory** | `code/simulation/generator.py` | NumPy `.npz` (arrays `time`, `state`, `noise`; dict `params` with `seed`, `N`, `sigma_noise`, `trial_id`) | `contracts/trajectory.schema.yaml` |
| **Baseline** | `code/analysis/baseline.py` | JSON (single object) | `contracts/baseline.schema.yaml` |
| **FTLE Result (single)** | `code/analysis/ftle.py` | JSON (object) | `contracts/ftle_result.schema.yaml` |
| **FTLE Results (aggregated)** | `code/analysis/ftle.py` (aggregation) | JSON (array of FTLE Result objects) | `contracts/ftle_results.schema.yaml` |
| **Regression Results** | `code/analysis/regression.py` | JSON (mixed‑effects + Tobit summary) | `contracts/regression_results.schema.yaml` |
| **Results Bundle** | Pipeline end‑stage | JSON (combines baseline, FTLE, regression, escape probabilities) | `contracts/results.schema.yaml` |
| **Plots** | `code/analysis/plotting.py` | PNG files | – (visual artifact) |

## Data Flow
1. **Generation** → `data/raw/*.npz`.  
2. **Baseline Validation** reads clean raw file → writes `baseline_{N}.json`.  
3. **FTLE Computation** reads each raw file → appends entries to `ftle_results.json` (validated against `ftle_results.schema.yaml`).  
4. **Statistical Analysis** consumes `ftle_results.json` + `baseline_{N}.json` → writes `regression_results.json` (validated against `regression_results.schema.yaml`).  
5. **Bundling** creates `results.json` (validated against `results.schema.yaml`).  
6. **Visualization** consumes `regression_results.json` → writes PNGs.  
7. **Manifest** computes SHA‑256 for every file in `data/` and stores them under `state/artifacts/manifest.yaml`.  

## Integrity & Hygiene
- **Immutability**: Raw `.npz` files are never overwritten.  
- **Checksums**: Generated automatically after each pipeline stage; CI fails on mismatch.  
- **Versioning**: `state/projects/PROJ-101-...yaml` records the git commit hash and artifact hash map.  
- **Reproducibility**: All random seeds are stored in each trajectory’s metadata (`params.seed`).  

---
