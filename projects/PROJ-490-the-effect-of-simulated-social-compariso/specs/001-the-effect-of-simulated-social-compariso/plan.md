# Implementation Plan: The Effect of Simulated Social Comparison on Self-Esteem in Virtual Reality

**Branch**: `001-simulated-social-comparison-self-esteem` | **Date**: 2024-01-15 | **Spec**: `specs/001-simulated-social-comparison-self-esteem/spec.md`
**Input**: Feature specification from `/specs/001-simulated-social-comparison-self-esteem/spec.md`

## Summary

This project implements a statistical analysis pipeline to investigate the effect of simulated social comparison on self-esteem in virtual reality (VR). The primary requirement is to locate a real-world dataset containing the Rosenberg Self-Esteem Scale (RSES), Iowa-Netherlands Comparison Orientation Measure (INCOM), and longitudinal pre/post self-esteem data. If no such dataset exists (as indicated by the verified dataset search), the system MUST fall back to generating a synthetic dataset with known ground-truth parameters (interaction β = 0.2) to validate the pipeline's ability to recover effects. The technical approach involves data ingestion, multiple imputation (MICE) for missing values (assuming MAR), linear regression modeling (ANCOVA approach to avoid mathematical coupling) with interaction terms, and rigorous assumption validation (normality, homoscedasticity, collinearity) followed by bootstrap resampling for stability.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `numpy`, `scikit-learn`, `statsmodels`, `miceforest` (or `sklearn.impute.IterativeImputer` as CPU-safe alternative), `scipy`, `pyyaml`, `pytest`, `matplotlib`  
**Storage**: Local file system (`data/`, `code/`); CSV/Parquet/JSON formats  
**Testing**: `pytest` with contract tests explicitly targeting `contracts/dataset.schema.yaml`, `contracts/output.schema.yaml`, and `contracts/results.schema.yaml`  
**Target Platform**: Linux (GitHub Actions free-tier runner)  
**Project Type**: computational-research-pipeline  
**Performance Goals**: Complete end-to-end analysis (including A sufficient number of bootstrap iterations) within ≤6 hours on 2 CPU cores, ~7 GB RAM.  
**Constraints**: NO GPU/CUDA; NO heavy deep learning; synthetic data only if real data lacks required variables (RSES, INCOM, pre/post); strict framing of results as "Pipeline Validation" for synthetic data.  
**Scale/Scope**: N ≥ 100 participants; single ANCOVA model; 1,000 bootstrap iterations.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Implementation Strategy |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | All random seeds pinned in `code/`. Dependencies pinned in `requirements.txt`. External datasets fetched from canonical HuggingFace URLs (or synthetic generator with fixed seed). |
| **II. Verified Accuracy** | **PASS** | **Implementation**: The `Reference-Validator` agent will be invoked in the CI pipeline to verify all external citations (dataset URLs, validation literature) before any review points are awarded. No citations will be included in the final report unless verified. |
| **III. Data Hygiene** | **PASS** | Raw data (or synthetic seed) checksummed in `state/`. Transformations (imputation, change score calc) produce new files. No PII in `data/`. |
| **IV. Single Source of Truth** | **PASS** | All figures/stats in `paper/` will trace to `data/` derived files. No hand-typed numbers. |
| **V. Versioning Discipline** | **PASS** | Artifact hashes tracked in `state/`. `updated_at` timestamps managed by Advancement-Evaluator. **Specific**: The `docs/analysis_plan.md` file will be checksummed and its hash recorded in `state/` to ensure version control linkage. |
| **VI. Ethical Human Subjects** | **PASS** | **Hard Gate**: The real-data path is **blocked** unless the system verifies the presence of IRB approval documentation and informed consent forms in the dataset source metadata. If such documentation is missing, the system MUST immediately trigger synthetic data generation (FR-011) and label results "Pipeline Validation Only". |
| **VII. Statistical Analysis Transparency** | **PASS** | `analysis_plan.md` (derived from this `plan.md`) will be version-controlled and hash-tracked. Model specs and diagnostics exported as CSV/JSON. |

## Project Structure

### Documentation (this feature)

```text
specs/001-simulated-social-comparison-self-esteem/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── dataset.schema.yaml
│   ├── output.schema.yaml
│   └── results.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-490-the-effect-of-simulated-social-compariso/
├── code/
│   ├── __init__.py
│   ├── main.py                # Entry point
│   ├── data/
│   │   ├── download.py        # Dataset fetching / synthetic generation
│   │   ├── preprocess.py      # MICE, ANCOVA covariate prep, missingness checks
│   │   └── config.py          # Seed management
│   ├── analysis/
│   │   ├── regression.py      # Model fitting (ANCOVA), assumption checks (visual + stat)
│   │   ├── bootstrap.py       # 1,000 iterations stability
│   │   └── sensitivity.py     # Threshold sweeps, parameter recovery, MNAR sensitivity
│   └── utils/
│       ├── logger.py
│       └── validators.py      # Schema validation (pytest targets)
├── data/
│   ├── raw/                   # Downloaded or synthetic raw data
│   └── processed/             # Cleaned, imputed data
├── tests/
│   ├── contract/              # Schema validation tests for dataset.schema.yaml, output.schema.yaml, results.schema.yaml
│   └── unit/                  # Logic tests
├── docs/
│   └── analysis_plan.md       # Pre-registration artifact (hash-tracked in state/)
└── requirements.txt
```

**Structure Decision**: Single project structure selected. The `code/` directory is split into `data`, `analysis`, and `utils` to enforce separation of concerns (ingestion vs. modeling vs. validation) and ensure the pipeline can be run end-to-end without manual intervention.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **Synthetic Data Generator** | Required by FR-011/US-1 as a fallback if no real dataset contains RSES+INCOM+Pre/Post. | Simple mock data lacks ground-truth parameters for parameter recovery validation (FR-011, SC-005). |
| **MICE Imputation** | Required by FR-002 for missingness < 20%. | Mean/median imputation introduces bias and violates the statistical rigor requirement for correlation structures. |
| **Bootstrap (1,000 iters)** | Required by FR-005/SC-004 for stability. | Single run lacks confidence in effect stability; analytical standard errors are insufficient for non-normal distributions. |
| **ANCOVA Model** | Required to avoid mathematical coupling (regressing change on baseline). | Change-score regression is statistically invalid for this hypothesis; ANCOVA is the standard correction. |
| **Visual Diagnostics** | Required for robust assumption checking (Shapiro/Breusch-Pagan have low power). | Sole reliance on p-values is methodologically weak for small samples; visual checks are mandatory. |