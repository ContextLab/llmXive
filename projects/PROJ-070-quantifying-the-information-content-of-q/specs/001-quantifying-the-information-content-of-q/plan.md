# Implementation Plan: Quantifying the Information Content of Quantum Entanglement in Many-Body Systems

**Branch**: `001-quantifying-information-content-of-entanglement` | **Date**: 2026-07-16 | **Spec**: `specs/001-quantifying-information-content-of-entanglement/spec.md`

## Summary

This project implements a CPU-tractable computational pipeline to test the hypothesis that structured entanglement in 1D quantum many-body systems (Heisenberg and Transverse-Field Ising models) exhibits a distinct correlation between bipartite entanglement entropy and compression-based Kolmogorov complexity estimates. The system generates wavefunction coefficients via Exact Diagonalization (N<=20) and DMRG (N>20), computes entanglement via SVD of reduced density matrices (using sparse solvers), estimates complexity via lossless compression ratios on **reduced** representations (singular values/subsystem vectors), and validates these findings against null models (random product states and Haar-random ensembles). The pipeline includes bootstrap resampling for statistical rigor and produces visualizations of the correlation landscape.

Crucially, to avoid confounding system size with entanglement structure, the analysis computes **entropy per spin** and **Normalized Compression Distance (NCD)** relative to a random baseline of the same size, and performs correlation analysis **within fixed spin-count groups** and via **partial correlation** controlling for N.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `numpy`, `scipy`, `h5py`, `pandas`, `matplotlib`, `seaborn`, `scikit-learn`, `tenpy` (for DMRG)  
**Storage**: HDF5/NumPy files for wavefunction data; temporary files for compression artifacts.  
**Testing**: `pytest` with `pytest-cov` for code coverage.  
**Target Platform**: Linux (GitHub Actions free-tier runner: 2 CPU, ~7 GB RAM).  
**Project Type**: Computational Research CLI / Pipeline.  
**Performance Goals**: Complete full pipeline (load, compute, resample, plot) within 6 hours; peak memory < 7 GB.  
**Constraints**: CPU-only execution; **Sparse matrix formats (CSR/CSC) are mandatory** for all wavefunction and density matrix representations (Constitution Principle VI). Dense SVD is prohibited without explicit justification and memory profiling.  
**Scale/Scope**: -40 spin systems; A representative set of configurations; A sufficient number of bootstrap iterations.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Implementation Note |
| :--- | :--- | :--- |
| **I. Reproducibility** | **Pass** | All random seeds pinned in `code/`; datasets generated internally via ED/DMRG with pinned seeds; `requirements.txt` pins versions. |
| **II. Verified Accuracy** | **Pass** | Citations to Calabrese/Cardy and Brown/Susskind will be validated against primary sources before publication; no unverified URLs in `research.md`. |
| **III. Data Hygiene** | **Pass** | Generated data checksummed; no in-place modification; derivations written to new files with hash tracking in `state/`. |
| **IV. Single Source of Truth** | **Pass** | All figures/statistics trace to `data/` rows and `code/` blocks; no hand-typed numbers in output docs. |
| **V. Versioning Discipline** | **Pass** | Artifacts carry content hashes; `state/` updated on change. |
| **VI. Quantum State Representation Fidelity** | **Pass** | **Mandatory**: Wavefunction coefficients and reduced density matrices stored as sparse arrays (CSR/CSC). Dense formats prohibited without explicit justification. SVD performed via `scipy.sparse.linalg.svds` (ARPACK). |
| **VII. Algorithmic Information Proxy Validation** | **Pass** | **Normalized Compression Distance (NCD)** computed alongside raw ratios. NCD calculated as (C(xy) - min(C(x),C(y))) / max(C(x),C(y)) where y is a random baseline. Null models (random product, Haar) explicitly generated to validate baseline. |

## Project Structure

### Documentation (this feature)

```text
specs/001-quantifying-information-content-of-entanglement/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/           # Phase 1 output
    ├── dataset.schema.yaml
    └── output.schema.yaml
```

### Source Code (repository root)

```text
projects/PROJ-070-quantifying-the-information-content-of-q/
├── code/
│   ├── __init__.py
│   ├── main.py                 # Entry point, CLI orchestration
│   ├── data_loader.py          # Internal generation (ED/DMRG), streaming
│   ├── metrics.py              # Entanglement (SVD sparse) and Complexity (Compression on reduced)
│   ├── null_models.py          # Random product, Haar ensemble generators
│   ├── statistics.py           # Correlation (Partial, Stratified), Bootstrap, T-tests
│   └── viz.py                  # Matplotlib/Seaborn plotting
├── data/
│   ├── raw/                    # Generated datasets (HDF5/NPY)
│   └── processed/              # Computed metrics (Parquet/CSV)
├── tests/
│   ├── unit/
│   ├── integration/
│   └── contract/
└── requirements.txt
```

