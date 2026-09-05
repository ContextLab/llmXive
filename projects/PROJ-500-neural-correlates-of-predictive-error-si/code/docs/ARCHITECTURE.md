# Architecture Design

## Data Flow

1. **Ingestion (T014)**: Raw EEG data is streamed from OpenNeuro/HF.
2. **Preprocessing (T015-T018)**: Data is filtered, ICA components removed, and epochs created.
3. **Alignment (T021-T026)**: MMN amplitudes are calculated and aligned with behavioral accuracy blocks.
4. **Modeling (T029-T034)**: LME models are fitted to the aligned data.

## Module Responsibilities

- `src/data/ingest.py`: Handles data fetching and metadata validation.
- `src/data/preprocess.py`: Implements signal processing steps.
- `src/data/align.py`: Calculates MMN and performs lagged alignment.
- `src/analysis/model.py`: Fits statistical models and performs inference.
- `src/utils/`: Provides shared utilities (logging, config, checksums).

## Performance Considerations

- **Streaming**: All large dataset operations use streaming to keep RAM usage < 7GB.
- **Batching**: Processing is done in batches to avoid memory spikes.
- **Parallelism**: Independent tasks (e.g., subject processing) can be parallelized.

## Testing Strategy

- **Contract Tests**: Validate data schemas (T012, T019, T027).
- **Integration Tests**: Verify pipeline stages work together (T013, T020).
- **Unit Tests**: Test individual functions (e.g., T031 permutation test).
- **Performance Tests**: Verify runtime constraints (T037).