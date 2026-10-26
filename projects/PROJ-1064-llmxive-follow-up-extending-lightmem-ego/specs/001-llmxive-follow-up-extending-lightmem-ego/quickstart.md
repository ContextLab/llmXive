# Quickstart: Semantic Decay Retrieval

This guide walks you through setting up the environment and running the benchmark on the verified Ego4D dataset.

## 1. Install Dependencies
From the project root:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 2. Download the Ego4D Data
Run the provided download script, which fetches the verified dataset and verifies checksums:

```bash
python src/data/download.py --output-dir data/raw/
```

The script will:

* Download the Ego4D dataset (`ego4d/ego4d`) using the `datasets` library.
* Stream each example to `data/raw/` as a JSON line file `manifest.jsonl`.
* Compute a SHA‑256 checksum for each written file.
* Write a `CHECKSUMS.txt` file with one line per file:
      <checksum>  <filename>
  Any mismatch aborts with a clear error.

## 3. Preprocess the Data
Create the processed parquet file and the FAISS index:

```bash
python src/data/preprocess.py \
    --raw-dir data/raw/ \
    --output data/processed/memory_nodes.parquet
```

This step:

* Reads the `manifest.jsonl` and the accompanying `embeddings.npy` archive.
* Flags `is_rare` events (≤ 5 occurrences).
* Writes `memory_nodes.parquet`.
* Builds `faiss_hnsw.index` (deterministic, CPU‑only).

## 4. Run the Full Benchmark
Execute the end‑to‑end pipeline (validation mode first, then full evaluation):

```bash
# Quick validation to ensure the pipeline works
python src/cli/run.py --mode validation

# Full evaluation (may take up to a few hours on the free CI runner)
python src/cli/run.py --mode full
```

The script will:

* Perform the deterministic λ grid search.
* Evaluate both retrievers on the full query set.
* Record latency, CPU cycles, and run McNemar’s test.
* Write `evaluation_report.json` to the project root.
* Produce a human‑readable markdown summary `report.md`.

## 5. Verify the Output
Confirm that the JSON conforms to the contract schema:

```bash
pytest tests/contract/test_evaluation_report.py
```

All tests should pass, indicating that the report meets the required structure and that all functional requirements have been satisfied.
