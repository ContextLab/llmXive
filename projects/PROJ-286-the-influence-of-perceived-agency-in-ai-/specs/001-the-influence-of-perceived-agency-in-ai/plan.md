# Implementation Plan: The Influence of Perceived Agency in AI Interactions on Trust

**Branch**: `001-perceived-agency-trust` | **Date**: 2026-07-14 | **Spec**: `spec.md`
**Input**: Feature specification from `spec.md`

## Summary

This project implements a computational psychology experiment to test whether increasing a user's perception of agency (even when illusory) increases trust in AI recommendations. The system consists of two distinct components: (1) an experimental task interface (simulated for this implementation) that randomizes participants into High Agency, Low Agency, or Control conditions and captures behavioral adherence and psychometric trust scores (Lee & See, 2004); and (2) a reproducible statistical analysis pipeline that performs planned directional contrasts, pairwise comparisons with family-wise error correction (Tukey), and sensitivity analyses on exclusion thresholds. The implementation adheres to the project constitution by enforcing reproducibility via pinned seeds, verifying all citations against primary sources, and ensuring data hygiene via checksums.

**Critical Distinction**: This implementation uses **simulated data** solely to validate the *pipeline logic* (code correctness, statistical formulas). It **cannot** validate the causal hypothesis regarding human psychology. The statistical pipeline is designed to process **real human data** (e.g., from Prolific/MTurk) when available, which is required for hypothesis testing. The plan explicitly separates "Pipeline Validation" (Phase 1, simulated) from "Hypothesis Testing" (future phase, real data).

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `numpy`, `scipy`, `statsmodels`, `matplotlib`, `seaborn`, `pyyaml`, `pydantic`, `requests`  
**Storage**: Local CSV files (`data/raw/`, `data/processed/`)  
**Testing**: `pytest` (unit tests for statistical logic, integration tests for pipeline execution)  
**Target Platform**: Linux (GitHub Actions free-tier runner: 2 CPU, ~7 GB RAM)  
**Project Type**: Computational Experiment / Data Analysis Pipeline  
**Performance Goals**: Full pipeline execution (simulated data generation + analysis) < 15 minutes.  
**Constraints**: Must run entirely on CPU; no GPU required. Memory usage < 4 GB.  
**Scale/Scope**: Simulated dataset generation (N=200-500 participants) for pipeline validation; analysis code designed to handle real data up to N=10,000.

## Constitution Check

*Gates determined based on constitution file*

1.  **Principle I (Reproducibility)**: **SATISFIED**. The plan mandates `random.seed` pinning in `code/` and deterministic data loading. The pipeline is designed to run end-to-end on a fresh runner.
2.  **Principle II (Verified Accuracy)**: **SATISFIED**. The plan includes a specific step (Phase 0) to verify the Lee & See (Year) citation (DOI/Title) against the **Crossref API** before hardcoding survey items. The "hardcoded list" concern is addressed by moving the *verification* of the list into the pipeline setup, ensuring the code uses the *verified* items, not an unverified guess. The script outputs a `citation_log.json` with verified metadata.
3.  **Principle III (Data Hygiene)**: **SATISFIED**. All raw data (simulated or real) will be checksummed before processing. Derivations will produce new files. PII will be excluded from the schema.
4.  **Principle IV (Single Source of Truth)**: **SATISFIED**. Figures and statistics in the final report will be generated programmatically from the `data/` artifacts, not hand-typed.
5.  **Principle V (Versioning Discipline)**: **SATISFIED**. The plan includes content hashing for all artifacts in `data/` and `code/`.
6.  **Principle VI (Experimental Manipulation Fidelity)**: **SATISFIED**. The High/Low agency conditions are implemented as distinct UI logic (slider availability vs. static display) in the simulation, ensuring the predictor is a controlled interface feature.
7.  **Principle VII (Behavioral Outcome Isolation)**: **SATISFIED**. The trust score calculation (Lee & See scale) is mathematically independent of the agency condition logic. The analysis treats condition as a categorical predictor and trust as an independent outcome.

## Project Structure

### Documentation (this feature)

```text
specs/001-perceived-agency-trust/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/           # Phase 1 output
```

### Source Code (repository root)

