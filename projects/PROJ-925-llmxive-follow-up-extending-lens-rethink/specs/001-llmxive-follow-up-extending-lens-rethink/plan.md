# Implementation Plan: llmXive follow-up: extending "Lens: Rethinking Training Efficiency for Foundational Text-to-Image Mo"

**Branch**: `001-llmxive-lens-extension` | **Date**: 2026-07-16 | **Spec**: `specs/001-llmxive-follow-up-extending-lens-rethink/spec.md`
**Input**: Feature specification from `specs/001-llmxive-follow-up-extending-lens-rethink/spec.md`

## Summary

This feature implements a CPU-tractable research pipeline to analyze the "alignment gap" between CLIP scores and *human* ratings in image captions. The system extracts linguistic features (semantic surprisal via BERT perplexity, syntactic complexity, caption length) from raw captions, calculates a deviation target ($| \text{CLIP\_Score} - \text{Human\_Rating} |$) using verified human preference data from Pick-a-Pic, and trains an XGBoost model to predict this deviation. The pipeline strictly adheres to CPU constraints, ensures feasibility on free-tier CI runners via data streaming, and includes rigorous statistical significance testing (Benjamini-Hochberg) and sensitivity analysis (multi-seed sweep).

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `xgboost`, `scikit-learn`, `transformers`, `spacy`, `datasets`, `pandas`, `numpy`  
**Storage**: Local filesystem (`data/` for raw/processed, `code/` for scripts)  
**Testing**: `pytest` (unit tests for feature extraction, integration tests for pipeline)  
**Target Platform**: Linux (GitHub Actions free-tier: CPU, 7GB RAM)  
**Project Type**: Data Science / Research Pipeline  
**Performance Goals**: Feature extraction < 5s/caption; End-to-end < 6h; RAM < 7GB  
**Constraints**: CPU-only training; No GPU; **Streaming data** is the primary mechanism for satisfying the 7GB RAM limit (Constitution Principle VII); Strict reproducibility (pinned seeds)  
**Scale/Scope**: Subset of Pick-a-Pic (stratified sample to fit RAM)

> Empirical specifics (exact sample sizes, correlation values) are deferred to the implementation phase based on the actual data availability and compute runtime.

## Constitution Check

*Gates determined based on constitution file:*

1.  **Reproducibility**: Plan mandates pinned random seeds in `code/` and canonical dataset sources. **PASS**.
2.  **Verified Accuracy**: All citations in `research.md` point to verified URLs (Pick-a-Pic, BERT models) or standard libraries. **PASS**.
3.  **Data Hygiene**: Plan requires checksumming raw data and recording checksums in the `artifact_hashes` map of `state/projects/PROJ-925-llmxive-follow-up-extending-lens-rethink.yaml`. **PASS**.
4.  **Single Source of Truth**: `contracts/` is declared the Single Source of Truth for schema validation; pipeline outputs trace back to `data/`. **PASS**.
5.  **Versioning**: Plan includes a specific step to generate content hashes (e.g., `sha256sum`) and update `state/projects/PROJ-925-llmxive-follow-up-extending-lens-rethink.yaml` with `updated_at` and `artifact_hashes`. **PASS**.
6.  **Linguistic Feature Isolation**: Plan explicitly separates text-only feature extraction from image/rating data. **PASS**.
7.  **CPU-Tractability**: Model choice (XGBoost) and inference (BERT on CPU) are verified to run within 7GB RAM/2 CPU limits; **streaming** is the explicit mechanism to ensure this. **PASS**.

## Project Structure

### Documentation (this feature)

```text
specs/001-llmxive-follow-up-extending-lens-rethink/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (SSoT for schemas)
│   ├── dataset.schema.yaml
│   ├── feature_vector.schema.yaml
│   ├── deviation_target.schema.yaml
│   └── significance_results.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-925-llmxive-follow-up-extending-lens-rethink/
├── code/
│   ├── __init__.py
│   ├── requirements.txt
│   ├── data/
│   │   ├── download.py          # Fetches Pick-a-Pic data (streaming)
│   │   ├── preprocess.py        # Calculates deviation target & covariates
│   │   ├── features.py          # Extracts linguistic features
│   │   └── train.py             # XGBoost training & significance testing
│   └── tests/
│       ├── test_features.py
│       └── test_train.py
├── data/
│   ├── raw/                     # Raw downloads (checksummed)
│   └── processed/               # Derived CSVs/Parquets
└── docs/                        # Generated reports
```

