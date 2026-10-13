# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/analysis/train.py: synthetic/fake INPUT data not authorized by the spec — “…Data]:         """Create dummy graph data objects from feature vec…”

## ⚠ DATA-UNAVAILABLE failure — switch to a REAL, REACHABLE data source

These commands failed because the external dataset is NOT reachable AS WRITTEN on the free CI runner: a Hugging Face dataset that was renamed (canonical names like `openai_humaneval` now require a `namespace/name`), had its loading script removed (`datasets` >= 3 dropped `trust_remote_code` script datasets), is gated, or needs network the runner lacks. RE-TRYING THE DOWNLOAD AS-IS WILL NEVER SUCCEED. Fix it with REAL data, in this order:

1. CORRECT the source: use the dataset's current canonical id (`namespace/name`), a public mirror, or a direct file URL, and stream / download only a SMALL REAL SAMPLE (the first N rows, one split, a few files). A verified real source may be injected below — use it.
2. If that exact dataset is truly unreachable, switch to a DIFFERENT but genuinely-public dataset that supports the SAME analysis/metric, and say so honestly in the README.
3. Do NOT substitute synthetic / fake / hand-built data for the real dataset. A result computed on invented data is NOT a real finding and is REJECTED by the deterministic fabrication gate — swapping in synthetic data is the single most common reason this loop never converges. The ONLY exception is a project whose OWN research question is about synthetic / simulated data (its idea says so).
4. If, after the above, NO real data can be obtained on the CI runner, do NOT fabricate a result: leave the run to FAIL so it escalates honestly (model-tier escalation / re-plan), rather than producing a fake finding.

- `python code/data/download.py`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 fabricated/simulated-result signal(s) — results are not real measurements: code/analysis/train.py: synthetic/fake INPUT data not authorized by the spec — “…Data]:         """Create dummy graph data objects from feature vec…”; 2 command(s) failed: python code/data/download.py (rc=1); python code/analysis/train.py --config config.yaml (rc=1); 4 declared deliverable(s) absent: data/processed/processed_data.csv; data/processed/test.csv; data/processed/train.csv

## Failing / missing run-book commands

- python code/data/download.py -> rc=1

2026-10-13 13:17:22,852 INFO DataLoader: Loading dataset delaney (split=train)
2026-10-13 13:17:23,196 INFO httpx2: HTTP Request: HEAD https://huggingface.co/datasets/delaney/resolve/main/README.md "HTTP/1.1 401 Unauthorized"
2026-10-13 13:17:23,196 ERROR DataLoader: Failed to load dataset from Hugging Face: Dataset 'delaney' doesn't exist on the Hub or cannot be accessed.
2026-10-13 13:17:23,196 ERROR __main__: Data download failed: Unable to fetch dataset 'delaney'.

- python code/analysis/train.py --config config.yaml -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-422-predicting-molecular-permeability-coeffi/lib/python3.11/site-packages/torch/jit/_script.py:1491: FutureWarning: `torch.jit.script` is deprecated. Please switch to `torch.compile` or `torch.export`.
  warnings.warn(
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-422-predicting-molecular-permeability-coeffi/code/analysis/train.py", line 27, in <module>
    from models.gnn import MPNN, create_mpnn_model, train_epoch, validate_epoch
ImportError: cannot import name 'create_mpnn_model' from 'models.gnn' (/home/runner/work/llmXive/llmXive/projects/PROJ-422-predicting-molecular-permeability-coeffi/code/models/gnn.py)


## Declared deliverables still missing

- data/processed/processed_data.csv
- data/processed/test.csv
- data/processed/train.csv
- data/raw/checksums.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/processed_data.csv` is declared but was NOT written. Scripts referencing it:
    - `code/data/preprocess.py` — NOT invoked by the run-book
    - `code/data/split.py` — NOT invoked by the run-book
    - `code/models/gnn.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/processed_data.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/test.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/__init__.py` — NOT invoked by the run-book
    - `code/analysis/ablation.py` — NOT invoked by the run-book
    - `code/analysis/comparative_report.py` — NOT invoked by the run-book
    - `code/analysis/evaluate.py` — NOT invoked by the run-book
    - `code/analysis/explain.py` — NOT invoked by the run-book
    - `code/analysis/generate_stratification_report.py` — NOT invoked by the run-book
    - `code/analysis/power_analysis.py` — NOT invoked by the run-book
    - `code/analysis/statistical_tests.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/test.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/train.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/__init__.py` — NOT invoked by the run-book
    - `code/analysis/ablation.py` — NOT invoked by the run-book
    - `code/analysis/comparative_report.py` — NOT invoked by the run-book
    - `code/analysis/evaluate.py` — NOT invoked by the run-book
    - `code/analysis/explain.py` — NOT invoked by the run-book
    - `code/analysis/generate_stratification_report.py` — NOT invoked by the run-book
    - `code/analysis/train.py` — IS a run-book command
    - `code/data/download.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/train.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/checksums.json` is declared but was NOT written. Scripts referencing it:
    - `code/data/download.py` — IS a run-book command
  Make ONE of these WRITE `data/raw/checksums.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
