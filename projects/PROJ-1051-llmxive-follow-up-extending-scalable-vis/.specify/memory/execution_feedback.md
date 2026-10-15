# Execution failures — fix these before the analysis can run

## ⚠ DATA-UNAVAILABLE failure — switch to a REAL, REACHABLE data source

These commands failed because the external dataset is NOT reachable AS WRITTEN on the free CI runner: a Hugging Face dataset that was renamed (canonical names like `openai_humaneval` now require a `namespace/name`), had its loading script removed (`datasets` >= 3 dropped `trust_remote_code` script datasets), is gated, or needs network the runner lacks. RE-TRYING THE DOWNLOAD AS-IS WILL NEVER SUCCEED. Fix it with REAL data, in this order:

1. CORRECT the source: use the dataset's current canonical id (`namespace/name`), a public mirror, or a direct file URL, and stream / download only a SMALL REAL SAMPLE (the first N rows, one split, a few files). A verified real source may be injected below — use it.
2. If that exact dataset is truly unreachable, switch to a DIFFERENT but genuinely-public dataset that supports the SAME analysis/metric, and say so honestly in the README.
3. Do NOT substitute synthetic / fake / hand-built data for the real dataset. A result computed on invented data is NOT a real finding and is REJECTED by the deterministic fabrication gate — swapping in synthetic data is the single most common reason this loop never converges. The ONLY exception is a project whose OWN research question is about synthetic / simulated data (its idea says so).
4. If, after the above, NO real data can be obtained on the CI runner, do NOT fabricate a result: leave the run to FAIL so it escalates honestly (model-tier escalation / re-plan), rather than producing a fake finding.

- `python -m src.data.download  --dataset-name layout_corpus  --output-dir data/raw`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 5 command(s) failed: python -m src.data.download  --dataset-name layout_corpus  --output-dir data/raw (rc=1); python -m src.data.preprocess  --input-dir data/raw/layout_corpus  --output-parquet data/processed/document_pairs.parquet  --schema contracts/documentpair.schema.yaml (rc=1); python -m src.data.latent_generator  --input-parquet data/processed/document_pairs.parquet  --output-parquet data/processed/document_pairs_with_latent.parquet  --encoder-name resnet18  --device cpu (rc=1)

## Failing / missing run-book commands

- python -m src.data.download  --dataset-name layout_corpus  --output-dir data/raw -> rc=1
Loading PubLayNet dataset via `datasets.load_dataset`...

❌ ERROR: Dataset 'hustvl/publaynet' doesn't exist on the Hub or cannot be accessed.

- python -m src.data.preprocess  --input-dir data/raw/layout_corpus  --output-parquet data/processed/document_pairs.parquet  --schema contracts/documentpair.schema.yaml -> rc=1

2026-10-15 20:08:30,801 ERROR __main__: Preprocessing failed: [Errno 2] No such file or directory: 'contracts/documentpair.schema.yaml'

- python -m src.data.latent_generator  --input-parquet data/processed/document_pairs.parquet  --output-parquet data/processed/document_pairs_with_latent.parquet  --encoder-name resnet18  --device cpu -> rc=1

Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-1051-llmxive-follow-up-extending-scalable-vis/src/data/latent_generator.py", line 17, in <module>
    import torch
ModuleNotFoundError: No module named 'torch'

- python -m src.data.download  --dataset-name docvqa  --output-dir data/raw/docvqa -> rc=1
.43 examples/s]
Generating test split:  80%|████████  | 4160/5188 [00:06<00:02, 437.43 examples/s]
Generating test split:  82%|████████▏ | 4260/5188 [00:06<00:01, 509.80 examples/s]
Generating test split:  83%|████████▎ | 4324/5188 [00:07<00:01, 506.84 examples/s]
Generating test split:  87%|████████▋ | 4524/5188 [00:07<00:01, 607.62 examples/s]
Generating test split:  89%|████████▉ | 4624/5188 [00:07<00:01, 513.52 examples/s]
Generating test split:  91%|█████████ | 4724/5188 [00:07<00:01, 459.00 examples/s]
Generating test split:  93%|█████████▎| 4824/5188 [00:08<00:00, 436.41 examples/s]
Generating test split:  95%|█████████▍| 4924/5188 [00:08<00:00, 409.44 examples/s]
Generating test split:  97%|█████████▋| 5024/5188 [00:08<00:00, 437.43 examples/s]
Generating test split:  99%|█████████▉| 5124/5188 [00:08<00:00, 421.86 examples/s]
Generating test split: 100%|██████████| 5188/5188 [00:09<00:00, 297.53 examples/s]
Generating test split: 100%|██████████| 5188/5188 [00:09<00:00, 558.97 examples/s]

Saving DocVQA:   0%|          | 0/10537 [00:00<?, ?it/s]
Saving DocVQA:   0%|          | 0/10537 [00:01<?, ?it/s]
❌ ERROR: memoryview: a bytes-like object is required, not 'PngImageFile'

- python -m pytest -k "contract" tests/ -> rc=2
roject.toml
plugins: anyio-4.15.1
collected 3 items / 1 error / 2 deselected / 1 selected

==================================== ERRORS ====================================
_ ERROR collecting projects/PROJ-1051-llmxive-follow-up-extending-scalable-vis/tests/test_latent_generator.py _
ImportError while importing test module '/home/runner/work/llmXive/llmXive/projects/PROJ-1051-llmxive-follow-up-extending-scalable-vis/tests/test_latent_generator.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/importlib/__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
tests/test_latent_generator.py:18: in <module>
    from src.data.latent_generator import main as generate_latents
src/data/latent_generator.py:17: in <module>
    import torch
E   ModuleNotFoundError: No module named 'torch'
=========================== short test summary info ============================
ERROR tests/test_latent_generator.py
!!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
======================== 2 deselected, 1 error in 0.69s ========================


