# Execution failures — fix these before the analysis can run

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python -m src.data.download  --dataset-name publaynet  --output-dir data/raw`
  - script usage: `download.py [-h] --primary-name PRIMARY_NAME --fallback-name`
  - argparse error: `download.py: error: the following arguments are required: --primary-name, --fallback-name`
- run-book command: `python -m src.data.download  --dataset-name docvqa  --output-dir data/raw/docvqa`
  - script usage: `download.py [-h] --primary-name PRIMARY_NAME --fallback-name`
  - argparse error: `download.py: error: the following arguments are required: --primary-name, --fallback-name`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 8 command(s) failed: python -m src.data.download  --dataset-name publaynet  --output-dir data/raw (rc=2); python -m src.data.preprocess  --input-dir data/raw/publaynet  --output-parquet data/processed/document_pairs.parquet  --schema contracts/documentpair.schema.yaml (rc=1); python -m src.data.latent_generator  --input-parquet data/processed/document_pairs.parquet  --output-parquet data/processed/document_pairs_with_latent.parquet  --encoder-name layoutlmv3-base  --device cpu (rc=1)

## Failing / missing run-book commands

- python -m src.data.download  --dataset-name publaynet  --output-dir data/raw -> rc=2

usage: download.py [-h] --primary-name PRIMARY_NAME --fallback-name
                   FALLBACK_NAME
download.py: error: the following arguments are required: --primary-name, --fallback-name

- python -m src.data.preprocess  --input-dir data/raw/publaynet  --output-parquet data/processed/document_pairs.parquet  --schema contracts/documentpair.schema.yaml -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-1051-llmxive-follow-up-extending-scalable-vis/bin/python: No module named src.data.preprocess

- python -m src.data.latent_generator  --input-parquet data/processed/document_pairs.parquet  --output-parquet data/processed/document_pairs_with_latent.parquet  --encoder-name layoutlmv3-base  --device cpu -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-1051-llmxive-follow-up-extending-scalable-vis/bin/python: No module named src.data.latent_generator

- python -m src.utils.split_generator  --input-parquet data/processed/document_pairs_with_latent.parquet  --output-dir data/splits  --seed 42  --train-ratio 0.8 --val-ratio 0.1 --test-ratio 0.1 -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-1051-llmxive-follow-up-extending-scalable-vis/bin/python: Error while finding module specification for 'src.utils.split_generator' (ModuleNotFoundError: No module named 'src.utils')

- python -m src.models.distilled  --data-parquet data/processed/document_pairs_with_latent.parquet  --splits-dir data/splits  --seed $SEED  --output-dir artifacts/models/distilled_$SEED  --max-epochs 5  --batch-size 16 -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-1051-llmxive-follow-up-extending-scalable-vis/bin/python: Error while finding module specification for 'src.models.distilled' (ModuleNotFoundError: No module named 'src.models')

- python -m src.models.baseline  --data-parquet data/processed/document_pairs.parquet  --splits-dir data/splits  --seed $SEED  --output-dir artifacts/models/baseline_$SEED  --max-epochs 5  --batch-size 16 -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-1051-llmxive-follow-up-extending-scalable-vis/bin/python: Error while finding module specification for 'src.models.baseline' (ModuleNotFoundError: No module named 'src.models')

- python -m src.data.download  --dataset-name docvqa  --output-dir data/raw/docvqa -> rc=2

usage: download.py [-h] --primary-name PRIMARY_NAME --fallback-name
                   FALLBACK_NAME
download.py: error: the following arguments are required: --primary-name, --fallback-name

- python -m src.eval.downstream  --distilled-dir artifacts/models/distilled_*/  --baseline-dir artifacts/models/baseline_*/  --test-data data/raw/docvqa/test.parquet  --results-path artifacts/eval/downstream_results.json -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-1051-llmxive-follow-up-extending-scalable-vis/bin/python: Error while finding module specification for 'src.eval.downstream' (ModuleNotFoundError: No module named 'src.eval')

