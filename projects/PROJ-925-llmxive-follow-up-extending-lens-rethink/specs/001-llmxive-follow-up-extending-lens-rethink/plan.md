# Implementation Plan: llmXive follow-up: extending "Lens: Rethinking Training Efficiency for Foundational Text-to-Image Mo"

**Branch**: `001-llmxive-lens-extension` | **Date**: 2026-07-16 | **Spec**: `spec.md`
**Input**: Feature specification from `specs/001-llmxive-follow-up-extending-lens-rethink/spec.md`

## Summary

This feature implements a CPU-tractable research pipeline to quantify the "human-model disagreement" between CLIP scores and human preference ratings in text-to-image captions. The primary requirement is to extract linguistic features (BERT Perplexity, syntactic complexity) from raw text, compute a deviation target variable ($| \text{CLIP\_Score} - \text{Human\_Rating} |$), and train a Gradient Boosted Trees model (XGBoost) to predict this disagreement. The technical approach strictly adheres to CPU-only constraints, open-data availability (Pick-a-Pic), and rigorous statistical testing (Benjamini-Hochberg correction, 1,000 iteration permutation importance) to ensure reproducibility on free-tier CI runners. The analysis operates on a stratified random sample of **[deferred] rows** to ensure the feature extraction phase completes within the 6-hour CI limit.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `transformers` (for DistilBERT perplexity), `spacy` (for dependency parsing), `xgboost` (CPU-only training), `scikit-learn` (metrics/permutation), `pandas`, `pyarrow` (for parquet streaming), `ruff`, `black`.  
**Storage**: Local file system (`data/raw`, `data/processed`, `results`).  
**Testing**: `pytest` with `hypothesis` for edge cases (short captions, missing values).  
**Target Platform**: GitHub Actions free-tier runner (2 CPU, 7 GB RAM, no GPU).  
**Project Type**: Research CLI / Data Pipeline.  
**Performance Goals**: Feature extraction < 5s/caption for 10k samples; Full pipeline < 6h; Memory < 6 GB peak.  
**Constraints**: No GPU usage; No access-gated data (must use open HuggingFace datasets like Pick-a-Pic); Strict separation of text-feature extraction from image/rating metadata.  
**Scale/Scope**: Stratified random sample of [deferred] rows from Pick-a-Pic to fit memory/disk limits while maintaining statistical power.

> **Note on Dataset Strategy**: The plan explicitly uses the **Pick-a-Pic** dataset (verified via HuggingFace) which contains both captions and human preference scores (`preference_score`). If this column is missing, the pipeline halts with a loud error. No unverified sources or derivations are permitted.

## Constitution Check

*GATE: Must pass before Phase 0 research.*

| Principle | Status | Action Required (Implementation Detail) |
| :--- | :--- | :--- |
| **I. Reproducibility** | **Pass** | Pin `transformers`, `spacy`, `xgboost` versions in `requirements.txt`. Use `datasets` streaming to ensure same source. |
| **II. Verified Accuracy** | **Pass** | All dataset URLs strictly from the provided "Verified datasets" block (Pick-a-Pic). No invented URLs. |
| **III. Data Hygiene** | **Pass** | Raw data downloaded to `data/raw` with checksums. Processed data written to `data/processed` with new filenames. |
| **IV. Single Source of Truth** | **Pass** | All metrics in `results/` trace to specific CSV rows. No hand-typed numbers in paper. |
| **V. Versioning** | **Pass** | Content hashes recorded in `state/...yaml` for all data artifacts. |
| **VI. Linguistic Feature Isolation** | **Pass** | Enforced by restricting imports in `features.py` to text-processing libraries only. No image data or ratings passed to the feature extractor. |
| **VII. CPU-Tractability** | **Pass** | XGBoost configured with `tree_method='hist'` (CPU optimized). No CUDA devices. DistilBERT inference on CPU with `device="cpu"`. |

## Project Structure

### Documentation (this feature)

```text
specs/001-llmxive-follow-up-extending-lens-rethink/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── dataset.schema.yaml
│   ├── feature_vector.schema.yaml
│   ├── deviation_target.schema.yaml
│   └── significance_results.schema.yaml
└── tasks.md             # Phase 2 output (generated later)
```

### Source Code (repository root)

