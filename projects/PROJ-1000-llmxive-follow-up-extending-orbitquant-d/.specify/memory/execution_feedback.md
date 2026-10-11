# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/run_router_inference.py: self-declared fabricated metric — “…entropy, matrix index, and a placeholder metric structure.…”
- code/runners/router_inference_runner.py: self-declared fabricated metric — “…# For this runner, we simulate the metric collection structure.…”
- code/analysis/clustering.py: synthetic/fake INPUT data not authorized by the spec — “…cluster center values to generate synthetic activations         # th…”
- code/run_quantization_validation.py: synthetic/fake INPUT data not authorized by the spec — “…# We'll create a dummy input to the model's main bloc…”

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python code/main.py --mode full`
  - script usage: `main.py [-h] --phase {init,validate}`
  - argparse error: `main.py: error: the following arguments are required: --phase`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 4 fabricated/simulated-result signal(s) — results are not real measurements: code/run_router_inference.py: self-declared fabricated metric — “…entropy, matrix index, and a placeholder metric structure.…”; code/runners/router_inference_runner.py: self-declared fabricated metric — “…# For this runner, we simulate the metric collection structure.…”; code/analysis/clustering.py: synthetic/fake INPUT data not authorized by the spec — “…cluster center values to generate synthetic activations         # th…”; 4 command(s) failed: python code/data/download_coco.py (rc=1); python code/main.py --mode full (rc=2); python -m pytest tests/unit/ (rc=2); 6 declared deliverable(s) absent: data/processed/clustering_report.json; data/processed/correlation_results.json; data/processed/diverse_prompts.csv

## Failing / missing run-book commands

- python code/data/download_coco.py -> rc=1
0-llmxive-follow-up-extending-orbitquant-d/lib/python3.11/site-packages/datasets/__init__.py", line 17, in <module>
    from .arrow_dataset import Column, Dataset
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-1000-llmxive-follow-up-extending-orbitquant-d/lib/python3.11/site-packages/datasets/arrow_dataset.py", line 59, in <module>
    import pyarrow as pa
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-1000-llmxive-follow-up-extending-orbitquant-d/lib/python3.11/site-packages/pyarrow/__init__.py", line 59, in <module>
    from pyarrow.lib import (BuildInfo, CppBuildInfo, RuntimeInfo, set_timezone_db_path,
  File "pyarrow/lib.pyx", line 42, in init pyarrow.lib
ImportError: pyarrow requires NumPy 2.0 or newer, found 1.26.4

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-1000-llmxive-follow-up-extending-orbitquant-d/code/data/download_coco.py", line 14, in <module>
    raise RuntimeError("The 'datasets' library is required. Please run 'pip install datasets'.")
RuntimeError: The 'datasets' library is required. Please run 'pip install datasets'.

- python code/main.py --mode full -> rc=2

usage: main.py [-h] --phase {init,validate}
main.py: error: the following arguments are required: --phase

- python -m pytest tests/unit/ -> rc=2
1.17/x64/lib/python3.11/importlib/__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
tests/unit/test_validate_clustering.py:15: in <module>
    from validation.validate_clustering import (
E   ImportError: cannot import name 'REQUIRED_TOP_LEVEL_KEYS' from 'validation.validate_clustering' (/home/runner/work/llmXive/llmXive/projects/PROJ-1000-llmxive-follow-up-extending-orbitquant-d/code/validation/validate_clustering.py)
=========================== short test summary info ============================
ERROR tests/unit/test_clustering.py - FileNotFoundError: [Errno 2] No such fi...
ERROR tests/unit/test_download_diverse_prompts.py - RuntimeError: The 'datase...
ERROR tests/unit/test_entropy.py
ERROR tests/unit/test_entropy_edge_cases.py
ERROR tests/unit/test_load_matrices.py
ERROR tests/unit/test_proxy_failure.py
ERROR tests/unit/test_router_inference.py
ERROR tests/unit/test_timing.py - FileNotFoundError: [Errno 2] No such file o...
ERROR tests/unit/test_validate_clustering.py
!!!!!!!!!!!!!!!!!!! Interrupted: 9 errors during collection !!!!!!!!!!!!!!!!!!!!
============================== 9 errors in 3.71s ===============================


- python -m pytest tests/integration/ -> rc=2
e>
    from pyarrow.lib import (BuildInfo, CppBuildInfo, RuntimeInfo, set_timezone_db_path,
pyarrow/lib.pyx:42: in init pyarrow.lib
    ???
E   ImportError: pyarrow requires NumPy 2.0 or newer, found 1.26.4

During handling of the above exception, another exception occurred:
tests/integration/test_preprocess.py:9: in <module>
    from code.data.download_coco import main as download_coco_main
code/data/download_coco.py:14: in <module>
    raise RuntimeError("The 'datasets' library is required. Please run 'pip install datasets'.")
E   RuntimeError: The 'datasets' library is required. Please run 'pip install datasets'.
=========================== short test summary info ============================
ERROR tests/integration/test_activation_variance.py
ERROR tests/integration/test_download_diverse_prompts.py
ERROR tests/integration/test_full_pipeline.py - FileNotFoundError: [Errno 2] ...
ERROR tests/integration/test_generate_correlation_results.py
ERROR tests/integration/test_preprocess.py - RuntimeError: The 'datasets' lib...
!!!!!!!!!!!!!!!!!!! Interrupted: 5 errors during collection !!!!!!!!!!!!!!!!!!!!
============================== 5 errors in 3.14s ===============================



## Declared deliverables still missing

- data/processed/clustering_report.json
- data/processed/correlation_results.json
- data/processed/diverse_prompts.csv
- data/processed/final_evaluation_report.json
- data/processed/prompts.csv
- data/processed/quantized_activations.json

## ✅ VERIFIED REAL DATA SOURCE — use THIS in the data loader

Do NOT invent or guess a download URL/API (a hallucinated endpoint will 404). A real source was discovered AND verified by actually loading real data from it:

- **Install**: add `pycocotools` to the project's `requirements.txt` and `pip install pycocotools`.
- **Verified**: this loads **25014** real records with fields: image_id, file_name, height, width, caption.
- **Working access recipe** (this EXACT code was executed and returned real data — base the loader on it):

```python
import urllib.request, zipfile, json, os, tempfile
url = "http://images.cocodataset.org/annotations/annotations_trainval2017.zip"
with urllib.request.urlopen(url) as resp:
    data = resp.read()
