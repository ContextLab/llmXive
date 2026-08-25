# Implementation Plan: llmXive follow-up: extending "Lens: Rethinking Training Efficiency for Foundational Text-to-Image Mo"

**Branch**: `001-llmxive-lens-extension` | **Date**: 2026-07-16 | **Spec**: `specs/001-llmxive-follow-up-extending-lens-rethink/spec.md`

## Summary

This feature implements a CPU-tractable pipeline to predict the "alignment gap" (deviation between CLIP scores and human ratings) in the 'pick-a-pic' dataset using only linguistic features of the text captions. The approach strictly adheres to the project constitution: no image generation is performed, no GPU is used for training, and all statistical rigor (permutation tests, FDR correction, sensitivity sweeps) is enforced. The pipeline extracts linguistic uncertainty (ln(perplexity)), syntactic depth, and noun-phrase density, then trains an XGBoost regressor to explain the deviation, controlling for caption length and complexity.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `transformers` (for BERT perplexity, `distilbert-base-uncased`), `spacy` (for dependency parsing), `xgboost` (for CPU-only training), `scikit-learn` (for metrics/splitting), `pandas`, `numpy`, `pyyaml`, `torch` (CPU-only for BERT inference), `ruff`, `black`.  
**Storage**: Local filesystem (`data/raw`, `data/processed`, `results`). No external DB.  
**Testing**: `pytest` with `pytest-cov`.  
**Target Platform**: Linux (GitHub Actions free-tier: A small number of CPU cores and 7 GB RAM).  
**Project Type**: Research pipeline / CLI.  
**Performance Goals**: End-to-end run < 6 hours on CPU; Memory < 7 GB.  
**Constraints**: Strict CPU-only for training; no image data in feature extraction; Z-score normalization for target (with fallback to rank-based if distributional assumptions fail); exclusion (not imputation) for short captions.  
**Scale/Scope**: Processing the full 'pick-a-pic' dataset (or a verified subset) via streaming to fit memory.

> **Note on Data**: The plan relies on the 'pick-a-pic' dataset. As per the "Verified datasets" block provided in the context, NO verified source URL exists for 'pick-a-pic'. The implementation will attempt to load it via the standard `datasets` library (if available on HF Hub) or a known canonical path. If the dataset is not fetchable programmatically without credentials, the system will halt with a `DataSchemaError` as mandated by FR-003, rather than fabricating data.

## Constitution Check

*GATE: Must pass before Phase 0 research.*

- **Principle I (Reproducibility)**: PASS. All random seeds pinned in `code/config.py`. Dependencies pinned in `requirements.txt`.
- **Principle II (Verified Accuracy)**: PASS. Dataset citations restricted to verified URLs or standard library loaders. No invented URLs. The plan halts if the standard loader fails, avoiding fabrication.
- **Principle III (Data Hygiene)**: PASS. Raw data immutable; processed data checksummed.
- **Principle IV (Single Source of Truth)**: PASS. All results derived from `data/processed` artifacts.
- **Principle V (Versioning Discipline)**: PASS. Content hashing of artifacts implemented; state file updated on artifact change via `state/projects/PROJ-925-llmxive-follow-up-extending-lens-rethink.yaml`.
- **Principle VI (Linguistic Feature Isolation)**: PASS. `code/data/features.py` explicitly forbids image imports. Covariates derived from text only.
- **Principle VII (CPU-Tractability)**: PASS. XGBoost used; `torch` restricted to CPU-only inference (quantized); no CUDA.

## Project Structure

### Documentation (this feature)

```text
specs/001-llmxive-follow-up-extending-lens-rethink/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/           # Phase 1 output
    ├── dataset.schema.yaml
    ├── feature_vector.schema.yaml
    ├── deviation_target.schema.yaml
    └── significance_results.schema.yaml
```

### Source Code (repository root)

```text
projects/PROJ-925-llmxive-follow-up-extending-lens-rethink/
├── code/
│   ├── data/
│   │   ├── loader.py          # Fetches pick-a-pic, validates schema
│   │   ├── features.py        # Extracts linguistic features (text-only)
│   │   └── preprocess.py      # Computes deviation target, handles exclusions
│   ├── models/
│   │   └── train.py           # XGBoost training, permutation tests, sensitivity sweeps
│   ├── utils/
│   │   ├── config.py          # Seeds, paths, hyperparameters
│   │   └── logging.py         # Structured logging
│   └── tests/
│       ├── unit/
│       ├── integration/
│       ├── contract/          # Schema validation tests
│       └── test_constitution.py # Static analysis for import guards
├── data/
│   ├── raw/                   # Downloaded parquet/jsonl (immutable)
│   └── processed/             # features.csv, deviation.csv, results.json
├── docs/
│   └── ...
└── requirements.txt
```

**Structure Decision**: Single project structure selected. The `code/` directory is split into `data/`, `models/`, and `utils/` to enforce the separation of concerns mandated by the spec (feature extraction vs. target calculation vs. model training). This aligns with the "Linguistic Feature Isolation" principle.

## Complexity Tracking

No complexity violations identified. The plan strictly follows the CPU-first, text-only constraints. The sensitivity analysis (FR-006) is computationally intensive but feasible within the 6-hour window via streaming and efficient XGBoost CPU execution.

