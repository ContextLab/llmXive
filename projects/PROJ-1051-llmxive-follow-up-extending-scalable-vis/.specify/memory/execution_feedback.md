# Execution failures — fix these before the analysis can run

## ⚠ DATA-UNAVAILABLE failure — switch to a REAL, REACHABLE data source

These commands failed because the external dataset is NOT reachable AS WRITTEN on the free CI runner: a Hugging Face dataset that was renamed (canonical names like `openai_humaneval` now require a `namespace/name`), had its loading script removed (`datasets` >= 3 dropped `trust_remote_code` script datasets), is gated, or needs network the runner lacks. RE-TRYING THE DOWNLOAD AS-IS WILL NEVER SUCCEED. Fix it with REAL data, in this order:

1. CORRECT the source: use the dataset's current canonical id (`namespace/name`), a public mirror, or a direct file URL, and stream / download only a SMALL REAL SAMPLE (the first N rows, one split, a few files). A verified real source may be injected below — use it.
2. If that exact dataset is truly unreachable, switch to a DIFFERENT but genuinely-public dataset that supports the SAME analysis/metric, and say so honestly in the README.
3. Do NOT substitute synthetic / fake / hand-built data for the real dataset. A result computed on invented data is NOT a real finding and is REJECTED by the deterministic fabrication gate — swapping in synthetic data is the single most common reason this loop never converges. The ONLY exception is a project whose OWN research question is about synthetic / simulated data (its idea says so).
4. If, after the above, NO real data can be obtained on the CI runner, do NOT fabricate a result: leave the run to FAIL so it escalates honestly (model-tier escalation / re-plan), rather than producing a fake finding.

- `python -m src.data.download  --dataset-name publaynet  --output-dir data/raw`
- `python -m src.data.download  --dataset-name docvqa  --output-dir data/raw/docvqa`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 4 command(s) failed: python -m src.data.download  --dataset-name publaynet  --output-dir data/raw (rc=1); python -m src.data.preprocess  --input-dir data/raw/publaynet  --output-parquet data/processed/document_pairs.parquet  --schema contracts/documentpair.schema.yaml (rc=1); python -m src.data.latent_generator  --input-parquet data/processed/document_pairs.parquet  --output-parquet data/processed/document_pairs_with_latent.parquet  --encoder-name layoutlmv3-base  --device cpu (rc=1)

## Failing / missing run-book commands

- python -m src.data.download  --dataset-name publaynet  --output-dir data/raw -> rc=1
Downloading dataset 'layoutparser/publaynet' via the 🤗 datasets library...
⚠️ Warning: Failed to download 'layoutparser/publaynet': Dataset 'layoutparser/publaynet' doesn't exist on the Hub or cannot be accessed.
Primary dataset provided 0 pages, which is less than the required 10000. Attempting fallback download...
Downloading dataset 'layoutparser/docbank' via the 🤗 datasets library...
⚠️ Warning: Failed to download 'layoutparser/docbank': Dataset 'layoutparser/docbank' doesn't exist on the Hub or cannot be accessed.

=== Summary of layout‑annotation pages ===
  Primary (PubLayNet): 0
  Fallback (DocBank) added: 0
  TOTAL: 0


❌ ERROR: Insufficient total pages with layout annotations: 0 (minimum required is 10000). Pipeline aborting as per FR‑007.

- python -m src.data.preprocess  --input-dir data/raw/publaynet  --output-parquet data/processed/document_pairs.parquet  --schema contracts/documentpair.schema.yaml -> rc=1

2026-10-14 19:10:26,926 ERROR __main__: Preprocessing failed: Input directory does not exist: data/raw/publaynet

- python -m src.data.latent_generator  --input-parquet data/processed/document_pairs.parquet  --output-parquet data/processed/document_pairs_with_latent.parquet  --encoder-name layoutlmv3-base  --device cpu -> rc=1

2026-10-14 19:10:28,641 ERROR __main__: Latent generation failed: Unable to read Parquet file 'data/processed/document_pairs.parquet': [Errno 2] No such file or directory: 'data/processed/document_pairs.parquet'

- python -m src.data.download  --dataset-name docvqa  --output-dir data/raw/docvqa -> rc=1
Downloading generic dataset 'docvqa' via 🤗 datasets...


❌ ERROR: Failed to download generic dataset 'docvqa': Dataset 'docvqa' doesn't exist on the Hub or cannot be accessed.

