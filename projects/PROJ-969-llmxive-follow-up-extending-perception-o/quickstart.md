# Quickstart: Running the Prejudice-Gap Study

## Prerequisites
- Python 3.11 environment with the project dependencies installed
 (`pip install -r requirements.txt`).
- Internet access to the Hugging Face Hub (primary dataset `mmbench/ocean`
 and open-source MLLMs).

## Step 1 — Acquire and validate the primary dataset (T001)

```bash
python -m code.src.data.load_dataset
```

This streams the **real** `mmbench/ocean` validation split
(`datasets.load_dataset("mmbench/ocean", split="validation", streaming=True)`),
iterates ALL records, normalizes them, validates every record against
`specs/001-llmxive-follow-up-extending-perception-o/contracts/video_metadata.schema.yaml`,
and writes:

| Artifact | Description |
|---|---|
| `data/raw/video_metadata.jsonl` | One schema-validated per-video metadata record per line (video_id, video_url, transcript, setting, culture, behavior_tags, expert trait labels). |
| `data/raw/checksums.json` | SHA-256 checksums of the written raw files. |
| `data/raw/dataset_stats.json` | Record count, field-presence counts, missing-tag counts, and the sample-size/power limitation statement. |

The loader fails loudly (raises) on any fetch/parse/schema failure — there is
NO synthetic or mock fallback. MM-OCEAN (spec FR-001) has no verified public
URL; `mmbench/ocean` is the verified open primary dataset (deviation #1).

## Step 2 — Validate the loader (T001 tests)

```bash
pytest code/tests/test_load_dataset.py
```

Verifies schema conformance of every written record, record-count agreement
with `dataset_stats.json`, checksum integrity, and that a forced fetch
failure raises.

## Subsequent stages

Later tasks add: the context knowledge base (`python -m...`), prompt
conditions and order randomisation, CPU-only MLLM inference
(`python -m code.src.inference.run_inference --pilot|--full|--quant-control`),
metrics (`python -m code.src.metrics.compute_metrics`), statistics
(`python -m code.src.analysis.stats`), and the single orchestrator
`python -m code.src.run_all`. This file will be extended as those tasks
land; the full run-book lives in
`specs/001-llmxive-follow-up-extending-perception-o/quickstart.md`.
