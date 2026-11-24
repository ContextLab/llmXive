# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/src/router_evaluation.py: self-declared fabricated metric — “…uter...")     model = None  # Placeholder     metrics = {         "accuracy": 0.0,…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 fabricated/simulated-result signal(s) — results are not real measurements: code/src/router_evaluation.py: self-declared fabricated metric — “…uter...")     model = None  # Placeholder     metrics = {         "accuracy": 0.0,…”; 1 run-book script(s) missing (plan/impl path mismatch): bash ./run_gpu.sh; 2 command(s) failed: python -m src.run_pipeline --mode full (rc=1); python -m src.verify_artifacts (rc=1); 3 declared deliverable(s) absent: data/processed/convergence_results_core.csv; data/processed/convergence_results_sensitivity.csv; data/processed/entropy_results.csv

## Failing / missing run-book commands

- python -m src.run_pipeline --mode full -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-979-llmxive-follow-up-extending-loopcoder-v2/bin/python: No module named src.run_pipeline

- bash ./run_gpu.sh -> rc=-1

shell script must be an existing project-local .sh file
- python -m src.verify_artifacts -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-979-llmxive-follow-up-extending-loopcoder-v2/bin/python: No module named src.verify_artifacts


## Declared deliverables still missing

- data/processed/convergence_results_core.csv
- data/processed/convergence_results_sensitivity.csv
- data/processed/entropy_results.csv

## ✅ VERIFIED REAL DATA SOURCE — use THIS in the data loader

Do NOT invent or guess a download URL/API (a hallucinated endpoint will 404). A real source was discovered AND verified by actually loading real data from it:

- **Install**: add `datasets` to the project's `requirements.txt` and `pip install datasets`.
- **Verified**: this loads **164** real records with fields: task_id, prompt, canonical_solution, test, entry_point.
- **Working access recipe** (this EXACT code was executed and returned real data — base the loader on it):

```python
import sys
from datasets import load_dataset, concatenate_datasets

# Load the full HumanEval dataset (namespace/name required)
ds_dict = load_dataset("openai/openai_humaneval")

# Merge all available splits into a single Dataset
all_ds = concatenate_datasets([ds_dict[split] for split in ds_dict])

record_count = len(all_ds)
if record_count == 0:
    raise ValueError("No records loaded")

print(f"RECORDS={record_count}")

sample = all_ds[0]
print(f"FIELDS={','.join(sample.keys())}")
```

Write the loader to use this source/recipe, persist the records to the declared raw/processed data files, and DELETE any old code that fetches from a guessed website endpoint.

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/convergence_results_core.csv` is declared but was NOT written. Scripts referencing it:
    - `code/scripts/run_merge_convergence.py` — NOT invoked by the run-book
    - `code/scripts/run_router_training.py` — NOT invoked by the run-book
    - `code/scripts/run_survival_assumptions.py` — NOT invoked by the run-book
    - `code/src/inference.py` — NOT invoked by the run-book
    - `code/src/robustness.py` — NOT invoked by the run-book
    - `code/src/router_evaluation.py` — NOT invoked by the run-book
    - `code/tests/test_robustness.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/convergence_results_core.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/convergence_results_sensitivity.csv` is declared but was NOT written. Scripts referencing it:
    - `code/scripts/run_inference_sensitivity.py` — NOT invoked by the run-book
    - `code/scripts/run_merge_convergence.py` — NOT invoked by the run-book
    - `code/tests/test_robustness.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/convergence_results_sensitivity.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/entropy_results.csv` is declared but was NOT written. Scripts referencing it:
    - `code/scripts/run_entropy.py` — NOT invoked by the run-book
    - `code/scripts/run_model_pilot.py` — NOT invoked by the run-book
    - `code/scripts/run_router_integration.py` — NOT invoked by the run-book
    - `code/scripts/run_router_training.py` — NOT invoked by the run-book
    - `code/scripts/run_survival_assumptions.py` — NOT invoked by the run-book
    - `code/src/aggregation.py` — NOT invoked by the run-book
    - `code/src/analysis.py` — NOT invoked by the run-book
    - `code/src/entropy.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/entropy_results.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
