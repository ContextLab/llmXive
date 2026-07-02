# Implementation Plan: Quantifying the Effect of Disorder on Electronic Transport in 1D Chains

**Branch**: `[001-quantifying-disorder-effect]` | **Date**: 2026-06-07 | **Spec**: `specs/001-quantifying-disorder-effect/spec.md`
**Input**: Feature specification from `specs/001-quantifying-disorder-effect/spec.md`

## Summary

This feature implements a computational study of the 1D Anderson model. The primary requirement is to quantify the relationship between disorder strength ($W$) and the electronic localization length ($\xi$) using two independent numerical methods: **Participation Ratio (PR) Finite-Size Scaling** and the **Transfer Matrix Method (TM)**. 

Crucially, the plan corrects the methodology to avoid circular definitions: $\xi$ is not defined as $C \times \text{PR}$ for a single $L$. Instead, $\xi$ is extracted by fitting the saturation of $\text{PR}(L)$ across multiple system sizes ($L \in \{100, 200, 400, 800\}$). The Transfer Matrix method is implemented with **QR-based orthogonalization** at every step to ensure convergence to the true Lyapunov exponent per Oseledec's theorem. The study is designed to run on CPU‑only infrastructure, utilizing sparse linear algebra for large systems and rigorous statistical methods (Bonferroni correction for pairwise comparisons only) to handle multiple hypothesis testing.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `numpy`, `scipy`, `matplotlib`, `pandas`, `h5py`, `pytest`, `joblib`  
**Storage**: Local file system (`data/`), HDF5 for large matrix/eigenstate dumps. No external database.  
**Testing**: `pytest` with contract tests against schema definitions.  
**Target Platform**: Linux (GitHub Actions Free Tier: 2 CPU, ~7 GB RAM, no GPU).  
**Performance Goals**: Complete 1000 realizations (10 widths × 100 samples) within 6 h on CPU; peak RAM < 7 GB.  
**Constraints**: No GPU usage; strict double‑precision arithmetic; open boundary conditions only.  
**Scale/Scope**: System sizes $L \in \{100, 200, 400, 800, 1600\}$; Disorder widths $W \in \{0.1, 0.2, …, 2.0\}$ (≈10 values); Multiple realizations per width.

> Domain‑specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

| Principle | Compliance Strategy |
|-----------|---------------------|
| **I. Reproducibility** | Random seeds pinned in `code/generate_hamiltonian.py`. All synthetic data generated via `numpy.random.Generator` with explicit seed logging. `requirements.txt` pins exact versions. CI runs on a fresh environment. |
| **II. Verified Accuracy** | No external datasets used (synthetic only). Citations in `research.md` will be validated against primary physics literature via the Reference‑Validator Agent. |
| **III. Data Hygiene** | Raw Hamiltonian matrices and eigenstates stored in `data/raw/` with SHA‑256 checksums recorded in `data/metadata/checksums.json`. No in‑place modification; derived statistics stored in `data/processed/`. |
| **IV. Single Source of Truth** | All figures, tables, and numbers in the paper are generated directly from `data/processed/` via scripts in `code/`. No manual transcription. |
| **V. Versioning Discipline** | Artifacts tracked via content hashes in `state/`. Changes to `code/` invalidate cached `data/` results. |
| **VI. Numerical Stability** | Eigenvalue problems solved with `scipy.linalg.eigh` (dense) or `scipy.sparse.linalg.eigsh` (sparse). **Residual norms and convergence flags for every eigenvalue problem are logged in `data/metadata/residuals.json`.** Transfer‑matrix products use QR‑based orthogonalization with logarithmic accumulation; convergence diagnostics (γ vs L) are stored. |
| **VII. Synthetic Data Provenance** | Every Hamiltonian generation logs `realization_id`, `seed`, `W`, `L`, and **`realization_index`** in `data/metadata/provenance.json`. The full provenance record is stored and referenced by downstream scripts. |

## Project Structure

### Documentation (this feature)

```text
specs/001-quantifying-disorder-effect/
├── plan.md                # This file
├── research.md            # Phase 0 output
├── data-model.md          # Phase 1 output
├── quickstart.md          # Phase 1 output
├── contracts/             # Phase 1 output (Schemas)
└── tasks.md               # Phase 2 output (Generated later)
```

