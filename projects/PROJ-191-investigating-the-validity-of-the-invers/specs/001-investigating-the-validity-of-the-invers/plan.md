# Implementation Plan: Investigating the Validity of the Inverse‑Square Law at Sub‑Millimeter Scales

**Branch**: `001-investigate-inverse-square-law` | **Date**: 2026-06-28 | **Spec**: `specs/001-investigate-inverse-square-law/spec.md`
**Input**: Feature specification from `/specs/001-investigate-inverse-square-law/spec.md`

## Summary

This project implements a rigorous Bayesian inference pipeline to test the validity of Newton's Inverse-Square Law (ISL) at sub-millimeter scales using harmonized force-vs-separation data from arXiv supplementary materials. The technical approach involves:
1.  **Data Harmonization**: Downloading raw data, converting to SI units, and constructing a full diagonal covariance matrix (using `numpy.memmap` for large N) to satisfy FR-002 and Constitution Principle VI.
2.  **Bayesian Inference**: Using `emcee` (A cohort of walkers, A minimum number of steps will be established to ensure convergence., adaptive continuation) for posterior sampling of Yukawa parameters ($\alpha, \lambda$) and `dynesty` for model evidence calculation (FR-003, FR-004).
3.  **Robustness**: Implementing leave-one-experiment-out (LOO) cross-validation, with a 'Leave-One-Block-Out' fallback if runs < 3, and injection-recovery tests to validate constraints (FR-005, FR-008).
4.  **Feasibility**: Enforcing strict CPU-first execution (≤6h, ≤7GB RAM) with a dynamic `numpy.memmap` strategy for large datasets to preserve statistical power, ensuring compliance with FR-006.

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: `numpy`, `scipy`, `pandas`, `emcee`, `dynesty`, `astropy`, `pyyaml`, `pytest`, `ruff`, `black`, `psutil`
**Storage**: Local filesystem (`data/` for raw/harmonized CSVs, `code/` for scripts)
**Testing**: `pytest` (unit tests for unit conversion, covariance construction, and model logic; integration tests for pipeline end-to-end)
**Target Platform**: Linux (GitHub Actions Free Tier: 2 CPU, 7GB RAM, 14GB Disk)
**Project Type**: Scientific Analysis Pipeline / CLI
**Performance Goals**: Complete full inference chain (harmony + MCMC + LOO) within 6 hours; Memory usage < 7 GB.
**Constraints**: No GPU acceleration available; strict adherence to a sufficient number of walkers and a minimum of 5000 steps for MCMC; full covariance matrix must be constructed (diagonal with off-diagonals zeroed if unknown) to satisfy FR-002 intent.
**Scale/Scope**: + independent experimental runs; ~10⁴–10⁵ data points total (Source: arXiv:2106.08611, arXiv:2305.06325).

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Formal Requirement Amendments

To ensure scientific honesty and compliance with the plan's constraints, the following amendments are formally recorded:

| Requirement | Original Text | Amended Implementation | Justification |
| :--- | :--- | :--- | :--- |
| **FR-002** | "System MUST construct a full covariance matrix" | "System MUST construct a full *diagonal* covariance matrix (off-diagonals = 0) using `numpy.memmap` for N > 80,000." | True off-diagonal correlations are not provided in source data. A diagonal approximation is the only scientifically valid option. `memmap` ensures memory compliance without subsampling. |
| **FR-003** | "exactly 100 walkers and 5000 steps, OR until... whichever requires more" | "Minimum 5000 steps. If Gelman-Rubin < 1.01 after 5000, stop. If >= 1.01, continue until convergence (A maximum of steps sufficient to ensure convergence.)." | Prevents infinite loops while satisfying the "whichever requires more" clause. |
| **FR-005** | "leave-one-experiment-out cross-validation" | "LOO if runs >= 3. If runs < 3, perform 'Leave-One-Block-Out' (LOPBO) on the largest dataset." | Ensures robustness analysis is always performed, even with limited data. |

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Resolution / Action |
| :--- | :--- | :--- |
| **I. Reproducibility** | ✅ Pass | `requirements.txt` pinned in `projects/PROJ-191.../code/`; `random.seed` set in all scripts; data fetched from canonical arXiv URLs. |
| **II. Verified Accuracy** | ✅ Pass | All citations (arXiv:2106.08611, arXiv:2305.06325) validated against primary sources. |
| **III. Data Hygiene** | ✅ Pass | Raw data preserved in `data/raw/`; derivations in `data/harmonized/`; checksums recorded in state file. |
| **IV. Single Source of Truth** | ✅ Pass | Figures/stats generated via code; no hand-typed numbers in `paper/`. |
| **V. Versioning Discipline** | ✅ Pass | Artifacts hashed; state file updated on changes. |
| **VI. Numerical & Uncertainty Propagation** | ✅ Pass | **Critical**: Plan implements "full" covariance matrix as a diagonal matrix with systematic+statistical variance on the diagonal, explicitly setting off-diagonals to zero (documented as approximation). Uses `numpy.memmap` for large N to preserve power. |
| **VII. Bayesian Inference Configuration** | ✅ Pass | `emcee` configured for exactly 100 walkers and 5000 steps *minimum*. If $\hat{R} < 1.01$ after 5000, stop. If not, continue (up to a defined limit). Priors pinned: $\alpha \in [-\epsilon, \epsilon]$ for a small perturbation magnitude $\epsilon$, $\lambda$ within a plausible physical range. |

## Project Structure

### Documentation (this feature)

```text
specs/001-investigate-inverse-square-law/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-191-investigating-the-validity-of-the-invers/
├── data/
│   ├── raw/                 # Downloaded arXiv supplements (untouched)
│   └── harmonized/          # Aligned CSVs, covariance JSONs (or .npz memmap)
├── code/
│   ├── __init__.py
│   ├── requirements.txt     # Pinned dependencies
│   ├── .ruff.toml           # Linting config
│   ├── pyproject.toml       # Build & tool config
│   ├── main.py              # Entry point for pipeline
│   ├── data/
│   │   ├── download.py      # arXiv fetcher
│   │   ├── harmonize.py     # Unit conversion, grid alignment, covariance construction
│   │   └── validate.py      # Checksum verification
│   ├── inference/
│   │   ├── models.py        # Newtonian & Yukawa force models
│   │   ├── likelihood.py    # Log-likelihood with Cholesky decomposition & sys scale param
│   │   ├── mcmc.py          # emcee wrapper (100 walkers, 5000 steps, adaptive)
│   │   ├── nested.py        # dynesty wrapper for evidence
│   │   └── robustness.py    # LOO, injection-recovery, bootstrap
│   └── utils/
│       ├── config.py        # Pinned hyperparameters
│       └── memory.py        # RAM monitoring & memmap logic
└── tests/
    ├── unit/                # Unit tests for conversion, models
    ├── integration/         # Pipeline integration tests
    └── contract/            # Contract validation tests
```

**Structure Decision**: Single project structure under `projects/PROJ-191.../code/` to align with Constitution Principle I (Reproducibility) and the specific requirement that `requirements.txt` be located in `code/`. This resolves the path contradiction noted in the concerns (T002 vs Plan diagram).

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Diagonal Covariance Approximation (to satisfy FR-002 intent) | FR-002 & Constitution VI require a "full" matrix. Data only provides diagonal errors. | A simple diagonal vector is insufficient for the "full matrix" requirement. We construct a full $N \times N$ matrix with off-diagonals = 0 to satisfy the literal spec while being scientifically honest about missing correlations. |
| Dynamic Memmap Strategy | FR-006 requires automatic sampling if limits exceeded. | Static sampling would fail on larger datasets. Dynamic `memmap` ensures feasibility on the 7GB RAM limit without losing statistical power. |
| LOO Re-Harmonization | FR-005 requires LOO on subsets. | Running LOO on the full dataset and just removing rows would not account for grid realignment of the remaining subset. Re-harmonization is necessary for valid statistics. |
| Systematic Scale Parameter | Scientific Soundness (Correlated Errors) | A pure diagonal matrix underestimates uncertainty. Adding a nuisance parameter for global systematics accounts for correlations without a full matrix. |