**Structure Decision**: Single-project structure selected to minimize overhead. The computational pipeline is linear (Load -> Compute -> Analyze -> Plot), fitting naturally into a modular script-based architecture within `code/`. No frontend/backend split required.

**Entity-to-Schema Mapping**:
- `QuantumState` (data-model) -> `dataset.schema.yaml` (wavefunction array + metadata).
- `EntanglementMetric` & `ComplexityMetric` (data-model) -> `output.schema.yaml` (metrics array).
- `CorrelationResult` (data-model) -> `output.schema.yaml` (correlation_results object).

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Sparse Matrix Handling** | Required by Constitution Principle VI for 40-spin systems. | Dense full-state vectors (2^40) are impossible; dense reduced matrices (2^20) risk RAM overflow. Sparse representation (CSR/CSC) ensures safety margin and adheres to <7GB RAM constraint. |
| **Partial Correlation / Stratified Analysis** | Required to decouple System Size N from entanglement structure (Scientific Soundness concern). | Simple correlation across varying N is confounded by Hilbert space dimension. Must control for N. |
| **Normalized Compression Distance (NCD)** | Required by Constitution Principle VII to validate algorithmic proxy. | Raw compression ratio is dominated by vector length. NCD relative to a random baseline isolates structural compressibility. |
| **Internal Data Generation (ED/DMRG)** | Required as primary data source (no verified external datasets exist). | Relying on external data for N=10-40 is infeasible (no source). ED (N<=20) and DMRG (N>20) are the only viable paths. |
| **Compression on Reduced Representation** | Required to avoid metric being a proxy for vector length. | Compressing full 2^N vector masks structural correlations. Compression on singular values/subsystem vectors isolates structure. |

## Data Availability & Feasibility

- **Primary Data Source**: Internal generation.
  - **N <= 20**: Exact Diagonalization (ED) using `scipy.sparse.linalg.eigsh`.
  - **N > 20**: DMRG using `TeNPy` library (CPU-optimized).
- **Dataset Strategy**: No external Zenodo/HF datasets exist for the specific N=10-40 wavefunction coefficients required. The pipeline will generate data deterministically based on pinned seeds.
- **Streaming**: For DMRG (N>20), wavefunctions will be generated and processed in chunks to avoid loading the full state vector into RAM.
- **Feasibility**: ED for N=20 (2^20 ~ 1M elements) is trivial. DMRG for N=40 is feasible on CPU with sparse tensors. SVD on reduced density matrices (2^20 elements) using `scipy.sparse.linalg.svds` (ARPACK) fits within 7GB RAM.

## Compute Feasibility (CPU-First)

- **SVD**: For 40 spins, the reduced density matrix is ~2^20 x 2^20. Dense SVD is prohibited. The plan uses `scipy.sparse.linalg.svds` with the 'ARPACK' algorithm (Lanczos) targeting the largest singular values, with a target sparsity threshold and memory profiling step.
- **Compression**: Trivial CPU load on reduced vectors (e.g., 2^20 elements or fewer).
- **Bootstrap**: 1000 iterations of correlation on ~50 points is negligible (< 1 minute).
- **Total Runtime**: Estimated < 2 hours on 2-core CPU, well within the 6-hour limit.
- **GPU**: Not required. The SVD and compression operations are efficient on CPU.

## Risks & Mitigations

| Risk | Impact | Mitigation |
| :--- | :--- | :--- |
| **DMRG Convergence** | Medium | Use robust DMRG settings (sweep count, truncation error threshold); fallback to ED for smaller N if DMRG fails. |
| **Memory Overflow (N=40)** | High | Strict use of sparse matrices; streaming generation; limit N to 30 if 40 exceeds memory even with sparse ops. |
| **Compression Bias** | Medium | Use multiple compressors (gzip, lzma, bzip2) and compare results; use NCD relative to random baseline. |
| **Numerical Instability** | Medium | Filter NaNs/Infs; fail if valid count < 8 (FR-008). |
| **Confounding by N** | High | Mandate partial correlation and stratified analysis to control for system size. |