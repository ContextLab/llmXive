# Implementation Plan: Investigating the Predictive Power of Machine Learning for Identifying Novel Phase-Change Materials

**Branch**: `001-phase-change-predictive-power` | **Date**: 2026-07-13 | **Spec**: `specs/001-phase-change-predictive-power/spec.md`

## Summary

This project investigates the predictive power of machine learning (ML) to identify novel phase-change materials (PCMs) by analyzing structural and compositional descriptors. The approach involves retrieving materials data from the Materials Project (MP) API, computing elemental and graph-based descriptors, training baseline (Random Forest, Gradient Boosting) and interpretable models (SHAP, PySR symbolic regression), and validating derived rules against an independent literature set. The implementation prioritizes CPU-first execution within GitHub Actions constraints (limited CPU, constrained RAM) and includes a GPU escape hatch via Kaggle for any CUDA-restricted operations, though the primary plan targets CPU-tractable methods.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pymatgen`, `scikit-learn`, `pysr`, `shap`, `pandas`, `pyyaml`, `requests`, `huggingface_hub`  
**Storage**: Local file system (CSV/Parquet/JSON) under `data/`  
**Testing**: `pytest`  
**Target Platform**: Linux (GitHub Actions free-tier runner)  
**Project Type**: Computational research pipeline  
**Performance Goals**: Complete data retrieval and feature engineering within 2 hours; model training within 2 hours; symbolic regression within 4 hours.  
**Constraints**: ≤7 GB RAM, ≤14 GB disk, no local GPU (unless offloaded to Kaggle).  
**Scale/Scope**: [deferred]–[deferred] compounds from MP; external validation set of a representative number of literature PCMs (or a random sample of materials).

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Principle I (Reproducibility (NON-NEGOTIABLE))**: All random seeds will be pinned in `code/`. External datasets (MP, NIST) will be fetched via programmatic APIs or verified URLs. `requirements.txt` will pin versions.
- **Principle II (Verified Accuracy)**: Citations in `research.md` and `data-model.md` will be verified by the Reference-Validator Agent against the primary source. The plan does not rely on a 'Verified datasets' block in the prompt for verification; the Agent performs this.
- **Principle III (Data Hygiene)**: Raw data will be stored in `data/raw/` with checksums. Derivations (features, models) will be written to new files in `data/processed/` and `data/results/`. No in-place modification.
- **Principle IV (Single Source of Truth)**: Every figure, statistic, or interpretation in the paper MUST trace back to exactly one row in this project's `data/` and one block in this project's `code/`. Derived numbers MUST NOT be hand-typed into the paper.
- **Principle V (Versioning Discipline)**: Artifacts will be content-hashed. The `state` file will be updated by the Advancement-Evaluator Agent on artifact changes, not by implementation scripts.
- **Principle VI (Numerical Stability)**: The feature extraction pipeline will include explicit checks for `nan`/`inf` in graph representations and elemental descriptors, logging and handling them per a documented protocol.
- **Principle VII (Independent Physical Validation)**: A separate set of known PCMs from literature (or a random sample of materials) will be used for validation, excluded from all training, validation, and test splits. The rules derived from symbolic regression will be tested against this set.

## Project Structure

### Documentation (this feature)

```text
specs/001-phase-change-predictive-power/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── dataset.schema.yaml
│   ├── model_output.schema.yaml
│   ├── validation_result.schema.yaml
│   └── target_decision.schema.yaml
└── tasks.md             # Phase 2 output (generated later)
```

### Source Code (repository root)

```text
projects/PROJ-229-investigating-the-predictive-power-of-ma/
├── data/
│   ├── raw/             # Raw downloads (MP API, NIST, Literature)
│   ├── processed/       # Feature-engineered datasets
│   ├── results/         # Model outputs, metrics, formulas
│   └── external/        # Literature PCM data (if separate)
├── code/
│   ├── data/            # Retrieval and preprocessing scripts
│   ├── models/          # Training, SHAP, PySR scripts
│   ├── utils/           # Feature extraction, graph building, validation
│   └── main.py          # Orchestration entry point
├── tests/
│   ├── unit/            # Unit tests for features, models
│   ├── integration/     # Integration tests for pipeline
│   └── contract/        # Schema validation tests
├── config.yaml          # Configuration for thresholds, seeds
├── requirements.txt     # Dependencies
└── README.md            # Project overview
```

**Structure Decision**: Single project structure chosen for simplicity and alignment with the computational research nature of the project. All code is modularized into `data`, `models`, and `utils` for clarity.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | The project scope is contained within CPU constraints and open datasets. | N/A |

## Phases and Tasks

### Phase 0: Setup
- **T001a**: Create data directories (`data/raw`, `data/processed`, `data/results`, `data/external`).
- **T001b**: Create code directories (`code/data`, `code/models`, `code/utils`).
- **T001c**: Create test directories (`tests/unit`, `tests/integration`, `tests/contract`).
- **T003**: Configure linting and formatting tools (create `pyproject.toml` with flake8 and black configs).

### Phase 0.5: Target Consistency Check & Literature Data Acquisition
- **T005a**: Fetch a sample of Materials Project data (e.g., first 1000 compounds) to calculate Pearson correlation between `melting_point` and `latent_heat` (if available). Write `data/results/target_decision.json` with the selected target variable (`latent_heat` or `melting_point`) and the correlation value.
- **T013**: Fetch literature PCM data from a verified source (e.g., Hugging Face dataset or DOI). If inaccessible, log a warning and proceed to use a pre-defined fallback set of PCMs.
- **T013a**: Map the literature data to the target variable using `data/results/target_decision.json`. Write `data/results/mapping_log.json`.
- **T013b**: If the target variable is `melting_point` (fallback), write `data/results/fallback_decision.json` to indicate the change in research scope. Do not mutate `target_decision.json`.

### Phase 1: Data Retrieval and Preprocessing
- **T011a**: Retrieve full Materials Project data for compounds with melting point and heat capacity data. Limit to [deferred] compounds.
- **T012**: Compute elemental and structural descriptors. Check for numerical stability (nan/inf) and handle them.

### Phase 2: Feature Engineering and Collinearity Check
- **T014**: Aggregate graph representations into scalar descriptors for PySR.
- **T015**: Perform collinearity check on predictors. Write `data/results/collinearity_report.json` with flagged dependencies and adjusted interpretation text.

### Phase 3: Model Training
- **T017**: Train baseline models (Random Forest, Gradient Boosting).
- **T018**: Train interpretable models (SHAP, PySR). If PySR fails, fallback to Lasso regression.
- **T019**: Generate `data/results/symbolic_formula.json` (or `data/results/lasso_formula.json` if PySR fails).

### Phase 4: Validation and Sensitivity Analysis
- **T023**: Validate derived rules against the literature set. Use `data/results/target_decision.json` to determine the target variable. Calculate Spearman correlation and ranking accuracy (if applicable).
- **T024**: Perform sensitivity analysis on feature importance thresholds. Read thresholds from `config.yaml` and target from `data/results/target_decision.json`. Write `data/results/sensitivity_analysis.json`.
- **T025**: Perform multicollinearity test (train model with and without `melting_point`). Write `data/results/multicollinearity_test.json`.

### Phase 5: Feasibility and Reporting
- **T026a**: Measure computational feasibility (time, memory). Write `data/results/feasibility_report.json`.
- **T026c**: Generate the final report. Read the 'Critical Methodological Note' from `plan.md` and inject it verbatim into the report. Ensure all statistics trace to specific data rows and code blocks.

## Reproducibility Requirements

- A `requirements.txt` (or `pyproject.toml`) at `projects/PROJ-229-investigating-the-predictive-power-of-ma/code/`
  pins every Python dependency.
- The Code-Execution Agent runs each task in an isolated virtualenv built
  from this requirements file; no global packages are assumed.
- Every notebook or script under `code/` is runnable end-to-end without
  manual intervention.

## Data Hygiene

- Every file under `data/` is checksummed in the project's
  `state/projects/PROJ-229-investigating-the-predictive-power-of-ma.yaml` `artifact_hashes` map.
- Raw data is preserved unchanged; derivations are written to new
  filenames.
- No commits are accepted that fail the Repository-Hygiene Agent's PII
  scan.

## Verified Accuracy Gate

The Reference-Validator Agent runs at three points:

1. On every artifact write that introduces or modifies citations.
2. Inside the Advancement-Evaluator before awarding any review point.
3. As a blocking gate on the `research_review` → `research_accepted`
   transition.

A reviewer's score MUST be set to 0.0 if the reviewed artifact has any
citation in `unreachable` or `mismatch` status.

## Versioning

This constitution carries its own semver. Initial version:
**1.0.0** — ratified 2026-07-13.

Amendments follow the parent llmXive constitution's amendment procedure
(open a PR; update the version line; record a Sync Impact Report).

## Governance

The Advancement-Evaluator Agent is the sole writer of this project's
`current_stage`. The principal agent for this project is
**flesh_out**.

Review-point thresholds for this project follow `web/about.html`. The
parser at `src/llmxive/config.py` is the single source these numbers
flow from.

**Project ID**: PROJ-229-investigating-the-predictive-power-of-ma | **Field**: materials science | **Ratified**: 2026-07-13