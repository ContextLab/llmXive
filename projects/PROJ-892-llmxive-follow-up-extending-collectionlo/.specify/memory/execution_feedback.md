# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/statistical_analysis.py: self-declared fabricated metric — “…ambi     # For now, we return mock results     return {         "poster…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 fabricated/simulated-result signal(s) — results are not real measurements: code/statistical_analysis.py: self-declared fabricated metric — “…ambi     # For now, we return mock results     return {         "poster…”; 2 command(s) failed: python code/main.py --phase prepare (rc=1); python code/main.py --phase analyze (rc=1); 4 declared deliverable(s) absent: data/analysis_results.json; data/references/other_effect_refs.json; data/results.csv

## Failing / missing run-book commands

- python code/main.py --phase prepare -> rc=1
    line 210, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-892-llmxive-follow-up-extending-collectionlo/code/main.py", line 174, in main
    run_baseline_generation_loop()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-892-llmxive-follow-up-extending-collectionlo/code/main.py", line 128, in run_baseline_generation_loop
    results = run_fp16_generation(prompts, seeds, config)
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-892-llmxive-follow-up-extending-collectionlo/code/main.py", line 47, in run_fp16_generation
    adapter, base_model = load_fp16_adapter_and_base_model()
                          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-892-llmxive-follow-up-extending-collectionlo/code/data_loader.py", line 144, in load_fp16_adapter_and_base_model
    raise FileNotFoundError(f"FP16 adapter not found at {adapter_path}. Run T002 first.")
FileNotFoundError: FP16 adapter not found at /home/runner/work/llmXive/llmXive/projects/PROJ-892-llmxive-follow-up-extending-collectionlo/data/models/collection_lora.safetensors. Run T002 first.
- python code/main.py --phase analyze -> rc=1
    v
2026-09-07 21:49:55,208 - ERROR - Pipeline failed: Results file not found at /home/runner/work/llmXive/llmXive/projects/PROJ-892-llmxive-follow-up-extending-collectionlo/data/results.csv
2026-09-07 21:49:55,208 - INFO - CI timing recorded: 0.27s
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-892-llmxive-follow-up-extending-collectionlo/code/main.py", line 210, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-892-llmxive-follow-up-extending-collectionlo/code/main.py", line 192, in main
    analysis_main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-892-llmxive-follow-up-extending-collectionlo/code/statistical_analysis.py", line 136, in main
    results_df = load_results_data()
                 ^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-892-llmxive-follow-up-extending-collectionlo/code/statistical_analysis.py", line 23, in load_results_data
    raise FileNotFoundError(f"Results file not found at {results_path}")
FileNotFoundError: Results file not found at /home/runner/work/llmXive/llmXive/projects/PROJ-892-llmxive-follow-up-extending-collectionlo/data/results.csv

## Declared deliverables still missing

- data/analysis_results.json
- data/references/other_effect_refs.json
- data/results.csv
- data/subspace_ranks_merged.json

## ✅ VERIFIED REAL DATA SOURCE — use THIS in the data loader

Do NOT invent or guess a download URL/API (a hallucinated endpoint will 404). A real source was discovered AND verified by actually loading real data from it:

- **Install**: add `pycocotools` to the project's `requirements.txt` and `pip install pycocotools`.
- **Verified**: this loads **25014** real records with fields: image_id, id, caption.
- **Working access recipe** (this EXACT code was executed and returned real data — base the loader on it):

```python
import os, urllib.request, zipfile, tempfile
from pycocotools.coco import COCO

url = "http://images.cocodataset.org/annotations/annotations_trainval2017.zip"
tmp_dir = tempfile.mkdtemp()
zip_path = os.path.join(tmp_dir, "coco_ann.zip")
urllib.request.urlretrieve(url, zip_path)

target = "annotations/captions_val2017.json"
json_path = os.path.join(tmp_dir, "captions_val2017.json")
with zipfile.ZipFile(zip_path, "r") as z:
    with z.open(target) as src, open(json_path, "wb") as dst:
        dst.write(src.read())

coco = COCO(json_path)
ann_ids = coco.getAnnIds()
print(f"RECORDS={len(ann_ids)}")
sample_ann = coco.loadAnns(ann_ids[:1])[0]
print("FIELDS=" + ",".join(sample_ann.keys()))
```

Write the loader to use this source/recipe, persist the records to the declared raw/processed data files, and DELETE any old code that fetches from a guessed website endpoint.

## ⚠ SHARED-MODULE CONTRACT — fix the DEFINITION, tolerant of ALL callers