```text
projects/PROJ-286-the-influence-of-perceived-agency-in-ai-/
├── code/
│   ├── __init__.py
│   ├── config.py                # Configuration for seeds, paths, thresholds
│   ├── simulation/
│   │   ├── __init__.py
│   │   ├── task_generator.py    # Simulates the experimental interface
│   │   └── survey_builder.py    # Builds the Lee & See survey
│   ├── analysis/
│   │   ├── __init__.py
│   │   ├── power_analysis.py    # Pre-study power calculation
│   │   ├── contrasts.py         # Planned contrasts and Tukey HSD
│   │   └── sensitivity.py       # Threshold sweeping
│   ├── utils/
│   │   ├── checksum.py          # Data hygiene utilities
│   │   └── citation_validator.py# Verifies DOI/Title against Crossref API
│   └── main.py                  # Orchestration script
├── data/
│   ├── raw/                     # Raw exports (simulated or real)
│   └── processed/               # Cleaned data for analysis
├── tests/
│   ├── test_contrasts.py
│   └── test_sensitivity.py
└── docs/
    └── protocol.md              # Pre-registered protocol (generated by T042)
```

**Structure Decision**: Single project structure (`code/`) chosen. The project is a linear pipeline (Simulation -> Analysis) rather than a complex web service. This minimizes overhead and aligns with the "Computational Experiment" type.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A | No violations found in this revision. | N/A |

## Implementation Phases

### Phase 0: Research & Validation (Pre-Implementation)
*Goal: Verify citations, define power analysis, and resolve panel concerns regarding "Verified Accuracy" and "Protocol Dependencies".*

1.  **Citation Verification (FR-000 / Constitution II)**:
    *   Execute `code/utils/citation_validator.py` to verify the Lee & See (2004) citation (DOI: `10.1518/hfes.46.1.50_30392`) against the **Crossref API**.
    *   The script fetches metadata (Title, Authors, Year) and compares it against the expected values.
    *   **Verification of Content**: While the API returns metadata, the *survey items* (text) are verified by cross-referencing the `survey_metadata.yaml` file against the official supplement/appendix linked in the API metadata or the primary publication's PDF. The script logs this verification status in a `data/processed/citation_log.json` file. If the API fetch fails, metadata mismatches, or the item text cannot be verified against the source document, the pipeline halts.
    *   **Output**: `data/processed/citation_log.json` containing `{author, year, title, doi, item_verification_status}`. This log is explicitly parsed in Phase 3 to populate the `citations` array in the final output.
2.  **Power Analysis (SC-002)**:
    *   Run `code/analysis/power_analysis.py` to determine N required for Power ≥ 0.80, α = 0.05, f = 0.25 (medium effect).
    *   Generate `docs/power_analysis_report.md`.
3.  **Protocol Definition (Resolving T038/T008)**:
    *   **Resolution of Circular Dependency**: The workflow is reordered to be strictly linear:
        1.  **Define Config**: `sensitivity_config` ranges are defined in `config.yaml` based on standard practice (70-95%).
        2.  **Generate Protocol**: `docs/protocol.md` is generated *referencing* the `config.yaml` ranges.
        3.  **Consistency Check**: A script validates that `config.yaml` matches the ranges documented in `docs/protocol.md`.
    *   This eliminates the circular dependency: Config -> Protocol -> Validation. The justification for ranges comes from the config definition and standard practice, not the protocol itself.

### Phase 1: Experimental Simulation & Data Generation
*Goal: Generate a valid dataset reflecting the experimental design for pipeline validation.*

1.  **Condition Logic**: Implement `High Agency` (sliders active), `Low Agency` (sliders disabled), and `Control` (static display) in `simulation/task_generator.py`.
2.  **Randomization**: Ensure participants are randomly assigned to conditions.
3.  **Data Capture**: Record `Condition_ID`, `Adherence_Rate` (secondary behavioral metric, NOT a direct proxy for Trust), `Trust_Score` (derived mean of multiple items, **included in raw CSV for schema compliance**), `Attention_Score` (continuous scale, derived from 5 attention questions), Cognitive_Load_Score (continuous, Likert-type scale), and `Perceived_Agency_Score` (manipulation check).
    *   **Note**: `Adherence_Rate` is captured as a secondary outcome. It is **not** assumed to be a direct proxy for Trust without empirical validation.
    *   **Attention Check**: The attention check consists of a series of **5 distinct questions**. `Attention_Score` is calculated as the percentage of correct answers (, 20, 40, 60, 80, 100).
4.  **Data Hygiene**: Write raw data to `data/raw/simulation_run_YYYYMMDD.csv` and generate a checksum.