```text
projects/PROJ-925-llmxive-follow-up-extending-lens-rethink/
├── code/
│   ├── __init__.py
│   ├── data/
│   │   ├── __init__.py
│   │   ├── loader.py          # Handles streaming/download, raises on failure
│   │   ├── features.py        # Extracts perplexity, depth, density (Text -> Vector)
│   │   └── preprocess.py      # Computes deviation, handles missing values
│   ├── models/
│   │   ├── __init__.py
│   │   └── train.py           # XGBoost training, permutation importance, stability loop
│   ├── utils/
│   │   └── stats.py           # Benjamini-Hochberg, p-value calculation
│   └── tests/
│       ├── test_features.py
│       ├── test_preprocess.py
│       └── test_train.py
├── data/
│   ├── raw/                   # Downloaded parquet shards (immutable)
│   └── processed/             # features.csv, deviation.csv, stability_metrics.json
├── results/
│   └── model_artifacts/       # Trained XGBoost model, logs
├── docs/
│   └── README.md
├── pyproject.toml             # Linting config (Black, Ruff)
└── requirements.txt           # Pinned dependencies
```

**Structure Decision**: Chosen structure separates data ingestion (`loader`), feature engineering (`features`), target engineering (`preprocess`), and modeling (`train`). This enforces Constitution Principle VI (Linguistic Feature Isolation) by ensuring `features.py` has no dependency on image data or ratings. The `data/` directory is at the project root, not nested under `code/`, resolving the conflict in T001/T009.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **Permutation Significance Test** | Required by FR-006 and SC-004 to validate feature importance against random chance. | A simple model accuracy metric does not prove *which* features are significant; it only measures overall performance. |
| **Streaming Data Loading** | Dataset size (large-scale) exceeds CI RAM (7GB). | Loading the full dataset into memory would crash the runner. Streaming allows processing row-by-row. |
| **Stability Loop (SC-005)** | Required to prove results are not artifacts of a single random seed. | A single train/test split cannot guarantee robustness; the loop is mandatory for the research claim. |
| **Confounding Control** | Required to address methodology concerns about spurious correlations. | Without controlling for caption length or image complexity, observed correlations may be confounded. |

## Implementation Phases & Task Dependencies

### Phase 0: Research & Data Strategy
- **T001**: Define dataset strategy (Pick-a-Pic) and verify column presence.
- **T002**: Define statistical methodology (raw difference, permutation testing).

### Phase 1: Data Engineering & Contracts
- **T004**: Define and validate `contracts/*.schema.yaml` files. **(Hard Dependency for T018)**
- **T009**: Implement `code/data/loader.py` with strict column checks.
- **T018**: Implement `code/data/features.py` (DistilBERT perplexity) and validate against `feature_vector.schema.yaml`.

### Phase 2: Target Engineering
- **T025**: Implement `code/data/preprocess.py` (raw difference, zero variance check) and validate against `deviation_target.schema.yaml`.

### Phase 3: Modeling & Stability
- **T033**: Implement `code/models/train.py` with:
  - **Stability Loop**: Iterate over **5 seeds** (0, 42, 123, 2024, 9999).
  - **Inside Loop**: Re-sample data (T013b logic), retrain model, calculate feature importance.
  - **Permutation**: 1,000 iterations for null distribution.
  - **Correction**: Apply Benjamini-Hochberg.
  - **Output**: `results/stability_metrics.json`.

## Risk Mitigation

| Risk | Mitigation |
| :--- | :--- |
| **Dataset lacks Human Ratings** | `loader.py` checks for `preference_score` column immediately. If missing, the pipeline exits with a clear error message. No synthetic data is generated. |
| **BERT Inference too slow** | Use `distilbert-base-uncased` instead of `bert-base`. Limit sample size to 10k to ensure < 6h runtime. |
| **Zero Variance in Target** | `preprocess.py` checks variance before training. If zero, raises `ValueError`. |
| **Feature Extraction Fails** | `features.py` wraps extraction in `try/except`. Failed rows are logged and excluded, not imputed. |
| **Data Loader Errors** | `loader.py` removes `try/except` blocks that suppress errors. Fetch errors now raise explicit exceptions. |
| **Confounding Variables** | Include caption length and image complexity as covariates in the XGBoost model to isolate linguistic effects. |