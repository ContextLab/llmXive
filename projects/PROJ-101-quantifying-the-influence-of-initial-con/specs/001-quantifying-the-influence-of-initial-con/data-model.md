# Data Model: Quantifying the Influence of Initial Conditions on Chaotic Systems

## Overview
All artifacts reside under `data/`. Raw trajectories are immutable; processed results are derived and validated against JSON schemas located in `specs/.../contracts/`. Checksums are recorded in `state/artifacts/manifest.yaml` (platform‑owned).

## Directory Layout
```
data/
├── raw/
│   └── trajectories_N{N}_sigma{sigma}_trial{t}.npz
├── processed/
│   ├── baseline_{N}.json            # Clean asymptotic exponent (baseline.schema.yaml)
│   ├── baseline_per_window_{N}.json # Per‑window baseline estimates (mean, std, convergence error)
│   ├── ftle_results.json            # Aggregated FTLE entries and status flags
│   ├── regression_results.json      # Mixed‑effects summary, Tobit summary, escape probabilities, **baseline_variance_used** flag
│   ├── results.json                 # Bundle containing all above plus metadata
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
| **Baseline** | `code/analysis/baseline.py` | JSON object with fields `system_dimension`, `lambda_max`, `convergence_error`, `status`, `trajectory_length`, `algorithm`, optional `baseline_variance`, `sample_count` | `contracts/baseline.schema.yaml` |
| **Baseline per window** | `code/analysis/baseline.py` | JSON array of objects each with `window_size`, `lambda_mean`, `lambda_std`, `convergence_error` | `contracts/baseline.schema.yaml` |
| **FTLE Result (single)** | `code/analysis/ftle.py` | JSON object (see `ftle_result.schema.yaml`) | `contracts/ftle_result.schema.yaml` |
| **FTLE Results (aggregated)** | `code/analysis/ftle.py` (aggregation) | JSON array of FTLE results | `contracts/ftle_results.schema.yaml` |
| **Regression Results** | `code/analysis/regression.py` | JSON with mixed‑effects summary, Tobit summary, escape probabilities, `baseline_variance_used` flag | `contracts/regression_results.schema.yaml` |
| **Results Bundle** | Pipeline end‑stage | JSON combining baseline, FTLE, regression, escape probabilities, generation timestamp | `contracts/results.schema.yaml` |
| **Plots** | `code/analysis/plotting.py` | PNG files (no schema) | – |

## Data Flow
1. **Generation** → `data/raw/*.npz`.  
2. **Baseline Validation** reads clean raw file → writes `baseline_{N}.json` and `baseline_per_window_{N}.json`.  
3. **FTLE Computation** reads each raw file → appends entries to `ftle_results.json`.  
4. **Statistical Analysis** consumes `ftle_results.json` + `baseline_{N}.json` → writes `regression_results.json`.  
5. **Bundling** creates `results.json`.  
6. **Visualization** consumes `regression_results.json` → writes PNGs.  
7. **Manifest** computes SHA‑256 for every file in `data/` and records them under `state/artifacts/manifest.yaml`.

## Integrity & Hygiene
- **Immutability**: Raw `.npz` files are never overwritten.  
- **Checksums**: Generated automatically after each pipeline stage; CI fails on mismatch.  
- **Versioning**: `state/projects/PROJ-101-quantifying-the-influence-of-initial-con.yaml` records the git commit hash and artifact hash map.  
- **Reproducibility**: All random seeds are stored in each trajectory’s metadata (`params.seed`).  

## Propagation of Baseline Uncertainty
The `baseline_variance` (or per‑window `lambda_std`) captured in Phase 3 is **propagated as observation‑level weights** in the mixed‑effects regression (Phase 6). This explicitly acknowledges algorithmic differences between Rosenstein baseline and QR‑based FTLE computation and prevents under‑estimation of uncertainty in the deviation metric \(\Delta\lambda\).

---

