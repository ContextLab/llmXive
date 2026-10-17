# Implementation Plan: Asymptotic Behavior of Random Matrix Eigenvalues with Sparse Perturbations

**Branch**: `feature/asymptotic-random-matrix` | **Date**: 2026-10-17 | **Spec**: [spec.md](../spec.md)  
**Input**: Feature specification from `/specs/feature/asymptotic-random-matrix/spec.md`

## Summary
The project will empirically verify the BBP phase‑transition threshold for large Wigner matrices perturbed by deterministic sparse matrices.  
Technical approach: generate synthetic Wigner ensembles (CPU‑tractable, scaled by \(1/\sqrt N\)), construct sparse perturbations of configurable rank \(k\) and support density \(p\), compute the top‑10 eigenvalues with ARPACK (`scipy.sparse.linalg.eigsh`), **detect outliers using the theoretical semicircle edge (±2) plus a tolerance of 0.05** (not an empirical bulk estimate), and sweep perturbation norms (\(\theta\)) and sparsity density to estimate the critical threshold \(\theta_c\). All steps are deterministic via pinned random seeds and validated against JSON schemas.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `numpy`, `scipy`, `pandas`, `pyarrow`, `pydantic`, `matplotlib`, `tqdm`  
- **Storage**: File‑system (Parquet/CSV under `data/processed/`)  
- **Testing**: `pytest` + schema validation (`jsonschema`)  
- **Target Platform**: Linux GitHub Actions runner (multiple CPU cores, moderate RAM) – **CPU‑first**; no GPU required.  
- **Project Type**: Research‑oriented CLI library + analysis notebooks.  
- **Performance Goals**: Complete a full sweep (500 repetitions per config) for \(N\le2000\) within ≈ 5 h on the CI runner.  
- **Constraints**:  
  - **SC‑001** – Memory ≤ 7 GB.  
  - **SC‑002** – CPU‑only; must use iterative solvers (ARPACK).  
  - **SC‑003** – Full reproducibility via fixed seeds and checksums.  
  - **SC‑004** – Numerical tolerance \(1\text{e-}10\) for eigenvalue convergence.  
  - **SC‑005** – All output files must conform to the JSON/YAML contracts in `contracts/`.  

## Constitution Check
| Principle | How the plan satisfies it |
|-----------|--------------------------|
| I. Reproducibility | Fixed seeds recorded in `SimulationRun`; deterministic file hashes; `requirements.txt` pins all packages. |
| II. Verified Accuracy | No external citations beyond the arXiv semicircle reference (already verified). |
| III. Data Hygiene | Raw matrices are written to `data/raw/` with SHA‑256 checksums; transformations write new files; no PII. |
| IV. Single Source of Truth | Every figure/table draws directly from processed Parquet files validated against schemas. |
| V. Versioning Discipline | All artifacts (code, data, schemas) are version‑controlled; `state/projects/...yaml` records content hashes automatically. |
| VI. Spectral Numerical Stability | ARPACK configured with `tol=1e-10`, `maxiter=1000`; bulk edge validated against theoretical \(\pm2\). |
| VII. Sparse Perturbation Structural Fidelity | Perturbation generation logs rank \(k\), pattern type, and support density; schema enforces these fields. |

## Project Structure
```text
src/
├── simulation/
│   ├── wigner.py            # Wigner matrix generator
│   ├── perturbation.py      # Sparse deterministic perturbations
│   └── eigen_solver.py      # ARPACK wrapper, outlier detection (theoretical edge)
├── analysis/
│   ├── sweep.py             # Parameter sweep driver
│   ├── sensitivity.py       # Sparsity density sweep
│   ├── finite_size.py       # N‑sweep analysis (new)
│   └── aggregation.py       # Build AggregatedThreshold records
├── utils/
│   ├── checksum.py          # SHA‑256 utilities
│   └── logger.py            # Structured logging
├── cli.py                    # Entry point (`python -m src.cli ...`)
└── __main__.py              # Alias for CLI

data/
├── raw/                     # Serialized dense Wigner matrices (optional)
├── processed/               # Parquet files for SimulationRun, EigenvalueResult, AggregatedThreshold
└── checksums.yaml           # File‑level SHA‑256 map

tests/
├── contract/
│   └── test_schemas.py      # JSON‑schema validation
└── integration/
    └── test_t001.py         # End‑to‑end reproducibility test

contracts/
├── simulation_run.schema.yaml
├── eigenvalue_result.schema.yaml
└── aggregated_threshold.schema.yaml
```

## Complexity Tracking
No constitution violations require justification; the plan adheres to all principles.

## Phases & Tasks
| Phase | Description | FR/SC addressed |
|-------|-------------|-----------------|
| **0 – Foundations** | Install dependencies, set up logging, implement `checksum.py`. | SC‑001, SC‑003 |
| **1 – Core Generators** | Implement `wigner.py` (FR‑001) and `perturbation.py` (FR‑002). | FR‑001, FR‑002, SC‑004 |
| **2 – Eigenvalue Engine** | Implement `eigen_solver.py` using ARPACK (FR‑003, SC‑002, SC‑004). | FR‑003, SC‑002, SC‑004 |
| **3 – Outlier Logic** | Define outlier rule **λ > 2 + 0.05** (theoretical semicircle edge) (FR‑004). **Empirical bulk edge (99th percentile) is recorded only for diagnostics**. | FR‑004 |
| **4 – Parameter Sweep** | `sweep.py` loops over \(\theta\) grid, records `SimulationRun` and `EigenvalueResult` (FR‑005). **500 repetitions per configuration** give standard error ≤ 0.022, satisfying power requirements. | FR‑005, SC‑001 |
| **5 – Sparsity Sensitivity** | `sensitivity.py` varies support density \(p\) (FR‑006). | FR‑006 |
| **6 – Aggregation & Curve Fit** | `aggregation.py` produces `AggregatedThreshold` with sigmoid fit for \(\theta_c\) (FR‑007). | FR‑007 |
| **7 – Finite‑Size Analysis (N‑sweep)** | `finite_size.py` sweeps \(N\in\{500,1000,1500,2000\}\) for a representative subset of \((k,\theta,\text{pattern})\) configurations, quantifying finite‑size effects on bulk edge and outlier probability. This directly addresses the confounding role of matrix dimension. | Addresses methodology‑7cd8bfa6 |
| **8 – Schema Validation** | `tests/contract/test_schemas.py` validates every output file against contracts (SC‑005). | SC‑005 |
| **9 – End‑to‑End Test** | `tests/integration/test_t001.py` runs a full sweep, checks reproducibility of top eigenvalue within \(1\text{e-}6\) (SC‑003). | SC‑003 |
| **10 – Documentation** | Write `research.md`, `data-model.md`, `quickstart.md`; generate figures. | All FR/SC |
| **11 – Release** | Tag version, update `requirements.txt`, push to repo. | All FR/SC |

Each phase will be executed sequentially on the CI runner; intermediate artifacts are persisted to `data/processed/` and validated before proceeding to the next phase.

---