with tempfile.TemporaryDirectory() as td:
    zip_path = os.path.join(td, "coco.zip")
    with open(zip_path, "wb") as f:
        f.write(data)
    with zipfile.ZipFile(zip_path, "r") as z:
        with z.open('annotations/captions_val2017.json') as jf:
            coco_data = json.load(jf)
img_map = {img['id']: img for img in coco_data['images']}
records = []
for ann in coco_data['annotations']:
    img = img_map[ann['image_id']]
    records.append({
        'image_id': ann['image_id'],
        'file_name': img['file_name'],
        'height': img['height'],
        'width': img['width'],
        'caption': ann['caption']
    })
print(f"RECORDS={len(records)}")
print("FIELDS=image_id,file_name,height,width,caption")
```

Write the loader to use this source/recipe, persist the records to the declared raw/processed data files, and DELETE any old code that fetches from a guessed website endpoint.

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/clustering_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/clustering.py` — NOT invoked by the run-book
    - `code/analysis/load_matrices.py` — NOT invoked by the run-book
    - `code/analysis/mse_validator.py` — NOT invoked by the run-book
    - `code/analysis/router.py` — NOT invoked by the run-book
    - `code/analysis/router_api_docs.py` — NOT invoked by the run-book
    - `code/config.py` — NOT invoked by the run-book
    - `code/main.py` — IS a run-book command
    - `code/main_validation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/clustering_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/correlation_results.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/clustering.py` — NOT invoked by the run-book
    - `code/analysis/generate_correlation_results.py` — NOT invoked by the run-book
    - `code/analysis/sensitivity.py` — NOT invoked by the run-book
    - `code/analysis/visualization.py` — NOT invoked by the run-book
    - `code/main_validation.py` — NOT invoked by the run-book
    - `code/run_correlation.py` — NOT invoked by the run-book
    - `code/validation/validate_correlation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/correlation_results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/diverse_prompts.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/entropy_proxy.py` — NOT invoked by the run-book
    - `code/config.py` — NOT invoked by the run-book
    - `code/data/download_diverse_prompts.py` — NOT invoked by the run-book
    - `code/data/preprocess.py` — NOT invoked by the run-book
    - `code/evaluation/timing.py` — NOT invoked by the run-book
    - `code/run_correlation.py` — NOT invoked by the run-book
    - `code/run_evaluation.py` — NOT invoked by the run-book
    - `code/run_router_inference.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/diverse_prompts.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/final_evaluation_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/statistical_test.py` — NOT invoked by the run-book
    - `code/run_evaluation.py` — NOT invoked by the run-book
    - `code/run_evaluation_modular.py` — NOT invoked by the run-book
    - `code/utils/data_streaming.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/final_evaluation_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/prompts.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/correlation.py` — NOT invoked by the run-book
    - `code/analysis/entropy_proxy.py` — NOT invoked by the run-book
    - `code/analysis/sensitivity.py` — NOT invoked by the run-book
    - `code/config.py` — NOT invoked by the run-book
    - `code/data/download_diverse_prompts.py` — NOT invoked by the run-book
    - `code/data/preprocess.py` — NOT invoked by the run-book
    - `code/evaluation/metrics.py` — NOT invoked by the run-book
    - `code/evaluation/timing.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/prompts.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/quantized_activations.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/mse_validator.py` — NOT invoked by the run-book
    - `code/quantization/static_baseline.py` — NOT invoked by the run-book
    - `code/quantization/w2a4_engine.py` — NOT invoked by the run-book
    - `code/run_quantization_validation.py` — NOT invoked by the run-book
    - `code/utils/data_streaming.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/quantized_activations.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
## Platform-owned paths written inside the project

A script in this project created `state/` inside the project directory. Those names belong to the platform, and a copy of them here is a SHADOW: the verifier resolves the paths a task names relative to this project, so it reads the shadow instead of canonical state and rejects work on the strength of a stale record.

Write your outputs under `data/`, `figures/`, `code/` and `paper/`. Do not record artifact hashes, run state or project status yourself — the platform owns `state/` and derives hashes at verification time. Delete the directories listed above and drop whatever step created them.
