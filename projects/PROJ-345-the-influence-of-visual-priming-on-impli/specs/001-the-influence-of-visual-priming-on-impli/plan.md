# Implementation Plan: The Influence of Visual Priming on Implicit Attitudes Towards Ambiguous Social Stimuli

**Branch**: `001-visual-priming-implicit-attitudes` | **Date**: 2024-05-24 | **Spec**: `specs/001-visual-priming-implicit-attitudes/spec.md`
**Input**: Feature specification from `/specs/001-visual-priming-implicit-attitudes/spec.md`

## Summary

This project implements a statistical analysis pipeline to investigate the influence of visual priming on implicit attitudes using secondary IAT (Implicit Association Test) data. The system ingests public IAT datasets, links trial-level response times to stimulus metadata, derives prime valence and ambiguity scores using CPU-optimized models (if human-rated data is missing, per FR-001), and fits linear mixed-effects models to test for associations. The plan strictly adheres to the observational nature of the data, framing all findings as associational. It includes robust handling of missing data (halting if >10% of stimuli are missing), collinearity checks (VIF), and multiple-comparison corrections (FDR). The pipeline is designed to run on CPU-first infrastructure (GitHub Actions free tier) with an optional GPU fallback for heavy inference tasks, ensuring reproducibility and data hygiene per the project constitution.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `numpy`, `scikit-learn`, `statsmodels`, `pyyaml`, `reportlab`, `torch` (CPU backend), `transformers` (CPU-optimized models), `datasets` (HuggingFace).  
**Storage**: Local file system (`data/raw/`, `data/processed/`, `reports/`). No external database.  
**Testing**: `pytest` for unit tests on data ingestion and model fitting logic.  
**Target Platform**: Linux (GitHub Actions Runner / Kaggle Notebook).  
**Project Type**: Data Science Pipeline / Statistical Analysis.  
**Performance Goals**: Complete full pipeline on sampled dataset within 6 hours; model convergence within 3 optimizer attempts.  
**Constraints**: CPU-first execution; memory < 7GB; no PII in output; strict adherence to data availability (derivation allowed if human data missing, per FR-001).  
**Scale/Scope**: Single dataset ingestion (IAT/OSF); linear mixed-effects modeling on a large number of trials (sampled if necessary).

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Compliance Status | Implementation Detail |
|-----------|-------------------|-----------------------|
| **I. Reproducibility** | **PASS** | Random seeds pinned in `code/`. External datasets fetched from canonical HuggingFace URLs. `requirements.txt` pins all versions. |
| **II. Verified Accuracy** | **PASS** | All dataset URLs in `research.md` are from the verified block. Citations validated against primary sources. |
| **III. Data Hygiene** | **PASS** | `data/` files checksummed. Raw data immutable. Derivations in `data/processed/`. PII scan implemented (`code/main.py`) with specific types: email, phone, ssn, name. |
| **IV. Single Source of Truth** | **PASS** | All figures/stats trace to `data/processed/` and `code/`. No hand-typed numbers in reports. |
| **V. Versioning Discipline** | **PASS** | Content hashes recorded in state file. `updated_at` timestamp managed by agent. |
| **VI. Distinct Stimulus Set Integrity** | **PASS** | `data/primes/` and `data/targets/` directories enforced. Data separation logic implemented in `preprocess.py` before merging into `linked_trials.csv`. |

## Project Structure

### Documentation (this feature)

```text
specs/001-visual-priming-implicit-attitudes/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── dataset.schema.yaml
│   ├── linkage_status.schema.yaml
│   ├── output.schema.yaml
│   └── sensitivity_analysis.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
code/
├── main.py              # Entry point, CLI interface (--step ingest, preprocess, model, report)
├── ingest.py            # Data ingestion, metadata extraction
├── preprocess.py        # Valence/Ambiguity derivation, linkage, cleaning, stimulus separation
├── model.py             # LME fitting, diagnostics (VIF, convergence, robust SE)
├── report.py            # Visualization, PDF generation, sensitivity analysis embedding
├── config.py            # Configuration, thresholds (LINKAGE_THRESHOLD=95.0)
└── requirements.txt     # Dependencies

data/
├── raw/                 # Downloaded raw datasets
├── processed/           # Cleaned, linked, derived data
├── primes/              # Prime stimuli metadata (separate)
└── targets/             # Target stimuli metadata (separate)

reports/
├── final_report.pdf     # Final output (includes sensitivity analysis)
├── sensitivity_analysis.csv
└── pii_scan.json

state/
├── model_convergence_metrics.json
├── vif_flag.json
└── linkage_status.json

tests/
├── unit/                # Unit tests
├── integration/         # Integration tests
└── contract/            # Schema validation tests
```

**Structure Decision**: Single project structure selected. The pipeline is linear (Ingest -> Preprocess -> Model -> Report) and does not require a microservices or web application architecture. All processing is local to the runner.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Linear Mixed-Effects (LME)** | Required to account for repeated measures (trials within participants) and random effects (participant ID). | Standard linear regression ignores clustering, inflating Type I error rates. |
| **FDR Correction** | Required by FR-004 for multiple hypothesis testing (interactions, subgroups). | Bonferroni is too conservative for exploratory subgroup analysis; FDR balances power and error control. |
| **VIF Check** | Required by FR-005 to detect collinearity between derived valence and ambiguity. | Omitting VIF could lead to spurious claims of independent effects when predictors are correlated. |
| **CPU-First + Optional GPU** | Required by compute constraints (7GB RAM, no local GPU) while maintaining methodological rigor. | Pure CPU for large transformers is infeasible; pure GPU is not available on free CI. The hybrid approach ensures feasibility without fabrication. |
| **Stimulus Separation** | Required by Constitution Principle VI. | Merging primes and targets prior to modeling confounds the causal relationship. |

