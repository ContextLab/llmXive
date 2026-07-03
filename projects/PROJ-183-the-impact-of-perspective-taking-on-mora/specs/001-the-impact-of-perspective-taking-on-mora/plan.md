# Implementation Plan: The Impact of Perspective-Taking on Moral Outrage in Online Discourse

**Branch**: `001-perspective-taking-moral-outrage` | **Date**: 2024-05-21 | **Spec**: `specs/001-perspective-taking-moral-outrage/spec.md`

## Summary

This project implements a computational pipeline to simulate and analyze a psychological experiment investigating whether perspective-taking prompts reduce moral outrage in online discourse. The system ingests the "Against the Others!" dataset, curates high-outrage stimuli, simulates participant responses using empirically grounded noise models, and performs statistical analysis using Linear Mixed-Effects Models (LMM) to account for stimulus nesting. The implementation is strictly CPU-bound to ensure reproducibility on GitHub Actions free-tier runners.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: pandas, scipy, statsmodels, numpy, requests, pyyaml  
**Storage**: Local CSV/JSON files (`data/`), no external database  
**Testing**: pytest (unit tests for data ingestion, randomization, and statistical logic)  
**Target Platform**: Linux (GitHub Actions Runner)  
**Project Type**: Computational Research Pipeline / CLI  
**Performance Goals**: Entire pipeline (data load, simulation, analysis) < 1 hour on 2 CPU / 7GB RAM  
**Constraints**: No GPU, no external API calls during CI (datasets must be local or cached), strict random seed pinning for reproducibility.  
**Scale/Scope**: ~40 stimuli, ~200 simulated participants, <10MB data footprint.

> **Dataset Note**: The "Against the Others!" dataset is the primary source. **CRITICAL**: The pipeline is currently BLOCKED until a verified URL is provided in `config.py`. If the URL is unreachable or the dataset lacks required "high-outrage" + "topic" metadata, the system must halt with a clear error (FR-001, FR-002).

## Constitution Check

*GATE: Must pass before Phase 0 research.*

| Principle | Status | Verification / Action |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | Plan mandates `random_seed` pinning in `code/`, deterministic data loading, and CI execution. |
| **II. Verified Accuracy** | **BLOCKED** | **Action Required**: The plan relies on a dataset URL that must be provided in `config.py`. The pipeline halts if the URL is unreachable or the dataset lacks required fields. Status remains BLOCKED until a verified URL is entered. |
| **III. Data Hygiene** | **PASS** | Plan enforces checksums for raw data, no in-place modification, and distinct files for derived data. |
| **IV. Single Source of Truth** | **PASS** | All statistics in the final report will be generated programmatically from `data/` via `code/`. |
| **V. Versioning Discipline** | **PASS** | Artifacts will be hashed; `state/` files updated on change. |
| **VI. Participant Ethics** | **PASS** | Synthetic data only for simulation; human data phase (US-4) requires explicit consent logic (to be implemented in `code/`). |
| **VII. Measurement Integrity** | **PASS** | The 7-item Moral Outrage Scale scoring algorithm will be version-controlled and linked to raw data. |

## Project Structure

### Source Code (repository root)

```text
projects/PROJ-183-the-impact-of-perspective-taking-on-mora/
├── code/
│   ├── __init__.py
│   ├── config.py                 # Random seeds, paths, constants
│   ├── data/
│   │   ├── __init__.py
│   │   ├── ingest.py             # FR-001, FR-002: Download & filter dataset
│   │   ├── stimuli.py            # FR-003: Generate instruction variants
│   │   └── simulation.py         # FR-004, FR-005: Assign & score synthetic participants
│   ├── analysis/
│   │   ├── __init__.py
│   │   ├── stats.py              # FR-006, FR-007: LMM, Mann-Whitney U, power analysis
│   │   └── pipeline.py           # Orchestration: Load -> Simulate -> Analyze
│   └── main.py                   # Entry point
├── data/
│   ├── raw/                      # Downloaded datasets (checksummed)
│   ├── processed/                # Curated stimuli, simulated responses
│   └── human/                    # Placeholder for human data (US-4)
├── tests/
│   ├── test_ingest.py
│   ├── test_simulation.py
│   └── test_stats.py
├── contracts/
│   ├── stimulus.schema.yaml
│   └── response.schema.yaml
├── requirements.txt
└── README.md
```

**Structure Decision**: Single-project structure with modular `code/` sub-packages. This minimizes overhead and aligns with the "CLI/Research Pipeline" type. All data is local to ensure CI reproducibility.

## Phase Breakdown & Requirement Mapping

