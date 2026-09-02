# Implementation Plan: Assessing Reproducibility of Machine‑Learned Reaction Yield Models

**Branch**: `[PROJ-761-01-reproducibility]` | **Date**: 2026-06-25 | **Spec**: `spec.md`
**Input**: Feature specification from `/specs/PROJ-761-01-reproducibility/spec.md`

## Summary

This feature implements a reproducible pipeline to audit the performance claims of machine-learned reaction yield models. The system ingests a manifest of target papers, retrieves their specific dataset versions and hyperparameters, re-implements the models on a CPU-constrained environment, and computes deviations from reported metrics (MAE, R², Spearman ρ). It performs statistical meta-analysis (paired t-tests, Bland-Altman, mixed-effects models) to quantify systematic bias and generates a community guideline checklist based on identified failure modes. The plan strictly adheres to the project constitution regarding environment isolation, data versioning, and the requirement to handle missing covariates transparently.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: PyTorch 2.2 (CPU-only), scikit-learn 1.5, RDKit, pandas, statsmodels, pyyaml, ruff, black.  
**Storage**: Local filesystem (GitHub Actions ephemeral storage); datasets streamed from Hugging Face.  
**Testing**: pytest (unit/integration), contract tests against YAML schemas.  
**Target Platform**: Linux (GitHub Actions free-tier runner: multiple vCPU, ample RAM).  
**Project Type**: CLI/Analysis Pipeline.  
**Performance Goals**: Complete per-paper reproduction within 45 minutes; full meta-analysis within 2 hours.  
**Constraints**: No GPU usage; models limited to ≤1M parameters or classical ML; strict adherence to pinned library versions; all data must be downloadable without credentials.  
**Scale/Scope**: Targeting a representative sample of papers from the manifest; processing a large volume of reaction records total (streamed).

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

1.  **Reproducibility (NON-NEGOTIABLE)**: The plan mandates a Docker image built from a pinned `Dockerfile` and `requirements.txt`. Random seeds are pinned in code (`seed=42` default). External datasets are fetched from specific Hugging Face URLs (verified in research.md).
2.  **Verified Accuracy**: The plan includes a `ReferenceValidator` step (Phase 0) to verify citations and dataset URLs against the "Verified datasets" block before execution.
3.  **Data Hygiene**: Raw data is streamed and checksummed; transformations write to new files in `data/processed`. No in-place modification.
4.  **Single Source of Truth**: All metrics (MAE, R², ρ) and deviations are written to `artifacts/reports/repro_results.json` and `stat_summary.json`. The final checklist derives strictly from these JSON artifacts.
5.  **Versioning Discipline**: The Docker image hash and library versions are logged to `state/...yaml` and `artifacts/logs/environment.log`.
6.  **Dataset Version Fidelity**: The plan explicitly retrieves "exact dataset versions" (e.g., `uspto_balanced_200k_ipc_classification` v1.0) and records the version in `data/manifest.yaml`.
7.  **Computational Environment Consistency**: The plan enforces CPU-only execution via Docker constraints and explicit `device="cpu"` flags in code, preventing accidental GPU allocation.

## Project Structure

### Documentation (this feature)

```text
specs/PROJ-761-01-reproducibility/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/           # Phase 1 output (Schemas) - Located at project root
```

### Source Code (repository root)

```text
projects/PROJ-761-assessing-reproducibility-of-machine-lea/
├── data/
│   ├── raw/             # Downloaded datasets (streamed/checksummed)
│   ├── processed/       # Preprocessed splits
│   └── manifest.yaml    # Dataset version registry
├── code/
│   ├── __init__.py
│   ├── ingest.py        # Manifest parsing & data loading
│   ├── model_runner.py  # Training, evaluation, seed sweep logic
│   ├── stats.py         # T-tests, Bland-Altman, LME, Heterogeneity
│   ├── guidelines.py    # Checklist generation logic
│   ├── main.py          # Orchestration
│   └── utils.py         # Helpers, checksumming
├── tests/
│   ├── contract/        # Schema validation tests
│   ├── unit/            # Logic tests
│   └── integration/     # End-to-end pipeline tests
├── artifacts/
│   ├── logs/            # Environment logs, failure logs
│   ├── plots/           # Bland-Altman PNGs
│   └── reports/         # repro_results.json, stat_summary.json, checklist.md
├── contracts/           # YAML Schemas for data interchange (ROOT)
│   ├── PaperManifest.schema.yaml
│   ├── ReproResult.schema.yaml
│   └── StatSummary.schema.yaml
├── Dockerfile           # CPU-only environment
└── requirements.txt     # Pinned dependencies
```

