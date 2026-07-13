# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/sensitivity_analyzer.py: synthetic/fake INPUT data not authorized by the spec — “…resent, we skip to avoid fake data.             if human_co…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 fabricated/simulated-result signal(s) — results are not real measurements: code/sensitivity_analyzer.py: synthetic/fake INPUT data not authorized by the spec — “…resent, we skip to avoid fake data.             if human_co…”; 1 command(s) failed: python code/main.py --num-tasks 100 --output-dir data/processed (rc=2)

## Failing / missing run-book commands

- python code/main.py --num-tasks 100 --output-dir data/processed -> rc=2
    Warning: LLM_API_KEY not found in environment. Local models will be used if available.

usage: main.py [-h] [--dataset DATASET] [--model MODEL]
               [--batch-size BATCH_SIZE]
main.py: error: unrecognized arguments: --num-tasks 100 --output-dir data/processed

## ✅ VERIFIED REAL DATA SOURCE — use THIS in the data loader

Do NOT invent or guess a download URL/API (a hallucinated endpoint will 404). A real, installable source was discovered AND verified by actually loading data from it:

- **Install**: add `datasets` to the project's `requirements.txt` and `pip install datasets`.
- **Verified**: this loads **164** real records with fields: task_id, prompt, canonical_solution, test, entry_point.
- **Working access recipe** (this EXACT code was executed and returned real data — base the loader on it):

```python
import datasets

ds_dict = datasets.load_dataset('openai/openai_humaneval')
total_records = sum(len(split) for split in ds_dict.values())
print(f"RECORDS={total_records}")

first_split = next(iter(ds_dict.values()))
print("FIELDS=" + ",".join(first_split.column_names))
```

Write the loader to use this package/recipe, persist the records to the declared raw/processed data files, and DELETE any old code that fetches from a website endpoint.
