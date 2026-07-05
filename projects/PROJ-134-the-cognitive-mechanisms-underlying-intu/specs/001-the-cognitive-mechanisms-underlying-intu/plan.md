# Implementation Plan: The Cognitive Mechanisms Underlying Intuitive Moral Judgments in Virtual Environments

**Branch**: `001-cognitive-mechanisms-moral-judgments` | **Date**: 2024-05-21 | **Spec**: [link]
**Input**: Feature specification from `/specs/001-cognitive-mechanisms-moral-judgments/spec.md`

## Summary

This feature implements a **Pipeline Validation** phase for the investigation of how visual salience of avatar expressions in VR modulates moral foundation activation. Due to the absence of verified real-world VR interaction logs and a verified "Moral Stories" dataset URL, the current implementation **simulates** the experimental data structure to verify the statistical engine (PyMC3), data ingestion, and reporting pipelines. 

**Critical Distinction**: This phase validates the *methodology and code*. It does **not** validate the scientific hypothesis regarding human cognition. Scientific claims regarding the effect of salience on judgment are explicitly deferred until **Phase 4: Data Acquisition** (real data ingestion). The synthetic data is generated with a known "ground truth" to ensure the Bayesian model can correctly recover parameters (validating the estimator), not to claim empirical discovery.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `numpy`, `pymc>=5.0.0`, `scikit-learn`, `pyyaml`, `requests`, `seaborn`, `statsmodels`  
**Storage**: Local CSV/Parquet files in `data/` (raw and derived); **YAML state file** for metadata (no SQLite).  
**Testing**: `pytest` (unit tests for data ingestion, model convergence checks, schema validation, parameter recovery).  
**Target Platform**: Linux (GitHub Actions Free Tier: 2 CPU, ~7GB RAM, No GPU).  
**Project Type**: Computational Research / Data Analysis Pipeline (Validation Phase).  
**Performance Goals**: Full pipeline (ingestion -> modeling -> reporting) must complete within 6 hours on CPU. Model convergence (R-hat < 1.05) must be achieved.  
**Constraints**: No CUDA/GPU usage. No 8-bit/4-bit quantization. Data subset to fit ~GB RAM.  
**Scale/Scope**: ~200 participants (simulated), ~50 moral vignettes.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. Current phase uses synthetic data with known ground truth for validation.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **I. Reproducibility**: Plan ensures `random_seed` is pinned in `code/`. External datasets (if any) are fetched from canonical HuggingFace URLs. `requirements.txt` will pin all versions. Synthetic data generation uses a fixed seed.
- **II. Verified Accuracy**: All dataset URLs in `research.md` are sourced exclusively from the "Verified datasets" block of the user message. The "Moral Stories" dataset is explicitly marked as **Simulated** (bypassing URL verification) with a clear warning in the report. No fabricated URLs are used for real data.
- **III. Data Hygiene**: Raw data ingestion preserves original files. Derived data (merged CSVs) will be written to new files with checksums recorded in `state/`. PII scan will be enforced (no participant names/emails in committed data).
- **IV. Single Source of Truth**: All figures and statistics in the final report will be generated programmatically from `data/` and `code/`. No hand-typed numbers. The `state/...yaml` file is the sole source for artifact hashes.
- **V. Versioning Discipline**: **Explicit Mechanism Added**: A dedicated `code/utils/hashing.py` script calculates SHA-256 checksums for all derived artifacts and updates the `state/...yaml` `artifact_hashes` map upon generation.
- **VI. VR Manipulation Fidelity**: The plan explicitly defines the "salience" variable as a mapping of blend-shape parameters (low/high) in the data model. This mapping is logged in `data/` to ensure the 'perceptual salience' variable is reproducible.
- **VII. Psychometric Instrument Integrity**: **Explicit Mechanism Added**: A validation step (US-6) compares the distribution of the synthetic MFQ data against published norms (Gervais et al., 2011) to ensure the simulation mimics real psychometric properties, even without real participants.

## Project Structure

### Documentation (this feature)

```text
specs/001-cognitive-mechanisms-moral-judgments/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── dataset.schema.yaml
│   └── model_output.schema.yaml
└── tasks.md             # Phase 2 output (NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
code/
├── __init__.py
├── config.py            # Paths, seeds, constants
├── data/
│   ├── __init__.py
│   ├── ingest.py        # US-1: Ingestion and merging (Simulated MFQ)
│   ├── preprocess.py    # US-1: Cleaning, alignment, salience mapping
│   └── simulation.py    # US-1: Generate synthetic VR logs with ground truth
├── models/
│   ├── __init__.py
│   ├── bayesian.py      # US-2: PyMC3 model definition
│   └── regression.py    # US-3: Mixed-effects regression
├── analysis/
│   ├── __init__.py
│   ├── model_comparison.py # US-2: AIC/WAIC, PPC
│   └── validation.py    # US-3: Sensitivity analysis, Bonferroni, Parameter Recovery
├── utils/
│   ├── hashing.py       # US-5: Checksum calculation and state update
│   └── norms.py         # US-6: Psychometric validation against Gervais et al.
├── reports/
│   └── generate_report.py # US-3: Final report generation (Pipeline Validation)
└── tests/
    ├── test_ingest.py
    ├── test_model.py
    └── test_schema.py

data/
├── raw/                 # Downloaded parquet files (checksummed)
├── processed/           # Merged CSVs, derived features
└── logs/                # Exclusion logs, VR mapping logs
```

