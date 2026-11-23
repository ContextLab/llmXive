# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/src/analysis/evaluate.py: synthetic/fake INPUT data not authorized by the spec — “…xist_ok=True)          # Mock data for demonstration if rea…”
- code/src/analysis/evaluate.py: synthetic/fake INPUT data not authorized by the spec — “…old results found. Using simulated data for demonstration.")…”

## ⚠ COMPUTE-ENVIRONMENT failure — RE-SCOPE the method, don't just edit the script

These commands failed because the analysis needs hardware the FREE, CPU-only CI runner does NOT have (a GPU/CUDA, 8-bit quantization via bitsandbytes, or more RAM than is available). This is NOT a code bug you can patch by tweaking the failing line — the analysis MUST run on a CPU-only free runner (Constitution IV). RE-SCOPE the approach: drop `load_in_8bit` / `device_map='cuda'` and load in default precision on CPU; use a SMALLER model; REDUCE the dataset subset / sample / batch size; prefer a CPU-tractable method. Change the METHOD, not just the line that threw:

- `python -c "import torch; import rdkit; print('CPU:', torch.cuda.is_available())"`

## ⚠ DATA-UNAVAILABLE failure — switch to a REAL, REACHABLE data source

These commands failed because the external dataset is NOT reachable AS WRITTEN on the free CI runner: a Hugging Face dataset that was renamed (canonical names like `openai_humaneval` now require a `namespace/name`), had its loading script removed (`datasets` >= 3 dropped `trust_remote_code` script datasets), is gated, or needs network the runner lacks. RE-TRYING THE DOWNLOAD AS-IS WILL NEVER SUCCEED. Fix it with REAL data, in this order:

1. CORRECT the source: use the dataset's current canonical id (`namespace/name`), a public mirror, or a direct file URL, and stream / download only a SMALL REAL SAMPLE (the first N rows, one split, a few files). A verified real source may be injected below — use it.
2. If that exact dataset is truly unreachable, switch to a DIFFERENT but genuinely-public dataset that supports the SAME analysis/metric, and say so honestly in the README.
3. Do NOT substitute synthetic / fake / hand-built data for the real dataset. A result computed on invented data is NOT a real finding and is REJECTED by the deterministic fabrication gate — swapping in synthetic data is the single most common reason this loop never converges. The ONLY exception is a project whose OWN research question is about synthetic / simulated data (its idea says so).
4. If, after the above, NO real data can be obtained on the CI runner, do NOT fabricate a result: leave the run to FAIL so it escalates honestly (model-tier escalation / re-plan), rather than producing a fake finding.

- `python code/src/data/download.py --source ufukhaman`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 fabricated/simulated-result signal(s) — results are not real measurements: code/src/analysis/evaluate.py: synthetic/fake INPUT data not authorized by the spec — “…xist_ok=True)          # Mock data for demonstration if rea…”; code/src/analysis/evaluate.py: synthetic/fake INPUT data not authorized by the spec — “…old results found. Using simulated data for demonstration.")…”; 5 command(s) failed: python code/src/data/download.py --source ufukhaman (rc=1); python code/src/data/parse.py --input data/raw/uspto_subset.parquet --output data/processed/graphs.h5 (rc=1); python code/src/analysis/train.py --epochs 200 --patience 5 --device cpu --cv-folds 5 (rc=1)

## Failing / missing run-book commands

- python -c "import torch; import rdkit; print('CPU:', torch.cuda.is_available())" -> rc=1

Traceback (most recent call last):
  File "<string>", line 1, in <module>
ModuleNotFoundError: No module named 'torch'

- python code/src/data/download.py --source ufukhaman -> rc=1

Failed to download/validate USPTO subset: 404 Client Error: Not Found for url: https://raw.githubusercontent.com/ufukhaman/USPTO-Yield-Prediction/main/data/uspto_yield_sample.csv

- python code/src/data/parse.py --input data/raw/uspto_subset.parquet --output data/processed/graphs.h5 -> rc=1
n
    df = pd.read_parquet(args.input)
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-536-predicting-molecular-reactivity-using-gr/lib/python3.11/site-packages/pandas/io/parquet.py", line 670, in read_parquet
    return impl.read(
           ^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-536-predicting-molecular-reactivity-using-gr/lib/python3.11/site-packages/pandas/io/parquet.py", line 265, in read
    path_or_handle, handles, filesystem = _get_path_or_handle(
                                          ^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-536-predicting-molecular-reactivity-using-gr/lib/python3.11/site-packages/pandas/io/parquet.py", line 139, in _get_path_or_handle
    handles = get_handle(
              ^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-536-predicting-molecular-reactivity-using-gr/lib/python3.11/site-packages/pandas/io/common.py", line 872, in get_handle
    handle = open(handle, ioargs.mode)
             ^^^^^^^^^^^^^^^^^^^^^^^^^
FileNotFoundError: [Errno 2] No such file or directory: 'data/raw/uspto_subset.parquet'

- python code/src/analysis/train.py --epochs 200 --patience 5 --device cpu --cv-folds 5 -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-536-predicting-molecular-reactivity-using-gr/code/src/analysis/train.py", line 17, in <module>
    from src.utils.seeding import set_seed, get_seed_hash, DeterministicContext
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-536-predicting-molecular-reactivity-using-gr/code/src/utils/seeding.py", line 15, in <module>
    import torch
ModuleNotFoundError: No module named 'torch'

- python code/src/models/explainers.py --model models/mpnn_fold_1.pt -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-536-predicting-molecular-reactivity-using-gr/code/src/models/explainers.py", line 19, in <module>
    import torch
ModuleNotFoundError: No module named 'torch'

- python code/src/analysis/uncertainty.py --model models/mpnn_fold_1.pt -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-536-predicting-molecular-reactivity-using-gr/code/src/analysis/uncertainty.py", line 17, in <module>
    from src.utils.seeding import set_seed
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-536-predicting-molecular-reactivity-using-gr/code/src/utils/seeding.py", line 15, in <module>
    import torch
ModuleNotFoundError: No module named 'torch'

## Platform-owned paths written inside the project

A script in this project created `.github/` inside the project directory. Those names belong to the platform, and a copy of them here is a SHADOW: the verifier resolves the paths a task names relative to this project, so it reads the shadow instead of canonical state and rejects work on the strength of a stale record.

Write your outputs under `data/`, `figures/`, `code/` and `paper/`. Do not record artifact hashes, run state or project status yourself — the platform owns `state/` and derives hashes at verification time. Delete the directories listed above and drop whatever step created them.
