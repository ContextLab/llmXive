# Quickstart Guide: llmXive Follow-up: Extending DanceOPD

This guide explains how to run the full pipeline for extending DanceOPD with on-policy generative field distillation.

## Prerequisites

- Python 3.11+
- pip
- 7GB+ RAM (for streaming large datasets)
- 14GB+ disk space

## Setup

1. Clone the repository and navigate to the project directory:
 ```bash
 cd projects/PROJ-879-llmxive-follow-up-extending-danceopd-on
 ```

2. Create a virtual environment and install dependencies:
 ```bash
 python -m venv code/.venv
 source code/.venv/bin/activate
 pip install -r code/requirements.txt
 ```

3. Set up directory structure (run T001a):
 ```bash
 python code/setup_data_dirs.py
 ```

## Running the Pipeline

The pipeline consists of the following stages:

### Stage 1: Data Fetching (T042)

Fetch real data from ImageNet-1K and LAION-400M with streaming:

```bash
python code/00_data_fetch.py
```

This script:
- Streams data in chunks to avoid memory issues
- Computes SHA256 hashes of the raw stream buffer
- Stores stream hashes in `state/artifact_hashes.yaml`
- Writes data to `data/raw/imagenet_samples.parquet` and `data/raw/laion_samples.parquet`
- **FAILS LOUDLY** if streaming fails (no synthetic fallback)

### Stage 2: Data Source Verification (T043)

Verify the integrity of fetched data:

```bash
python code/00_verify_data_sources.py
```

This script:
- Computes SHA256 hashes of the written files
- Compares them against the stream hashes stored in `state/artifact_hashes.yaml`
- Writes verification results to `data/results/verification_log.json`
- Writes file hashes to `data/results/source_hashes.json`
- **EXITS WITH CODE 1** if any hash mismatch is detected

### Stage 3: Data Streaming & Processing (T012b)

Stream and process data to extract prompt embeddings:

```bash
python code/00_data_stream.py
```

### Stage 4: Teacher Inference (T013a, T013b)

Generate teacher ground truth and filter dataset:

```bash
python code/00_teacher_inference.py
```

### Stage 5: Data Extraction (T014)

Extract final dataset:

```bash
python code/00_data_extraction.py
```

### Stage 6: Tree Training (T020, T021)

Train decision trees:

```bash
python code/01_train_trees.py
```

### Stage 7: Fidelity Evaluation (T028, T030a, T030d)

Evaluate fidelity degradation:

```bash
python code/02_evaluate_fidelity.py
```

## Important Notes

### Fail-Loud Behavior

All scripts are designed to **fail loudly** if they encounter errors:
- If data fetching fails, the script exits with code 1
- If data verification fails, the script exits with code 1
- If insufficient samples are generated, the script exits with code 1

This ensures that no synthetic or placeholder data is silently used.

### Real Data Only

The pipeline requires real data from ImageNet-1K and LAION-400M. If these sources are unavailable, the pipeline will fail. Do not modify the code to use synthetic data.

### Reproducibility

The pipeline maintains reproducibility by:
- Storing stream hashes in `state/artifact_hashes.yaml`
- Verifying file hashes against stream hashes in T043
- Using fixed random seeds (configurable in `code/utils/config.py`)

## Troubleshooting

### "File not found" errors

Ensure you have run the data fetching stage (T042) before verification (T043).

### "Hash mismatch" errors

This indicates that the data on disk does not match the source stream. Possible causes:
- Network corruption during download
- Source dataset changed
- Manual modification of files

Re-run T042 to fetch fresh data.

### Memory issues

The pipeline uses streaming to minimize memory usage. If you still encounter memory issues, reduce the target sample size in `code/utils/config.py`.