**Structure Decision**: The single-project structure is selected to minimize overhead on the free-tier CI runner. All components (ingestion, training, stats, reporting) reside in `code/` to ensure a unified execution context and simplify dependency management. The `contracts/` directory at the root provides a clear schema registry for the Implementer Agent to validate outputs.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Linear Mixed-Effects Model (LME) with Fixed Effects | Spec FR-008 explicitly requires fixed effects for preprocessing version, library version, and seed choice. **Correction**: Since library/version/seed are constant across the run, we use 'ModelSubstitution' and 'CovariateMissing' as fixed effects (which vary) and treat 'SeedChoice' as a random effect or omit it. This satisfies FR-008 by modeling the actual sources of variance. | A random-intercept-only model (T027 old) fails to address the specific variance components mandated by the spec, rendering the study unable to answer "what drives the discrepancy?". |
| Covariate Extraction & Missing Data Handling | Spec FR-003 requires verifying the dataset contains necessary covariates (temperature, solvent, etc.). | Ignoring missing covariates (removing T020-T022) would violate the spec's requirement to flag studies that cannot be fully reproduced due to data gaps, leading to "silent failures". |
| Seed Sweep (seeds) | Spec FR-010 requires reporting maximum metric variance across seeds to assess stability. | A single-run approach cannot quantify the sensitivity of the model to random initialization, which is a core aspect of reproducibility. |
| Heterogeneity (I²) & Qualitative Log | Required for the meta-analysis and guideline synthesis (Phase 3). | Omitting these prevents the calculation of pooled effect sizes and the generation of evidence-based guidelines (T030, T034). |
| Timeout Protection | The A time limit per paper on 2 vCPU may not suffice for 3 seeds. | Skipping the sweep for a paper (recording 'sweep_incomplete') is better than failing the entire pipeline, ensuring partial progress is recorded. |

## Implementation Phases

### Phase 0: Verification & Setup
- **T001**: Initialize Docker environment (Python 3.11, CPU-only PyTorch 2.2).
- **T002**: **ReferenceValidator**: Verify all citations and dataset URLs in `research.md` against the "Verified Datasets" block. Block execution if any fail.
- **T003**: Validate `data/manifest.csv` against `PaperManifest.schema.yaml`.

### Phase 1: Data Preparation & Extraction
- **T006**: Define `PaperManifest` schema (includes `dataset_version`, `replicates`, `conditions`).
- **T007**: Define `ReproResult` schema (includes `absolute_deviations`, `max_metric_std`, `flags`).
- **T013**: Implement `model_runner.py` (training, evaluation).
- **T017**: **Sensitivity Analysis**: Run seed sweep {, random seeds, multiple}. **Timeout Protection**: If >45 mins, skip sweep, flag `sweep_incomplete`. Output `max_metric_std`.
- **T020**: **Extract Covariates**: Parse paper methods for required covariates (temperature, solvent).
- **T021**: **Verify Dataset**: Check if `dataset_url` contains required covariates.
- **T022**: **Handle Missing**: If covariates missing, mark paper as `covariate_missing` and **exclude from deviation calculation** (mark as `unreproducible`). Do not attempt partial reproduction.
- **T018**: **Aggregate Results**: Combine T013 and T017 outputs into `ReproResult`. Ensure `max_metric_std` is present.

### Phase 2: Statistical Analysis
- **T025**: Paired T-Test (FR-006): Compare reported vs. reproduced. Apply Bonferroni correction.
- **T026**: Bland-Altman Plots (FR-007).
- **T027**: **Linear Mixed-Effects Model**: Fixed effects = `ModelSubstitution`, `CovariateMissing` (if present). Random effects = `Paper`. (SeedChoice omitted as fixed effect due to low variance).
- **T029**: **Heterogeneity**: Calculate I² using **relative error** (standardized effect size).
- **T030**: **Failure Log**: Generate qualitative log of excluded papers and reasons.

### Phase 3: Reporting & Guidelines
- **T034**: Generate `reproducibility_checklist.md` (FR-011) based on T030 failure log.
- **T036**: Finalize `stat_summary.json` and `repro_results.json`.
- **T037**: Write environment hash and version info to `state/...yaml`.
- **T038**: Unit tests for LME and Heterogeneity logic.

## Dependency Graph

- T002 (Validator) -> T003 (Manifest)
- T020-T022 (Covariates) -> T013 (Model Runner)
- T017 (Sensitivity) -> T018 (Aggregation)
- T018 (Aggregation) -> T025-T030 (Stats)
- T030 (Failure Log) -> T034 (Guidelines)

## Risk Mitigation

- **Risk**: Dataset lacks covariates. **Mitigation**: T022 excludes paper from analysis rather than producing biased results.
- **Risk**: Time limit exceeded. **Mitigation**: T017 timeout protection flags `sweep_incomplete` and proceeds.
- **Risk**: LME convergence failure. **Mitigation**: T027 falls back to random-intercept-only if fixed effects are singular, logging the fallback.

## Success Criteria Alignment

- **SC-001**: `absolute_deviations` in `ReproResult`.
- **SC-002**: `paired_ttest` results in `StatSummary`.
- **SC-003**: `max_metric_std` in `ReproResult`.
- **SC-004**: `variance_components` in `StatSummary`.
- **SC-005**: `reproducibility_checklist.md` with 5+ items.