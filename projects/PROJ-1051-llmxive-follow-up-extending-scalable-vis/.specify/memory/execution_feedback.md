# Execution failures — fix these before the analysis can run

## ⚠ DATA-UNAVAILABLE failure — switch to a REAL, REACHABLE data source

These commands failed because the external dataset is NOT reachable AS WRITTEN on the free CI runner: a Hugging Face dataset that was renamed (canonical names like `openai_humaneval` now require a `namespace/name`), had its loading script removed (`datasets` >= 3 dropped `trust_remote_code` script datasets), is gated, or needs network the runner lacks. RE-TRYING THE DOWNLOAD AS-IS WILL NEVER SUCCEED. Fix it with REAL data, in this order:

1. CORRECT the source: use the dataset's current canonical id (`namespace/name`), a public mirror, or a direct file URL, and stream / download only a SMALL REAL SAMPLE (the first N rows, one split, a few files). A verified real source may be injected below — use it.
2. If that exact dataset is truly unreachable, switch to a DIFFERENT but genuinely-public dataset that supports the SAME analysis/metric, and say so honestly in the README.
3. Do NOT substitute synthetic / fake / hand-built data for the real dataset. A result computed on invented data is NOT a real finding and is REJECTED by the deterministic fabrication gate — swapping in synthetic data is the single most common reason this loop never converges. The ONLY exception is a project whose OWN research question is about synthetic / simulated data (its idea says so).
4. If, after the above, NO real data can be obtained on the CI runner, do NOT fabricate a result: leave the run to FAIL so it escalates honestly (model-tier escalation / re-plan), rather than producing a fake finding.

- `python -m src.data.download  --primary-name docbank  --fallback-name pubmed-layout`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 8 command(s) failed: python -m src.data.download  --primary-name docbank  --fallback-name pubmed-layout (rc=1); python -m src.data.preprocess  --input-dir data/raw  --output-path data/processed/document_pairs.parquet  --schema contracts/documentpair.schema.yaml (rc=1); python -m src.data.latent_generator  --input-path data/processed/document_pairs.parquet  --output-path data/processed/document_pairs_with_latent.parquet  --encoder-name layoutlmv3-base  --device cpu (rc=1)

## Failing / missing run-book commands

- python -m src.data.download  --primary-name docbank  --fallback-name pubmed-layout -> rc=1
Attempting to download dataset 'docbank' from hub identifier 'nielsr/docbank'...
⚠️ Warning: Failed to download dataset 'nielsr/docbank': Dataset 'nielsr/docbank' doesn't exist on the Hub or cannot be accessed.
Primary dataset 'docbank' provided 0 pages, which is less than the minimum 10000. Attempting fallback...
Attempting to download dataset 'pubmed-layout' from hub identifier 'nielsr/pubmed-layout'...
⚠️ Warning: Failed to download dataset 'nielsr/pubmed-layout': Dataset 'nielsr/pubmed-layout' doesn't exist on the Hub or cannot be accessed.

=== Summary of layout-annotation pages ===
  Primary (docbank): 0
  Fallback (pubmed-layout): 0
  TOTAL: 0


❌ ERROR: Insufficient total pages with layout annotations: 0 (minimum required is 10000). Pipeline aborting as per FR-007.

- python -m src.data.preprocess  --input-dir data/raw  --output-path data/processed/document_pairs.parquet  --schema contracts/documentpair.schema.yaml -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-1051-llmxive-follow-up-extending-scalable-vis/bin/python: No module named src.data.preprocess

- python -m src.data.latent_generator  --input-path data/processed/document_pairs.parquet  --output-path data/processed/document_pairs_with_latent.parquet  --encoder-name layoutlmv3-base  --device cpu -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-1051-llmxive-follow-up-extending-scalable-vis/bin/python: No module named src.data.latent_generator

- python -m src.utils.split_generator  --input-path data/processed/document_pairs_with_latent.parquet  --output-dir data/splits  --seed 42  --train-ratio 0.8 --val-ratio 0.1 --test-ratio 0.1 -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-1051-llmxive-follow-up-extending-scalable-vis/bin/python: Error while finding module specification for 'src.utils.split_generator' (ModuleNotFoundError: No module named 'src.utils')

- python -m src.models.distilled  --data-path data/processed/document_pairs_with_latent.parquet  --splits-dir data/splits  --seed $SEED  --output-dir artifacts/models/distilled_$SEED  --max-epochs 5  --batch-size 16 -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-1051-llmxive-follow-up-extending-scalable-vis/bin/python: Error while finding module specification for 'src.models.distilled' (ModuleNotFoundError: No module named 'src.models')

- python -m src.models.baseline  --data-path data/processed/document_pairs.parquet  --splits-dir data/splits  --seed $SEED  --output-dir artifacts/models/baseline_$SEED  --max-epochs 5  --batch-size 16 -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-1051-llmxive-follow-up-extending-scalable-vis/bin/python: Error while finding module specification for 'src.models.baseline' (ModuleNotFoundError: No module named 'src.models')

- python -m src.eval.downstream  --distilled-dir artifacts/models/distilled_*/  --baseline-dir artifacts/models/baseline_*/  --test-data data/processed/downstream_test.parquet  --results-path artifacts/eval/downstream_results.json -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-1051-llmxive-follow-up-extending-scalable-vis/bin/python: Error while finding module specification for 'src.eval.downstream' (ModuleNotFoundError: No module named 'src.eval')

- python -m pytest -k "contract" tests/ -> rc=4
============================= test session starts ==============================
platform linux -- Python 3.11.17, pytest-8.2.0, pluggy-1.6.0
rootdir: /home/runner/work/llmXive/llmXive
configfile: pyproject.toml
collected 0 items

============================ no tests ran in 0.00s =============================

ERROR: file or directory not found: tests/