## Task Breakdown

### Phase 0: Setup & Data Acquisition

- **T001**: Initialize project directory structure. Create `code/data`, `code/tests`, `code/utils`, `code/models`, `data/raw`, `data/processed`, `docs`.
- **T002**: Configure environment. Create `requirements.txt` with pinned versions. Note: `torch` included for CPU-only BERT inference, not GPU training.
- **T003**: Configure linting. Add `pyproject.toml` (Black settings) and `.ruff.toml`.
- **T004**: Define schema contracts. Create `dataset.schema.yaml`, `feature_vector.schema.yaml`, `deviation_target.schema.yaml`, `significance_results.schema.yaml` in `contracts/`.
- **T009**: Data Loading & Validation. Attempt to load 'pick-a-pic' via `datasets.load_dataset`. **If load fails**, raise `DataSchemaError` with message "Missing required dataset or column: pick-a-pic/human_rating" and halt. **If loaded**, verify presence of `caption`, `clip_score`, `human_rating`.

### Phase 1: Feature Extraction

- **T014**: Linguistic Feature Extraction. Implement `features.py`.
  - **Logic**: Iterate captions. Compute `linguistic_uncertainty_proxy` as `ln(perplexity)` using `distilbert-base-uncased` (masked mode). Compute `syntactic_depth` (spaCy). Compute `noun_phrase_density`, `caption_length_tokens`, `textual_complexity` (including `lexical_diversity` and `syntactic_variety`).
  - **Error Handling**: If BERT fails, catch exception, log `caption_id`, and exclude row (FR-012).
- **T015**: Short Caption Handling.
  - **Logic**: If a caption is too short to compute a meaningful dependency tree (e.g., < 3 tokens), **exclude** the sample from the training matrix. Log the `caption_id` and reason to `data/logs/exclusions.log`. Do **not** assign a default depth of 0.
- **T026**: Proxy Validation. Compute correlation between `linguistic_uncertainty_proxy` and a semantic entropy baseline (if available) on a held-out set. If $r < 0.3$, log a warning and flag the construct validity risk. (Acknowledge circularity risk if baseline is LLM-derived).

### Phase 2: Target Calculation

- **T021a**: CLIP Score Validation. Verify that `clip_score` is present in the dataset. **Do not generate** CLIP scores via inference. If missing, raise `DataSchemaError`.
- **T022**: Target Variable Calculation.
  - **Logic**: Compute Z-score normalization (subtract mean, divide by std) for `clip_score` and `human_rating`. **Distributional Check**: If distributions are non-Gaussian (Shapiro-Wilk p < 0.05), switch to rank-based inverse normal transformation (INT). Calculate `deviation_score` = $| Z(\text{CLIP}) - Z(\text{Human}) |$.
  - **Zero Variance Check**: If `deviation_score` has zero variance, halt with `ValueError("Target not learnable: zero variance detected")` (FR-010).
- **T025**: Join Features and Target. Merge feature matrix with deviation scores. Output `data/processed/deviation.csv`.

### Phase 3: Model Training & Analysis

- **T030**: XGBoost Training & Significance Testing.
  - **Logic**: Train XGBoost regressor (CPU-only). Compute permutation importance (test statistic = drop in MSE). Generate null distribution via permutations. Calculate p-values. Apply **Benjamini-Yekutieli** correction (for arbitrary dependence) to control FDR $\le 0.05$.
  - **Interaction Analysis**: Compute SHAP interaction values to detect feature interactions.
  - **Multicollinearity Check**: Compute VIF for features.
- **T031**: Fixed Iteration Count. Ensure $N=1,000$ permutations are used. No dynamic reduction.
- **T033**: Sensitivity Analysis.
  - **Threshold Sweep**: Repeat significance testing for a range of standard significance levels (e.g., conventional thresholds).
  - **Data Variance**: Repeat training with different random seeds (e.g., multiple seeds) to assess stability.
  - **Output**: JSON file `results/stability_metrics.json` with `mean_rank` and `std_dev_rank` for each feature across sweeps.
- **T042**: Noise Robustness Analysis (FR-008).
  - **Logic**: Inject Gaussian noise (as per spec) and heteroscedastic ordinal noise (for validity) into human ratings. Re-run regression. Compare feature importance stability.
  - **Output**: Separate section in `results/stability_metrics.json` for `noise_robustness_results`.

### Phase 4: Reporting & Constitution Enforcement

- **T045**: Constitution Enforcement Test Execution. Run `code/tests/test_constitution.py` to verify no image imports in `features.py` and no GPU usage in `train.py`. **Must pass** before marking T014/T029 complete.
- **T046**: Covariate Calculation. Ensure `caption_length_tokens` is calculated and included as a covariate (FR-007).

## Risk Management

- **Data Availability**: High risk. If 'pick-a-pic' is not fetchable, the project halts. No synthetic data is generated.
- **Methodological Validity**: Acknowledged risks regarding target variable construction and circular validation. Mitigated by sensitivity analyses and explicit reporting of limitations.
- **Compute Feasibility**: Low risk. CPU-only methods selected. Streaming used for large datasets.