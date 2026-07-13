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
    usage: main.py [-h] [--dataset DATASET] [--model MODEL]
               [--batch-size BATCH_SIZE] [--output-dir OUTPUT_DIR]
main.py: error: unrecognized arguments: --num-tasks 100

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

## ⚠ SHARED-MODULE CONTRACT — fix the DEFINITION, tolerant of ALL callers

One or more failures are API-CONTRACT errors on a symbol YOUR OWN code defines and that MANY scripts call in DIFFERENT ways. Rewriting the definition to match one caller breaks the others — that is why this keeps failing. Fix the DEFINITION **once** so it is compatible with EVERY call site listed below: accept ``*args, **kwargs``, branch on what was actually passed, and NEVER raise on an unexpected call shape. For an auxiliary utility (e.g. logging), doing nothing on an unrecognized shape is fine. Do NOT edit the call sites — edit only the defining module.

**CRITICAL — ADD, do not REPLACE.** Edit the defining module *in place*: ADD the missing methods/parameters and PRESERVE every function, method, and attribute that already exists. Do NOT rewrite the file from scratch and do NOT delete a definition to make room for another. Each round that deletes a previously-working symbol just moves the failure to that symbol next round — an infinite loop. The fix is cumulative: the module must satisfy ALL callers from ALL rounds simultaneously.

**This list is CUMULATIVE across every fix round** — it includes contracts you may have ALREADY satisfied in an earlier round. Keep satisfying them while you fix the rest. Do NOT remove a method or parameter merely because it is absent from this round's traceback; if it is listed here, some script still depends on it.

### `get_model_config` — defined in `code/config.py`; called 4 way(s):

- code/config.py: codebase (e.g. ``get_model_config()`` without arguments in ``main.py``).
- code/llm_generator.py: config = get_model_config(candidate_model)
- code/main.py: default=get_model_config().fallback_model,
- code/main.py: model_cfg = get_model_config(args.model)

Make `get_model_config` in `code/config.py` accept ALL of the above.
