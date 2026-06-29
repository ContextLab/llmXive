# Implementation Plan: Quantifying Entanglement Entropy in Randomly Perturbed Quantum Spin Chains

**Branch**: `[PROJ-308-001-quantify-entanglement]` | **Date**: 2026-06-24 | **Spec**: `spec.md`
**Input**: Feature specification from `specs/001-quantifying-entanglement-entropy-in-rand/spec.md`

## Summary

This feature implements a computational workflow to quantify entanglement entropy scaling in randomly perturbed XXZ Heisenberg spin chains. The system generates random Hamiltonians, computes ground states via imaginary-time TEBD using the TeNPy library, calculates von Neumann entropy for all bipartitions, and performs statistical regression to extract scaling exponents ($\alpha$) and thermal slopes ($\beta$).

**Critical Methodological Update**: The plan now employs a **multi-model selection approach** (Logarithmic vs. Constant vs. Linear) using AIC to distinguish phases. This corrects the category error of using a linear fit to identify an area law. The workflow includes a **pilot variance estimation** step to dynamically adjust the number of disorder realizations ($N_{\text{real}}$) if variance is too high, and an **adaptive bond dimension** strategy to prevent systematic bias in the critical regime.

## Technical Context

**Language/Version**: Python 3.10+  
**Primary Dependencies**: `tenpy` (CPU-only, pinned to specific commit/version for reproducibility), `numpy`, `scipy`, `pandas`, `matplotlib`, `pytest`  
**Storage**: 
- `data/`: Raw entropy data, processed fits, plots.
- `state/`: **Single Source of Truth** for versioning, checksums, and advancement metadata (per Constitution Principle V).
- `code/`: Scripts and libraries.
**Testing**: `pytest` (unit tests for Hamiltonian generation, regression logic; integration tests for full workflow).  
**Target Platform**: GitHub Actions `ubuntu-latest` (2 vCPUs, ~7 GB RAM, CPU-only).  
**Project Type**: Scientific CLI / Computational Physics Library  
**Performance Goals**: Complete workflow for $L=30, \delta=0.2, N=100$ within 6 hours; memory usage < 6 GB.  
**Constraints**: Double-precision arithmetic only; no GPU; strict input validation ($L$ within a moderate range, $0 \le \delta \le 1$); a sufficient number of bootstrap resamples.  
**Scale/Scope**: Single chain length per run (default 30); grid scan support via `delta_grid.csv`; A finite set of disorder realizations will be employed.

> **Note on Compute Feasibility**: The plan explicitly implements an adaptive bond dimension strategy (starting from a lower bound up to 400) with a convergence check. If convergence fails at chi=400, the realization is flagged as 'numerically unresolved' and excluded from the final fit to prevent systematic bias. This ensures the 6-hour CPU limit is respected while maintaining numerical accuracy.

## Constitution Check

*GATE: Must pass before Phase 0 research.*

| Principle | Status | Implementation Detail |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | Random seeds pinned in config; TeNPy version pinned; `requirements.txt` enforces dependency freeze; full workflow runnable on fresh runner. |
| **II. Verified Accuracy** | **PASS** | All theoretical references (Refael-Moore, CFT) cited in `research.md` and validated by the Reference-Validator Agent against primary sources before `research_accepted`. No citations in `plan.md` require separate validation as all scientific claims are deferred to `research.md`. |
| **III. Data Hygiene** | **PASS** | Raw entropy data stored as CSV; checksums recorded in `state/`; no in-place modification; derivatives (fits) stored separately. |
| **IV. Single Source of Truth** | **PASS** | All figures and statistics in `scaling_fit.txt` and `bootstrap_summary.txt` are generated directly from `entropy_data.csv` and `data/raw/metadata.json`. The `state/` YAML file tracks all artifact hashes. |
| **V. Versioning Discipline** | **PASS** | Artifacts in `data/` and `code/` carry content hashes; `state/projects/PROJ-308-...yaml` is updated on change to track advancement. |
| **VI. Numerical Stability** | **PASS** | Double-precision enforced in TeNPy config; truncation error thresholds logged; convergence tolerance strictly enforced. |
| **VII. Statistical Sampling** | **PASS** | Minimum 50 realizations enforced (default 100); pilot study determines if N=100 is sufficient for target CI width; bootstrap resamples with sufficient quantity to ensure stability, with pinned seed; `data/raw/metadata.json` records $N_{\text{real}}$ as the SSoT for this metric. |

## Project Structure

### Documentation (this feature)

```text
specs/PROJ-308-001-quantifying-entanglement/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (generated later)
```

### Source Code (repository root)

```text
projects/PROJ-308-quantifying-entanglement-entropy-in-rand/
├── code/
│   ├── __init__.py
│   ├── config.py              # Parameter validation, defaults
│   ├── hamiltonian.py         # XXZ + random couplings generation
│   ├── ground_state.py        # TEBD imaginary time evolution
│   ├── entropy.py             # Von Neumann entropy calculation
│   ├── analysis.py            # Regression, bootstrap, plotting, model selection
│   ├── cli.py                 # Entry point for workflow execution
│   └── requirements.txt       # Pinned dependencies
├── data/
│   ├── raw/                   # Generated entropy_data.csv, metadata.json
│   └── processed/             # Fitted parameters, plots
├── state/                     # Versioning and advancement metadata
│   └── projects/
│       └── PROJ-308-quantifying-entanglement-entropy-in-rand.yaml
├── tests/
│   ├── unit/
│   │   ├── test_hamiltonian.py
│   │   └── test_entropy.py
│   └── integration/
│       └── test_workflow.py
└── docs/
    └── ...
```

**Structure Decision**: Single-project structure (`code/`, `data/`, `state/`, `tests/`) selected to align with the scientific workflow nature (CLI-driven, data-centric) and to simplify CI configuration for a single runner job.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **Bootstrap Resampling (1000+)** | Required by FR-006 and SC-001/SC-002 for robust error estimation and CI width. | Simple analytic error bars are insufficient for non-Gaussian distributions in disordered systems. |
| **TEBD with Double Precision** | Required by Constitution Principle VI for numerical stability. | Single precision often leads to convergence failure or spurious entropy values in long chains. |
| **Grid Scan Support** | Required by US-2 and FR-010 to map the MBL-thermal crossover. | Single-parameter runs do not provide the phase diagram needed for the scientific objective. |
| **Adaptive Bond Dimension** | Required to avoid systematic bias in the critical regime where chi > 200 may be needed. | Hard cap (chi=200) risks artificially suppressing entropy and mimicking an area law. |
| **Model Selection (AIC)** | Required to correctly distinguish Area Law (Constant) from Logarithmic growth and Volume Law (Linear). | Simple R² comparison between Log and Linear fits is mathematically unsound for identifying area laws. |

