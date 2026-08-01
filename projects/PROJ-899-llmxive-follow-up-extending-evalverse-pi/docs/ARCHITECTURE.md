# Architecture Decision Records (ADR)

## ADR-001: CPU-First Feature Extraction

**Status**: Accepted
**Context**: The project targets CPU-tractable analysis for 10k video clips within 6 hours, with a strict memory cap of 7GB.
**Decision**: We use OpenCV (CPU) for optical flow and HOG, and Librosa for audio features. No GPU-accelerated libraries (e.g., PyTorch CUDA) are used in the core feature extraction pipeline.
**Consequence**: Feature extraction is slower per clip than GPU equivalents but ensures accessibility and deterministic resource usage. Memory usage is managed via chunked processing in `src/cli/run_pipeline.py`.

## ADR-002: Validation Gate Strategy

**Status**: Accepted
**Context**: To prevent wasted compute on invalid data or poor proxies, we enforce strict gates.
**Decision**:
- **T040**: Calculate global error rate. If > 5%, exclude bad samples but continue.
- **T041**: Correlate VLM proxy scores with human scores. If r < 0.70, exit with code 1.
- **T021**: Profile memory/time. If peak > 7GB or projected time > 6h, exit with code 1.
**Consequence**: The pipeline may fail early, but this prevents generating misleading results from bad data or infeasible configurations.

## ADR-003: Sensitivity Analysis Methodology

**Status**: Accepted
**Context**: Decision boundaries (e.g., r ≥ 0.85) must be robust.
**Decision**: We perform a threshold sweep over {0.80, 0.85, 0.90} for every dimension. We calculate "flip rates" to identify dimensions where small threshold changes alter the classification (feature-sufficient vs. VLM-required).
**Consequence**: This adds computational overhead (T026) but provides critical methodological verification (SC-004).

## ADR-004: Data Model Serialization

**Status**: Accepted
**Context**: Intermediate data must be stored efficiently and reproducibly.
**Decision**:
- Raw data: Original format (e.g., TAR/ZIP).
- Processed features: CSV/Parquet (via `pandas`).
- Configuration/State: JSON.
**Consequence**: Ensures human readability for debugging and standard library compatibility for portability.

## ADR-005: Error Handling in Feature Extraction

**Status**: Accepted
**Context**: Video clips may have missing audio tracks or corrupted frames.
**Decision**: `src/data/preprocess.py` catches exceptions per clip, returns null/zero vectors, logs a warning, and continues. The sample is not discarded entirely unless the error rate exceeds the T040 threshold.
**Consequence**: Robustness against noisy real-world data, with explicit logging for auditability.
