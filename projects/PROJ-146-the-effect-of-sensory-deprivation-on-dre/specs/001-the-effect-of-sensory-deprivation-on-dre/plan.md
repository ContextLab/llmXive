# Implementation Plan: The Effect of Sensory Deprivation on Dream Recall and Bizarreness (Simulation Study)

**Branch**: `001-sensory-deprivation-dreams` | **Date**: 2026-07-04 | **Spec**: `specs/001-sensory-deprivation-dreams/spec.md`

## Summary

This project implements a **Simulation Study** to validate a statistical pipeline for analyzing the effect of sensory deprivation on dream recall and bizarreness. Since no public dataset contains experimentally controlled sensory deprivation metadata linked to standardized bizarreness scores, the primary mechanism is a synthetic data generator. The pipeline ingests data (real or synthetic), fits mixed-effects models (logistic for recall, linear/ordinal for bizarreness), performs sensitivity analyses (threshold sweeps, bootstrapping), and outputs a comprehensive report. All findings are framed as associational.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `numpy`, `statsmodels`, `scikit-learn`, `seaborn`, `pyyaml`, `pytest`  
**Storage**: Local CSV/Parquet files (`data/`), JSON outputs (`results/`)  
**Testing**: `pytest` (unit tests for data generation, contract tests for schemas)  
**Target Platform**: Linux (GitHub Actions free-tier: limited CPU resources, constrained RAM, no GPU)  
**Project Type**: CLI / Data Analysis Pipeline  
**Performance Goals**: Complete full pipeline (generation + modeling + bootstrap) in < 6 hours on CPU-only runner.  
**Constraints**: No GPU; synthetic data must be reproducible via pinned seeds; memory usage < 6GB; no causal language in reports.  
**Scale/Scope**: N=200 simulated participants (clusters), each with 3 repeated measures (600 total records).  
**Note on Dependencies**: The stack is **pure Python**. `rpy2` and `lme4` are explicitly excluded. Mixed-effects ordinal regression is approximated via fixed-effects `statsmodels.OrderedModel` (with known limitations on clustering), as no CPU-tractable mixed-effects ordinal library exists in pure Python.

## Constitution Check

*GATE: Must pass before Phase 0 research.*

| Principle | Compliance Status | Implementation Detail |
|-----------|-------------------|-----------------------|
| **I. Reproducibility** | **COMPLIANT** | Random seeds pinned in `code/`; synthetic data generator deterministic; `requirements.txt` pins versions. |
| **II. Verified Accuracy** | **COMPLIANT** | Citations in `research.md` restricted to verified URLs; no fabricated dataset links. |
| **III. Data Hygiene** | **COMPLIANT** | Raw data immutable; checksums recorded; synthetic data clearly labeled in `data/synthetic/`. |
| **IV. Single Source of Truth** | **COMPLIANT** | All stats in `paper/` derived from `results/` JSON/CSV; no hand-typed numbers. |
| **V. Versioning Discipline** | **COMPLIANT** | Content hashes tracked in state file; `updated_at` updated on artifact changes. |
| **VI. Ethical Treatment** | **COMPLIANT** | `data/ethics/` directory created with 'Ethics Waiver for Synthetic Data' placeholder. |
| **VII. Standardized Protocol** | **COMPLIANT** | Generator **reads** `data/protocols/protocol.yaml` for all simulation parameters (duration, intensity, effect sizes, ICC). This file is the SSoT for the simulation. |

## Project Structure

### Documentation (this feature)

```text
specs/001-sensory-deprivation-dreams/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── dataset.schema.yaml
│   ├── processed-data.schema.yaml
│   └── model-output.schema.yaml
└── tasks.md             # Phase 2 output (generated later)
```

### Source Code (repository root)

```text
projects/PROJ-146-the-effect-of-sensory-deprivation-on-dre/
├── data/
│   ├── raw/                  # Real data (if any)
│   ├── synthetic/            # Generated synthetic datasets (latent variables only)
│   ├── processed/            # Cleaned data with derived 'condition' (temporary)
│   ├── protocols/            # Machine-readable protocol definitions (protocol.yaml)
│   └── ethics/               # Ethics documentation (waiver for synthetic data)
├── code/
│   ├── __init__.py
│   ├── generate_data.py      # Synthetic data generator (reads protocols)
│   ├── ingest.py             # Data ingestion logic (derives condition from intensity)
│   ├── models.py             # Mixed-effects model fitting
│   ├── sensitivity.py        # Threshold sweep & bootstrap (generates multiple datasets internally)
│   ├── report.py             # Report generation
│   └── requirements.txt
├── results/
│   ├── models/               # Fitted model outputs (JSON/CSV)
│   └── reports/              # Final HTML/PDF reports
└── tests/
    ├── unit/
    └── contract/
```

**Structure Decision**: Single project structure chosen to minimize overhead for a data-analysis-only pipeline. All code resides in `code/` with clear separation of concerns. The `data/processed/` directory is used for temporary files where `condition` is derived from `deprivation_intensity` for specific analysis runs.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Synthetic Data Generator** | No real dataset exists with required metadata (sensory deprivation tags + bizarreness). | Using a real dataset without tags would require imputation, introducing bias and violating data hygiene. |
| **Mixed-Effects Models** | Repeated measures per participant require random intercepts to avoid pseudoreplication. | Fixed-effects only would inflate Type I error rates due to within-subject correlation. |
| **Ordinal Model Robustness** | Bizarreness is ordinal.; linear model assumes interval data. | Using only linear model risks invalid inference if interval assumption fails. (Note: Fixed-effects ordinal used as approximation due to `statsmodels` limitations; this is a known constraint on FR-008). |
| **Bootstrap Validation** | Small sample size (N=200) may yield unstable CIs; bootstrap provides empirical stability check. | Parametric CIs alone may not capture non-normality in effect estimates. |
| **Dynamic Thresholding** | To test "definition ambiguity" of sensory deprivation, the binary label must be derived from a continuous latent variable. | Storing a fixed binary `condition` would make the threshold sweep impossible without regenerating data for every threshold. |
| **ICC Misspecification** | To test robustness, the generator intentionally creates a mismatch between true and assumed ICC. | A perfect match would only validate arithmetic, not the model's robustness to structural mis-specification. |