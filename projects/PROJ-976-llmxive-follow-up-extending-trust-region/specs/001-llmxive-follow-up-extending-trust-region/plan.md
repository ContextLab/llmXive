# Implementation Plan: llmXive follow-up: extending "Trust-Region Behavior Blending for On-Policy Distillation"

**Branch**: `001-llmxive-trb-diversity-profile` | **Date**: 2026-07-12 | **Spec**: `specs/001-llmxive-follow-up-extending-trust-region/spec.md`

## Summary

This feature implements a static diversity profiling pipeline to analyze lexical and syntactic metrics on teacher outputs. **Critical Scope Note**: The original spec's requirement to predict "optimal KL budgets" ($\varepsilon_0$) and "training collapse" from ground-truth sweep logs cannot be fulfilled because the available verified datasets (`tr-books-tokenized`, `Tr-beir-formatted`) do not contain these training dynamics. The project scope is revised to a **Feasibility & Pipeline Validation** study: correlating static diversity profiles with *proxy quality scores* (relevance scores in BEIR, text length/entropy in Book Corpus) and *simulated* stability metrics. The goal is to validate the *feasibility* of the diversity profiling pipeline and the *generalization* of diversity patterns across domains (Book Corpus vs. BEIR), while explicitly flagging the inability to validate the core "collapse prediction" hypothesis.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `scikit-learn`, `spacy`, `numpy`, `jsonlines`, `pyyaml`  
**Storage**: Local filesystem (CSV/JSONL) for feature matrices and analysis results.  
**Testing**: `pytest` with unit tests for metric computation.  
**Target Platform**: Linux (GitHub Actions free-tier runner: CPU, 7 GB RAM).  
**Project Type**: Research pipeline / Data analysis library.  
**Performance Goals**: Feature extraction on 10k samples < 30 mins; Total runtime < 6 hours.  
**Constraints**: CPU-only execution; No GPU/CUDA; Memory footprint < 7 GB; No external API calls during runtime.  
**Scale/Scope**: A substantial number of teacher output samples across two domains (Book Corpus, BEIR).

## Constitution Check

*GATE: Must pass before Phase 0 research.*

- **Principle I (Reproducibility)**: Plan enforces fixed random seeds in `code/` scripts and requires all data to be fetched from verified URLs (HuggingFace) with checksums recorded in `data/`.
- **Principle II (Verified Accuracy)**: All citations in `research.md` are verified by the Reference-Validator Agent against primary sources with title-token-overlap >= 0.7. The prompt-provided "Verified datasets" block serves as the initial candidate list, but active verification is required. The plan explicitly acknowledges that the verified datasets lack ground-truth sweep logs.
- **Principle III (Data Hygiene)**: Raw data (TRB sweep logs, teacher outputs) will be stored in `data/raw/` with checksums. Derived features stored in `data/processed/`. No in-place modification.
- **Principle IV (Single Source of Truth)**: All metrics (Correlation, FPR proxy) will be computed by `code/` scripts and logged to `data/results/`. The paper will reference these specific files, not hand-typed values.
- **Principle V (Versioning)**: Artifacts (feature matrices) will be hashed. The plan includes a step to update `state/` timestamps upon artifact generation.
- **Principle VI (Static Diversity Profiling)**: The plan strictly prohibits real-time teacher inference. All features are derived from pre-existing text files.
- **Principle VII (Cross-Dataset Generalization)**: The plan explicitly separates training (Source: Book Corpus) and validation (Target: BEIR) phases, ensuring no data leakage. **Note**: The "generalization" claim is limited to the proxy domains.

## Project Structure

### Documentation (this feature)

```text
specs/001-llmxive-trb-diversity-profile/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-976-llmxive-follow-up-extending-trust-region/
├── code/
│   ├── __init__.py
│   ├── config.py              # Paths, seeds, hyperparameters
│   ├── metrics/
│   │   ├── __init__.py
│   │   ├── lexical.py         # distinct-4, entropy
│   │   └── syntactic.py       # parse tree depth variance
│   ├── pipelines/
│   │   ├── __init__.py
│   │   ├── extract_features.py # Main entry for FR-001
│   │   └── analyze_correlations.py # Main entry for Phase 3
│   └── utils/
│       ├── __init__.py
│       └── data_loader.py     # Loads verified datasets
├── data/
│   ├── raw/                   # Downloaded datasets
│   ├── processed/             # Feature matrices, proxy labels
│   └── results/               # Correlation reports, baseline comparisons
├── tests/
│   ├── unit/
│   │   ├── test_lexical.py
│   │   └── test_syntactic.py
│   └── integration/
│       └── test_pipeline.py
└── requirements.txt
```