### Phase 2: Statistical Analysis Pipeline
*Goal: Execute the analysis logic defined in the spec.*

1.  **Manipulation Check (Prerequisite)**:
    *   Perform ANOVA on `Perceived_Agency_Score` by condition.
    *   **Failure Mode**: If p > 0.05, the analysis halts and reports "Manipulation Failed". No Trust results are interpreted.
2.  **Cognitive Load Check**:
    *   Perform ANOVA on `Cognitive_Load_Score` by condition.
    *   If significant, `Cognitive_Load_Score` is included as a covariate in the main Trust analysis (ANCOVA).
3.  **Omnibus Test**:
    *   Run Omnibus ANOVA (F-test) on `Trust_Score` by condition.
    *   **Decision**: If Omnibus is NOT significant (p > 0.05), report null result. Do not proceed to post-hoc tests.
4.  **Planned Contrasts (Conditional on Omnibus)**:
    *   Execute `code/analysis/contrasts.py` using `statsmodels` with custom contrast coding:
        *   Contrast 1: High vs. Low (Vector: [1, -1, 0]).
        *   Contrast 2: (High + Low) vs. Control (Vector: [0.5, 0.5, -1]).
        *   Output: t-stat, df, p-value (raw).
5.  **Pairwise Comparisons & Unified Correction (Conditional on Omnibus)**:
    *   If Omnibus is significant, compute all 3 pairwise comparisons (High vs. Low, High vs. Control, Low vs. Control).
    *   **Unified Correction Strategy**: To control the family-wise error rate for the entire set of inferences (2 planned contrasts + 3 pairwise comparisons = 5 tests), apply a **Holm-Bonferroni correction** to all 5 p-values. This prevents Type I error inflation that would occur from running separate corrections.
    *   **Decision Tree**: Report results for all 5 tests with the unified adjusted p-values.
6.  **Effect Sizes**: Calculate Cohen's d for all significant pairwise comparisons (FR-004).
7.  **Sensitivity Analysis**: Execute `code/analysis/sensitivity.py` sweeping the `Attention_Score` threshold across a range of increasing values to verify result stability (FR-006). The `Attention_Score` is derived from the 5 attention questions, making the threshold sweep mathematically valid.

### Phase 3: Reporting & Validation
*Goal: Generate the final report and validate against contracts.*

1.  **Report Generation**: Compile results into `docs/results_report.md`.
2.  **Citation Injection**: Parse the `data/processed/citation_log.json` file (produced in Phase 0) to extract `author`, `year`, `title`, `doi` and inject it into the `citations` array of the final output. This ensures the `experiment_output.schema.yaml` requirement is met.
3.  **Contract Validation**: Run `tests/contract/test_schema.py` to ensure output matches `contracts/experiment_output.schema.yaml`.
4.  **Final Check**: Verify all SCs are met.

## Resolve Panel Concerns

- **T038/T008 (Circular Dependency)**: Resolved by reordering workflow: Config -> Protocol -> Validation. Justification comes from config definition, not the protocol.
- **T000/T000b (Hardcoded Citations)**: Resolved by introducing a `citation_validator` step in Phase 0 that fetches metadata from the **Crossref API** and verifies item text against the source document. The list is an adaptation, not hardcoded truth.
- **T009 (Schema Conflation)**: Resolved by separating schema (keys: `trust_item_1`...) from content (values: text in `survey_metadata.yaml`).
- **Methodology (Simulation vs. Causal)**: Explicitly stated that simulation validates code, not causal effects. Real data required for hypothesis testing.
- **Methodology (Contrasts)**: Mandated ANOVA with custom contrast coding, not separate t-tests.
- **Methodology (Sensitivity)**: Added `Attention_Score` (continuous) derived from 5 questions to enable threshold sweeping.
- **Methodology (Cognitive Load)**: Added `Cognitive_Load_Score` as a covariate/manipulation check.
- **Scientific Soundness (Adherence)**: Clarified Adherence as secondary outcome, not a direct proxy for Trust.
- **Scientific Soundness (Hierarchical Testing)**: Defined decision tree: Omnibus -> (Contrasts AND Tukey). Tukey is performed if Omnibus is significant, with a unified Holm-Bonferroni correction across all 5 tests.
- **Scientific Soundness (Manipulation Check)**: Added mandatory ANOVA on `Perceived_Agency_Score` with halt condition.
- **Scientific Soundness (Attention Check)**: Defined specific task (5 questions) and justified threshold range (70-95% based on 5 items).
