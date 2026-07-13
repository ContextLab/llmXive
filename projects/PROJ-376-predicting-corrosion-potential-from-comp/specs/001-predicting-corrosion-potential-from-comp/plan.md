# Implementation Plan: Predicting Corrosion Potential from Composition and Environment

**Branch**: `001-predict-corrosion-potential` | **Date**: 2024-05-21 | **Spec**: `specs/001-predicting-corrosion-potential-from-comp/spec.md`
**Input**: Feature specification from `/specs/001-predicting-corrosion-potential-from-comp/spec.md`

## Summary

This project implements a data-driven pipeline to predict corrosion potential (E_corr) of metallic alloys based on elemental composition and environmental conditions (pH, temperature). The approach involves ingesting data from a **single verified source**, performing a rigorous "Compositional Clustering" (Leave-One-Cluster-Out) split to prevent data leakage, training CPU-optimized ensemble models (Random Forest, Gradient Boosting), and conducting statistical significance testing on feature importances using a permutation-based approach. The pipeline is designed to run entirely on CPU-only GitHub Actions runners within a limited time window.

**Critical Note on Data & Spec Contradictions**: 
1. **No Merging Strategy**: The project explicitly rejects the "fuzzy match" merge between Materials Project (DFT) and NIST (Experimental) mandated in the source spec. This merge is scientifically invalid due to the category error between computed ground states and dynamic electrochemical measurements. If no single verified dataset contains the joint distribution of (Composition, Environment, Corrosion), the pipeline **halts** with a `DataInsufficientError`.
2. **No Imputation**: The project rejects the "median imputation" of missing pH mandated in the source spec. Missing pH records are **excluded** to preserve environmental variance.
3. **Split Strategy**: The project replaces the "Leave-One-Alloy-Family-Out" (base metal) split mandated in the source spec with "Compositional Clustering" (Leave-One-Cluster-Out) to ensure true generalization to unseen compositions.
4. **Permutation Count**: The project increases the permutation count to 2000 (vs. 100 in spec) to ensure statistical power.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `scikit-learn`, `pandas`, `requests`, `numpy`, `matplotlib`, `seaborn`, `pyyaml`, `huggingface_hub`  
**Storage**: Local filesystem (`data/` for raw/processed data, `code/` for scripts)  
**Testing**: `pytest` (unit tests for data transformers, integration tests for pipeline flow)  
**Target Platform**: GitHub Actions `ubuntu-latest` (CPU-only, ~7GB RAM)  
**Project Type**: Data Science Pipeline / CLI  
**Performance Goals**: Complete full training/evaluation cycle in < 6 hours; model inference < 5 seconds for new samples.  
**Constraints**: No GPU usage; **No Materials Project API calls** (rejected as invalid); strict adherence to "no composition leakage" in splits.  
**Scale/Scope**: Target dataset size in the range of hundreds to thousands of records (dependent on public data availability); models trained on < 10,000 rows.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Action/Note |
|-----------|--------|-------------|
| **I. Reproducibility** | **PASS** | Plan mandates pinned `random_state` in all sklearn estimators and data splitting. External data sources are defined by URL in `research.md`. CI uses `MOCK_DATA=1` to load `tests/fixtures/mock_corpus.json` for reproducibility without live API calls. |
| **II. Verified Accuracy** | **PASS** | All dataset URLs in `research.md` are restricted to the verified list provided in the prompt. **If the schema check fails (e.g., missing fields in the verified NIST source), the pipeline halts immediately.** No "Simulation Mode" or synthetic data fallback is used, as this would violate Verified Accuracy. |
| **III. Data Hygiene** | **PASS** | Plan includes checksumming steps for raw data downloads. No in-place modifications; derived data written to new files with versioned names. |
| **IV. Single Source of Truth** | **PASS** | Final metrics (R², RMSE) will be generated programmatically and stored in `data/results/model_metrics.json`, and feature importance in `data/results/feature_importance.json`, which the paper will reference. |
| **V. Versioning Discipline** | **PASS** | Artifacts (data, models) will be tracked via content hashes in the project state file. |
| **VI. Composition-Environment Feature Integrity** | **PASS** | Plan explicitly defines feature engineering to use only weight fractions and categorical/numerical environmental variables, excluding unverified microstructural proxies. |
| **VII. Leakage-Aware Validation Strategy** | **PASS** | The plan mandates a "Compositional Clustering" split (Leave-One-Cluster-Out) as the *only* valid splitting strategy. Random shuffling is prohibited. A minimum cluster count (>=3) is enforced to ensure statistical validity. |

