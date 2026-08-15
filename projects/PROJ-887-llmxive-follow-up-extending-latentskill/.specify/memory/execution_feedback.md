# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/scripts/generate_dummy_index.py: synthetic/fake INPUT data not authorized by the spec — “…red dependency file with dummy data. """ import os import sy…”
- code/src/validation/linearity_check.py: synthetic/fake INPUT data not authorized by the spec — “…ted      by T022c. T022c generates synthetic composite adapters by in…”
- code/src/validation/linearity_check.py: synthetic/fake INPUT data not authorized by the spec — “…k")          # Check for mock data indicator     # The spec…”
- code/src/validation/linearity_check.py: synthetic/fake INPUT data not authorized by the spec — “…"If pairs.yaml contains mock data (due to staged mode), fl…”
- code/src/validation/linearity_check.py: synthetic/fake INPUT data not authorized by the spec — “…logger.warning("Detected mock data in pairs.yaml. Flagging…”

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python src/evaluation/runner.py  --vectors data/processed/skill_vectors.npy  --metadata data/processed/skill_metadata.json  --tasks data/raw/composite_tasks.json  --runs 5  --output data/results/eval_log.csv`
  - script usage: `runner.py [-h] --adapter ADAPTER --task TASK --output OUTPUT`
  - argparse error: `runner.py: error: the following arguments are required: --adapter, --task`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 5 fabricated/simulated-result signal(s) — results are not real measurements: code/scripts/generate_dummy_index.py: synthetic/fake INPUT data not authorized by the spec — “…red dependency file with dummy data. """ import os import sy…”; code/src/validation/linearity_check.py: synthetic/fake INPUT data not authorized by the spec — “…ted      by T022c. T022c generates synthetic composite adapters by in…”; code/src/validation/linearity_check.py: synthetic/fake INPUT data not authorized by the spec — “…k")          # Check for mock data indicator     # The spec…”; 4 command(s) failed: python src/ingestion/download_weights.py --output data/raw (rc=1); python src/ingestion/flatten_lora.py --input data/raw --output data/processed (rc=1); python src/evaluation/runner.py  --vectors data/processed/skill_vectors.npy  --metadata data/processed/skill_metadata.json  --tasks data/raw/composite_tasks.json  --runs 5  --output data/results/eval_log.csv (rc=2); 4 declared deliverable(s) absent: data/processed/skill_index.npz; data/raw/alfworld_weights.npz; data/raw/searchqa_weights.npz

## Failing / missing run-book commands

- python src/ingestion/download_weights.py --output data/raw -> rc=1
    2026-08-15 15:25:32,066 - __main__ - INFO - Starting LoRA weights download and validation
2026-08-15 15:25:32,067 - __main__ - WARNING - No checksum found for alfworld_weights.npz
2026-08-15 15:25:32,067 - __main__ - ERROR - Unexpected error processing alfworld-weights: get_data_path() missing 1 required positional argument: 'relative_path'
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-887-llmxive-follow-up-extending-latentskill/src/ingestion/download_weights.py", line 361, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-887-llmxive-follow-up-extending-latentskill/src/ingestion/download_weights.py", line 319, in main
    output_path = process_dataset(
                  ^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-887-llmxive-follow-up-extending-latentskill/src/ingestion/download_weights.py", line 266, in process_dataset
    data_path = get_data_path()
                ^^^^^^^^^^^^^^^
TypeError: get_data_path() missing 1 required positional argument: 'relative_path'
- python src/ingestion/flatten_lora.py --input data/raw --output data/processed -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-887-llmxive-follow-up-extending-latentskill/src/ingestion/flatten_lora.py", line 24, in <module>
    from src.utils.config import get_data_path, ensure_directories
ImportError: cannot import name 'get_data_path' from 'src.utils.config' (/home/runner/work/llmXive/llmXive/projects/PROJ-887-llmxive-follow-up-extending-latentskill/src/utils/config.py)
- python src/evaluation/runner.py  --vectors data/processed/skill_vectors.npy  --metadata data/processed/skill_metadata.json  --tasks data/raw/composite_tasks.json  --runs 5  --output data/results/eval_log.csv -> rc=2
    usage: runner.py [-h] --adapter ADAPTER --task TASK --output OUTPUT
                 [--model MODEL]
runner.py: error: the following arguments are required: --adapter, --task
- python src/evaluation/stats.py  --input data/results/eval_log.csv  --output data/results/stats_summary.json -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-887-llmxive-follow-up-extending-latentskill/src/evaluation/stats.py", line 13, in <module>
    from src.utils.config import get_project_root, get_results_path
ImportError: cannot import name 'get_results_path' from 'src.utils.config' (/home/runner/work/llmXive/llmXive/projects/PROJ-887-llmxive-follow-up-extending-latentskill/src/utils/config.py)

## Declared deliverables still missing

- data/processed/skill_index.npz
- data/raw/alfworld_weights.npz
- data/raw/searchqa_weights.npz
- data/results/stats_report.json

## ⚠ SHARED-MODULE CONTRACT — fix the DEFINITION, tolerant of ALL callers

One or more failures are API-CONTRACT errors on a symbol YOUR OWN code defines and that MANY scripts call in DIFFERENT ways. Rewriting the definition to match one caller breaks the others — that is why this keeps failing. Fix the DEFINITION **once** so it is compatible with EVERY call site listed below: accept ``*args, **kwargs``, branch on what was actually passed, and NEVER raise on an unexpected call shape. For an auxiliary utility (e.g. logging), doing nothing on an unrecognized shape is fine. Do NOT edit the call sites — edit only the defining module.

**CRITICAL — ADD, do not REPLACE.** Edit the defining module *in place*: ADD the missing methods/parameters and PRESERVE every function, method, and attribute that already exists. Do NOT rewrite the file from scratch and do NOT delete a definition to make room for another. Each round that deletes a previously-working symbol just moves the failure to that symbol next round — an infinite loop. The fix is cumulative: the module must satisfy ALL callers from ALL rounds simultaneously.

**This list is CUMULATIVE across every fix round** — it includes contracts you may have ALREADY satisfied in an earlier round. Keep satisfying them while you fix the rest. Do NOT remove a method or parameter merely because it is absent from this round's traceback; if it is listed here, some script still depends on it.

### `get_data_path` — defined in `code/src/utils/config.py`; called 2 way(s):

- code/src/ingestion/download_weights.py: data_dir = get_data_path() / "raw"
- code/src/retrieval/vector_db.py: data_dir = get_data_path(project_root)

Make `get_data_path` in `code/src/utils/config.py` accept ALL of the above.

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/skill_index.npz` is declared but was NOT written. Scripts referencing it:
    - `code/src/evaluation/run_sensitivity_sweep.py` — NOT invoked by the run-book
    - `code/src/retrieval/vector_db.py` — NOT invoked by the run-book
    - `code/src/retrieval/strategies.py` — NOT invoked by the run-book
    - `code/src/validation/linearity_check.py` — NOT invoked by the run-book
    - `code/tests/unit/test_vector_db.py` — NOT invoked by the run-book
    - `code/tests/unit/test_strategies_serialization.py` — NOT invoked by the run-book
    - `code/tests/unit/test_run_sensitivity_sweep.py` — NOT invoked by the run-book
    - `code/tests/validate/test_linearity_check.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/skill_index.npz` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/raw/alfworld_weights.npz` is declared but was NOT written. Scripts referencing it:
    - `code/src/ingestion/download_weights.py` — NOT invoked by the run-book
    - `code/src/retrieval/vector_db.py` — NOT invoked by the run-book
    - `code/tests/unit/test_vector_db_execution.py` — NOT invoked by the run-book
    - `code/scripts/run_t014b.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/alfworld_weights.npz` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/raw/searchqa_weights.npz` is declared but was NOT written. Scripts referencing it:
    - `code/src/ingestion/download_weights.py` — NOT invoked by the run-book
    - `code/src/retrieval/vector_db.py` — NOT invoked by the run-book
    - `code/tests/unit/test_vector_db_execution.py` — NOT invoked by the run-book
    - `code/scripts/run_t014b.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/searchqa_weights.npz` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/results/stats_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/src/evaluation/stats.py` — NOT invoked by the run-book
    - `code/src/evaluation/report_generator.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/stats_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
