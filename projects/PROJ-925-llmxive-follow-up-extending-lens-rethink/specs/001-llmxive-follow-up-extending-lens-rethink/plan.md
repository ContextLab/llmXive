# Implementation Plan: llmXive follow-up: extending "Lens: Rethinking Training Efficiency for Foundational Text-to-Image Mo"

**Branch**: `001-llmxive-lens-extension` | **Date**: 2026-07-16 | **Spec**: `specs/001-llmxive-follow-up-extending-lens-rethink/spec.md`

## Summary
This feature implements a CPU-tractable research pipeline to investigate the "alignment gap" between CLIP scores and human preferences. The system extracts linguistic features (uncertainty proxy, syntactic complexity, visual token density) from captions, calculates an alignment deviation score using a dataset with pre-computed CLIP scores (or a small-scale on-the-fly subset), and trains a Gradient Boosted Trees model (XGBoost) to predict this deviation. The plan strictly adheres to the "CPU-Tractability" and "Linguistic Feature Isolation" constitution principles, ensuring all operations run on standard CPU hardware without GPU dependencies.

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: `transformers` (for BERT perplexity), `spacy` (for syntactic parsing), `xgboost` (for CPU training), `pandas`, `numpy`, `scikit-learn` (for metrics/permutation), `datasets` (Hugging Face), `tracemalloc` (built-in for memory profiling), `time` (built-in for timing).
**Storage**: Local file system (`data/raw`, `data/processed`, `results`).
**Testing**: `pytest` with contract validation against YAML schemas.
**Target Platform**: Linux (GitHub Actions Free Tier: 2 CPU, ~7 GB RAM).
**Project Type**: Research Data Pipeline / Machine Learning.
**Performance Goals**: Feature extraction < 5s/caption; Training < 6h total; Memory < 7 GB.
**Constraints**: No GPU imports; No synthetic data substitution; Strict separation of text-only feature extraction from image/metadata processing.
**Scale/Scope**: 
- **Primary**: Dataset with pre-computed CLIP scores (e.g., LAION-CLIP-Subset) or verified pick-a-pic subset.
- **Fallback**: If no verified dataset is available, the pipeline halts with `DataSchemaError`. No synthetic data or alternative datasets are used.

## Constitution Check

| Principle | Status | Enforcement Mechanism |
| :--- | :--- | :--- |
| **I. Reproducibility** | PASS | Seeds pinned in `config.yaml`; `requirements.txt` pins versions; CI runs isolated; N=1000 permutation count pinned in `config.yaml`. |
| **II. Verified Accuracy** | PASS | Citations validated against primary sources; no hallucinated URLs; data source fallback is explicit (halt on error). |
| **III. Data Hygiene** | PASS | Checksums recorded; raw data immutable; derived data in new files. |
| **IV. Single Source of Truth** | PASS | All results trace to `data/processed` via `code/` scripts. |
| **V. Versioning Discipline** | PASS | `main.py` includes a post-run hook that computes SHA-256 of `data/processed` and updates `state/projects/...yaml` `updated_at` timestamp. |
| **VI. Linguistic Feature Isolation** | PASS | `features.py` explicitly blocks image/CLIP imports; inputs are text-only. 'Image Complexity' is replaced by 'visual_token_density' (text-derived). |
| **VII. CPU-Tractability** | PASS | `train.py` sets `torch.set_num_threads(1)`; XGBoost used (CPU-native); no CUDA; on-the-fly CLIP limited to N=1000. |

## Project Structure

### Directory Tree
```text
projects/PROJ-925-llmxive-follow-up-extending-lens-rethink/
├── code/
│   ├── data/
│   │   ├── __init__.py
│   │   ├── loader.py          # Fetches dataset (with pre-computed scores or small subset)
│   │   ├── features.py        # Extracts linguistic vectors (Text only)
│   │   └── preprocess.py      # Calculates deviation, handles missing data
│   ├── models/
│   │   ├── __init__.py
│   │   └── train.py           # XGBoost CPU training & permutation test
│   ├── utils/
│   │   ├── config.py          # Seeding, paths, constants (N=1000 pinned)
│   │   └── validation.py      # Schema validation helpers
│   └── main.py                # Orchestration, profiling, versioning hook
├── data/
│   ├── raw/                   # Downloaded datasets (immutable)
│   └── processed/             # features.csv, deviation.csv, results/
├── tests/
│   ├── contract/              # Tests for schema validation (pytest)
│   ├── integration/           # End-to-end pipeline tests
│   └── unit/                  # Feature extraction logic tests
├── docs/
├── results/                   # Model outputs, logs, stability metrics
├── requirements.txt
├── .ruff.toml
├── pyproject.toml
└── README.md
```

