# Implementation Plan: Detecting Statistical Power Drift in Replicated Studies

**Branch**: `001-detect-power-drift` | **Date**: 2024-05-21 | **Spec**: `specs/001-detecting-statistical-power-drift-in-rep/spec.md`
**Input**: Feature specification from `/specs/001-detecting-statistical-power-drift-in-rep/spec.md`

## Summary

This feature implements a statistical pipeline to detect temporal drift in post-hoc statistical power within replication studies. The system calculates power estimates from reported effect sizes and sample sizes, fits a linear mixed-effects model to isolate the residual trend of power over time (adjusting for effect size and N), and validates findings via non-parametric permutation tests and sensitivity analyses across alpha thresholds. The implementation adheres to strict compute constraints (CPU-only, limited RAM) and data hygiene principles.

**Key Methodological Correction**: To avoid tautology, the outcome variable is defined as **Residual Power** (the residual of a preliminary regression of Power on Effect Size and Sample Size) or the Non-Centrality Parameter (NCP) is modeled directly. This ensures the drift model predicts unexplained variance rather than a deterministic function of its inputs.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `statsmodels` (for LMM/GLMM), `scipy`, `matplotlib`, `pyyaml`, `datasets` (HuggingFace)  
**Storage**: Local filesystem (`data/raw`, `data/derived`), CSV/Parquet formats  
**Testing**: `pytest` (unit tests for power formulas, integration tests for pipeline)  
**Target Platform**: Linux (GitHub Actions runner)  
**Project Type**: Data analysis pipeline / CLI  
**Performance Goals**: Complete full pipeline (download -> model -> plot) within 3.14 hours on 2-core CPU.  
**Constraints**: No GPU; must handle missing data gracefully; must stream large datasets if >7GB.  
**Scale/Scope**: Analysis of a substantial set of replication records (OSF data subset).

> Note: The "3.14 hours" runtime limit is a project constraint derived from the CI runner's maximum job duration policy.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **I. Reproducibility**: Plan mandates `random_seed` pinning in `code/` and deterministic dataset fetching from HuggingFace.
- **II. Verified Accuracy**: All citations in `research.md` are limited to the verified dataset URLs provided in the `Dataset Strategy` section below.
- **III. Data Hygiene**: Raw data will be checksummed; derived files (`residuals.csv`, `power_estimates.csv`) will be generated with explicit derivation logs.
- **IV. Single Source of Truth**: All plots and statistics will be generated programmatically from `data/derived` files; no manual entry.
- **V. Versioning**: Artifacts will include content hashes. The `state/projects/PROJ-150-detecting-statistical-power-drift-in-rep.yaml` file will be updated by a dedicated `update_state.py` script upon completion of each phase.
- **VI. Power Re-estimation Consistency**: Power will be calculated post-hoc using Cohen's *d* and N, ignoring author-reported power.
- **VII. Temporal Drift Modeling Rigor**: The plan explicitly includes the LMM (`residual_power ~ year + (1|field)`) and a permutation test.

## Project Structure

### Documentation (this feature)

```text
specs/001-detecting-statistical-power-drift-in-rep/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
code/
├── download_data.py         # Fetches OSF data from HuggingFace
├── calculate_power.py       # Computes post-hoc power (FR-001)
├── fit_model.py             # LMM fitting and LRT (FR-002, FR-003)
├── robustness.py            # Permutation test (FR-004) & Sensitivity (FR-005)
├── aggregate.py             # Inverse-variance weighting (FR-006) & Input Permutation (FR-007)
├── visualize.py             # Generates scatter plots (FR-009)
├── validate_source.py       # Schema validation (T007) - WRITES data/derived/schema_validation.json
├── update_state.py          # Updates state/ YAML (Constitution Principle V)
└── requirements.txt         # Pinned dependencies

data/
├── raw/                     # Downloaded parquet/CSV (checksummed)
└── derived/
    ├── power_estimates.csv  # Intermediate power calculations
    ├── residuals.csv        # Residuals for plotting (T013)
    └── schema_validation.json # Validation output (T007)

results/
└── power_drift_scatter.png  # Final visualization (T013)
```

**Structure Decision**: Single-project structure chosen to minimize I/O overhead on the CI runner. All scripts are modular but orchestrated sequentially to ensure data flows correctly from download to visualization.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Linear Mixed-Effects Model (LMM) | Required by FR-002 and Constitution Principle VII to control for field heterogeneity. | Simple linear regression would ignore clustering by `field` and `original_study_id`, violating statistical rigor. |
| Residual Power Outcome | Required to avoid tautology (Power = f(d, N)). | Modeling raw Power while including d and N as covariates creates a mathematically unstable model. |
| Permutation Test (large-scale)

The research question focuses on assessing the statistical significance of observed patterns through randomization. The method involves a permutation test with a large number of iterations to approximate the null distribution, ensuring robust p-value estimation without parametric assumptions. References: (DOI/arXiv/author-year). | Required by Constitution Principle VII to validate against model misspecification. | Parametric assumptions alone are insufficient for the "skeptical peer reviewer" scenario (US-2). |
| Sensitivity Sweep | Required by FR-005 to address alpha-threshold dependency. | Single alpha test fails to satisfy SC-003 stability measurement. |
| DerSimonian-Laird Aggregation | Required by FR-006 to combine field-specific slopes. | Simple averaging ignores heterogeneity between fields. |
| Input Permutation (FR-007) | Required to validate that drift is not an artifact of input distribution changes. | Year permutation (FR-004) only tests year drift; input permutation tests the stability of the relationship between inputs and drift. |

## Data Merging Strategy

To resolve conflicts if multiple datasets contain values for the same study ID:
1. **Primary Source**: The OSF Replication Project (Nosek et al.) is the ground truth.
2. **Fallback Logic**: If a study is missing in the primary source, check secondary sources.
3. **Conflict Resolution**: If a study exists in multiple sources with different values, the value from the primary source is used. If missing in primary, the value from the secondary source with the highest data completeness (most fields filled) is selected.
4. **Validation**: Any study with missing `effect_size` or `sample_size` in all sources is dropped with a warning (FR-008).

## Versioning Mechanism

To satisfy Constitution Principle V:
- The `state/projects/PROJ-150-detecting-statistical-power-drift-in-rep.yaml` file is the single source of truth for project state.
- The `update_state.py` script is responsible for updating this file.
- It runs after each major phase (download, calculation, modeling, robustness) to update the `updated_at` timestamp and record content hashes of the new artifacts.
- The `state/` directory structure is defined in the `Project Structure` section above.

## Cross-Reference of Verified Datasets

To satisfy Constitution Principle II:
- The 'Verified Datasets' block in `research.md` lists the exact URLs used.
- The 'Dataset Strategy' in `research.md` and the 'Technical Context' in `plan.md` explicitly reference these same URLs.
- No fallback to unverified sources is permitted; if the verified sources are inaccessible, the pipeline halts.