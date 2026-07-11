# Implementation Plan: Asymptotic Behavior of Random Matrix Eigenvalues with Sparse Perturbations

**Branch**: `001-asymptotic-behavior-of-random-matrix-eig` | **Date**: 2026-07-11 | **Spec**: `spec.md`
**Input**: Feature specification from `specs/001-asymptotic-behavior-of-random-matrix-eig/spec.md`

## Summary

This project implements a computational simulation to investigate how the rank and sparsity pattern of deterministic perturbations affect the emergence of outlier eigenvalues in the limiting spectral distribution of Wigner matrices. The approach involves generating synthetic Wigner matrices of varying dimensions ($N \in [100, 2000]$), applying low-rank deterministic perturbations with specific sparsity structures (diagonal, block-sparse, random sparse), and computing the extreme eigenvalues using CPU-tractable iterative solvers (ARPACK) to detect phase transitions in outlier emergence. The study adheres to the project constitution's strict reproducibility and numerical stability requirements, ensuring all results are associative correlations derived from simulated data.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `numpy`, `scipy` (for ARPACK/`eigsh`), `scikit-learn` (for data aggregation and curve fitting), `pandas`, `matplotlib`, `pyyaml`  
**Storage**: Local filesystem (`data/`), SQLite (optional for metadata, default to CSV/Parquet for simplicity)  
**Testing**: `pytest`  
**Target Platform**: Linux (GitHub Actions Free Tier: 2 CPU, 7 GB RAM)  
**Project Type**: Computational Research / Simulation Library  
**Performance Goals**: Complete full parameter sweep (N=2000, 100 iterations, 20 norms) within 6 hours CPU time; memory usage < 7 GB.  
**Constraints**: No GPU; iterative solvers only for N > 500; fixed random seeds for reproducibility; strict adherence to constitutional Principle VI (Spectral Numerical Stability).  
**Scale/Scope**: Synthetic dataset generation; ~ matrix instances; ~ eigenvalue computations.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Compliance Status | Implementation Strategy |
|-----------|-------------------|-------------------------|
| **I. Reproducibility** | **PASS** | Random seeds pinned in `code/`. `requirements.txt` pins all versions. `data/` files are generated deterministically from code. |
| **II. Verified Accuracy** | **PASS** | All citations in `research.md` and the final paper will be processed by the **Reference-Validator Agent** to verify reachability and title overlap (≥0.7) against primary sources before inclusion. Fabrication is prohibited; unverified accuracy is a blocking violation. |
| **III. Data Hygiene** | **PASS** | All generated data files will be checksummed (SHA-256) and recorded in `state/`. Raw data preserved; derivations in new files. |
| **IV. Single Source of Truth** | **PASS** | All figures and statistics in the final paper will be generated directly from `data/` via `code/` scripts, with no hand-typed values. |
| **V. Versioning Discipline** | **PASS** | Content hashes will be computed for all artifacts. The **Advancement-Evaluator Agent** will automatically invalidate stale review records when these hashes change, ensuring versioning discipline is enforced by the system. |
| **VI. Spectral Numerical Stability** | **PASS** | Iterative solvers (`scipy.sparse.linalg.eigsh`) used with `tol=1e-10` via `LinearOperator` on dense matrices. Results validated against theoretical semicircle edge ($\pm$ threshold) and empirical bulk edge. |
| **VII. Sparse Perturbation Structural Fidelity** | **PASS** | Perturbation matrices constructed with explicit rank and sparsity metadata. Spectral norm $\theta$ and structural properties are verified during generation and recorded in `data/` metadata (e.g., `SimulationRun` and `AggregatedThreshold` entities) to ensure structural fidelity is preserved in output artifacts. |

## Project Structure

### Documentation (this feature)

```text
specs/001-asymptotic-behavior-of-random-matrix-eig/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
projects/PROJ-551-asymptotic-behavior-of-random-matrix-eig/
├── code/
│   ├── requirements.txt
│   ├── __init__.py
│   ├── generators/
│   │   ├── wigner.py        # Wigner matrix generation (FR-001) - Dense only
│   │   └── perturbation.py  # Sparse perturbation construction (FR-002) - Rank-preserving
│   ├── analysis/
│   │   ├── eigen_solver.py  # Iterative solver wrapper (FR-003, FR-010) - LinearOperator
│   │   ├── outlier_detect.py # Outlier detection logic (FR-004) - Empirical edge
│   │   └── threshold_sweep.py # Parameter sweep execution (FR-005, FR-006) - Curve fitting
│   ├── utils/
│   │   ├── config.py        # Seed, tolerance, and path configuration
│   │   └── checksum.py      # Data hygiene utilities (Constitution III)
│   └── main.py              # Orchestration script
├── data/
│   ├── raw/                 # Generated matrices (if stored) or metadata
│   ├── processed/           # Eigenvalue results, outlier flags, thresholds
│   └── checksums.json       # SHA-256 hashes
├── tests/
│   ├── contract/            # Schema validation tests
│   ├── integration/         # Full sweep simulation tests
│   └── unit/                # Generator and solver unit tests
├── docs/
│   └── paper/               # Draft paper (future)
└── state/
    └── projects/
        └── PROJ-551-asymptotic-behavior-of-random-matrix-eig.yaml
```

**Structure Decision**: Single project structure selected to minimize overhead for a computational research task. `code/` contains all logic; `data/` stores generated artifacts; `tests/` ensures contract compliance.

**Dependency Mapping**:
- `scikit-learn`: Used in `analysis/threshold_sweep.py` for sigmoid curve fitting (estimating $\theta_c$) and data handling utilities, directly supporting FR-005 and FR-006.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Iterative Solvers (ARPACK)** | Required for $N=2000$ to extract top eigenvalues efficiently without full diagonalization. | Direct dense diagonalization (`numpy.linalg.eigh`) is $O(N^3)$ and wasteful when only top 10 are needed. |
| **Dense Wigner Storage** | Wigner matrices are inherently dense; sparse storage would destroy spectral properties. | Storing as sparse is mathematically incorrect for the Wigner ensemble. Memory (~32MB for N=2000) is negligible. |
| **Rank-Preserving Perturbation** | Requires exact rank $k$ to test BBP theory; random zeroing destroys rank. | Simple masking reduces rank; must use dense core embedding. |
| **Monte Carlo Sweep (100 runs)** | Required to estimate probability of outlier emergence (SC-003). | Single-run analysis cannot capture the probabilistic nature of the phase transition. |