**Structure Decision**: Single `code/` directory with modular sub-packages (`data`, `models`, `analysis`, `utils`) to separate concerns. `utils/hashing.py` and `utils/norms.py` added to satisfy Constitution Principles V and VII.

## User Stories & Phases

### User Story 1 - Data Ingestion, Experimental Construction, and Preprocessing Pipeline (Priority: P1)
**Status**: Partially Implemented (Simulation Only)
The system MUST ingest raw data from a **Synthetic MFQ Generator** (based on Gervais et al. norms) and a **Simulated Moral Stories** dataset, construct the experimental VR conditions by mapping text stories to VR scenes with controlled blend-shape parameters (low vs. high salience), and ingest **Simulated** VR interaction logs (response times, gaze tracking, in-VR judgment inputs) with a known ground truth.
*   **Gap**: Real VR logs and "Moral Stories" dataset are missing. The system simulates them with a `ground_truth_effect` parameter to validate the pipeline.
*   **Test**: The pipeline can be tested by running the ingestion and construction scripts against the synthetic data and verifying that the model recovers the `ground_truth_effect` within a credible interval.

### User Story 2 - Bayesian Model Execution and Comparison (Priority: P2)
**Status**: Implemented (Validation Mode)
The system MUST execute a Bayesian decision model on the **Simulated** data to estimate the effect of visual salience. The model treats foundation scores as covariates and salience as a fixed-effect predictor.
*   **Validation**: The model must recover the `ground_truth_effect` (defined in the simulation) to prove the estimator works.
*   **Comparison**: Compare against a baseline model using AIC/WAIC. The goal is to verify the model selection procedure works correctly when the truth is known.

### User Story 3 - Statistical Validation and Reporting (Priority: P3)
**Status**: Implemented (Validation Mode)
The system MUST perform hierarchical mixed-effects regression and apply Bonferroni correction.
*   **Reporting**: The report will explicitly state "Pipeline Validation: PASSED/FAILED" based on parameter recovery, not "Hypothesis Supported".

### User Story 4 - Real Data Integration (Priority: P4 - Deferred)
**Status**: Not Implemented (Future Phase)
The system MUST be capable of ingesting **Real** VR interaction logs and a verified "Moral Stories" dataset when available.
*   **Action**: This phase is a placeholder. The pipeline is designed to accept real data in the same schema.

### User Story 5 - Artifact Hashing & State Update (Priority: P1)
**Status**: Implemented
The system MUST calculate SHA-256 checksums for all derived data and update the `state/...yaml` file's `artifact_hashes` map to satisfy Constitution Principle V.

### User Story 6 - Psychometric Instrument Integrity Validation (Priority: P1)
**Status**: Implemented
The system MUST validate that the synthetic MFQ data distribution matches the published norms (Gervais et al.) to satisfy Constitution Principle VII.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Synthetic Data with Ground Truth | Required to validate the Bayesian pipeline in the absence of real data. | Running the pipeline on random noise would not validate the estimator's ability to recover effects. |
| Parameter Recovery Check | Required to distinguish "Pipeline Validation" from "Scientific Discovery". | Without this, the analysis is a tautology (testing data generated by the code). |
| Hashing & State Update Script | Required by Constitution Principle V (Versioning Discipline). | Manual updates are error-prone and violate the "Single Source of Truth" principle. |

## Success Criteria (Revised)

- **SC-001**: Model convergence rate is measured against the standard Bayesian inference benchmark (R-hat < 1.05).
- **SC-002**: **Pipeline Validation**: The model must recover the `ground_truth_effect` within the 95% credible interval. (Not "ΔAIC > 10" for scientific evidence yet).
- **SC-003**: Interaction significance is measured by the correct computation and reporting of the Bonferroni-corrected p-value (Pipeline Check).
- **SC-004**: Sensitivity analysis coverage is measured against the required threshold set {, 10, 20}.
- **SC-005**: **Artifact Integrity**: All derived files must have checksums recorded in `state/...yaml`.
- **SC-006**: **Psychometric Validity**: Synthetic MFQ distribution must match Gervais et al. (2011) norms within 1 standard deviation.

## Risk Assessment

- **Missing Real Data**: The primary risk is that the current phase cannot answer the scientific question. **Mitigation**: The report explicitly states "Pipeline Validation Only" and defers scientific claims to Phase 4.
- **Simulation Bias**: The synthetic data might not capture real-world complexity. **Mitigation**: Use multivariate normal distributions based on published norms to maximize realism.
- **Convergence Failure**: **Mitigation**: Sensitivity analysis and fallback to MLE.