**Structure Decision**: Single-project structure with modular `code/` directories. This aligns with the research nature of the project, keeping data processing and analysis logic distinct but in a single codebase for easier reproducibility on the GitHub Actions runner.

## Complexity Tracking

No violations of the constitution were found that require justification. The modular structure is standard for Python data science projects and ensures maintainability without unnecessary abstraction.

## Phase Breakdown

### Phase 0: Research & Dataset Strategy
- **Goal**: Confirm dataset availability and variable fit.
- **FR-001, FR-002, FR-005, FR-006, FR-007, FR-008**: Map to dataset verification steps.
- **Action**: Verify that the "Verified datasets" block contains the necessary text samples.
- **Critical Data Constraint**: The verified datasets (`tr-books-tokenized`, `Tr-beir-formatted`) **lack** ground-truth `optimal_epsilon_0` and `collapse_label`.
- **Decision**: The project will **not** attempt to train a predictor for these missing variables. Instead, it will:
  1. Compute diversity profiles for all samples.
  2. Use available metadata (e.g., relevance scores in BEIR) as *proxy* targets for correlation analysis.
  3. **Explicitly report the inability to validate the core "collapse prediction" hypothesis** via a "Blocking Gap Report".
- **Blocking Condition**: If the datasets lack *any* metadata that can serve as a proxy for quality or stability, the project will halt and report a blocking gap.

### Phase 1: Data Model & Contracts
- **Goal**: Define schemas for input/output.
- **FR-001, FR-002**: Define `DiversityProfile` and `TrainingInstance` schemas.
- **Action**: Create YAML contracts for feature matrices and analysis results, referencing `contracts/dataset.schema.yaml` and `contracts/model_output.schema.yaml`.
- **Constraint**: Ensure schemas handle edge cases (empty strings, parse failures) as defined in the spec.
- **Domain Update**: The `domain` enum in `TrainingInstance` is updated to `['book_corpus', 'beir']` to reflect actual data.

### Phase 2: Implementation (Feature Extraction)
- **Goal**: Implement FR-001, FR-008.
- **Action**: Build `metrics/lexical.py` and `metrics/syntactic.py`.
- **Constraint**: Ensure CPU-only, batched processing to fit 7GB RAM.

### Phase 3: Correlation & Baseline Analysis (Revised from "Model Training")
- **Goal**: Implement FR-006, FR-007, SC-001, SC-005.
- **Action**:
  1. Compute diversity profiles for Source (Book Corpus) and Target (BEIR).
  2. Compute correlation coefficients between diversity metrics and *proxy* targets (e.g., relevance scores).
  3. **Baseline Comparison**: Calculate the performance of a fixed-default baseline (e.g., mean relevance) vs. a diversity-based ranking. **Record the delta** to satisfy SC-001.
  4. **Record Source Performance Metrics**: Store correlation coefficients for Source and Target to calculate the generalization gap (SC-005).
  5. **Log Results**: Save all metrics to `data/results/` as required by Constitution Principle IV.
- **Constraint**: No model training on missing ground truth. Use statistical correlation.

### Phase 4: Statistical Rigor & Reporting
- **Goal**: Implement FR-006 (Permutation test) and SC-001-SC-006.
- **Action**: Generate final metrics and validation reports.
- **Constraint**: Document power limitations if sample size is small.

## Compute Feasibility

- **Hardware**: 2 CPU cores, 7 GB RAM.
- **Strategy**:
  - **Feature Extraction**: Process in batches of a manageable size. (as per spec). Use `spaCy` in `en_core_web_sm` (small model) for syntactic parsing to minimize memory.
  - **Analysis**: Use `scikit-learn`'s `pearsonr` and `scipy.stats` for correlation tests. These are CPU-optimized and fit within memory.
  - **Data Size**: Limit dataset to a large-scale sample size.. If larger, sample down to fit RAM.
  - **Runtime**: Total estimated time < 4 hours (leaving 2h buffer).

## Risk Mitigation

- **Dataset Mismatch**: If verified datasets do not contain the required "optimal $\varepsilon_0$" or "collapse labels", the plan halts the predictive modeling phase and reports the gap (Constitution Principle II). The project proceeds with proxy analysis only.
- **Parse Failures**: `syntactic.py` will implement a try/except block returning `NaN` for parse failures, logged as warnings (Spec Edge Cases).
- **Collinearity**: If `distinct-4` and `ngram_entropy` are highly correlated, the plan will note this in `research.md` and avoid claiming independent effects (Statistical Rigor).
- **Circular Logic**: The analysis explicitly avoids predicting the hyperparameter that generated the text. It correlates text features with *independent* proxy scores (e.g., relevance) to avoid circularity.