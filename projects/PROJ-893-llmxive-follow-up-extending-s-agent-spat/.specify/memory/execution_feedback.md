# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/data/validate_distribution.py: synthetic/fake INPUT data not authorized by the spec — “…population file, we will generate a synthetic reference based on the…”

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python code/solver/run_solver.py --input data/derived/constraints.jsonl --output data/derived/predictions.jsonl`
  - script usage: `run_solver.py [-h] --input INPUT --output OUTPUT --latency-log`
  - argparse error: `run_solver.py: error: the following arguments are required: --latency-log, --exclusion-log`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 fabricated/simulated-result signal(s) — results are not real measurements: code/data/validate_distribution.py: synthetic/fake INPUT data not authorized by the spec — “…population file, we will generate a synthetic reference based on the…”; 7 command(s) failed: python code/data/download.py --sample-size 1000 (rc=1); python code/data/extract_geometry.py --input data/raw --output data/derived/constraints.jsonl (rc=1); python code/solver/run_solver.py --input data/derived/constraints.jsonl --output data/derived/predictions.jsonl (rc=2); 10 declared deliverable(s) absent: data/derived/failure_classification.json; data/derived/solver_failures.json; data/derived/vlm_baseline.csv

## Failing / missing run-book commands

- python code/data/download.py --sample-size 1000 -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-893-llmxive-follow-up-extending-s-agent-spat/code/data/download.py", line 9, in <module>
    from huggingface_hub import HfApi, hf_hub_download, RepositoryNotFoundError
ImportError: cannot import name 'RepositoryNotFoundError' from 'huggingface_hub' (/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-893-llmxive-follow-up-extending-s-agent-spat/lib/python3.11/site-packages/huggingface_hub/__init__.py)

- python code/data/extract_geometry.py --input data/raw --output data/derived/constraints.jsonl -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-893-llmxive-follow-up-extending-s-agent-spat/code/data/extract_geometry.py", line 128, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-893-llmxive-follow-up-extending-s-agent-spat/code/data/extract_geometry.py", line 98, in main
    logger.info(f"Loading scene data from {input_dir}...")
    ^^^^^^^^^^^
AttributeError: 'function' object has no attribute 'info'

- python code/solver/run_solver.py --input data/derived/constraints.jsonl --output data/derived/predictions.jsonl -> rc=2

usage: run_solver.py [-h] --input INPUT --output OUTPUT --latency-log
                     LATENCY_LOG --exclusion-log EXCLUSION_LOG
                     [--wall-clock-log WALL_CLOCK_LOG]
run_solver.py: error: the following arguments are required: --latency-log, --exclusion-log

- python code/benchmark/metrics.py --predictions data/derived/predictions.jsonl --baseline data/raw/merged.csv --output data/derived/benchmark_results.csv -> rc=1
Error: scipy is required. Install with: pip install scipy


- python code/benchmark/analyze_failures.py --results data/derived/benchmark_results.csv --output data/derived/failure_report.json -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-893-llmxive-follow-up-extending-s-agent-spat/code/benchmark/analyze_failures.py", line 91, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-893-llmxive-follow-up-extending-s-agent-spat/code/benchmark/analyze_failures.py", line 88, in main
    analyze_failures(args.results, args.output)
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-893-llmxive-follow-up-extending-s-agent-spat/code/benchmark/analyze_failures.py", line 36, in analyze_failures
    logger.error(f"Benchmark results not found: {results_path}")
    ^^^^^^^^^^^^
AttributeError: 'function' object has no attribute 'error'

- python -m pytest tests/unit/ -> rc=3
^^^^^^^^^^^^^^^^^^^^^^^^
INTERNALERROR>   File "<frozen importlib._bootstrap>", line 1204, in _gcd_import
INTERNALERROR>   File "<frozen importlib._bootstrap>", line 1176, in _find_and_load
INTERNALERROR>   File "<frozen importlib._bootstrap>", line 1147, in _find_and_load_unlocked
INTERNALERROR>   File "<frozen importlib._bootstrap>", line 690, in _load_unlocked
INTERNALERROR>   File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-893-llmxive-follow-up-extending-s-agent-spat/lib/python3.11/site-packages/_pytest/assertion/rewrite.py", line 178, in exec_module
INTERNALERROR>     exec(co, module.__dict__)
INTERNALERROR>   File "/home/runner/work/llmXive/llmXive/projects/PROJ-893-llmxive-follow-up-extending-s-agent-spat/tests/unit/test_metrics.py", line 11, in <module>
INTERNALERROR>     from benchmark.metrics import (
INTERNALERROR>   File "/home/runner/work/llmXive/llmXive/projects/PROJ-893-llmxive-follow-up-extending-s-agent-spat/tests/unit/../../code/benchmark/metrics.py", line 14, in <module>
INTERNALERROR>     sys.exit(1)
INTERNALERROR> SystemExit: 1

============================== 1 skipped in 0.65s ==============================

mainloop: caught unexpected SystemExit!

- python -m pytest tests/integration/test_pipeline.py -> rc=4
============================= test session starts ==============================
platform linux -- Python 3.11.17, pytest-8.2.2, pluggy-1.6.0
rootdir: /home/runner/work/llmXive/llmXive
configfile: pyproject.toml
plugins: anyio-4.15.1
collected 0 items

============================ no tests ran in 0.00s =============================

ERROR: file or directory not found: tests/integration/test_pipeline.py



## Declared deliverables still missing

- data/derived/failure_classification.json
- data/derived/solver_failures.json
- data/derived/vlm_baseline.csv
- data/raw/sampled_manifest.json
- data/results/distribution_validity.json
- data/results/dry_run_status.json
- data/results/pilot_validity.json
- data/results/sensitivity_analysis.csv
- data/results/vlm_trace_audit.json
- data/results/wall_clock_time.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/derived/failure_classification.json` is declared but was NOT written. Scripts referencing it:
    - `code/benchmark/generate_failure_report.py` — NOT invoked by the run-book
    - `code/main.py` — NOT invoked by the run-book
    - `code/validate/acceptance_checker.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/derived/failure_classification.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/derived/solver_failures.json` is declared but was NOT written. Scripts referencing it:
    - `code/main.py` — NOT invoked by the run-book
    - `code/validate/acceptance_checker.py` — NOT invoked by the run-book
    - `code/validate/merge_exclusions.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/derived/solver_failures.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/derived/vlm_baseline.csv` is declared but was NOT written. Scripts referencing it:
    - `code/benchmark/generate_benchmark_results.py` — NOT invoked by the run-book
    - `code/benchmark/sensitivity.py` — NOT invoked by the run-book
    - `code/data/load_vlm_baseline.py` — NOT invoked by the run-book
    - `code/data/validate_vlm_purity.py` — NOT invoked by the run-book
    - `code/main.py` — NOT invoked by the run-book
    - `code/validate/acceptance_checker.py` — NOT invoked by the run-book
    - `code/validate/vlm_audit.py` — NOT invoked by the run-book
    - `code/validate/vlm_trace_auditor.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/derived/vlm_baseline.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/sampled_manifest.json` is declared but was NOT written. Scripts referencing it:
    - `code/data/download.py` — IS a run-book command
    - `code/data/validate_pilot_mode.py` — NOT invoked by the run-book
    - `code/data/verify_checksum.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/sampled_manifest.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/distribution_validity.json` is declared but was NOT written. Scripts referencing it:
    - `code/data/validate_distribution.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/distribution_validity.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/dry_run_status.json` is declared but was NOT written. Scripts referencing it:
    - `code/validate/dry_run.py` — NOT invoked by the run-book
    - `code/validate/vlm_audit.py` — NOT invoked by the run-book
    - `code/validate/vlm_trace_auditor.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/dry_run_status.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/pilot_validity.json` is declared but was NOT written. Scripts referencing it:
    - `code/data/validate_pilot_mode.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/pilot_validity.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/sensitivity_analysis.csv` is declared but was NOT written. Scripts referencing it:
    - `code/benchmark/sensitivity.py` — NOT invoked by the run-book
    - `code/main.py` — NOT invoked by the run-book
    - `code/validate/acceptance_checker.py` — NOT invoked by the run-book
    - `code/validate/final_report_generator.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/sensitivity_analysis.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/vlm_trace_audit.json` is declared but was NOT written. Scripts referencing it:
    - `code/validate/vlm_audit.py` — NOT invoked by the run-book
    - `code/validate/vlm_trace_auditor.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/vlm_trace_audit.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/wall_clock_time.json` is declared but was NOT written. Scripts referencing it:
    - `code/solver/run_solver.py` — IS a run-book command
  Make ONE of these WRITE `data/results/wall_clock_time.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
## Platform-owned paths written inside the project

A script in this project created `state/` inside the project directory. Those names belong to the platform, and a copy of them here is a SHADOW: the verifier resolves the paths a task names relative to this project, so it reads the shadow instead of canonical state and rejects work on the strength of a stale record.

Write your outputs under `data/`, `figures/`, `code/` and `paper/`. Do not record artifact hashes, run state or project status yourself — the platform owns `state/` and derives hashes at verification time. Delete the directories listed above and drop whatever step created them.