One or more failures are API-CONTRACT errors on a symbol YOUR OWN code defines and that MANY scripts call in DIFFERENT ways. Rewriting the definition to match one caller breaks the others — that is why this keeps failing. Fix the DEFINITION **once** so it is compatible with EVERY call site listed below: accept ``*args, **kwargs``, branch on what was actually passed, and NEVER raise on an unexpected call shape. For an auxiliary utility (e.g. logging), doing nothing on an unrecognized shape is fine. Do NOT edit the call sites — edit only the defining module.

**CRITICAL — ADD, do not REPLACE.** Edit the defining module *in place*: ADD the missing methods/parameters and PRESERVE every function, method, and attribute that already exists. Do NOT rewrite the file from scratch and do NOT delete a definition to make room for another. Each round that deletes a previously-working symbol just moves the failure to that symbol next round — an infinite loop. The fix is cumulative: the module must satisfy ALL callers from ALL rounds simultaneously.

**This list is CUMULATIVE across every fix round** — it includes contracts you may have ALREADY satisfied in an earlier round. Keep satisfying them while you fix the rest. Do NOT remove a method or parameter merely because it is absent from this round's traceback; if it is listed here, some script still depends on it.

### `load_fp16_adapter_and_base_model` — defined in `code/data_loader.py`; called 4 way(s):

- code/main.py: adapter, base_model = load_fp16_adapter_and_base_model()
- code/data_loader.py: 1. load_fp16_adapter_and_base_model() - No args, uses defaults
- code/data_loader.py: 2. load_fp16_adapter_and_base_model(adapter_path, base_model_path) - Two positional args
- code/data_loader.py: 3. load_fp16_adapter_and_base_model(adapter_path=..., base_model_path=...) - Keyword args

Make `load_fp16_adapter_and_base_model` in `code/data_loader.py` accept ALL of the above.

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/analysis_results.json` is declared but was NOT written. Scripts referencing it:
    - `code/summary_report.py` — NOT invoked by the run-book
    - `code/statistical_analysis.py` — NOT invoked by the run-book
    - `code/run_e2e_validation.py` — NOT invoked by the run-book
    - `code/main.py` — IS a run-book command
  Make ONE of these WRITE `data/analysis_results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/references/other_effect_refs.json` is declared but was NOT written. Scripts referencing it:
    - `code/dependency_checker.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/references/other_effect_refs.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/results.csv` is declared but was NOT written. Scripts referencing it:
    - `code/validate_results.py` — NOT invoked by the run-book
    - `code/generator.py` — NOT invoked by the run-book
    - `code/summary_report.py` — NOT invoked by the run-book
    - `code/final_hash_check.py` — NOT invoked by the run-book
    - `code/quantization_logging.py` — NOT invoked by the run-book
    - `code/statistical_analysis.py` — NOT invoked by the run-book
    - `code/metrics.py` — NOT invoked by the run-book
    - `code/run_e2e_validation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/subspace_ranks_merged.json` is declared but was NOT written. Scripts referencing it:
    - `code/validate_results.py` — NOT invoked by the run-book
    - `code/statistical_analysis.py` — NOT invoked by the run-book
    - `code/main.py` — IS a run-book command
    - `code/dependency_checker.py` — NOT invoked by the run-book
    - `code/data_loader.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/subspace_ranks_merged.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.

## ⚠ CROSS-SCRIPT DATA CONTRACT — make the PRODUCER write what consumers read

One or more failures are DATA-SCHEMA mismatches BETWEEN scripts that exchange a file: a CONSUMER requires column/key names (or a file) that the PRODUCER did not write. The traceback you saw shows only the CONSUMER's EXPECTATION — never the producer's ACTUAL output — which is why this keeps failing. Below is the REAL schema each producer wrote on disk (read from the actual file) versus what the consumers require. Pick ONE canonical schema and make the **PRODUCER** write exactly the columns/keys the consumers read (preferred when one producer feeds several consumers), editing the producer IN PLACE. Do NOT fake or stub the data.

**This list is CUMULATIVE across every fix round** — keep satisfying a contract you already fixed while you fix the rest; do not drop a column merely because it is absent from this round's traceback.

### `home/runner/work/llmXive/llmXive/projects/PROJ-892-llmxive-follow-up-extending-collectionlo/data/results.csv`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/statistical_analysis.py`, `code/run_e2e_validation.py`, `code/main.py`, `code/analyze_subspace_ranks.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `home/runner/work/llmXive/llmXive/projects/PROJ-892-llmxive-follow-up-extending-collectionlo/data/results.csv`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/validate_results.py`, `code/statistical_analysis.py`, `code/run_e2e_validation.py`, `code/main.py`, `code/analyze_subspace_ranks.py`.
