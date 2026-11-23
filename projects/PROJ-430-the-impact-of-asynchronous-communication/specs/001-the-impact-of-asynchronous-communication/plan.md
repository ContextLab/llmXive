# Implementation Plan: Asynchronous Communication Delays and Team Cohesion

**Branch**: `001-asynchronous-delays-cohesion` | **Date**: 2024-05-21 | **Spec**: `specs/001-the-impact-of-asynchronous-communication/spec.md`
**Input**: Feature specification from `/specs/001-the-impact-of-asynchronous-communication/spec.md`

## Summary

This project investigates the **association** between response-time variability in asynchronous communication channels and perceived team cohesion in distributed software teams. 

**Critical Methodological Update**: Addressing the ecological fallacy concern (methodology-7eaac9), the primary analysis is now performed at the **Contributor Pair level** (N = pairs). We model pair-level delay variance against pair-level sentiment using Hierarchical Linear Modeling (HLM) to account for project-level clustering. Project-level aggregation (median) is retained only as a secondary robustness check.

The technical approach involves ingesting GitHub event data, deriving temporal metrics per pair, applying VADER sentiment analysis to English-only comments, and performing statistical correlation and regression analysis while controlling for confounders. The pipeline is designed to run on a CPU-first GitHub Actions runner.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `numpy`, `scikit-learn`, `vaderSentiment`, `langdetect`, `requests`, `matplotlib`, `seaborn`, `pyyaml`, `statsmodels`, `pylmm` (or `statsmodels` mixedlm)  
**Storage**: Local file system (CSV/Parquet) under `data/`  
**Testing**: `pytest`  
**Target Platform**: Linux (GitHub Actions Free Tier)  
**Project Type**: Data Analysis Pipeline / Research Script  
**Performance Goals**: Complete analysis within 6 hours; peak RAM < 6.0 GB.  
**Constraints**: No local GPU; must handle API rate limits; must exclude bot events; must filter non-English text.  
**Scale/Scope**: Sample of active open-source projects (sample size deferred to research phase).

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **I. Reproducibility**: The plan mandates pinning random seeds in `code/` and fetching datasets from canonical sources (GitHub API, VADER PyPI) on every run. A `code/utils/checksums.py` script generates SHA-256 hashes for all data artifacts and updates the `state` file automatically.
- **II. Verified Accuracy**: All citations in `research.md` and `data-model.md` are validated against the `# Verified datasets` block (defined in research.md) before execution.
- **III. Data Hygiene**: All files in `data/` will be checksummed. Raw data is immutable; derivations create new files. PII scanning is enforced.
- **IV. Single Source of Truth**: All figures and statistics in the final output will trace back to specific rows in `data/derived/` and code blocks in `code/`.
- **V. Versioning Discipline**: Artifacts will carry content hashes; the `state` file will be updated automatically by `code/utils/checksums.py` upon artifact generation.
- **VI. Modality Separation**: The pipeline explicitly separates timestamp parsing (Phase 1) from text sentiment analysis (Phase 2), storing intermediate features in distinct files (`timestamp_features.parquet` vs `sentiment_features.parquet`) to prevent circularity.

## Project Structure

### Documentation (this feature)

```text
specs/001-asynchronous-delays-cohesion/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── project_metrics.schema.yaml
│   ├── statistical_results.schema.yaml
│   ├── dataset.schema.yaml
│   └── pair_metrics.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-430-the-impact-of-asynchronous-communication/
├── code/
│   ├── __init__.py
│   ├── ingestion.py           # T010, T011: Fetch & Filter
│   ├── metrics.py             # T015: Pair-level calculations
│   ├── sentiment.py           # T021: VADER analysis
│   ├── analysis.py            # T031-T035: HLM & Regression
│   ├── validation.py          # T023, T023a: Validation logic
│   └── utils/
│       ├── checksums.py       # T003: Hashing
│       └── config.py          # T003: Config loading
├── data/
│   ├── raw/                   # T010: Raw API JSON
│   ├── derived/               # T015, T021, T035: Parquet/JSON
│   ├── validation/            # T022: Manual ground truth (if exists)
│   └── logs/                  # T016: Rate limit & error logs
├── tests/
│   ├── unit/                  # Unit tests for functions
│   └── integration/           # End-to-end pipeline tests
├── config/
│   ├── pyproject.toml         # T003: Linting/Formatting config
│   └── .pre-commit-config.yaml
├── requirements.txt
└── README.md
```

**Structure Decision**: A modular Python script structure is chosen to ensure testability and separation of concerns (Ingestion, Metrics, Sentiment, Analysis). This aligns with the requirement for reproducible, isolated stages.

## Configuration & Linting