**Structure Decision**: Standard research pipeline structure. `code/data` handles ingestion and transformation, `code/models` handles training. Strict separation ensures Principle VI compliance. `main.py` handles profiling and versioning. Note: `specs/.../contracts/` contains the YAML schema definitions, while `tests/contract/` contains the Python pytest fixtures that validate data against these schemas.

### Linting & Formatting
- **Tooling**: `ruff` for linting, `black` for formatting.
- **Config**: `pyproject.toml` contains Black settings; `.ruff.toml` contains linting rules.
- **Enforcement**: CI runs `ruff check` and `black --check` before tests.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **Permutation Test (N=1000)** | Required by FR-006 for significance. Pinned in `config.yaml` for reproducibility (Principle I). | Random sampling of features is insufficient; null distribution requires rigorous resampling to control FDR. |
| **BERT Perplexity** | Required by FR-001 for uncertainty proxy. | Simple token counts (e.g., entropy) do not capture semantic uncertainty; BERT provides necessary depth. |
| **Streaming Data** | Dataset may exceed available RAM. | Loading full dataset into memory risks OOM; streaming allows processing of full scale within limits. |
| **Visual Token Density** | Required by FR-007 to control for image complexity. | Direct image processing violates Principle VI; text-derived proxy is the only compliant alternative. |
| **Strict Data Fallback** | Required to satisfy Principle II. | Using synthetic data or unverified datasets would invalidate the research question and violate data hygiene. |

## Implementation Phases

### Phase 1: Data Ingestion & Validation
- **Action**: `loader.py` fetches the dataset.
- **Constraint**: If 'pick-a-pic' is used, limit to N=1000 samples for on-the-fly CLIP inference. If pre-computed dataset available, load full.
- **Validation**: Check for `clip_score` and `human_rating` columns. Raise `DataSchemaError` if missing. **If the dataset source is unreachable or missing required columns, the pipeline halts immediately with a loud error.** No synthetic fallbacks are permitted.

### Phase 2: Feature Extraction (Text-Only)
- **Action**: `features.py` extracts:
  - `linguistic_uncertainty_proxy` (ln(perplexity))
  - `syntactic_depth` (max dependency depth)
  - `noun_phrase_density`
  - `visual_token_density` (ratio of noun phrases to total tokens, proxy for image complexity per FR-007)
  - `caption_length`
- **Constraint**: No image imports. `torch.set_num_threads(1)` enforced.
- **Logic**: Stream dataset in batches. Validate output against `feature_vector.schema.yaml`. Handle short captions by assigning default minimum depth or excluding with logging.

### Phase 3: Target Calculation & Profiling
- **Action**: `preprocess.py` calculates `deviation_score` = |normalized(clip) - normalized(human)|.
- **Validation**: Check for zero variance in target; raise `ValueError("Target not learnable")` if found.
- **Profiling**:
  - **Memory**: `tracemalloc` in `main.py` logs peak RSS to `results/memory_profile.json` (SC-002).
  - **Time**: `time` module in `main.py` logs wall-clock duration to `results/timing_profile.json` (SC-003).

### Phase 4: Modeling & Significance
- **Action**: `train.py` trains XGBoost.
- **Significance**:
  - **Feature Permutation**: For each feature $X_j$, shuffle values $N=1000$ times (keeping $Y$ fixed) to generate null distribution for importance. Calculate p-values and apply Benjamini-Hochberg correction.
  - **Stability Analysis**: Iterate over multiple random seeds (e.g., a small set of seeds). For each seed, train model and record feature importance ranks. Compute mean rank and standard deviation. Output `results/stability_metrics.json`.
  - **Sensitivity (FR-008)**: Inject Gaussian noise (sigma=0.01, 0.05, 0.1) into human ratings. Re-train model for each noise level. Aggregate: Compute Spearman rank correlation of feature importance vectors across noise levels.
- **Output**: `results/significance_results.json`, `results/stability_metrics.json`.

### Phase 5: Versioning & Output
- **Action**: `main.py` post-run hook.
- **Mechanism**: Compute SHA-256 of `data/processed` files. Update `state/projects/...yaml` `updated_at` and `artifact_hashes`.
- **Output**: Final results files.

## Risk Mitigation

| Risk | Mitigation |
| :--- | :--- |
| **Data Unavailability** | **HALT**: If verified dataset is missing, raise `DataSchemaError` and exit. No fallback to synthetic data. |
| **Circularity** | Reframe as 'text-driven metric instability'; use Text Permutation Null Model. |
| **OOM/Time Out** | Streaming data; strict N=1000 limit for on-the-fly CLIP; `tracemalloc` monitoring. |
| **Confounds** | Use `visual_token_density` (text-derived) to satisfy FR-007 without violating Principle VI. |