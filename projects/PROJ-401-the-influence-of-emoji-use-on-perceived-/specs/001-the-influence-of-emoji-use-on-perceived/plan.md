# Implementation Plan: The Influence of Emoji Use on Perceived Emotional Intensity in Text

**Branch**: `001-influence-of-emoji-on-intensity` | **Date**: 2026-08-01 | **Spec**: `specs/001-influence-of-emoji-on-perceived-intensity/spec.md`
**Input**: Feature specification from `specs/001-influence-of-emoji-on-perceived-intensity/spec.md`

## Summary

This project implements a rigorous feasibility study and statistical analysis pipeline. The primary objective is to determine if a public dataset exists containing `text_content`, `emoji` features, AND `human_intensity_score`. 

**Critical Finding**: Research indicates no verified dataset in the provided list contains the required `human_intensity_score` column. Consequently, the **primary execution path** for this project is the verification of this absence, followed by the generation of a formal "Data Unavailable" report. 

If, hypothetically, a dataset with the required columns were found, the pipeline would proceed to:
1. Extract objective emoji features (presence, count, type) via regex/Unicode normalization.
2. Perform correlation and regularized regression analyses (Lasso with cross-validated alpha).
3. Apply Bonferroni correction and report effect sizes.

However, the plan is structured such that the **successful generation of the "Data Unavailable" report** is the expected and valid completion state for the current resource constraints. This approach strictly adheres to the project constitution by refusing to use synthetic scores or invalid proxies.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `numpy`, `scipy`, `statsmodels`, `scikit-learn`, `emoji`, `datasets` (Hugging Face), `pyyaml`  
**Storage**: Local filesystem (`data/raw`, `data/processed`, `results`)  
**Testing**: `pytest` (unit tests for extraction logic; integration tests for pipeline reproducibility)  
**Target Platform**: Linux (GitHub Actions Free Tier: 2 CPU, ~7GB RAM)  
**Project Type**: Data Analysis CLI / Research Pipeline  
**Performance Goals**: Full pipeline execution ≤ 300 seconds for N=1000 messages (or ≤ 60 seconds for the verification-only path); memory usage < 4GB.  
**Constraints**: No GPU acceleration required; no synthetic data generation; strict adherence to human-rated outcome variables.  
**Scale/Scope**: Single dataset analysis (N ~ to a substantial volume of messages) OR immediate termination if data is missing.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Compliance Strategy |
|-----------|---------------------|
| **I. Reproducibility** | All random seeds (e.g., `np.random.seed`, `sklearn` splits) will be pinned. Dependencies pinned in `requirements.txt`. Data checksums recorded in `state`. |
| **II. Verified Accuracy** | Dataset sources cited only from the `# Verified datasets` block. No external claims made without verification. |
| **III. Data Hygiene** | Raw data stored in `data/raw` with checksums. Derived data in `data/processed` with new filenames. No in-place modification. |
| **IV. Single Source of Truth** | All statistics in the final report will be generated programmatically from `data/processed` and `code/` outputs. No manual entry. |
| **V. Versioning Discipline** | Artifact hashes tracked in `state/projects/...yaml`. |
| **VI. Human-Perception Grounding** | The pipeline explicitly checks for `human_intensity_score`. If missing, it halts with a "Data Unavailable" report. **This is the expected outcome for current resources.** No algorithmic sentiment scores will be used as a substitute. |
| **VII. Emoji Feature Independence** | Emoji features are extracted via regex/Unicode parsing from raw text *before* any correlation with intensity scores is computed. **Note**: Independence cannot be verified without the actual human-rated dataset; if the dataset is missing, the study halts rather than assuming validity. |

## Project Structure

### Documentation (this feature)

```text
specs/001-influence-of-emoji-on-intensity/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/           # Phase 1 output
    ├── dataset.schema.yaml
    ├── features.schema.yaml
    └── results.schema.yaml
```

### Source Code (repository root)

```text
projects/PROJ-401-the-influence-of-emoji-use-on-perceived-/code/
├── __init__.py
├── main.py              # Entry point for pipeline execution
├── config.py            # Configuration and constants
├── data/
│   ├── __init__.py
│   ├── loader.py        # Dataset ingestion and verification
│   └── extractor.py     # Emoji feature extraction
├── analysis/
│   ├── __init__.py
│   ├── stats.py         # Correlation, regression, power analysis
│   └── viz.py           # Plotting functions
├── utils/
│   ├── __init__.py
│   └── io.py            # Checksumming, file I/O
├── tests/
│   ├── __init__.py
│   ├── test_extractor.py
│   └── test_stats.py
└── requirements.txt
```

**Structure Decision**: Single project structure selected. The project is a linear data analysis pipeline (Load -> Extract -> Analyze -> Report) rather than a service or library, making a monolithic `code/` directory with modular sub-packages the most efficient approach for reproducibility and testing.

## Complexity Tracking

