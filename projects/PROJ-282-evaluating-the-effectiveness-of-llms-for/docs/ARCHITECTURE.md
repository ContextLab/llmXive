# System Architecture

## Component Overview

The llmXive pipeline is modular, with distinct components for data handling, model inference, and analysis.

### 1. Data Layer (`src/data/`)

- **Ingestion**: `ingest.py`, `download_*.py` handle fetching raw data.
- **Preprocessing**: `preprocess.py` cleans and parses code snippets.
- **Feature Extraction**: `feature_extractor.py` computes AST and semantic features.
- **Streaming**: `stream_processor.py` handles large datasets via chunked processing.

### 2. Model Layer (`src/models/`)

- **LLM Inference**: `llm_inference.py` manages model loading, prompting, and output parsing.
- **Static Analysis**: `static_analyzer.py` wraps external tools (Bandit, Cppcheck).
- **Data Models**: Pydantic classes (`CodeSnippet`, `FeatureVector`, etc.) enforce schema compliance.

### 3. Analysis Layer (`src/analysis/`)

- **Metrics**: `metrics.py` computes precision, recall, F1.
- **Regression**: `regression.py` performs logistic regression and correlation analysis.
- **Visualization**: `visualizer.py` generates plots (heatmaps, ROC curves).
- **Reporting**: `report_generator.py` aggregates results into `research.md`.

### 4. Utility Layer (`src/utils/`)

- **Config**: `config.py` manages global settings, seeds, and paths.
- **Logging**: `logger.py` provides structured JSON logging.
- **Monitoring**: `memory_monitor.py` tracks RAM usage and triggers batch resizing.
- **Validation**: `validate_urls.py`, `cpu_check.py` ensure environment correctness.

### 5. Orchestration (`src/orchestration/`)

- **DAG**: `orchestrator.py` defines task dependencies and execution order.
- **State**: `state_updater.py` tracks pipeline progress and artifacts.

## Data Flow

1. **Raw Data** -> `data/raw/` (via Downloaders)
2. **Parsed Snippets** -> `data/processed/parsed_snippets.parquet`
3. **Sampled Data** -> `data/processed/sampled_snippets.parquet`
4. **Features** -> `data/processed/features.csv`
5. **Predictions** -> `data/results/llm_predictions_raw.json`, `data/processed/static_predictions.csv`
6. **Metrics** -> `data/results/metrics.json`
7. **Report** -> `research.md`

## Error Handling

- **Fail Fast**: Critical errors (GPU detected, data fetch failure) abort the pipeline immediately.
- **Graceful Degradation**: Non-critical errors (malformed snippets) are logged, and processing continues.
- **Recovery**: State files allow resuming from the last completed task.
