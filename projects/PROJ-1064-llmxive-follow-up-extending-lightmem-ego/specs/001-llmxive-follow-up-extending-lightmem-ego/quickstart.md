# Quickstart: Semantic Decay Retrieval

This guide walks you through setting up the environment and running the benchmark on a publicly available dataset.

## 1. Install Dependencies
From the project root:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 2. Download the Dataset
Run the provided download script, which fetches a small public dataset and verifies checksums:

```bash
python src/data/download.py --output-dir data/raw/
```

The script will:

* Download a public **AG News** CSV file.
* Convert each example into an Ego4D‑like ``manifest.jsonl`` containing ``node_id``, ``timestamp`` (ISO‑8601), and ``event_label``.
* Compute a deterministic embedding with a fixed dimensionality for each example.
* Write a ``CHECKSUMS.txt`` file with SHA‑256 hashes for each file.

## 3. Preprocess the Data
Create the processed parquet file:

```bash
python src/data/preprocess.py \
    --raw-dir data/raw/ \
    --output data/processed/memory_nodes.parquet
```

This step:

* Reads the ``manifest.jsonl`` and ``embeddings.npy`` files.
* Flags ``is_rare`` events (≤ 5 occurrences of the same ``event_label``).
* Writes ``memory_nodes.parquet``.

## 4. Run the Full Benchmark
(Further steps – validation, full evaluation, reporting – are defined in later tasks.)

## 5. Verify the Output
```bash
pytest tests/contract/test_evaluation_report.py
```

All tests should pass, indicating that the generated artifacts conform to the required schema.