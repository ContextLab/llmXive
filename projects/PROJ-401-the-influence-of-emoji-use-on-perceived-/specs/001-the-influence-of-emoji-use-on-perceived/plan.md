# Implementation Plan: The Influence of Emoji Use on Perceived Emotional Intensity in Text

**Branch**: `001-influence-of-emoji-on-intensity` | **Date**: 2026-08-01 | **Spec**: `specs/001-influence-of-emoji-on-intensity/spec.md`
**Input**: Feature specification from `specs/001-influence-of-emoji-on-intensity/spec.md`

## Summary

This project investigates the association between emoji usage (presence, frequency, type) and **human-perceived** emotional intensity in text messages. The implementation follows a strict observational design: extracting objective emoji metrics from a verified dataset. 

**CRITICAL GATE**: The project prioritizes datasets with human-rated intensity scores. If no such dataset is available (e.g., using the CMU Text Message Corpus), the system **MUST** activate the "Synthetic Proxy Generation" module as defined in FR-002 and US-2. This module generates intensity scores using a **stochastic, non-circular algorithm** validated against a small human-annotated subset (N=20). The use of synthetic scores is **REQUIRED** when human data is missing, not prohibited, to satisfy the spec's requirement for a complete pipeline.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `ml-datasets` (for CMU corpus), `pandas`, `numpy`, `scipy`, `statsmodels`, `seaborn`, `emoji` (for extraction), `tqdm`  
**Storage**: Local file system (CSV/JSON for data, PNG for plots)  
**Testing**: `pytest` (unit tests for extraction, integration tests for pipeline reproducibility)  
**Target Platform**: Linux (GitHub Actions runner)  
**Project Type**: Data analysis pipeline / Research script  
**Performance Goals**: < 5 minutes for N=1000 messages; < 7 GB RAM usage  
**Constraints**: No GPU required; CPU-only statistical libraries; strict adherence to data checksums and reproducibility seeds.  
**Scale/Scope**: Dataset size N ≥ 128 (determined by power analysis). If human data is missing, N=128+ synthetic scores generated.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Compliance Strategy |
|-----------|---------------------|
| **I. Reproducibility** | All scripts use `random.seed(42)` (or pinned value). `requirements.txt` pins exact versions. Data loaded via `ml_datasets` (canonical source) with checksum verification. Synthetic proxy generation uses fixed seeds. |
| **II. Verified Accuracy** | Citations in `research.md` restricted to the "Verified datasets" block in the prompt. No hallucinated URLs. Proxy validity metrics (r ≥ 0.6) are verified against the human subset. |
| **III. Data Hygiene** | Raw data from `ml_datasets` saved to `data/raw/cmu_messages.csv` with checksum. Derived data (emoji features, synthetic scores) saved to `data/processed/` with distinct filenames. No in-place modification. |
| **IV. Single Source of Truth** | All statistics in the final report are generated programmatically from `data/processed/analysis_results.csv`. No hand-typed numbers. |
| **V. Versioning Discipline** | Artifact hashes recorded in `state/...yaml` upon generation. |
| **VI. Human-Perception Grounding** | **STRICT ENFORCEMENT**: If human-rated data exists, use it. If not, use the **Synthetic Proxy** module (FR-002) which is **validated** against a human subset (N=20) to ensure it approximates human perception (r ≥ 0.6) without circularity. Synthetic scores are flagged as `is_proxy=True`. |
| **VII. Emoji Feature Independence** | Emoji features (`emoji_count`, `emoji_types`) are extracted from raw text *before* any interaction with intensity scores. The synthetic proxy generation **excludes** text length and punctuation as predictors to prevent multicollinearity with control variables in the final regression. |

## Project Structure

### Documentation (this feature)

```text
specs/001-influence-of-emoji-on-intensity/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (not created by /speckit-plan)
```

### Source Code (repository root)

```text
src/
├── data/
│   ├── loaders.py           # Loads dataset and validates human ratings
│   ├── preprocessing.py     # Emoji extraction, text cleaning
│   ├── proxy_generator.py   # Synthetic proxy generation (stochastic, non-circular)
│   └── validation.py        # Checks for human-rated data presence, validates proxy
│
├── analysis/
│   ├── stats.py             # Correlation, regression, Bonferroni correction
│   └── viz.py               # Plot generation (seaborn)
│
├── main.py                  # Orchestrates pipeline
└── utils.py                 # Logging, checksums, seeding

tests/
├── unit/
│   ├── test_extraction.py   # FR-001 tests
│   ├── test_proxy_gen.py    # FR-002 tests (non-circular logic)
│   └── test_data_validation.py # FR-002b tests (proxy validity)
├── integration/
│   └── test_pipeline.py     # Reproducibility (SC-004)
└── contract/
    └── test_schema.py       # Validates data against contracts

requirements.txt
```

**Structure Decision**: Single project structure (`src/`, `tests/`) selected. This is a linear data analysis pipeline without a web frontend or mobile app. The separation of `data/`, `analysis/`, and `utils/` ensures modularity for testing and reproducibility.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Data Availability Gate** | Required to enforce Constitution Principle VI and determine if proxy is needed. | Using synthetic proxies without validation would violate the research question. |
| **Proxy Generation Module** | Required by FR-002 when human data is missing. | Skipping proxy generation would leave the project unable to run if human data is absent. |
| **Proxy Validity Check** | Required by FR-002b to ensure proxy approximates human perception. | Without validation, synthetic scores are scientifically invalid. |
| **Power Analysis Step** | Required to determine minimum N for FR-006 and to avoid underpowered conclusions. | Skipping power analysis risks Type II errors and violates FR-006. |
| **Bonferroni Correction** | Required by FR-005 to control family-wise error rate when testing multiple emoji types. | Uncorrected p-values would inflate Type I error, violating SC-002. |

## Phase Execution Order

1.  **Data Availability Check**: Verify the presence of human-rated intensity scores in the dataset.
2.  **Branching Logic**:
    *   **If Human Data Exists**: Proceed to Feature Extraction.
    *   **If Human Data Missing**: Execute **Proxy Generation** (FR-002) on N messages (N determined by power analysis).
3.  **Proxy Validation**: If proxy generated, run **Validity Check** (FR-002b) against held-out human subset (N=20). If r < 0.6, **HALT** and flag limitation.
4.  **Feature Extraction**: Extract emoji metrics (FR-001) -> `data/processed/features.csv`.
5.  **Power Analysis**: Determine N (FR-006).
6.  **Statistical Analysis**: Correlation, Regression, Bonferroni (FR-003, FR-004, FR-005). **Note**: Regression controls for text length/punctuation; proxy generation explicitly excludes these to avoid multicollinearity.
7.  **Visualization & Reporting**: Generate plots and final CSV (SC-003, SC-005).