## Project Structure

### Documentation (this feature)

```text
specs/001-predicting-corrosion-potential-from-comp/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-376-predicting-corrosion-potential-from-comp/
├── code/
│   ├── __init__.py
│   ├── data/
│   │   ├── __init__.py
│   │   ├── ingest.py          # Downloads and validates raw data
│   │   ├── preprocess.py      # Cleans, excludes missing pH, encodes
│   │   ├── split.py           # Compositional Clustering implementation (Hierarchical Agglomerative Clustering on composition)
│   ├── models/
│   │   ├── __init__.py
│   │   ├── train.py           # RF and GB training logic
│   │   ├── evaluate.py        # Metrics and baselines
│   │   └── interpret.py       # Permutation importance & PDP (2000 permutations)
│   └── main.py                # Orchestration script
├── data/
│   ├── raw/                   # Downloaded raw files (checksummed)
│   ├── processed/             # Cleaned/merged datasets
│   └── results/               # Model outputs and logs
├── tests/
│   ├── unit/
│   │   ├── test_preprocess.py
│   │   └── test_split.py
│   ├── integration/
│   │   └── test_pipeline.py
│   └── fixtures/
│       └── mock_corpus.json   # Verified mock data for CI (matches schema)
├── requirements.txt
└── README.md
```

**Structure Decision**: A modular `code/` directory with separation of concerns (data, models, main) is selected to ensure testability and adherence to the Reproducibility principle. The `data/` directory is split into `raw` and `processed` to enforce Data Hygiene (no in-place modification). The `tests/fixtures/mock_corpus.json` ensures CI reproducibility via the `MOCK_DATA=1` flag.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Compositional Clustering (LOAO) over Random Split** | Required by FR-004 and Constitution Principle VII to prevent data leakage where the model memorizes specific alloy compositions rather than learning generalizable composition-environment relationships. | A random split would likely result in the same alloy appearing in both train and test sets, inflating R² scores artificially and failing to validate generalization to *new* alloy compositions. |
| **Hierarchical Agglomerative Clustering for Split** | Required to derive `cluster_id` from `composition` (weight fractions) using cosine similarity (threshold defined by a high-similarity criterion). This replaces the "Alloy Family" definition in the spec, which is insufficient to prevent leakage. | Using "Alloy Family" (e.g., Fe-based) allows similar alloys (SS304 vs SS316) to leak between splits, invalidating the test set. |
| **Statistical Significance Testing (2000 Permutations)** | Required by SC-003 to distinguish true feature drivers from noise. 100 permutations (as in spec) are underpowered. | Relying solely on model-provided feature importance (e.g., Gini importance) is biased towards high-cardinality features and does not provide p-values for scientific rigor. |
| **Two-Model Comparison (RF vs GB)** | Required by FR-005 to identify the most robust algorithm for this specific data distribution. | Using a single model type risks suboptimal performance if that model is ill-suited to the non-linear interactions present in corrosion data. |
| **No Merge Strategy** | Required by scientific validity. | Merging Materials Project (DFT) and NIST (Experimental) creates a category error and invalidates the target variable definition. |
| **Exclusion of Missing pH** | Required to prevent bias. | Imputing pH with a median value destroys the variance required to learn composition-environment interactions. |
| **Pipeline Halt on Data Mismatch** | Required by Constitution Principle II (Verified Accuracy). | Fallback to synthetic data or "Simulation Mode" would invalidate scientific claims and violate the requirement for verified accuracy. |