**Structure Decision**: Single project structure with modular `code/` scripts. This minimizes overhead for a research pipeline where data flows sequentially (Download -> Preprocess -> Feature Extract -> Train). **Contracts** in `contracts/` serve as the Single Source of Truth for schema validation.

## Complexity Tracking

No complexity violations found. The design strictly adheres to the CPU constraint and data isolation principles.

## Implementation Phases

### Phase 0: Data Acquisition & Validation
- **Goal**: Fetch verified human-preference data and validate schema.
- **Steps**:
  1.  Stream `pick-a-pic` dataset via `datasets.load_dataset(..., streaming=True)`.
  2.  Validate presence of `caption`, `image`, `winner`, `loser` (or rating) columns.
  3.  Compute checksums for raw data chunks and record in `state/projects/PROJ-925-llmxive-follow-up-extending-lens-rethink.yaml` (Constitution Principle III).
  4.  **Edge Case Handling**: Log and exclude rows where `caption` is empty or `image` is missing.

### Phase 1: Feature Extraction & Covariate Calculation
- **Goal**: Extract linguistic features and control variables.
- **Steps**:
  1.  Compute **Semantic Surprisal** ($\ln(\text{Perplexity})$) using `bert-base-uncased` on CPU.
  2.  Compute **Syntactic Depth** (max dependency tree depth) via `spaCy`.
  3.  Compute **Noun-Phrase Density** and **Token Diversity**.
  4.  Compute **Covariates**: `caption_length` (token count) and `image_complexity` (optional proxy).
  5.  **Edge Case Handling**:
      -   If caption is too short for dependency parse, assign default depth=0 and log exclusion reason.
      -   If BERT inference fails, log caption ID and exclude row.
  6.  Output `features.csv` validated against `contracts/feature_vector.schema.yaml`.

### Phase 1.5: Data Validation & Edge Case Handling
- **Goal**: Ensure data integrity before training.
- **Steps**:
  1.  Check for **Zero Variance** in target variable ($| \text{CLIP} - \text{Human} |$). If variance is 0, halt training with error "Target not learnable".
  2.  Verify no `NaN` values in `features.csv` or `deviation.csv`.
  3.  Merge features and targets; drop any remaining incomplete rows.

### Phase 2: Target Variable Calculation
- **Goal**: Compute the alignment gap.
- **Steps**:
  1.  Compute CLIP score for each caption-image pair.
  2.  Convert `winner`/`loser` pairs to a normalized `human_rating` within a bounded unit interval.
  3.  Calculate $Y = | \text{CLIP\_Score} - \text{Human\_Rating} |$.
  4.  Output `deviation.csv` validated against `contracts/deviation_target.schema.yaml`.

### Phase 3: Model Training & Significance Testing
- **Goal**: Train XGBoost and perform statistical tests.
- **Steps**:
  1.  Train XGBoost on CPU with k-fold cross-validation.
  2.  Calculate **Permutation Importance** for all features.
  3.  **Permutation Test**: Run multiple iterations of label shuffling to build a null distribution..
  4.  Apply **Benjamini-Hochberg** correction to p-values (FDR < 0.05).
  5.  Log a random seed and method details for reproducibility.
  6.  Output `significance.json` validated against `contracts/significance_results.schema.yaml`.

### Phase 4: Sensitivity Analysis (SC-005)
- **Goal**: Measure robustness of feature rankings.
- **Steps**:
  1.  Re-run Phase with multiple different random seeds.
  2.  Aggregate feature importance rankings across seeds.
  3.  Calculate standard deviation of rankings for each feature.
  4.  Report stability metrics in final results.

### Phase 5: Versioning & Artifact Finalization
- **Goal**: Ensure reproducibility and state tracking.
- **Steps**:
  1.  Generate content hashes (SHA-256) for all `data/processed/` files.
  2.  Update `state/projects/PROJ-925-llmxive-follow-up-extending-lens-rethink.yaml` with `artifact_hashes` and `updated_at`.
  3.  Archive `code/` and `results/` for final review.