## Data Availability & Feasibility

- **Primary Dataset**: `davanstrien/ia_test_embeddings` (Verified: contains `response_time`, `participant_id`, `stimulus_id`).
- **Demographics Extraction Logic**: The pipeline explicitly maps the following columns from the primary dataset to model covariates:
  - `age` -> Fixed Effect: Age (continuous)
  - `gender` -> Fixed Effect: Gender (categorical, one-hot encoded)
  - `education` -> Fixed Effect: Education (ordinal/categorical)
  - **Logic**: If any of these columns are present in the raw dataset, they are included as fixed effects in the LME model. If a column is missing, the corresponding term is **omitted** from the model equation, and a `Demographics Missing: <column_name>` flag is written to `state/demographics_status.json`. No random slopes for demographics are computed if the fixed effect is omitted.
- **Derivation**: Ambiguity and Valence are derived via CPU-optimized models if human-rated data is missing (per FR-001).
- **Streaming**: `streaming=True` used for large datasets to stay within 7GB RAM.
- **GPU Fallback**: Optional for heavy inference (e.g., large transformer inference). Not required for standard pipeline.

## Task Ordering (Corrected for Logic & Dependencies)

The following order resolves circular dependencies and ensures data is available before consumption:

1.  **T001**: Initialize Environment & Config.
2.  **T002**: Ingest Raw Data (Download `davanstrien/ia_test_embeddings`).
3.  **T003**: Extract Stimulus Metadata (Separate Primes/Targets).
4.  **T004**: Linkage Check (Calculate `linked_metadata_percentage`).
    - *Output*: `data/processed/ingest_metrics.json` (Schema defined in contracts).
    - *Gate*: If < 95% (configurable), `HALT` or `WARN` (T005).
5.  **T005**: Handle Missing Linkage (Warn or Halt based on T004).
6.  **T006**: Load Human-Rated Ambiguity (If exists in source).
7.  **T007**: Derive Ambiguity (If T006 fails/missing).
    - *Dependency*: T006 (Check result first).
8.  **T008**: Merge Valence & Ambiguity Metadata.
9.  **T009**: Demographics Extraction & Flagging.
    - *Logic*: Check for `age`, `gender`, `education` columns. Write status to `state/demographics_status.json`.
10. **T010**: VIF Pre-Check (Predictor Correlation).
    - *Dependency*: T008 (Metadata merged).
11. **T011**: Fit LME Model.
    - *Logic*: If `Demographics Missing`, omit covariate term. If VIF > 5.0, flag but fit (T012).
    - *Dependency*: T009, T010.
12. **T012**: Post-Fit Diagnostics (Convergence, VIF Flagging).
    - *Dependency*: T011.
13. **T013**: Sensitivity Analysis (Sweep alpha).
    - *Dependency*: T011.
    - *Output*: `reports/sensitivity_analysis.csv`.
14. **T014**: Generate Interaction Plots.
15. **T015**: Embed Sensitivity Summary into PDF (T036b).
    - *Dependency*: T013, T014.
    - *Logic*: Parse `sensitivity_analysis.csv`, generate summary table, insert into PDF.
16. **T016**: Generate Final Report (T036a).
    - *Dependency*: T015.
    - *Output*: `reports/final_report.pdf`.

## Critical Design Changes & Resolutions

- **Ambiguity Derivation**: FR-001 mandates derivation if human data is missing. The plan explicitly implements T007 (Derive Ambiguity) as a fallback. The "valence only" fallback is **only** used if *both* human data and derivation fail (e.g., no image text for VAD).
- **Demographics Handling**: Resolved logical conflict. If demographics are missing, the model equation is **explicitly reduced** (covariate term removed) rather than attempting to fit a model with missing predictors. This is documented in `research.md` and enforced in `model.py`.
- **Sensitivity Analysis Integration**: Added T015 to explicitly parse `sensitivity_analysis.csv` and embed it into the PDF, ensuring SC-003 is met.
- **Linkage Threshold**: The threshold is defined as `LINKAGE_THRESHOLD` (default 95.0) in `config.py`, mapped to the "vast majority" requirement in SC-001.

## Report Requirements (Updated)

The final PDF (`reports/final_report.pdf`) MUST contain:
1.  **Interaction Plot**: Response time differences across prime valence.
2.  **Coefficient Table**: Fixed effects, SE, p-values (FDR corrected).
3.  **Sensitivity Analysis Summary**: A table or figure derived from `sensitivity_analysis.csv` showing significance rates across varying alpha levels.
4.  **Data Hygiene Report**: Linkage status, VIF flags, and demographics status.

## Compute Feasibility & GPU Strategy

- **CPU-First**: All data ingestion, preprocessing, and LME fitting (via `statsmodels` or `lme4` equivalent in Python) will run on CPU.
- **GPU Fallback**: Optional for heavy inference (e.g., large transformer inference). If the valence derivation step requires a large transformer model that exceeds CPU time limits:
  - The pipeline will attempt a scaled-down inference (e.g., -bit quantization, smaller batch size) on a free Kaggle GPU.
  - The execution agent will auto-detect CUDA requirements and offload the specific inference task.
  - **No Fabrication**: If the model cannot run on either CPU (scaled) or GPU (scaled), the pipeline halts; no synthetic data is generated.