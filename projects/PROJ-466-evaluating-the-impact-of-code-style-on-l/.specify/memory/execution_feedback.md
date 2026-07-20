# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/generation/tester.py: self-declared fabricated metric — “…ts     # For now, we return a placeholder result     # NOTE: This is a stub -…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 fabricated/simulated-result signal(s) — results are not real measurements: code/generation/tester.py: self-declared fabricated metric — “…ts     # For now, we return a placeholder result     # NOTE: This is a stub -…”; 1 command(s) failed: python code/main.py (rc=1); 4 declared deliverable(s) absent: data/processed/metrics_all.csv; data/processed/metrics_valid.csv; data/processed/samples_all.csv

## Failing / missing run-book commands

- python code/main.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-466-evaluating-the-impact-of-code-style-on-l/code/main.py", line 23, in <module>
    from config.loader import load_config
ModuleNotFoundError: No module named 'config.loader'

## Declared deliverables still missing

- data/processed/metrics_all.csv
- data/processed/metrics_valid.csv
- data/processed/samples_all.csv
- data/processed/samples_valid.csv

## ✅ VERIFIED REAL DATA SOURCE — use THIS in the data loader

Do NOT invent or guess a download URL/API (a hallucinated endpoint will 404). A real source was discovered AND verified by actually loading real data from it:

- **Install**: add `datasets` to the project's `requirements.txt` and `pip install datasets`.
- **Verified**: this loads **164** real records with fields: task_id, prompt, canonical_solution, test, entry_point.
- **Working access recipe** (this EXACT code was executed and returned real data — base the loader on it):

```python
import datasets

ds_dict = datasets.load_dataset("openai/openai_humaneval")
total_records = sum(len(split) for split in ds_dict.values())
print(f"RECORDS={total_records}")

first_split = next(iter(ds_dict.values()))
sample_record = first_split[0]
print("FIELDS=" + ",".join(sample_record.keys()))
```

Write the loader to use this source/recipe, persist the records to the declared raw/processed data files, and DELETE any old code that fetches from a guessed website endpoint.

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/metrics_all.csv` is declared but was NOT written. Scripts referencing it:
    - `code/generation/directories.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/metrics_all.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/metrics_valid.csv` is declared but was NOT written. Scripts referencing it:
    - `code/generation/directories.py` — NOT invoked by the run-book
    - `code/analysis/sensitivity.py` — NOT invoked by the run-book
    - `code/analysis/metrics.py` — NOT invoked by the run-book
    - `code/analysis/reporter.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/metrics_valid.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/samples_all.csv` is declared but was NOT written. Scripts referencing it:
    - `code/generation/directories.py` — NOT invoked by the run-book
    - `code/generation/pipeline.py` — NOT invoked by the run-book
    - `code/generation/generator.py` — NOT invoked by the run-book
    - `code/generation/tester.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/samples_all.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/samples_valid.csv` is declared but was NOT written. Scripts referencing it:
    - `code/generation/directories.py` — NOT invoked by the run-book
    - `code/generation/pipeline.py` — NOT invoked by the run-book
    - `code/analysis/metrics.py` — NOT invoked by the run-book
    - `code/analysis/reporter.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/samples_valid.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