- **Linting**: `ruff` configured in `pyproject.toml`.
- **Formatting**: `black` configured in `pyproject.toml`.
- **Pre-commit**: `pre-commit` hooks enforced via `.pre-commit-config.yaml`.
- **Environment**: `python -m venv venv` with `requirements.txt` pinned.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Modality Separation (Constitution VI) | Prevents circularity where timestamp extraction could influence sentiment scoring. | A single monolithic script would mix parsing logic, risking data leakage and violating the "phenomenon-vs-method" validation. |
| Rate Limit Handling | GitHub API imposes strict limits; unhandled requests cause pipeline failure. | Simple retries without exponential backoff or chunking would fail on large datasets (>100k events). |
| Multi-modal Validation (FR-009) | Required to establish construct validity of the VADER proxy. | Relying solely on VADER without manual ground truth correlation would fail SC-005. The pipeline now includes a conditional gate for external data and a synthetic fallback. |
| VIF Halt Condition (FR-008) | Prevents unstable regression coefficients. | Proceeding with high collinearity would produce misleading results. The pipeline halts and logs to `data/logs/vif_halt_warning.log`. |
| Pair-Level Analysis (Methodology) | Resolves ecological fallacy by modeling at the interaction level. | Project-level aggregation loses the relationship between specific pairs' delays and sentiments. |

## Implementation Phases

### Phase 0: Setup & Verification
- **Task 0.1**: Initialize environment, install dependencies (`requirements.txt`).
- **Task 0.2**: Verify `# Verified datasets` block in `research.md` is complete.
- **Task 0.3**: Run `code/utils/checksums.py` to initialize state tracking.
- **Task 0.4**: Verify `pyproject.toml` and `.pre-commit-config.yaml` exist and are valid.

### Phase 1: Data Ingestion & Temporal Metrics (Pair-Level)
- **Task 1.1 (T010)**: `code/ingestion.py` - `fetch_events(repo_list, sample_size)`. Implements exponential backoff for rate limits. Logs to `data/logs/rate_limit_events.log`.
- **Task 1.2 (T011)**: `code/ingestion.py` - `filter_bots(events)`. Explicitly excludes `[bot]` and GitHub Apps.
- **Task 1.3**: `code/metrics.py` - `calculate_pair_metrics(events)`. Computes `response_time_variance` and `mean_delay` for every distinct `ContributorPair` within a project.
- **Task 1.4 (T015)**: `code/metrics.py` - `aggregate_pair_metrics(events)`. Writes **pair-level** metrics to `data/derived/pair_metrics.parquet`. (Note: Project-level median aggregation is moved to Phase 3 for robustness check).
- **Task 1.5**: Output `data/derived/pair_metrics.parquet` and `data/derived/timestamp_features.parquet` (project-level summary).

### Phase 2: Sentiment Analysis (Pair-Level)
- **Task 2.1**: `code/sentiment.py` - `filter_english(texts)`. Uses `langdetect` with confidence ≥ 0.95. Logs exclusion rate.
- **Task 2.2**: `code/sentiment.py` - `apply_vader(texts)`. Computes compound score for each comment.
- **Task 2.3**: `code/sentiment.py` - `aggregate_pair_sentiment(events, pair_id)`. Computes mean sentiment per pair.
- **Task 2.4**: Output `data/derived/pair_sentiment.parquet`.

### Phase 3: Statistical Analysis (Primary: HLM)
- **Task 3.1**: Merge `pair_metrics.parquet` and `pair_sentiment.parquet`.
- **Task 3.2**: **Primary Analysis**: Run **Hierarchical Linear Model (HLM)** with `cohesion_proxy_score` as dependent variable, `response_time_variance` as predictor, and `project_id` as random effect. (Addressing methodology-7eaac9).
- **Task 3.3**: **Secondary Analysis**: Run OLS Regression with project-level aggregated metrics (median variance) for robustness check.
- **Task 3.4 (T034)**: **VIF Check**: Calculate VIF for control variables. If VIF > 5, halt and write `data/logs/vif_halt_warning.log`.
- **Task 3.5 (T029)**: **FDR Correction**: Apply Benjamini-Hochberg to stratified tests (language, size). Output `data/derived/fdr_corrected_results.json`.
- **Task 3.6**: Output `data/derived/statistical_results.json` and `data/derived/hlm_results.json`.

### Phase 4: Validation & Robustness
- **Task 4.1**: Check for `data/validation/manual_ground_truth.csv`.
- **Task 4.2 (T022)**: **If missing**: Generate `data/validation/sampling_request.yaml` (schema for external request) and proceed to **Synthetic Mode**.
- **Task 4.3 (T023)**: **If present**: Run `code/validation.py` - `validate_cohesion(vader_scores, manual_scores)`.
- **Task 4.4 (T023a)**: Compute Spearman correlation between VADER and manual scores. Output `data/validation/validity_report.json`.
- **Task 4.5 (Synthetic Mode)**: If manual data is missing, generate synthetic manual scores based on VADER distribution to test the validation pipeline logic. Flag results as "synthetic".
- **Task 4.6**: Output `data/validation/validity_report.json`.

## Contract Validation

- The `code/validation.py` script will use `pyyaml` to load schemas from `contracts/` and validate all generated `.json` and `.parquet` files before proceeding to the next phase.
- If validation fails, the pipeline halts and reports the specific schema violation.

## Compute Feasibility

- **CPU-First**: All methods (VADER, Spearman, OLS, HLM with small N) are CPU-tractable.
- **Data Streaming**: Ingestion uses `streaming=True` for large repos to stay within 7 GB RAM.
- **No GPU Required**: VADER and statistical models do not require GPU.
