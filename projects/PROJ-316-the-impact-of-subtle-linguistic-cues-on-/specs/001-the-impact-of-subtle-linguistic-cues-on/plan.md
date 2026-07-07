# Implementation Plan: The Impact of Subtle Linguistic Cues on Perceived Authenticity in AI Chatbots

**Branch**: `001-impact-of-subtle-linguistic-cues` | **Date**: 2026-06-28 | **Spec**: `specs/001-impact-of-subtle-linguistic-cues/spec.md`
**Input**: Feature specification from `specs/001-impact-of-subtle-linguistic-cues/spec.md`

## Summary

This project implements a reproducible statistical analysis pipeline to investigate whether subtle linguistic variations—specifically first-person pronoun frequency, hedge density, and emotional valence—predict human ratings of perceived authenticity in AI chatbot conversations.

**Critical Dependency**: The core statistical analysis (correlation/regression) is **blocked** pending the acquisition of a dataset containing **human authenticity ratings**. The current verified dataset (`MixSub-LLaMA-3.2`) contains only text. This plan explicitly includes **Phase 0: Data Acquisition & Annotation** to secure the required outcome variable (FR-009). The analysis pipeline will only execute once this phase is complete and verified.

The approach involves:
1. **Phase 0**: Secure human ratings (via verified dataset or manual annotation protocol).
2. **Phase 1**: Automated extraction of linguistic metrics from raw text using `spaCy`, `NLTK`, and `VADER`.
3. **Phase 2**: Computation of Pearson and Spearman correlations between these metrics and human authenticity scores, with multiple-comparison correction.
4. **Phase 3**: Fitting a multivariate linear regression model controlling for conversation length and turn count, including diagnostic checks for multicollinearity (VIF) and non-linearity.

All results are strictly framed as associational.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `spaCy` (v3.5, model `en_core_web_sm`), `NLTK` (v3.8), `vaderSentiment` (v3.3.2), `pandas`, `scikit-learn`, `statsmodels`, `scipy`, `matplotlib`, `seaborn`, `krippendorff` (for reliability)  
**Storage**: Local file system (CSV, JSONL, Parquet); no external database.  
**Testing**: `pytest` (unit tests for extraction logic; integration tests for pipeline).  
**Target Platform**: Linux (GitHub Actions free-tier runner: 2 CPU, ~7 GB RAM, no GPU).  
**Project Type**: Research data pipeline (CLI tools + analysis scripts).  
**Performance Goals**: Complete full pipeline (extraction + correlation + regression) on ≤10,000 sampled conversations within 6 hours on CPU-only runner.  
**Constraints**:  
- No GPU/CUDA; all models must run in default precision on CPU.  
- Dataset subset to ≤7 GB RAM / ≤14 GB disk.  
- All external datasets must be fetched from verified sources only.  
- **Blocking Condition**: No statistical analysis proceeds without verified human authenticity ratings (FR-009).  
- Handle edge cases: empty/short texts, missing ratings, skewed distributions.  
**Scale/Scope**: Up to 10,000 conversation records (post-acquisition); linguistic features + 2 controls.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Compliance Status | Action / Evidence |
|-----------|-------------------|-------------------|
| I. Reproducibility | ✅ Compliant | All scripts will pin random seeds; `requirements.txt` pins versions; external datasets fetched from canonical HuggingFace URL; CI runs on fresh runner. |
| II. Verified Accuracy | ⚠️ Pending | Requires verified dataset with human ratings. Current text-only dataset is insufficient. Compliance depends on Phase 0 completion. |
| III. Data Hygiene | ✅ Compliant | Raw data preserved; derivations written to new files; checksums recorded in state YAML; PII scan enforced. |
| IV. Single Source of Truth | ✅ Compliant | All statistics trace to one row in `data/` and one code block; no hand-typed numbers in reports. |
| V. Versioning Discipline | ✅ Compliant | Content hashes tracked; `updated_at` timestamp updated on artifact change; semver.0 ratified. |
| VI. Linguistic Feature Extraction Transparency | ✅ Compliant | Tool versions and parameters documented in `code/`; raw text and feature matrices stored separately in `data/`. |
| VII. Human Rating Documentation | ⚠️ Pending | Requires annotation protocol or verified dataset with ratings. Compliance depends on Phase 0 completion (Krippendorff's α ≥ 0.7). |

## Project Structure

### Documentation (this feature)

```text
specs/001-impact-of-subtle-linguistic-cues/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── dataset.schema.yaml
│   └── output.schema.yaml
└── tasks.md             # Phase 2 output (NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
src/
├── extraction/
│   ├── __init__.py
│   ├── pronoun_extractor.py
│   ├── hedge_extractor.py
│   └── sentiment_analyzer.py
├── analysis/
│   ├── __init__.py
│   ├── correlation.py
│   └── regression.py
├── utils/
│   ├── __init__.py
│   └── data_loader.py
├── main.py
└── config.py

tests/
├── contract/
├── integration/
└── unit/

data/
├── raw/
│   └── conversations.jsonl
├── processed/
│   ├── features.csv
│   └── ratings.csv
└── derived/
    └── analysis_results.csv

code/
└── requirements.txt
```

**Structure Decision**: Single-project structure selected for simplicity and alignment with research pipeline nature. Modular separation (`extraction/`, `analysis/`, `utils/`) ensures testability and traceability per Constitution Principle IV.

## Complexity Tracking

> No violations detected; complexity is minimal and justified by research requirements.

## Implementation Phases

### Phase 0: Data Acquisition & Annotation (Blocking)
**Goal**: Secure a dataset with human authenticity ratings or define a manual annotation protocol.
- **Step 0.1**: Verify availability of a public dataset with human authenticity ratings. If none exists, proceed to Step 0.2.
- **Step 0.2**: Define and execute a manual annotation protocol:
  - Recruit annotators.
  - Provide standardized instructions (-5 Likert scale for authenticity).
  - Calculate Krippendorff's alpha (target ≥ 0.7).
  - Generate `ratings.csv` (FR-009, SC-006).
- **Step 0.3**: Validate `ratings.csv` against `conversation_id` in `conversations.jsonl`.
- **Blocker**: Analysis pipeline (Phases 1-3) cannot start until `ratings.csv` exists and passes reliability checks.

### Phase 1: Linguistic Feature Extraction
**Goal**: Extract quantitative metrics from raw text.
- **Step 1.1**: Load `conversations.jsonl`.
- **Step 1.2**: Calculate `pronoun_rate`, `hedge_density`, `valence_score` (FR-001).
- **Step 1.3**: Handle edge cases (empty/short texts) per FR-006.
- **Output**: `features.csv`.

### Phase 2: Correlation Analysis
**Goal**: Compute associational relationships.
- **Step 2.1**: Merge `features.csv` and `ratings.csv`.
- **Step 2.2**: Compute Pearson and Spearman correlations (FR-002).
- **Step 2.3**: Apply Benjamini-Hochberg correction (SC-004).
- **Output**: `correlation_results.csv`, scatter plots.

### Phase 3: Multivariate Regression
**Goal**: Isolate unique contributions of linguistic features.
- **Step 3.1**: Fit multiple linear regression with controls (FR-003).
- **Step 3.2**: Compute VIF for multicollinearity (FR-005, SC-003).
- **Step 3.3**: Test for non-linearity (FR-010).
- **Output**: `regression_results.csv`, diagnostics.

### Phase 4: Reporting
**Goal**: Generate final report with associational disclaimer.
- **Step 4.1**: Compile results.
- **Step 4.2**: Append mandatory disclaimer (FR-004).
- **Output**: `analysis_results.csv`, `reports/`.