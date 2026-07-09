# Implementation Plan: The Role of Temporal Discounting in Procrastination on Cognitive Tasks

**Branch**: `001-temporal-discounting-procrastination` | **Date**: 2026-07-10 | **Spec**: `spec.md`
**Input**: Feature specification from `specs/001-temporal-discounting-procrastination/spec.md`

## Summary

This project implements a **Methodological Validation Pipeline** to test the ability to detect a pre-defined moderation effect between temporal discounting rates and procrastination, moderated by working memory (WM) load. The technical approach involves ingesting three distinct data sources (simulated or partial real-world proxies), fitting a hyperbolic model to derive individual discount rates ($k$), and performing a moderated OLS regression with bootstrapping. 

**Critical Scope Note**: Due to the absence of a verified real-world dataset containing all three constructs simultaneously, this study uses a **Synthetic Data Generation (SDG)** strategy based on validated literature parameters. The primary goal is **not** to empirically validate the existence of the phenomenon in the real world, but to:
1.  Validate the analysis pipeline's ability to recover a known "ground truth" interaction effect.
2.  Demonstrate the statistical robustness of the method under CPU constraints.
3.  Estimate the magnitude of the interaction effect with confidence intervals, acknowledging that the study is underpowered to detect small effects ($f^2 < 0.02$) with high significance.

The pipeline is designed to run entirely on CPU within a time-efficient window and a constrained RAM limit.

## Technical Context

**Language/Version**: Python  
**Primary Dependencies**: `pandas`, `numpy`, `scipy`, `statsmodels`, `scikit-learn`  
**Storage**: Local CSV/Parquet files (raw and derived), in-memory DataFrames  
**Testing**: `pytest` (unit tests for data harmonization, regression diagnostics, DGP recovery)  
**Target Platform**: Linux (GitHub Actions Free Tier: CPU, 7GB RAM)  
**Project Type**: Research pipeline / CLI  
**Performance Goals**: Complete full pipeline (ingestion → regression → bootstrap) in ≤6 hours  
**Constraints**: No GPU usage; no large model training; strict memory footprint (<7GB); strict reproducibility (random seeds).  
**Scale/Scope**: Synthetic dataset $N=500$ (optimized for CPU); pipeline designed to accept real data if available.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **I. Reproducibility**: **PASS**. The plan mandates `random_state` pinning in all stochastic steps (bootstrapping, DGP generation) and requires a `requirements.txt` with pinned versions. Data ingestion will use canonical sources or the defined DGP.
- **II. Verified Accuracy**: **CONDITIONAL PASS**. 
    - *Caveat*: The plan acknowledges that **NO verified real-world dataset** exists for the specific combination of variables (Discounting, Procrastination, n-back) in the provided list.
    - *Resolution*: Verified Accuracy is satisfied for the **Data Generating Process (DGP)** parameters, which are derived from cited meta-analyses and seminal papers (see `research.md` Section 2.2). The synthetic data is not a claim of empirical existence but a controlled environment for pipeline validation.
- **III. Data Hygiene**: **PASS**. The plan requires raw data to be stored unchanged in `data/raw/` and checksummed. All transformations (hyperbolic fitting, log transforms) will write to `data/processed/` with derivation logs. PII will be stripped during harmonization.
- **IV. Single Source of Truth**: **PASS**. The pipeline outputs a final analysis DataFrame and a JSON report of statistics. The paper will be generated programmatically from these outputs, ensuring no hand-typed numbers.
- **V. Versioning Discipline**: **PASS**. The implementation will generate content hashes for all data artifacts and update the `state` YAML file upon successful completion of each phase.
- **VI. Psychometric Validity and Construct Independence**: **PASS**. The plan explicitly separates the three data sources (Discounting, Procrastination, WM) in the DGP to ensure predictors and outcomes are derived from distinct paradigms, preventing mechanical construction of the relationship.
- **VII. Theoretical Symmetry in Null Result Reporting**: **PASS**. The analysis script will be designed to output effect sizes and p-values regardless of significance, and the reporting template will treat null results as valid scientific findings.

## Project Structure

### Documentation (this feature)

```text
specs/001-temporal-discounting-procrastination/
├── plan.md              # This file
├── research.md          # Phase 0 output (Updated with DGP details)
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── dataset.schema.yaml
│   └── output.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-196-the-role-of-temporal-discounting-in-proc/
├── data/
│   ├── raw/             # Downloaded raw files (CSV/ARFF) or DGP seed files
│   └── processed/       # Harmonized datasets, derived variables
├── code/
│   ├── __init__.py
│   ├── ingestion.py     # Data loading, harmonization, and DGP generation
│   ├── modeling.py      # Hyperbolic fitting and OLS regression
│   ├── robustness.py    # Bootstrapping and sensitivity analysis
│   └── main.py          # Orchestration script
├── tests/
│   ├── test_ingestion.py
│   ├── test_modeling.py
│   └── test_robustness.py
├── requirements.txt
└── README.md
```

**Structure Decision**: A single-project structure (Option 1) is selected. The project is a linear research pipeline (Ingest → Model → Validate) rather than a service or web app. This minimizes overhead and aligns with the CPU-only, batch-processing nature of the work.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | The project scope is well-bounded within standard statistical methods (OLS, Bootstrapping) and does not require complex architectural patterns. | Direct implementation is sufficient. |

## Phase Plan

### Phase 0: Research & Data Strategy (DGP Definition)
- **Goal**: Define the Data Generating Process (DGP) parameters based on cited literature (e.g., mean $k$, Cronbach's $\alpha$, interaction coefficient) and confirm the absence of verified real-world datasets.
- **Deliverable**: `research.md` containing the DGP specification, parameter sources, and a "Partial Proxy Strategy" for testing ingestion on real data subsets.
- **Constraint Check**: Ensure no dataset URL is fabricated. Explicitly state that the study is a **Methodological Validation** using synthetic data, not an empirical test of the hypothesis.

### Phase 1: Data Model & Contracts
- **Goal**: Define the schema for the unified dataset and the analysis output, ensuring it supports the DGP validation (e.g., `dgp_ground_truth` fields) and the synthetic data strategy.
- **Deliverable**: `data-model.md`, `quickstart.md`, and `contracts/*.schema.yaml`.
- **Constraint Check**: Ensure schemas cover all FR-001 to FR-010 requirements and explicitly support the `fit_status` and `dgp_ground_truth` fields required for pipeline validation.

### Phase 2: Implementation (Code Generation)
- **Goal**: Generate the Python scripts for ingestion (including DGP generator), modeling, and robustness.
- **Deliverable**: `code/ingestion.py`, `code/modeling.py`, `code/robustness.py`, `code/main.py`.
- **Constraint Check**: Ensure `random_state` is set. Ensure no GPU calls. Ensure runtime < 6h.

### Phase 3: Testing & Validation
- **Goal**: Execute the pipeline and verify that it recovers the DGP-specified interaction effect within the calculated confidence intervals.
- **Deliverable**: Pass/Fail report, checksums, and final `state` update.
- **Success Criteria**: The pipeline successfully estimates the interaction effect with a confidence interval that contains the DGP ground truth (if the effect is non-zero).