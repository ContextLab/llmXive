# Reproducibility Protocol

This document outlines the measures taken to ensure the scientific reproducibility of the llmXive pipeline.

## Determinism

- **Seeds**: All random number generators (Python `random`, NumPy, PyTorch) are seeded via `src/utils/config.py`.
- **Ordering**: Candidate models are processed in a deterministic, alphabetically ordered list.
- **Sampling**: Stratified sampling uses `random_state=42`.

## Artifact Integrity

- **Hashing**: All output files in `data/processed/` and `data/results/` are checksummed using SHA-256 via `src/utils/hash_artifacts.py`.
- **Manifests**: A manifest of all artifacts and their hashes is stored in `data/logs/artifact_hashes.json`.

## Data Provenance

- **Source Verification**: Datasets are downloaded from verified sources (Hugging Face, official repos).
- **No Fabrication**: The pipeline strictly prohibits synthetic data generation. If a real dataset cannot be fetched, the process fails with a clear error.
- **Logging**: All download attempts and failures are logged to `data/logs/ingest_logs.json`.

## Environment

- **Dependencies**: Exact versions are pinned in `requirements.txt`.
- **Hardware**: The pipeline is designed for CPU-only execution to ensure consistent performance across environments.
- **Runtime Limits**: Hard limits (6 hours total, 4.32s per sample) are enforced to prevent resource exhaustion.

## Verification Steps

To verify a run:

1. **Check Logs**: Ensure `data/logs/orchestration_log.json` shows all tasks completed successfully.
2. **Verify Hashes**: Run `python code/src/utils/hash_artifacts.py` and compare against `data/logs/artifact_hashes.json`.
3. **Inspect State**: Check `state/projects/PROJ-282-*.yaml` for final completion status.
4. **Review Report**: Validate `research.md` contains all required statistical outputs (McFadden R², McNemar p-value, etc.).

## Known Limitations

- **CPU Performance**: Inference on CPU is significantly slower than GPU. The 6-hour runtime limit may be reached with large datasets.
- **Model Selection**: The "best" CPU model is selected based on a small benchmark; this may not reflect performance on the full dataset.
- **Data Access**: Requires internet access for dataset downloads.