### Source Code (repository root)

```text
projects/PROJ-676-quantifying-the-effect-of-disorder-on-el/
├── code/
│   ├── __init__.py
│   ├── config.py              # Hyperparameters, seeds, paths
│   ├── generate_hamiltonian.py # FR‑001: Hamiltonian generation
│   ├── analyze_pr.py          # FR‑002, FR‑003: Participation‑Ratio analysis & finite-size scaling
│   ├── analyze_tm.py          # FR‑004, FR‑009: Transfer‑Matrix analysis with QR orthogonalization
│   ├── visualize.py           # FR‑006, US‑3: Plotting eigenstates
│   ├── stats.py               # FR‑005, FR‑010: Regression, Bonferroni for pairwise tests
│   └── main.py                # Orchestration script
├── data/
│   ├── raw/                   # Generated Hamiltonians (HDF5)
│   ├── processed/             # Localization lengths, PR values, scaling results
│   └── metadata/              # Provenance, checksums, residual norms, convergence traces
├── tests/
│   ├── unit/                  # Unit tests for math functions
│   ├── contract/              # Tests against schema definitions
│   └── integration/           # End‑to‑end workflow tests
├── docs/
│   └── …
└── requirements.txt
```

**Structure Decision**: A modular `code/` layout isolates each physical task, minimizing overhead for CPU‑only CI and simplifying data exchange via HDF5. The `main.py` orchestrates the workflow to guarantee that data generation precedes analysis (Computational Task Ordering).

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| **Dual Method Validation (PR + TM)** | Required by FR‑004 and US‑2 to ensure results are not method-dependent artifacts. | Single‑method analysis would fail robustness criteria and circular validation. |
| **Finite-Size Scaling for PR** | Required to correctly extract $\xi$ from $\text{PR}(L)$ saturation, avoiding the invalid $\xi \propto \text{PR}$ assumption for a single $L$. | Direct proportionality is scientifically flawed for finite systems. |
| **Sparse Solver Fallback** | Required by FR‑008 and US‑1 for $L=1600$ to stay within 7 GB RAM. | Dense diagonalization would exceed memory limits on the free‑tier runner. |
| **QR Orthogonalization in TM** | Required by FR‑009 and Principle VI to prevent numerical underflow and guarantee convergence to the true Lyapunov exponent (Oseledec's theorem). | Simple log-accumulation of a single vector norm yields biased estimates. |


## FR/SC Coverage Matrix

| ID | Description | Plan Implementation |
|----|-------------|---------------------|
| **FR-001** | Generate 1D Hamiltonian | `code/generate_hamiltonian.py` |
| **FR-002** | Compute PR for $|E|<0.1$ | `code/analyze_pr.py` |
| **FR-003** | Extract $\xi$ via scaling | `code/analyze_pr.py` (fit $\text{PR}(L)$ saturation) |
| **FR-004** | Implement TM method | `code/analyze_tm.py` (QR orthogonalization) |
| **FR-005** | Linear regression $\log\xi$ vs $\log W$ | `code/stats.py` |
| **FR-006** | Visualize eigenstates | `code/visualize.py` |
| **FR-007** | CPU-only, $\le$7GB RAM | Sparse fallback, HDF5 streaming |
| **FR-008** | Sparse solver fallback | `scipy.sparse.linalg.eigsh` for $L=1600$ |
| **FR-009** | Log-accumulation for TM | QR-based accumulation in `analyze_tm.py` |
| **FR-010** | Bonferroni correction | Applied to pairwise width comparisons in `stats.py` |
| **FR-011** | Parallelize realizations | `joblib` in `main.py` |
| **SC-001** | Slope $\approx -2$ | Regression on weak-disorder subset ($W<1.0$) |
| **SC-002** | Method agreement $\le$[deferred] | Compare $\xi_{PR}$ vs $\xi_{TM}$ |
| **SC-003** | Power $\ge$[deferred] | A priori power analysis documented |
| **SC-004** | Visual decay match | Compare fitted decay length to $\xi$ |
| **SC-005** | FWER $\le$0.05 | Bonferroni on pairwise tests |
| **SC-006** | Compute feasibility | Parallel execution, sparse fallback |