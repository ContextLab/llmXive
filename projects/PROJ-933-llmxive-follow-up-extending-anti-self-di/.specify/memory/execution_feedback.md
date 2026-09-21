# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/data/fetch_utils.py: synthetic/fake INPUT data not authorized by the spec — “…vent silent fallbacks to synthetic data.     """     pass  def l…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 fabricated/simulated-result signal(s) — results are not real measurements: code/data/fetch_utils.py: synthetic/fake INPUT data not authorized by the spec — “…vent silent fallbacks to synthetic data.     """     pass  def l…”; 1 run-book script(s) missing (plan/impl path mismatch): python main.py --mode full --timeout [configured duration]; 2 declared deliverable(s) absent: data/context_splits.json; data/teacher_distribution.json

## Failing / missing run-book commands

- python main.py --mode full --timeout [configured duration] -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-933-llmxive-follow-up-extending-anti-self-di/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-933-llmxive-follow-up-extending-anti-self-di/main.py': [Errno 2] No such file or directory

## Declared deliverables still missing

- data/context_splits.json
- data/teacher_distribution.json

## ✅ VERIFIED REAL DATA SOURCE — use THIS in the data loader

Do NOT invent or guess a download URL/API (a hallucinated endpoint will 404). A real source was discovered AND verified by actually loading real data from it:

- **Install**: add `datasets` to the project's `requirements.txt` and `pip install datasets`.
- **Verified**: this loads **15011** real records with fields: prompt_text, rationale_text.
- **Working access recipe** (this EXACT code was executed and returned real data — base the loader on it):

```python
import datasets, sys
ds = datasets.load_dataset("databricks/databricks-dolly-15k", split="train")
print(f"RECORDS={len(ds)}")
fields = ds.column_names
col_map = {"instruction": "prompt_text", "response": "rationale_text", "rating": "rationale_quality_score"}
present = [col_map[k] for k in col_map if k in fields]
print("FIELDS=" + ",".join(present))
```

Write the loader to use this source/recipe, persist the records to the declared raw/processed data files, and DELETE any old code that fetches from a guessed website endpoint.

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/context_splits.json` is declared but was NOT written. Scripts referencing it:
    - `code/data/validate_artifacts.py` — NOT invoked by the run-book
    - `code/data/test_context_sim.py` — NOT invoked by the run-book
    - `code/data/preprocess.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/context_splits.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/teacher_distribution.json` is declared but was NOT written. Scripts referencing it:
    - `code/data/validate_artifacts.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/teacher_distribution.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
