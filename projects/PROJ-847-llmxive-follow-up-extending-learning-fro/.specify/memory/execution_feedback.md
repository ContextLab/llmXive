# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/trainer.py: self-declared fabricated metric — “…U and generates deterministic dummy results suitable for the baseline st…”
- code/trainer.py: self-declared fabricated metric — “…* Computes a deterministic dummy accuracy based on the seed and the…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 fabricated/simulated-result signal(s) — results are not real measurements: code/trainer.py: self-declared fabricated metric — “…U and generates deterministic dummy results suitable for the baseline st…”; code/trainer.py: self-declared fabricated metric — “…* Computes a deterministic dummy accuracy based on the seed and the…”; 4 command(s) failed: python code/data.py --download (rc=1); python -m code.run_experiments  --mode fixed  --rhos 0.1 0.3 0.5 0.7 0.9  --seeds 42 43 44  --output outputs/fixed_baselines.csv (rc=1); python -m code.run_experiments  --mode adaptive  --seeds 42 43 44  --output outputs/adaptive_run.json (rc=1); 1 declared deliverable(s) absent: data/results/fixed_baselines.csv

## Failing / missing run-book commands

- python code/data.py --download -> rc=1
/llmXive/llmXive/projects/PROJ-847-llmxive-follow-up-extending-learning-fro/code/data.py", line 252, in main
    download_all()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-847-llmxive-follow-up-extending-learning-fro/code/data.py", line 199, in download_all
    n_gsm = _snapshot_to_jsonl(
            ^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-847-llmxive-follow-up-extending-learning-fro/code/data.py", line 175, in _snapshot_to_jsonl
    for row in iterable:
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-847-llmxive-follow-up-extending-learning-fro/code/data.py", line 101, in _fetch_parquet
    raise RuntimeError(
RuntimeError: Failed to parse Parquet file for openai/gsm8k/main/test: Unable to find a usable engine; tried using: 'pyarrow', 'fastparquet'.
A suitable version of pyarrow or fastparquet is required for parquet support.
Trying to import the above resulted in these errors:
 - Missing optional dependency 'pyarrow'. pyarrow is required for parquet support. Use pip or conda to install pyarrow.
 - Missing optional dependency 'fastparquet'. fastparquet is required for parquet support. Use pip or conda to install fastparquet.

- python -m code.run_experiments  --mode fixed  --rhos 0.1 0.3 0.5 0.7 0.9  --seeds 42 43 44  --output outputs/fixed_baselines.csv -> rc=1

2026-10-14 13:11:38,329 ERROR __main__: Failed to import training utilities: No module named 'torch'

- python -m code.run_experiments  --mode adaptive  --seeds 42 43 44  --output outputs/adaptive_run.json -> rc=1

2026-10-14 13:11:38,407 ERROR __main__: Adaptive mode not yet implemented in this task.

- python -m code.analysis  --fixed outputs/fixed_baselines.csv  --adaptive outputs/adaptive_run.json  --outdir outputs/statistics -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-847-llmxive-follow-up-extending-learning-fro/bin/python: No module named code.analysis


## Declared deliverables still missing

- data/results/fixed_baselines.csv

## ✅ VERIFIED REAL DATA SOURCE — use THIS in the data loader

Do NOT invent or guess a download URL/API (a hallucinated endpoint will 404). A real source was discovered AND verified by actually loading real data from it:

- **Install**: add `datasets` to the project's `requirements.txt` and `pip install datasets`.
- **Verified**: this loads **7473** real records with fields: question, answer.
- **Working access recipe** (this EXACT code was executed and returned real data — base the loader on it):

```python
import sys
from datasets import load_dataset

# Load the full GSM8K training split using the required config name
ds = load_dataset('openai/gsm8k', 'main', split='train')

records = len(ds)
print(f'RECORDS={records}')

fields = ds.column_names
print('FIELDS=' + ','.join(fields))
```

Write the loader to use this source/recipe, persist the records to the declared raw/processed data files, and DELETE any old code that fetches from a guessed website endpoint.

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/results/fixed_baselines.csv` is declared but was NOT written. Scripts referencing it:
    - `code/run_experiments.py` — IS a run-book command
    - `code/trainer.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/fixed_baselines.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
