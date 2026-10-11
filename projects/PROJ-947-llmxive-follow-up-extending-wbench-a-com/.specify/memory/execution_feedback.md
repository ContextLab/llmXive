# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/inference/runner.py: self-declared fabricated metric — “…m                  # Generate dummy scores (in real implementation, the…”
- code/inference/runner.py: metric `physics_score` assigned from an RNG draw (line 135)
- code/inference/runner.py: metric `consistency_score` assigned from an RNG draw (line 136)
- code/inference/runner.py: metric `motion_artifact_score` assigned from an RNG draw (line 137)
- code/utils/errors.py: self-declared fabricated metric — “…all back to synthetic data or mock values     instead of failing loudl…”
- code/utils/errors.py: synthetic/fake INPUT data not authorized by the spec — “…attempts to fall back to synthetic data or mock values     inste…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 6 fabricated/simulated-result signal(s) — results are not real measurements: code/inference/runner.py: self-declared fabricated metric — “…m                  # Generate dummy scores (in real implementation, the…”; code/inference/runner.py: metric `physics_score` assigned from an RNG draw (line 135); code/inference/runner.py: metric `consistency_score` assigned from an RNG draw (line 136); 1 run-book script(s) missing (plan/impl path mismatch): python code/analysis/correlation.py --results data/processed/inference_results.csv --output results/analysis_summary.csv; 4 command(s) failed: python code/data/download_wbench.py (rc=1); python code/entropy/generator.py --input data/raw/first_person.parquet --output data/processed/variants.csv --min-similarity 0.85 (rc=1); python code/inference/runner.py --variants data/processed/variants.csv --output data/processed/inference_results.csv --subsample-size 50 (rc=1); 5 declared deliverable(s) absent: data/processed/complexity_scores.csv; data/processed/fidelity_metrics.csv; data/processed/inference_results.csv

## Failing / missing run-book commands

- python code/data/download_wbench.py -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-947-llmxive-follow-up-extending-wbench-a-com/code/data/download_wbench.py", line 19, in <module>
    from datasets import load_dataset
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-947-llmxive-follow-up-extending-wbench-a-com/lib/python3.11/site-packages/datasets/__init__.py", line 22, in <module>
    from .arrow_dataset import Dataset
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-947-llmxive-follow-up-extending-wbench-a-com/lib/python3.11/site-packages/datasets/arrow_dataset.py", line 59, in <module>
    import pyarrow as pa
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-947-llmxive-follow-up-extending-wbench-a-com/lib/python3.11/site-packages/pyarrow/__init__.py", line 59, in <module>
    from pyarrow.lib import (BuildInfo, CppBuildInfo, RuntimeInfo, set_timezone_db_path,
  File "pyarrow/lib.pyx", line 42, in init pyarrow.lib
ImportError: pyarrow requires NumPy 2.0 or newer, found 1.26.4

- python code/entropy/generator.py --input data/raw/first_person.parquet --output data/processed/variants.csv --min-similarity 0.85 -> rc=1
.py", line 75, in fail_loudly
    raise error_type(full_message)
utils.errors.PipelineError: PipelineError: WBench dataset not found at /home/runner/work/llmXive/llmXive/projects/PROJ-947-llmxive-follow-up-extending-wbench-a-com/data/raw/wbench_dataset. Run download_wbench.py first.

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-947-llmxive-follow-up-extending-wbench-a-com/code/entropy/generator.py", line 375, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-947-llmxive-follow-up-extending-wbench-a-com/code/entropy/generator.py", line 372, in main
    fail_loudly(f"Generation pipeline failed: {str(e)}")
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-947-llmxive-follow-up-extending-wbench-a-com/code/utils/errors.py", line 75, in fail_loudly
    raise error_type(full_message)
utils.errors.PipelineError: PipelineError: Generation pipeline failed: PipelineError: WBench dataset not found at /home/runner/work/llmXive/llmXive/projects/PROJ-947-llmxive-follow-up-extending-wbench-a-com/data/raw/wbench_dataset. Run download_wbench.py first.

- python code/inference/runner.py --variants data/processed/variants.csv --output data/processed/inference_results.csv --subsample-size 50 -> rc=1
rk/llmXive/llmXive/projects/PROJ-947-llmxive-follow-up-extending-wbench-a-com/code/inference/runner.py", line 107, in run_inference_single_case
    if not validate_model_safety(model_id):
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-947-llmxive-follow-up-extending-wbench-a-com/code/inference/models.py", line 198, in validate_model_safety
    _estimate_model_size(model_id)
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-947-llmxive-follow-up-extending-wbench-a-com/code/inference/models.py", line 127, in _estimate_model_size
    fail_loudly(f"Failed to verify model {model_id} safety: {str(e)}")
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-947-llmxive-follow-up-extending-wbench-a-com/code/utils/logging.py", line 215, in fail_loudly
    raise RuntimeError(message)
RuntimeError: Failed to verify model test_model_v1 safety: test_model_v1 is not a local folder and is not a valid model identifier listed on 'https://huggingface.co/models'
If this is a private repository, make sure to pass a token having permission to this repo with `use_auth_token` or log in with `huggingface-cli login` and pass `use_auth_token=True`.

- python code/analysis/correlation.py --results data/processed/inference_results.csv --output results/analysis_summary.csv -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-947-llmxive-follow-up-extending-wbench-a-com/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-947-llmxive-follow-up-extending-wbench-a-com/code/analysis/correlation.py': [Errno 2] No such file or directory

- python -m pytest tests/ -> rc=2
generator.py)
_____________ ERROR collecting tests/unit/inference/test_runner.py _____________
ImportError while importing test module '/home/runner/work/llmXive/llmXive/projects/PROJ-947-llmxive-follow-up-extending-wbench-a-com/tests/unit/inference/test_runner.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/importlib/__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
tests/unit/inference/test_runner.py:21: in <module>
    from inference.runner import estimate_model_ram_usage, check_ram_budget, ResourceLimitError
