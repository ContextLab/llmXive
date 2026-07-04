# Implementation Plan: Statistical Analysis of Publicly Available Election Poll Aggregates

**Branch**: `001-statistical-poll-aggregation` | **Date**: 2024-05-21 | **Spec**: `specs/001-statistical-poll-aggregation/spec.md`
**Input**: Feature specification from `specs/001-statistical-poll-aggregation/spec.md`

## Summary

This project implements a comparative statistical analysis of three election forecasting methods: Simple Averaging, Accuracy-Weighted Averaging, and Bayesian Hierarchical Modeling. The system ingests raw poll data from FiveThirtyEight (verified), harmonizes the data, computes forecasts, and evaluates them against actual election outcomes using RMSE, MAE, and Hierarchical Meta-Analysis. The implementation strictly adheres to CPU-only constraints (limited cores, constrained RAM) and ensures reproducibility via pinned dependencies and checksummed data. **Note:** RealClearPolitics (RCP) data is excluded from the scope due to the absence of a verified source URL, ensuring compliance with the 'Verified Accuracy' principle.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `numpy`, `scipy`, `pymc` (v5+), `arviz`, `requests`, `pyyaml`, `statsmodels`  
**Storage**: Local CSV files (`data/raw/`, `data/processed/`), JSON metadata  
**Testing**: `pytest` with contract tests against YAML schemas  
**Target Platform**: GitHub Actions Free Tier (Linux, 2 CPU, ~7GB RAM, No GPU)  
**Project Type**: Data Analysis Pipeline / Statistical Library  
**Performance Goals**: Full pipeline completion < 4 hours on 2-core CPU  
**Constraints**: No GPU/CUDA; No large-LLM inference; Data subset to fit 7GB RAM; Deterministic random seeds  
**Scale/Scope**: Multiple election cycles (-2020), ~-2000 polls per cycle (FiveThirtyEight only)  

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **I. Reproducibility**: Plan mandates pinned `requirements.txt`, random seed setting in all scripts, and checksumming of raw data artifacts before processing.
- **II. Verified Accuracy**: Plan restricts dataset references to verified sources (FiveThirtyEight, MEDSL/Election Results). RealClearPolitics (RCP) is explicitly **excluded** from the scope because no verified URL exists, preventing "unreachable reference" errors. No fallback or runtime scraping is attempted.
- **III. Data Hygiene**: Plan enforces a "raw -> processed" flow where raw data is never modified; derivations are written to new files with checksums recorded in `state/`. Specifically, `weights.py` outputs to `data/processed/` and triggers a state update.
- **IV. Single Source of Truth**: All figures and statistics in the final output will be generated programmatically from `data/processed/` files, not hand-typed.
- **V. Versioning Discipline**: Artifacts will carry content hashes; `state/projects/...yaml` files will be updated on every run to include hashes of *derived* artifacts (e.g., `data/processed/poll_data_cleaned.csv`). The pipeline automatically computes the SHA-256 hash of every derived file and updates the `artifact_hashes` map in `state/projects/PROJ-206-statistical-analysis-of-publicly-availab.yaml`.
- **VI. Statistical Calibration Integrity**: Plan includes specific phases for calculating and reporting 95% credible interval coverage rates against actual outcomes, with a binomial test (null p0=0.95).
- **VII. Aggregation Methodology Transparency**: Plan requires explicit documentation of mathematical formulations for all three methods in `research.md`, including the static parameter Bayesian model.

## Project Structure

### Documentation (this feature)

```text
specs/001-statistical-poll-aggregation/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── dataset.schema.yaml
│   └── forecast.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
src/
├── data/
│   ├── download.py          # Ingests from verified sources (538 + Outcomes)
│   ├── harmonize.py         # Cleans and bins data, checks density
│   └── weights.py           # Calculates historical RMSE weights (out-of-sample)
├── models/
│   ├── frequentist.py       # Simple and Weighted averaging
│   └── bayesian.py          # PyMC hierarchical static model
├── evaluation/
│   ├── metrics.py           # RMSE, MAE, Coverage
│   └── meta_analysis.py     # Hierarchical Meta-Analysis of errors
├── utils/
│   ├── logging.py
│   └── config.py            # Seed pinning, path config
└── main.py                  # Pipeline orchestrator

tests/
├── contract/                # Schema validation tests
├── integration/             # End-to-end pipeline tests
└── unit/                    # Logic tests for weights, aggregation
```

**Structure Decision**: Single-project structure chosen to minimize overhead for a data analysis pipeline. Separation of `data`, `models`, and `evaluation` ensures modularity and testability while keeping dependencies manageable for the 2-core CPU constraint.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Bayesian Hierarchical Model (Static) | Required by FR-005 for uncertainty quantification. Changed from Random Walk to Static Parameter to correctly model election outcomes. | Simple averaging (FR-003) and weighted averaging (FR-004) are insufficient for the study's goal of comparing "calibrated uncertainty." |
| CPU-Only Constraint | Required by NFR-001 and GitHub Actions free tier limits. | GPU-accelerated methods (e.g., `torch.cuda`, `load_in_8bit`) would cause immediate job failure. |
| Hierarchical Meta-Analysis | Required to replace the invalid Diebold-Mariano test for static forecasts. | DM test assumes a forecast horizon and stationarity, which does not apply to a single static event per cycle. |
| Westfall-Young Correction | Required by FR-006 for statistical rigor under dependency. | Benjamini-Hochberg assumes independence, which is violated by correlated method errors. The Westfall-Young permutation method is explicitly selected to handle the high correlation between method errors. |

## Data Hygiene Alignment

- **Weights Calculation**: `src/data/weights.py` reads `data/raw/` and writes `data/processed/historical_weights.csv`.
- **State Update**: Upon successful write of any derived file (e.g., `weights.csv`, `cleaned.csv`), the pipeline automatically computes the SHA-256 hash and updates `state/projects/PROJ-206-statistical-analysis-of-publicly-availab.yaml` in the `artifact_hashes` map.
- **Raw Preservation**: Raw files in `data/raw/` are never overwritten; they are checksummed immediately upon download.

## Edge Case Handling

- **Low Data Density**: If < 5 polls in 30 days or < 3 distinct election cycles, the system halts and issues a warning (FR-008).
- **Global Poll Count**: If total poll count < 500, the system halts and reports a fatal error (FR-010).
- **Non-Convergence**: If R-hat > 1.05, the system reports an error and suggests increasing draws or simplifying the model.
- **Missing Outcomes**: If final election results are missing for a state/year, that cycle is excluded from the evaluation phase.
- **RCP Exclusion**: RealClearPolitics is explicitly excluded from the scope. No runtime fallback or scraping is attempted. If the spec requested it, the system logs a "Source Excluded" warning and proceeds with FiveThirtyEight data only.
- **Look-Ahead Bias Prevention**: The system enforces a strict temporal split where weights for cycle T are calculated using only data from cycles < T.