> **No violations detected.** The project scope is contained within a single statistical analysis workflow. No complex architectural patterns (e.g., microservices, complex state management) are required.

## Implementation Phases

### Phase 0: Data Ingestion & Verification (Critical Path)
*Addressing FR-001b, FR-002, FR-002c, US-1, US-2*

1.  **Task 0.1**: Load candidate datasets from the verified list using `datasets.load_dataset()`.
2.  **Task 0.2**: Verify schema presence: `text_content` and `human_intensity_score`.
3.  **Task 0.3**: **Decision Point**:
    *   **IF** `human_intensity_score` is missing:
        *   **Action**: Halt execution.
        *   **Output**: Generate `results/data_unavailable_report.md` detailing the missing modality and the specific dataset(s) checked.
        *   **Status**: Project Complete (Valid Termination).
    *   **IF** `human_intensity_score` is present:
        *   **Action**: Proceed to Phase 1.

### Phase 1: Feature Extraction (Conditional)
*Addressing FR-001, US-1*

1.  **Task 1.1**: Extract `emoji_presence` (binary), `emoji_count` (integer), and `emoji_types` (list of normalized Unicode code points) from `text_content`.
2.  **Task 1.2**: Handle edge cases: empty text strings, skin tone modifiers (normalize to base Unicode).
3.  **Task 1.3**: Compute covariates: `text_length`, `punctuation_count`.
4.  **Task 1.4**: Save processed dataset to `data/processed/messages_extracted.parquet`.

### Phase 2: Power Analysis & Sample Size Verification (Conditional)
*Addressing FR-006, SC-005*

1.  **Task 2.1**: Perform pre-study power analysis to determine minimum N required for Cohen's f² ≥ 0.02, power=0.80, α=0.05.
2.  **Task 2.2**: Compare actual N against required N.
3.  **Task 2.3**: **Decision Point**:
    *   **IF** N < required N:
        *   **Action**: Flag "Power Limitation Warning" in the final report.
    *   **IF** N >= required N:
        *   **Action**: Proceed to Phase 3.

### Phase 3: Statistical Analysis (Conditional)
*Addressing FR-003, FR-004, FR-004b, FR-005, US-3*

1.  **Task 3.1**: Compute Pearson/Spearman correlation between `emoji_count` and `intensity_score`.
2.  **Task 3.2**: **Feature Collapsing**: Collapse emoji types with frequency < 5 into a single "Rare" category to prevent high dimensionality.
3.  **Task 3.3**: Perform Lasso Regression with `alpha` determined via **k-fold cross-validation

The specific value to remove/generalize: 'k'

Rewritten passage:
k-fold cross-validation is employed to evaluate the model's generalization performance.** (not fixed at 0.1) to select optimal regularization strength.
4.  **Task 3.4**: Apply Bonferroni correction to p-values for multiple hypothesis tests.
5.  **Task 3.5**: Calculate Standardized Beta coefficients.
6.  **Task 3.6**: Generate visualizations (correlation plot, coefficient plot).

### Phase 4: Reproducibility Verification (Conditional)
*Addressing SC-004*

1.  **Task 4.1**: Re-run the entire pipeline (Phases 0-3) on the same input data.
2.  **Task 4.2**: Compare output checksums of all generated artifacts (JSON, CSV, PNG).
3.  **Task 4.3**: Generate `results/reproducibility_report.md` confirming bit-for-bit match or documenting discrepancies.

### Phase 5: Performance Benchmarking (Conditional)
*Addressing SC-005*

1.  **Task 5.1**: Measure total execution time of the pipeline.
2.  **Task 5.2**: Compare against the baseline of ≤ 300 seconds for N=1000 (or scaled linearly).
3.  **Task 5.3**: Generate `results/performance_report.md` confirming compliance or flagging delays.

## Success Criteria

1.  **Data Verification**: The pipeline successfully identifies the absence of `human_intensity_score` in the verified datasets and generates a valid "Data Unavailable" report. (Primary Outcome)
2.  **Statistical Rigor**: If data were available, the pipeline would correctly apply Bonferroni correction, cross-validated Lasso, and report Standardized Betas.
3.  **Reproducibility**: The pipeline produces bit-for-bit identical outputs on re-run (SC-004).
4.  **Performance**: The pipeline executes within the 300-second limit (SC-005).
5.  **Constitutional Compliance**: No synthetic scores are generated; the pipeline halts if human-rated data is missing (Principle VI).

## Risk Mitigation

*   **Risk**: No dataset contains `human_intensity_score`.
    *   **Mitigation**: This is the expected outcome. The "Data Unavailable" report is the valid scientific deliverable.
*   **Risk**: High dimensionality of emoji types causing Lasso instability.
    *   **Mitigation**: Feature collapsing (frequency < 5) and cross-validated alpha selection.
*   **Risk**: Underpowered sample size.
    *   **Mitigation**: Explicit power analysis (Phase 2) and warning flags.