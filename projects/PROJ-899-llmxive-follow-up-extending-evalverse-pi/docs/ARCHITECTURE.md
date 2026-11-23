# Architecture: llmXive Feature Distillation Pipeline

## Design Principles
1. **Reproducibility**: All data sources and random seeds are explicitly configured.
2. **CPU-First**: No GPU dependencies; optimized for multi-core CPU execution.
3. **Modularity**: Distinct phases for data, features, models, and reports.
4. **Gate-Driven**: Validation gates (T040, T041, T021) enforce quality before proceeding.

## Component Overview

### Data Layer (`code/src/data/`)
- **download.py**: Fetches and verifies EvalVerse dataset from Zenodo.
- **preprocess.py**: Extracts optical flow, HOG, and audio features (Librosa/OpenCV).
- **models.py**: Data structures (`VideoClip`, `FeatureVector`, `DimensionScore`).
- **profiles.py**: Memory and timing profiling using `psutil`.

### Model Layer (`code/src/models/`)
- **train.py**: Ridge, Lasso, and XGBoost training pipelines.
- **metrics.py**: Pearson/Spearman correlation, bootstrapping, permutation tests.
- **evaluate.py**: Baseline comparisons, scaling validation, sensitivity analysis.

### Report Layer (`code/src/reports/`)
- **generate.py**: Produces JSON/CSV reports from analysis results.

### CLI Layer (`code/src/cli/` & `code/scripts/`)
- **run_pipeline.py**: Orchestrates the full pipeline.
- **generate_*.py**: Specialized scripts for timing and sensitivity reports.

## Data Flow
1. **Fetch**: Raw data downloaded to `data/raw/`.
2. **Preprocess**: Features extracted to `data/processed/`.
3. **Train**: Models trained on processed features.
4. **Evaluate**: Correlations calculated, baselines compared.
5. **Profile**: Memory/time metrics collected and projected.
6. **Report**: Final artifacts written to `reports/` and `data/`.

## Gate Logic
- **T040 (Quality Gate)**: Excludes samples with error rate > 5%.
- **T041 (Validation Gate)**: Halts if VLM proxy correlation < 0.70.
- **T021 (Feasibility Gate)**: Halts if peak memory > 7GB or projected time > 6h.

## Extensibility
New feature extractors or models can be added by implementing the corresponding interface in `preprocess.py` or `train.py` and updating the pipeline script.
