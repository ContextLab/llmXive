# Implementation Plan: Normalized Gaps Between Consecutive Squarefree Numbers

**Branch**: `001-normalized-squarefree-gaps` | **Date**: 2026-08-20 | **Spec**: `specs/001-normalized-gaps-between-consecutive-squa/spec.md`
**Input**: Feature specification from `/specs/001-normalized-gaps-between-consecutive-squa/spec.md`

## Summary

This project validates the hypothesis that normalized gaps between consecutive squarefree integers follow a standard exponential distribution (rate=1). The technical approach involves implementing a deterministic linear sieve (O(N log log N)) to generate squarefree sequences up to $N=10^7$, computing raw and normalized gaps, and performing a Lilliefors-style goodness-of-fit test via Monte Carlo simulation with a sufficient number of resamples to account for the estimated mean. A control dataset generated via random thinning (probability $/\zeta(2)$) serves as a baseline, alongside a secondary Gamma control to validate test power. All results are visualized via CDF/QQ-plots and convergence analysis charts.

**Critical Note on Spec Contradictions**:
The implementation plan below follows the *corrected* statistical methodology (Lilliefors via Monte Carlo, scaling analysis) and data standards (Parquet). The source `spec.md` contains flawed Success Criteria (SC-003, SC-004) that are statistically unsound. The plan explicitly rejects these and implements the corrected metrics:
- **SC-003 Correction**: Replaced "KS statistic within 10% between N values" with **KS * sqrt(N) stability**.
- **SC-004 Correction**: Replaced "R^2 > 0.99" with **Anderson-Darling statistic**.
- **SC-007 Addition**: Added **Gamma Control Rejection** to validate test power (missing from source spec).
The implementation will strictly follow these corrected metrics. The source `spec.md` is flagged for immediate update to align with this plan.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `numpy`, `scipy`, `matplotlib`, `pytest`, `pyarrow`  
**Storage**: Local file system (**Parquet**) under `data/`; no external database.  
**Testing**: `pytest` (unit, integration, and contract tests).  
**Target Platform**: GitHub Actions runner (Linux, 2 CPU, 7 GB RAM).  
**Project Type**: Computational research / CLI tool.  
**Performance Goals**: Generate $N=10^7$ in < 6 hours; peak memory < 2 GB.  
**Constraints**: No GPU required; deterministic sieving; no external data downloads (integer generation is local).  
**Scale/Scope**: $N \in \{10^6, 5\times10^6, 10^7\}$.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Implementation Note |
|-----------|--------|---------------------|
| **I. Reproducibility** | **PASS** | Random seeds pinned in `code/`. Sieve is deterministic. No external data dependencies (integers generated locally). |
| **II. Verified Accuracy** | **PASS** | Citations in `research.md` will be validated against the "Verified datasets" block (none required for generated data). |
| **III. Data Hygiene** | **PASS** | Generated data checksummed in `state/`. Raw data preserved; derivations written to new files. |
| **IV. Single Source of Truth** | **PASS** | All figures/stats trace to `data/` and `code/`. No hand-typed numbers. |
| **V. Versioning Discipline** | **PASS** | Artifacts carry content hashes. `state/` updated on change. All code and data paths are versioned via git. |
| **VI. Deterministic Number-Theoretic Sieving** | **PASS** | Linear sieve implementation ensures invariant ordered lists for a given $N$. No stochastic approximations in sieving. |
| **VII. Rigorous Statistical Convergence Validation** | **PASS** | KS statistic and p-value tracked across $N=10^6, 5\times10^6, 10^7$. Implementation uses **KS * sqrt(N) stability** (corrected SC-003) and **Anderson-Darling statistic** (corrected SC-004). Includes Gamma control (SC-007) to validate test power. |

## Project Structure

### Documentation (this feature)

```text
specs/001-normalized-squarefree-gaps/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (3 canonical schemas only)
└── tasks.md             # Phase 2 output (NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
projects/PROJ-722-normalized-gaps-between-consecutive-squa/
├── code/
│   ├── __init__.py
│   ├── sieve.py          # Linear sieve implementation (FR-001)
│   ├── gaps.py           # Gap calculation & normalization (FR-002)
│   ├── stats.py          # Lilliefors test & Monte Carlo (FR-003)
│   ├── viz.py            # CDF, QQ, Convergence plots (FR-004, FR-005)
│   ├── control.py        # Random thinning & Gamma controls (FR-006, FR-008)
│   └── main.py           # Orchestration script
├── data/
│   ├── raw/              # Generated squarefree sequences (checksummed, Parquet)
│   ├── processed/        # Normalized gaps, test results (Parquet/JSON)
│   └── figures/          # Generated plots
├── tests/
│   ├── contract/         # Schema validation tests
│   ├── integration/      # End-to-end pipeline tests
│   └── unit/             # Sieve and stats logic tests
├── requirements.txt
└── README.md
```

**Structure Decision**: Single project structure (Option 1) chosen for simplicity. All logic is contained within `code/` with a clear separation of concerns (sieve, gaps, stats, viz).

## Contract Mapping

The following schemas in `contracts/` correspond to the entities defined in `data-model.md`. Redundant schemas have been removed.

| Entity (data-model.md) | Contract File | Purpose |
|------------------------|---------------|---------|
| **SquarefreeSequence** | `SquarefreeSequence.schema.yaml` | Validates metadata and path for the generated integer sequence. |
| **GapDataset** | `GapDataset.schema.yaml` | Validates metadata and paths for raw/normalized gaps. |
| **TestResult** | `TestResult.schema.yaml` | Validates the output of the Lilliefors test (KS, p-value, N). |

*Note: Only the three canonical schemas above are present in `contracts/`. Redundant files (`dataset_schema.yaml`, `gap_dataset.schema.yaml`, `gap_dataset_schema.yaml`) have been removed to ensure coherence.*

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Lilliefors via Monte Carlo** | Standard KS test is invalid when parameters are estimated from data. | Using standard KS would yield incorrect p-values, violating Principle VII (Rigorous Statistical Convergence). |
| **Control Dataset (Random Thinning)** | Needed to distinguish between testing the distribution shape and validating the "random thinning" heuristic. | Testing only the squarefree gaps against Exponential(1) would not prove the heuristic; a baseline is required for comparison (FR-006). |
| **Secondary Control (Gamma)** | Needed to prove the test can reject non-exponential distributions. | Relying only on the random thinning control (which is exponential by construction) does not demonstrate the test's power to detect deviations (FR-008). |

### Corrected Success Criteria Implementation

The plan implements the following corrected metrics, overriding the flawed source spec:
1. **Convergence Metric**: Instead of SC-003's "[deferred] difference", the plan tracks **$KS \times \sqrt{N}$** for stability across $N$.
2.  **QQ-Plot Metric**: Instead of SC-004's "R^2 > 0.99", the plan uses the **Anderson-Darling statistic** (A^2) for tail sensitivity.
3.  **Test Power**: Added **SC-007** requiring the test to reject the Gamma control (p < 0.05).
