# Implementation Plan: 001-perceived-control-anxiety

**Branch**: `001-perceived-control-anxiety` | **Date**: 2024-05-21 | **Spec**: `specs/001-the-impact-of-perceived-control-over-dig/spec.md`
**Input**: Feature specification from `/specs/001-the-impact-of-perceived-control-over-dig/spec.md`

## Summary

This feature implements a computational pipeline to test the hypothesis that perceived control over digital interface elements (proxied by metadata) correlates with reduced anxiety markers in public social media traces. The approach involves ingesting a social media dataset, applying a CPU-tractable pre-trained NLP model for anxiety scoring (FR-002), extracting metadata-based control proxies strictly independent of text content (FR-003), and performing statistical correlation analysis with robustness checks (FR-004). The pipeline is designed to run entirely on a GitHub Actions free-tier runner (CPU-only, ≤7GB RAM) by utilizing efficient data sampling and lightweight inference.

## Technical Context

**Language/Version**: Python 3.10  
**Primary Dependencies**: `datasets` (HuggingFace), `transformers` (CPU-only), `scikit-learn`, `pandas`, `matplotlib`, `seaborn`, `requests`  
**Storage**: Local CSV/Parquet files under `data/` (raw and processed)  
**Testing**: `pytest` with `pytest-cov`  
**Target Platform**: Linux (GitHub Actions runner)  
**Project Type**: Computational Research Pipeline / CLI  
**Performance Goals**: Complete ingestion, inference, and analysis on a sample of ~10k posts within 6 hours on 2 CPU cores. Memory usage < 6GB.  
**Constraints**: No GPU/CUDA; no deep learning training; strict separation of metadata and text processing pipelines; p-value threshold for significance.  
**Scale/Scope**: Single dataset analysis; [deferred] to [deferred] rows depending on dataset availability and memory constraints.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Principle I (Reproducibility)**: Plan mandates pinned `requirements.txt` and random seed setting in all random operations (data sampling, model inference if applicable). External datasets will be fetched via canonical HuggingFace `load_dataset` calls.
- **Principle II (Verified Accuracy)**: All dataset and model citations in `research.md` will be cross-referenced against the `# Verified datasets` block provided at runtime. No hallucinated URLs.
- **Principle III (Data Hygiene)**: Pipeline will download raw data to `data/raw/` with checksums. Processed data (anxiety scores, control proxies) will be written to `data/processed/` as new files. No in-place modification.
- **Principle IV (Single Source of Truth)**: The `data/processed/final_analysis.csv` will be the sole source for the correlation statistics and visualization. The paper will reference this file directly.
- **Principle V (Versioning)**: All artifacts (data, code outputs) will be hashed. The plan includes steps to record these in `state/` (handled by the mechanical step).
- **Principle VI (Measurement Independence)**: The plan explicitly separates the `anxiety_scoring` module (text-only) from the `control_proxy_extraction` module (metadata-only). No text features will be used to derive `control_proxy`.
- **Principle VII (Operationalization)**: The `control_proxy` will be strictly defined as a function of `filter_applied` flags and `timestamp_regularity`, implemented in a dedicated module `code/services/proxy_extractor.py`.

## Project Structure

### Documentation (this feature)

```text
specs/001-the-impact-of-perceived-control-over-dig/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/           # Phase 1 output
    ├── dataset.schema.yaml
    └── analysis.schema.yaml
```

### Source Code (repository root)

```text
code/
├── __init__.py
├── config.py                # Global config, seeds, paths
├── main.py                  # Pipeline orchestrator
├── services/
│   ├── __init__.py
│   ├── data_ingestion.py    # FR-001: Download and cache dataset
│   ├── anxiety_scoring.py   # FR-002: NLP inference (CPU)
│   └── proxy_extractor.py   # FR-003: Metadata extraction
├── analysis/
│   ├── __init__.py
│   └── statistical_test.py  # FR-004: Correlation & normality check
└── viz/
    └── plot_results.py      # FR-005: Scatter plot generation

tests/
├── unit/
│   ├── test_anxiety_scoring.py
│   └── test_proxy_extractor.py
└── integration/
    └── test_pipeline.py

requirements.txt
```

**Structure Decision**: Single project structure (`code/`) selected to minimize overhead. Separation of concerns achieved via `services/` (data processing), `analysis/` (statistics), and `viz/` (plotting) modules. This aligns with Constitution Principle VI by keeping `anxiety_scoring.py` and `proxy_extractor.py` distinct.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | The pipeline is linear: Ingest -> Score -> Extract -> Analyze -> Plot. No complex orchestration or distributed computing is required. | N/A |

## Phase Breakdown

### Phase 0: Research & Dataset Validation
- **Goal**: Identify a verified social media dataset containing both text and metadata (timestamps, flags).
- **FR-001 Mapping**: Select dataset from verified sources (HuggingFace). Confirm it has `text`, `timestamp`, `user_id`, and `filter_applied` (or similar) fields.
- **FR-002 Mapping**: Identify a pre-trained anxiety model (e.g., `cardiffnlp/twitter-roberta-base-emotion` or similar) that runs on CPU and outputs probabilities.
- **SC-004/SC-005 Mapping**: Verify that the model inference on 10k samples fits within 6 hours and 7GB RAM. If not, plan for random sampling or chunked processing.
- **Constraint Check**: Ensure no dataset requires manual login or non-public access.

### Phase 1: Data Model & Contracts
- **Goal**: Define the schema for raw and processed data.
- **FR-003 Mapping**: Define `control_proxy` calculation logic in the data model.
- **FR-006 Mapping**: Define `confidence_score` field and exclusion logic (threshold 0.6).
- **Output**: `contracts/dataset.schema.yaml` and `contracts/analysis.schema.yaml`.

### Phase 2: Implementation (Orchestrated by Implementer Agent)
- **Step 1**: `data_ingestion.py` downloads data, checks checksum, saves to `data/raw/`.
- **Step 2**: `anxiety_scoring.py` loads model, filters non-English (if possible via metadata or simple check), infers scores, saves to `data/processed/scoring_results.csv` (corresponding to `AnxietyScoreRecord`).
- **Step 3**: `proxy_extractor.py` reads `data/raw/`, calculates `control_proxy`, saves to `data/processed/proxy_results.csv` (corresponding to `ControlProxyRecord`).
- **Step 4**: Merge results, filter by confidence >= 0.6 (FR-006).
- **Step 5**: `statistical_test.py` runs Shapiro-Wilk on marginal distributions of `anxiety_score` and `control_proxy`, chooses Pearson/Spearman, calculates r and p-value.
- **Step 6**: `plot_results.py` generates scatter plot with regression line.
- **Step 7**: Save final merged data to `data/processed/final_analysis.csv`.

### Phase 3: Verification & Reporting
- **Goal**: Validate results against Success Criteria.
- **SC-001**: Check row count of scored data (>= 95% of non-null).
- **SC-002/SC-003**: Verify output of r and p-value, check significance.
- **Constitution VI**: Audit code to ensure no text data leaks into `proxy_extractor`.

## Compute Feasibility Note

The plan explicitly avoids GPU/CUDA. The anxiety model will be loaded in default precision (float32) or lower if the library supports it without quantization libraries. Data processing will use `pandas` with chunking if necessary to stay within available RAM constraints. The total runtime is estimated to be < 2 hours for 10k samples on a 2-core CPU, well within the 6-hour limit.
