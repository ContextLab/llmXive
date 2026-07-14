# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/bug_detection.py: self-declared fabricated metric — “…st be of float dtype.")     # Placeholder accuracy.     return 0.0   def save_re…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 fabricated/simulated-result signal(s) — results are not real measurements: code/bug_detection.py: self-declared fabricated metric — “…st be of float dtype.")     # Placeholder accuracy.     return 0.0   def save_re…”; 2 command(s) failed: python code/ast_cloner.py (rc=1); python code/quickstart_validation.py (rc=1); 1 declared deliverable(s) absent: data/processed/clone_metrics.csv

## Failing / missing run-book commands

- python code/data_loader.py -> rc=1
    ample
    ds = load_dataset(
         ^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-261-evaluating-the-impact-of-code-duplicatio/code/.venv/lib/python3.11/site-packages/datasets/load.py", line 1698, in load_dataset
    builder_instance = load_dataset_builder(
                       ^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-261-evaluating-the-impact-of-code-duplicatio/code/.venv/lib/python3.11/site-packages/datasets/load.py", line 1325, in load_dataset_builder
    dataset_module = dataset_module_factory(
                     ^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-261-evaluating-the-impact-of-code-duplicatio/code/.venv/lib/python3.11/site-packages/datasets/load.py", line 1217, in dataset_module_factory
    raise e1 from None
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-261-evaluating-the-impact-of-code-duplicatio/code/.venv/lib/python3.11/site-packages/datasets/load.py", line 1177, in dataset_module_factory
    raise RuntimeError(f"Dataset scripts are no longer supported, but found {filename}")
RuntimeError: Dataset scripts are no longer supported, but found github-code.py
- python code/ast_cloner.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-261-evaluating-the-impact-of-code-duplicatio/code/ast_cloner.py", line 19, in <module>
    from .data_loader import download_and_save_sample
ImportError: attempted relative import with no known parent package
- python code/quickstart_validation.py -> rc=1
    ERROR:__main__:Missing required output files: [PosixPath('data/processed/clone_metrics.csv'), PosixPath('data/processed/perplexity_scores.csv')]
ERROR:__main__:Quickstart validation failed: Missing required output files: [PosixPath('data/processed/clone_metrics.csv'), PosixPath('data/processed/perplexity_scores.csv')]
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-261-evaluating-the-impact-of-code-duplicatio/code/quickstart_validation.py", line 29, in main
    validate_output_files()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-261-evaluating-the-impact-of-code-duplicatio/code/quickstart_validation.py", line 24, in validate_output_files
    raise FileNotFoundError(f"Missing required output files: {missing}")
FileNotFoundError: Missing required output files: [PosixPath('data/processed/clone_metrics.csv'), PosixPath('data/processed/perplexity_scores.csv')]

## Declared deliverables still missing

- data/processed/clone_metrics.csv

## ⚠ SHARED-MODULE CONTRACT — fix the DEFINITION, tolerant of ALL callers

One or more failures are API-CONTRACT errors on a symbol YOUR OWN code defines and that MANY scripts call in DIFFERENT ways. Rewriting the definition to match one caller breaks the others — that is why this keeps failing. Fix the DEFINITION **once** so it is compatible with EVERY call site listed below: accept ``*args, **kwargs``, branch on what was actually passed, and NEVER raise on an unexpected call shape. For an auxiliary utility (e.g. logging), doing nothing on an unrecognized shape is fine. Do NOT edit the call sites — edit only the defining module.

**CRITICAL — ADD, do not REPLACE.** Edit the defining module *in place*: ADD the missing methods/parameters and PRESERVE every function, method, and attribute that already exists. Do NOT rewrite the file from scratch and do NOT delete a definition to make room for another. Each round that deletes a previously-working symbol just moves the failure to that symbol next round — an infinite loop. The fix is cumulative: the module must satisfy ALL callers from ALL rounds simultaneously.

**This list is CUMULATIVE across every fix round** — it includes contracts you may have ALREADY satisfied in an earlier round. Keep satisfying them while you fix the rest. Do NOT remove a method or parameter merely because it is absent from this round's traceback; if it is listed here, some script still depends on it.

### `compute_clone_density_batch` — defined in `code/ast_cloner.py`; called 3 way(s):

- code/ast_cloner.py: * ``compute_clone_density_batch()`` – uses the default raw path.
- code/ast_cloner.py: * ``compute_clone_density_batch(raw_path=Path(...))`` – custom path.
- code/main.py: compute_clone_density_batch()

Make `compute_clone_density_batch` in `code/ast_cloner.py` accept ALL of the above.

### `download_and_save_sample` — defined in `code/data_loader.py`; called 5 way(s):

- code/ast_cloner.py: download_and_save_sample(sample_size=20)
- code/main.py: download_and_save_sample(sample_size=100)
- code/data_loader.py: * ``download_and_save_sample()`` – uses the default sample size of 100.
- code/data_loader.py: * ``download_and_save_sample(sample_size=200)`` – custom size.
- code/data_loader.py: * ``download_and_save_sample(path=Path(...), sample_size=…)`` – custom path.

Make `download_and_save_sample` in `code/data_loader.py` accept ALL of the above.

### `setup_memory_monitoring` — defined in `code/memory_monitor.py`; called 1 way(s):

- code/main.py: _ = setup_memory_monitoring()

Make `setup_memory_monitoring` in `code/memory_monitor.py` accept ALL of the above.

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/clone_metrics.csv` is declared but was NOT written. Scripts referencing it:
    - `code/bug_detection.py` — IS a run-book command
    - `code/ast_cloner.py` — IS a run-book command
    - `code/correlation_analysis.py` — IS a run-book command
    - `code/main.py` — NOT invoked by the run-book
    - `code/quickstart_validation.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/clone_metrics.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.

## ⚠ CROSS-SCRIPT DATA CONTRACT — make the PRODUCER write what consumers read

One or more failures are DATA-SCHEMA mismatches BETWEEN scripts that exchange a file: a CONSUMER requires column/key names (or a file) that the PRODUCER did not write. The traceback you saw shows only the CONSUMER's EXPECTATION — never the producer's ACTUAL output — which is why this keeps failing. Below is the REAL schema each producer wrote on disk (read from the actual file) versus what the consumers require. Pick ONE canonical schema and make the **PRODUCER** write exactly the columns/keys the consumers read (preferred when one producer feeds several consumers), editing the producer IN PLACE. Do NOT fake or stub the data.

**This list is CUMULATIVE across every fix round** — keep satisfying a contract you already fixed while you fix the rest; do not drop a column merely because it is absent from this round's traceback.

### `data/processed/clone_metrics.csv`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/model_metrics.py`, `code/bug_detection.py`, `code/ast_cloner.py`, `code/correlation_analysis.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `data/processed/clone_metrics.csv`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/model_metrics.py`, `code/config.py`, `code/bug_detection.py`, `code/ast_cloner.py`, `code/correlation_analysis.py`, `code/main.py`, `code/quickstart_validation.py`.

### `data/raw/github-code-sample.csv`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/ast_cloner.py`, `code/data_loader.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `data/raw/github-code-sample.csv`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/ast_cloner.py`, `code/data_loader.py`.
