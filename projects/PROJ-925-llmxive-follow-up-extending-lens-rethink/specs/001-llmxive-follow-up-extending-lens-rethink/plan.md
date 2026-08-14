# Implementation Plan: llmXive follow-up: extending "Lens: Rethinking Training Efficiency for Foundational Text-to-Image Mo"

**Branch**: `001-llmxive-lens-extension` | **Date**: 2026-07-16 | **Spec**: `specs/001-llmxive-follow-up-extending-lens-rethink/spec.md`
**Input**: Feature specification from `specs/001-llmxive-follow-up-extending-lens-rethink/spec.md`

## Summary

This feature implements a CPU-tractable pipeline to investigate the "alignment gap" between CLIP scores and human preference ratings using the 'pick-a-pic' dataset. The approach involves a distinct preprocessing phase (Phase 0) to generate missing scores, extracting linguistic features (uncertainty, complexity) from captions, calculating a deviation target, and training a Gradient Boosted Trees model (XGBoost) to predict this deviation. The plan strictly adheres to CPU-only constraints, avoids image processing in feature extraction, and implements rigorous statistical validation (permutation tests, FDR correction, Ridge regression for collinearity) as required by the specification.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `xgboost`, `scikit-learn`, `spacy`, `transformers`, `pandas`, `datasets`, `numpy`, `pyyaml`, `entropy`, `pytest`, `ruff`, `black`  
**Storage**: Local filesystem (`data/raw`, `data/processed`, `results`) with CSV/JSONL formats.  
**Testing**: `pytest` with `pytest-cov` and custom static analysis for constitution enforcement (validating imports against `contracts/` schemas).  
**Target Platform**: Linux (GitHub Actions Free Tier: vCPU, 7GB RAM).  
**Project Type**: Data Science Research Pipeline / CLI.  
**Performance Goals**: End-to-end pipeline < 6 hours on CPU; Feature extraction < 5s/caption.  
**Constraints**: No GPU usage; No image data in `features.py`; Strict error handling for missing data (no synthetic fallbacks).  
**Scale/Scope**: Full 'pick-a-pic' dataset (streamed) or a stratified sample (N=10,000 minimum) to ensure statistical power.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Principle I (Reproducibility)**: PASS. Plan includes pinned seeds, explicit dataset loading via `datasets` library, and `requirements.txt` generation.
- **Principle II (Verified Accuracy)**: PASS. All dataset references will be validated against the "# Verified datasets" block before use.
- **Principle III (Data Hygiene)**: PASS. Plan mandates checksumming of downloaded data and separation of raw/processed files.
- **Principle IV (Single Source of Truth)**: PASS. Every result in `results/` will be traced to a specific `caption_id` in `data/processed/`. A `state.yaml` file will record content hashes of all input and output artifacts to ensure versioning discipline. Every figure, statistic, or interpretation in the paper MUST trace back to exactly one row in this project's `data/` and one block in this project's `code/`.
- **Principle V (Versioning Discipline)**: PASS. Every artifact change updates the `state.yaml` timestamp. Content hashes are recorded in `state.yaml` to invalidate stale review records. Every artifact under this project carries a content hash.
- **Principle VI (Linguistic Feature Isolation)**: PASS. `features.py` design explicitly forbids image imports; `test_constitution.py` will enforce this via static analysis and schema validation against `contracts/feature_vector.schema.yaml`.
- **Principle VII (CPU-Tractability)**: PASS. Plan specifies `torch.set_num_threads(1)` and XGBoost CPU-only configuration; no CUDA dependencies planned.

## Project Structure

### Documentation (this feature)

```text
specs/001-llmxive-follow-up-extending-lens-rethink/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── dataset.schema.yaml          # Exercised by US-2, Phase 0 (Raw Input)
│   ├── feature_vector.schema.yaml   # Exercised by US-1, Phase 1 (Features)
│   ├── deviation_target.schema.yaml # Exercised by US-2, Phase 2 (Target)
│   └── significance_results.schema.yaml # Exercised by US-3, Phase 4 (Results)
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-925-llmxive-follow-up-extending-lens-rethink/
├── code/
│   ├── __init__.py
│   ├── config.py              # Configuration & seeds
│   ├── data/
│   │   ├── __init__.py
│   │   ├── loader.py          # Data fetching (streaming)
│   │   ├── features.py        # Linguistic feature extraction
│   │   ├── preprocess.py      # Target calculation & validation
│   │   ├── scores.py          # CLIP score generation (Phase 0)
│   │   └── train.py           # Model training & evaluation
│   ├── utils/
│   │   ├── __init__.py
│   │   └── stats.py           # Permutation tests, FDR, Ridge
│   └── tests/
│       ├── __init__.py
│       ├── test_constitution.py # Static analysis for imports & schemas (validates against contracts/)
│       ├── contract/
│       │   └── test_schemas.py  # Schema validation tests
│       └── unit/
│           ├── test_features.py
│           └── test_preprocess.py
├── data/
│   ├── raw/                   # Downloaded datasets (checksummed)
│   └── processed/             # Features, targets, deviations
├── results/                   # Model outputs, logs, stability metrics
├── docs/
└── requirements.txt
```

**Structure Decision**: The single-project structure is selected to maintain tight coupling between data loading, feature engineering, and model training, which is essential for the research pipeline's reproducibility. The separation of `data/`, `code/`, and `results/` adheres to standard data science hygiene principles (Principle III).

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | The plan adheres to a linear, single-pipeline flow. | N/A |

## Phase Mapping to Contracts

- **Phase 0 (Data Preprocessing & Score Generation)**: Validates `dataset.schema.yaml` (raw input) and generates `deviation_target.schema.yaml` (intermediate scores). **Exercises US-2**.
- **Phase 1 (Feature Extraction)**: Validates `feature_vector.schema.yaml` (text-only features). **Exercises US-1**.
- **Phase 2 (Target Calculation)**: Validates `deviation_target.schema.yaml` (final target). **Exercises US-2**.
- **Phase 3 (Model Training)**: Validates `deviation_target.schema.yaml` (input) and `significance_results.schema.yaml` (output). **Exercises US-3**.
- **Phase 4 (Statistical Rigor)**: Validates `significance_results.schema.yaml` (permutation/FDR results). **Exercises US-3**.

## Directory Structure Verification (T001)

The following directories and files MUST exist in the repository root:
- `projects/PROJ-925-llmxive-follow-up-extending-lens-rethink/code/`
- `projects/PROJ-925-llmxive-follow-up-extending-lens-rethink/code/data/`
- `projects/PROJ-925-llmxive-follow-up-extending-lens-rethink/code/tests/`
- `projects/PROJ-925-llmxive-follow-up-extending-lens-rethink/code/utils/`
- `projects/PROJ-925-llmxive-follow-up-extending-lens-rethink/data/raw/`
- `projects/PROJ-925-llmxive-follow-up-extending-lens-rethink/data/processed/`
- `projects/PROJ-925-llmxive-follow-up-extending-lens-rethink/docs/`
- `projects/PROJ-925-llmxive-follow-up-extending-lens-rethink/requirements.txt`
- `projects/PROJ-925-llmxive-follow-up-extending-lens-rethink/.ruff.toml` (or `pyproject.toml` with Black settings)