### Phase 0: Data Ingestion & Curation (FR-001, FR-002, US-1)
- **Goal**: Download "Against the Others!" dataset, filter for high-outrage posts on target topics, and verify count (n=40).
- **Steps**:
  1. Implement `code/data/ingest.py` to fetch data from the verified source.
  2. **Schema Verification**: Explicitly check that the dataset contains fields `outrage_label` and `topic` with values `high`, `climate`, and `immigration`. If missing, raise `DataInsufficientError` (Edge Case 1).
  3. Filter logic: `outrage_label == "high"` AND `topic in ["climate", "immigration"]`.
  4. Random selection: Sample a representative set of posts per topic.
  5. **Validation**: Assert `len(stimuli) == 40`. If not, raise `DataInsufficientError`.
  6. **FR-001/002 Mapping**: Direct implementation of ingestion, schema verification, and filtering logic.

### Phase 1: Stimulus Generation (FR-003, US-1)
- **Goal**: Generate paired instructions (Perspective-Taking vs. Control) for each stimulus.
- **Steps**:
  1. Implement `code/data/stimuli.py`.
  2. Define static prompt templates for "Perspective-Taking" and "Control Summarization".
  3. Attach both variants to each post ID in the JSON structure.
  4. **FR-003 Mapping**: Generates the two distinct instruction strings per post.

### Phase 2: Simulation Pipeline (FR-004, FR-005, US-2)
- **Goal**: Simulate 200 participants, assign conditions, and generate synthetic outrage scores using an empirically grounded noise model.
- **Steps**:
  1. Implement `code/data/simulation.py`.
  2. **Generative Model**: Generate data under two scenarios:
     - **H0 (Null)**: No effect of condition on outrage (validate Type I error).
     - **H1 (Alternative)**: Effect size d=0.4 (validate Power).
     - Noise parameters derived from pilot literature (variance, skew).
  3. Random assignment: Split 200 IDs into two groups (n=100 each, ±5% tolerance).
  4. Synthetic scoring: Generate Likert scores based on the generative model.
  5. **Attention Checks**: Inject 5 embedded checks per participant; store as a list of booleans. Flag `attention_checks_passed` if >2 missed (FR-008).
  6. **FR-004/005/008/009 Mapping**: Handles assignment, scoring, attention checks, and separation of synthetic data streams.

### Phase 3: Statistical Analysis (FR-006, FR-007, US-3)
- **Goal**: Compute LMM, effect size, and robustness check.
- **Steps**:
  1. Implement `code/analysis/stats.py`.
  2. **Primary Analysis (FR-006)**: Linear Mixed-Effects Model (LMM) with:
     - Fixed Effects: `Condition`, `Topic`, `Condition:Topic` interaction.
     - Random Effects: `(1 | Stimulus)`, `(1 | Participant)`.
     - Output: Fixed effect coefficients, p-values, 95% CI.
  3. **Sensitivity Analysis (FR-007)**: Mann-Whitney U test (non-parametric) as a primary check for ordinal data robustness.
  4. **FR-010**: Formal power analysis (using `statsmodels.stats.power`) to determine required sample size for human study.
  5. **SC-001/002/003 Mapping**: Outputs metrics against null hypothesis, effect size target, and robustness criteria.

### Phase 4: Human Experiment Interface (FR-011, US-4)
- **Goal**: Define the data schema and logic for human data collection (not the collection itself, but the interface).
- **Steps**:
  1. **Schema Definition**: Human data MUST conform to `contracts/response.schema.yaml` (identical to simulated data schema).
  2. Implement randomization logic for human assignment (FR-011).
  3. **FR-011/US-4 Mapping**: Ensures the pipeline can accept human data with the same structure and randomization logic.

## Compute Feasibility & Risk Mitigation

- **Risk**: Dataset unavailability.
  - **Mitigation**: `research.md` identifies the specific "Against the Others!" source. If the URL is unreachable or data lacks required fields, the pipeline halts with a clear error message, preventing silent failure.
- **Risk**: CPU/Time limits.
  - **Mitigation**: The dataset is small (text only). LMM and statistical tests are O(n). The entire pipeline is designed to run in <10 minutes on a standard CPU. No heavy ML models are used.
- **Risk**: Statistical Assumptions.
  - **Mitigation**: The plan explicitly includes the Mann-Whitney U test (FR-007) as a primary sensitivity analysis if normality/variance assumptions are violated (Edge Case 3). The LMM assumes interval scaling for the multi-point scale, which is standard in psychometrics, but this assumption is explicitly noted.