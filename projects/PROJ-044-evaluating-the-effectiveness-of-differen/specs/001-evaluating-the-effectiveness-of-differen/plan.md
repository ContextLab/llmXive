# Implementation Plan: Evaluating the Effectiveness of Differential Privacy in Federated Learning

**Branch**: `001-evaluating-dp-federated-learning` | **Date**: 2026-07-11 | **Spec**: `specs/001-evaluating-dp-federated-learning/spec.md`
**Input**: Feature specification from `/specs/001-evaluating-dp-federated-learning/spec.md`

## Summary

This feature implements a computational study evaluating how data heterogeneity (simulated via Dirichlet distributions) modulates the privacy-utility trade-off in Federated Learning (FL) with Differential Privacy (DP). **Scope Limitation:** Due to the absence of a verified, directly-downloadable source for the Shakespeare LEAF dataset in the project's `# Verified datasets` block, this implementation is limited to the **FEMNIST** dataset. The plan explicitly excludes Shakespeare to maintain Data Hygiene (Constitution Principle III) and Verified Accuracy (Principle II). The system will download FEMNIST, partition it across simulated clients, train models using FedAvg with Opacus-enabled DP, and perform rigorous statistical analysis (t-tests, sensitivity sweeps, mixed-effects models) to validate the "critical heterogeneity threshold" hypothesis (α ≤ 0.1).

## Gap Analysis (Spec vs. Plan)

| Spec Requirement | Plan Status | Reason |
|------------------|-------------|--------|
| **FR-001**: Download FEMNIST and Shakespeare | **Unmet (Partial)** | FEMNIST: Implemented. Shakespeare: **Excluded**. No verified source found in `# Verified datasets` block. Spec requires amendment to remove Shakespeare. |
| **US-1 Scenario 2**: Shakespeare partitioning | **Unmet** | Dependent on FR-001. Requires spec amendment to remove Shakespeare. |
| **US-1 Scenario 1**: FEMNIST partitioning | **Implemented** | FEMNIST source is verified. |
| **FR-002 - FR-007**: DP Training & Analysis | **Implemented** | FEMNIST-only scope. |

> **Action Required**: The Spec (`spec.md`) MUST be amended to remove references to Shakespeare datasets to align with the implementation plan. Until amended, FR-001 and US-1 Scenario 2 remain unmet requirements, and the plan is technically in violation of the Spec. The implementation will proceed with FEMNIST only, and the Spec must be updated to reflect this constraint before the project can advance to `research_accepted`.

## Technical Context

**Language/Version**: Python 3.10+  
**Primary Dependencies**: PyTorch (CPU), Opacus, Hugging Face `datasets`, `pandas`, `scipy`, `numpy`, `matplotlib`, `statsmodels`  
**Storage**: Local `data/` directory (raw + partitioned), `results/` (CSV logs), `artifacts/` (checksums)  
**Testing**: `pytest` (unit tests for partitioning logic, integration tests for training loop), statistical validation scripts  
**Target Platform**: Linux (GitHub Actions free-tier: 2 vCPU, 7GB RAM).  
**Performance Goals**: Complete 3 seeds × 5 ε values × 4 α values (0.05, 0.1, 0.5, 1.0) for FEMNIST within 6 hours on CPU.  
**Constraints**: Must run on CPU-first; no PII in data; checksums mandatory; Shakespeare excluded.  
**Scale/Scope**: A large-scale sample set (FEMNIST subset), A cohort of clients, A fixed number of training rounds per seed (reduced to a lower threshold if timeout risk detected).  

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **I. Reproducibility**: **PASS**. Plan mandates pinned seeds, canonical HF dataset sources, and re-runnable `code/` scripts.
- **II. Verified Accuracy**: **PASS**. All dataset URLs cited strictly from the `# Verified datasets` block (FEMNIST only). Shakespeare excluded to avoid fabrication.
- **III. Data Hygiene**: **PASS**. Plan includes checksumming of raw downloads and derivation logging for partitioned data.
- **IV. Single Source of Truth**: **PASS**. All metrics (accuracy, ε) logged to CSVs; figures generated directly from these logs.
- **V. Versioning Discipline**: **PASS**. Artifact hashes recorded in state YAML; code changes trigger state updates.
- **VI. Heterogeneity-Aware Evaluation**: **PASS**. Plan explicitly separates "majority" and "minority" client metrics based on Dirichlet partitions.
- **VII. Statistical Rigor**: **PASS**. Plan mandates multiple seeds per config (reduced for CPU feasibility), mixed-effects models, and sensitivity analysis on α.

## Project Structure

### Documentation (this feature)

```text
specs/001-evaluating-the-effectiveness-of-differen/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/           # Phase 1 output
    ├── dataset.schema.yaml
    └── results.schema.yaml
```

### Source Code (repository root)

```text
projects/PROJ-044-evaluating-the-effectiveness-of-differen/
├── data/
│   ├── raw/             # Downloaded parquet files
│   └── partitions/      # Client-specific splits (generated)
├── code/
│   ├── __init__.py
│   ├── data/
│   │   ├── download.py          # HF dataset fetcher
│   │   └── partition.py         # Dirichlet splitter
│   ├── models/
│   │   └── cnn.py               # FEMNIST model
│   ├── training/
│   │   ├── fedavg.py            # FL orchestrator
│   │   └── dp_utils.py          # Opacus wrapper
│   ├── analysis/
│   │   ├── stats.py             # t-tests, LMM, p-values
│   │   └── plots.py             # Sensitivity curves
│   └── main.py                  # CLI entry point
├── tests/
│   ├── unit/
│   │   └── test_partition.py
│   └── integration/
│       └── test_training_loop.py
├── requirements.txt
└── README.md
```

**Structure Decision**: Single project structure chosen to minimize overhead for a computational research pipeline. Data, code, and analysis are tightly coupled.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Shakespeare Exclusion** | No verified source found in `# Verified datasets` block. | Including unverified data violates Constitution Principle II (Verified Accuracy) and risks fabrication. |
| **Compute Fallback** | 6-hour CPU limit for full DP-FL training is tight. | Reducing rounds/seeds is preferred over relying on non-deterministic external GPU availability. |
| **Statistical Rigor (Mixed-Effects)** | Required to handle nested data structure (clients within seeds). | Simple t-tests ignore correlation within seeds, inflating Type I error. |
| **Heterogeneity Simulation** | Essential for US-1 and the core research question. | Homogeneous data would invalidate the study's premise. |

## Performance Goals & Convergence Check

- **Baseline Configuration**: 3 seeds × 5 ε values × 4 α values (0.05, 0.1, 0.5, 1.0) = 60 runs.
- **Total Runs**: 60 runs.
- **Time Budget**: 6 hours on GitHub Actions CPU.
- **Convergence Check**: Each run monitors loss. If loss plateaus before a predefined maximum number of rounds, training stops early.
- **Timeout Handling**: If a predefined time limit is approached (e.g., several hours), remaining rounds are reduced to a predefined threshold and the run is flagged as `is_time_limited=True` in the results CSV.
- **Metric Exclusion**: Runs flagged as `is_time_limited=True` are **excluded** from SC-001 (Convergence Speed) analysis because the "rounds to reach target" cannot be accurately measured for incomplete runs. The analysis script will explicitly filter these rows.
