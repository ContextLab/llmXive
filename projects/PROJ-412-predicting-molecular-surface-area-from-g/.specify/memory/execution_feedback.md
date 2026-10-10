# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/run_dry_run.py: synthetic/fake INPUT data not authorized by the spec — “…-run cannot proceed with synthetic data.")          # Take exact…”

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python code/models/train.py --model gcn --config code/config.py`
  - script usage: `train.py [-h] [--data_path DATA_PATH] [--split_path SPLIT_PATH]`
  - argparse error: `train.py: error: unrecognized arguments: --model gcn --config code/config.py`
- run-book command: `python code/models/train.py --model baseline --config code/config.py`
  - script usage: `train.py [-h] [--data_path DATA_PATH] [--split_path SPLIT_PATH]`
  - argparse error: `train.py: error: unrecognized arguments: --model baseline --config code/config.py`
- run-book command: `python code/eval/sensitivity.py --results artifacts/results.json --thresholds 0.01 0.05 0.1`
  - script usage: `sensitivity.py [-h] [--predictions PREDICTIONS]`
  - argparse error: `sensitivity.py: error: unrecognized arguments: --results artifacts/results.json --thresholds 0.01 0.05 0.1`

## ⚠ DATA-UNAVAILABLE failure — switch to a REAL, REACHABLE data source

These commands failed because the external dataset is NOT reachable AS WRITTEN on the free CI runner: a Hugging Face dataset that was renamed (canonical names like `openai_humaneval` now require a `namespace/name`), had its loading script removed (`datasets` >= 3 dropped `trust_remote_code` script datasets), is gated, or needs network the runner lacks. RE-TRYING THE DOWNLOAD AS-IS WILL NEVER SUCCEED. Fix it with REAL data, in this order:

1. CORRECT the source: use the dataset's current canonical id (`namespace/name`), a public mirror, or a direct file URL, and stream / download only a SMALL REAL SAMPLE (the first N rows, one split, a few files). A verified real source may be injected below — use it.
2. If that exact dataset is truly unreachable, switch to a DIFFERENT but genuinely-public dataset that supports the SAME analysis/metric, and say so honestly in the README.
3. Do NOT substitute synthetic / fake / hand-built data for the real dataset. A result computed on invented data is NOT a real finding and is REJECTED by the deterministic fabrication gate — swapping in synthetic data is the single most common reason this loop never converges. The ONLY exception is a project whose OWN research question is about synthetic / simulated data (its idea says so).
4. If, after the above, NO real data can be obtained on the CI runner, do NOT fabricate a result: leave the run to FAIL so it escalates honestly (model-tier escalation / re-plan), rather than producing a fake finding.

- `python code/data/ingest.py --source zinc15 --output data/processed/molecules.parquet`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 fabricated/simulated-result signal(s) — results are not real measurements: code/run_dry_run.py: synthetic/fake INPUT data not authorized by the spec — “…-run cannot proceed with synthetic data.")          # Take exact…”; 1 run-book script(s) missing (plan/impl path mismatch): python code/eval.py --models artifacts/gcn_model.pt artifacts/baseline_model.pt --test data/processed/splits/test.parquet; 5 command(s) failed: python code/data/ingest.py --source zinc15 --output data/processed/molecules.parquet (rc=1); python code/data/split.py --input data/processed/molecules.parquet --output data/processed/splits/ (rc=1); python code/models/train.py --model gcn --config code/config.py (rc=2); 6 declared deliverable(s) absent: data/processed/descriptors.parquet; data/processed/graphs_with_features.parquet; data/processed/paired_dataset.parquet

## Failing / missing run-book commands

- python code/data/ingest.py --source zinc15 --output data/processed/molecules.parquet -> rc=1
oesn't exist on the Hub. If the repo is private or gated, make sure to log in with `huggingface-cli login`.

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-412-predicting-molecular-surface-area-from-g/code/data/ingest.py", line 242, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-412-predicting-molecular-surface-area-from-g/code/data/ingest.py", line 211, in main
    for record in stream:
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-412-predicting-molecular-surface-area-from-g/code/data/ingest.py", line 95, in fetch_zinc15_streaming
    raise ValueError(f"Dataset fetch failed: {e}") from e
ValueError: Dataset fetch failed: Couldn't find a dataset script at /home/runner/work/llmXive/llmXive/projects/PROJ-412-predicting-molecular-surface-area-from-g/zinc15/filtered/filtered.py or any data file in the same directory. Couldn't find 'zinc15/filtered' on the Hugging Face Hub either: FileNotFoundError: Dataset 'zinc15/filtered' doesn't exist on the Hub. If the repo is private or gated, make sure to log in with `huggingface-cli login`.

- python code/data/split.py --input data/processed/molecules.parquet --output data/processed/splits/ -> rc=1
2026-10-10 23:40:49,188 - code.utils.logging - INFO - Starting T016: Data Splitting
2026-10-10 23:40:49,188 - code.utils.logging - ERROR - Failed to load processed data: Required input file not found: /home/runner/work/llmXive/llmXive/projects/PROJ-412-predicting-molecular-surface-area-from-g/data/processed/paired_dataset.parquet


- python code/models/train.py --model gcn --config code/config.py -> rc=2

usage: train.py [-h] [--data_path DATA_PATH] [--split_path SPLIT_PATH]
                [--output_path OUTPUT_PATH] [--batch_size BATCH_SIZE]
                [--epochs EPOCHS] [--lr LR] [--seed SEED] [--device DEVICE]
train.py: error: unrecognized arguments: --model gcn --config code/config.py

- python code/models/train.py --model baseline --config code/config.py -> rc=2

usage: train.py [-h] [--data_path DATA_PATH] [--split_path SPLIT_PATH]
                [--output_path OUTPUT_PATH] [--batch_size BATCH_SIZE]
                [--epochs EPOCHS] [--lr LR] [--seed SEED] [--device DEVICE]
train.py: error: unrecognized arguments: --model baseline --config code/config.py

- python code/eval.py --models artifacts/gcn_model.pt artifacts/baseline_model.pt --test data/processed/splits/test.parquet -> rc=2

/home/runner/work/llmXive/llmXive/projects/PROJ-412-predicting-molecular-surface-area-from-g/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-412-predicting-molecular-surface-area-from-g/code/eval.py': [Errno 2] No such file or directory

- python code/eval/sensitivity.py --results artifacts/results.json --thresholds 0.01 0.05 0.1 -> rc=2

usage: sensitivity.py [-h] [--predictions PREDICTIONS]
                      [--output-dir OUTPUT_DIR] [--report-dir REPORT_DIR]
                      [--chunk-size CHUNK_SIZE]
                      [--streaming-strategy STREAMING_STRATEGY]
sensitivity.py: error: unrecognized arguments: --results artifacts/results.json --thresholds 0.01 0.05 0.1


## Declared deliverables still missing

- data/processed/descriptors.parquet
- data/processed/graphs_with_features.parquet
- data/processed/paired_dataset.parquet
- data/processed/pilot_report.json
- data/splits/test_indices.csv
- data/splits/train_indices.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/descriptors.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/models/baseline.py` — NOT invoked by the run-book
    - `code/run_quickstart_validation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/descriptors.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/graphs_with_features.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/data/add_molecular_weight.py` — NOT invoked by the run-book
    - `code/data/logging_stats.py` — NOT invoked by the run-book
    - `code/run_comparison.py` — NOT invoked by the run-book
    - `code/run_quickstart_validation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/graphs_with_features.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/paired_dataset.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/data/split.py` — IS a run-book command
    - `code/models/baseline.py` — NOT invoked by the run-book
    - `code/models/train.py` — IS a run-book command
    - `code/run_quickstart_validation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/paired_dataset.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/pilot_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/data/pilot_study.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/pilot_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/splits/test_indices.csv` is declared but was NOT written. Scripts referencing it:
    - `code/data/split.py` — IS a run-book command
    - `code/eval/oracle_evaluation.py` — NOT invoked by the run-book
    - `code/models/train.py` — IS a run-book command
    - `code/run_comparison.py` — NOT invoked by the run-book
    - `code/run_dry_run.py` — NOT invoked by the run-book
    - `code/run_quickstart_validation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/splits/test_indices.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/splits/train_indices.csv` is declared but was NOT written. Scripts referencing it:
    - `code/data/split.py` — IS a run-book command
    - `code/models/train.py` — IS a run-book command
    - `code/run_comparison.py` — NOT invoked by the run-book
    - `code/run_dry_run.py` — NOT invoked by the run-book
    - `code/run_quickstart_validation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/splits/train_indices.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