E   ImportError: cannot import name 'estimate_model_ram_usage' from 'inference.runner' (/home/runner/work/llmXive/llmXive/projects/PROJ-947-llmxive-follow-up-extending-wbench-a-com/code/inference/runner.py)
=========================== short test summary info ============================
ERROR tests/integration/entropy/test_generator.py
ERROR tests/unit/inference/test_runner.py
!!!!!!!!!!!!!!!!!!! Interrupted: 2 errors during collection !!!!!!!!!!!!!!!!!!!!
========================= 2 skipped, 2 errors in 1.49s =========================



## Declared deliverables still missing

- data/processed/complexity_scores.csv
- data/processed/fidelity_metrics.csv
- data/processed/inference_results.csv
- data/processed/validity_flags.csv
- data/processed/variants.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/complexity_scores.csv` is declared but was NOT written. Scripts referencing it:
    - `code/entropy/run_pipeline.py` — NOT invoked by the run-book
    - `code/entropy/scorer.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/complexity_scores.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/fidelity_metrics.csv` is declared but was NOT written. Scripts referencing it:
    - `code/metrics/wbench_suite.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/fidelity_metrics.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/inference_results.csv` is declared but was NOT written. Scripts referencing it:
    - `code/inference/failure_handler.py` — NOT invoked by the run-book
    - `code/inference/run_inference.py` — NOT invoked by the run-book
    - `code/inference/runner.py` — IS a run-book command
    - `code/metrics/wbench_suite.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/inference_results.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/validity_flags.csv` is declared but was NOT written. Scripts referencing it:
    - `code/entropy/scorer.py` — NOT invoked by the run-book
    - `code/entropy/validator.py` — NOT invoked by the run-book
    - `code/inference/run_inference.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/validity_flags.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/variants.csv` is declared but was NOT written. Scripts referencing it:
    - `code/entropy/generator.py` — IS a run-book command
    - `code/entropy/run_pipeline.py` — NOT invoked by the run-book
    - `code/entropy/run_scorer.py` — NOT invoked by the run-book
    - `code/entropy/scorer.py` — NOT invoked by the run-book
    - `code/entropy/validator.py` — NOT invoked by the run-book
    - `code/inference/run_inference.py` — NOT invoked by the run-book
    - `code/inference/runner.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/variants.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
