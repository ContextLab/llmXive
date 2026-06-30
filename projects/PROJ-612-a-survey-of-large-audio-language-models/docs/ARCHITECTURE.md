# Architecture Overview

## Design Principles

1. **Modularity**: Each user story (US1, US2, US3) is implemented as an independent pipeline stage.
2. **Reproducibility**: All data artifacts are checksummed; logging is deterministic.
3. **CPU-Only**: No GPU dependencies; memory guards prevent OOM failures.
4. **Contract-First**: Schema definitions precede implementation to ensure test alignment.

## Data Flow

1. **Data Ingestion**: Raw datasets (LibriSpeech, FMA, ESC-50) are converted to JSON via `code/load_audio.py`.
2. **Inference**: Models generate captions via `code/run_inference.py`; outputs saved to `results/captions.json`.
3. **Detection**: Hallucinations flagged via `code/detect_hallucination.py`; rates computed with Wilson intervals.
4. **Analysis**: Training data estimates correlated with hallucination rates (US2); human judgments analyzed (US3).

## Error Handling

- **OOM/Timeout**: `code/runtime_guard.py` enforces limits and logs aborts.
- **Missing Data**: `code/handle_missing_data.py` flags unknowns without halting.
- **Model Exclusion**: Fuzzy matching skips models trained on test datasets.

## Testing Strategy

- **Contract Tests**: Validate output schemas before implementation.
- **Integration Tests**: Verify end-to-end pipeline on sample data.
- **Unit Tests**: Cover core logic (e.g., Cohen’s κ, Wilson intervals).
