# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/data/generator.py: synthetic/fake INPUT data not authorized by the spec — “…er(         description="Generate synthetic ALE execution traces for…”
- code/data/golden_set_generator.py: synthetic/fake INPUT data not authorized by the spec — “…er(         description="Generate automated synthetic ground truth subset (T01…”
- code/intervention/runner.py: synthetic/fake INPUT data not authorized by the spec — “…[ExecutionTrace]:     """Generate synthetic traces for execution whe…”
- code/intervention/runner.py: synthetic/fake INPUT data not authorized by the spec — “…ror:         # Fallback: generate synthetic traces         logger.wa…”

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python code/data/generator.py --seed 42 --num-tasks a sufficient batch size`
  - script usage: `generator.py [-h] [--seed SEED] [--num-tasks NUM_TASKS]`
  - argparse error: `generator.py: error: argument --num-tasks: invalid int value: 'a'`
- run-book command: `python code/analysis/sensitivity.py --results data/processed/experiment_results.json --intervals,3,5 --output data/processed/sensitivity_analysis.json`
  - script usage: `sensitivity.py [-h] [--results RESULTS] [--intervals INTERVALS]`
  - argparse error: `sensitivity.py: error: unrecognized arguments: --intervals,3,5`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 4 fabricated/simulated-result signal(s) — results are not real measurements: code/data/generator.py: synthetic/fake INPUT data not authorized by the spec — “…er(         description="Generate synthetic ALE execution traces for…”; code/data/golden_set_generator.py: synthetic/fake INPUT data not authorized by the spec — “…er(         description="Generate automated synthetic ground truth subset (T01…”; code/intervention/runner.py: synthetic/fake INPUT data not authorized by the spec — “…[ExecutionTrace]:     """Generate synthetic traces for execution whe…”; 12 command(s) failed: python code/data/generator.py --seed 42 --num-tasks a sufficient batch size (rc=2); python code/utils/verify_checksums.py (rc=1); python code/classification/parser.py --input data/raw/synthetic_ale.jsonl --output data/processed/classified_traces.json (rc=1); 6 declared deliverable(s) absent: data/processed/classification_report.json; data/processed/sensitivity_N1.json; data/processed/sensitivity_N3.json

## Failing / missing run-book commands

- python code/data/generator.py --seed 42 --num-tasks a sufficient batch size -> rc=2

usage: generator.py [-h] [--seed SEED] [--num-tasks NUM_TASKS]
                    [--output OUTPUT]
generator.py: error: argument --num-tasks: invalid int value: 'a'

- python code/utils/verify_checksums.py -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-840-llmxive-follow-up-extending-agents-last/code/utils/verify_checksums.py", line 8, in <module>
    from utils.seeds import verify_pairing
ImportError: cannot import name 'verify_pairing' from 'utils.seeds' (/home/runner/work/llmXive/llmXive/projects/PROJ-840-llmxive-follow-up-extending-agents-last/code/utils/seeds.py)

- python code/classification/parser.py --input data/raw/synthetic_ale.jsonl --output data/processed/classified_traces.json -> rc=1
Error parsing traces: Input file not found: data/raw/synthetic_ale.jsonl

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-840-llmxive-follow-up-extending-agents-last/code/classification/parser.py", line 135, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-840-llmxive-follow-up-extending-agents-last/code/classification/parser.py", line 123, in main
    parsed_data = parse_ale_trace(input_path)
                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-840-llmxive-follow-up-extending-agents-last/code/classification/parser.py", line 18, in parse_ale_trace
    raise FileNotFoundError(f"Input file not found: {input_path}")
FileNotFoundError: Input file not found: data/raw/synthetic_ale.jsonl

- python code/classification/validator.py --input data/processed/classified_traces.json --golden data/raw/golden_set.json -> rc=1

Input file not found: data/processed/classified_traces.json

- python code/intervention/runner.py --condition baseline --model models/llama-3-8b-instruct.Q4_K_M.gguf --seed 42 --output data/processed/baseline_results.json -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-840-llmxive-follow-up-extending-agents-last/code/intervention/runner.py", line 15, in <module>
    from data.generator import ExecutionTrace, FailureType, generate_trace
ModuleNotFoundError: No module named 'data.generator'

- python code/intervention/runner.py --condition intervention --checkpoint-interval 3 --model models/llama-3-8b-instruct.Q4_K_M.gguf --seed 42 --output data/processed/intervention_results.json -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-840-llmxive-follow-up-extending-agents-last/code/intervention/runner.py", line 15, in <module>
    from data.generator import ExecutionTrace, FailureType, generate_trace
ModuleNotFoundError: No module named 'data.generator'

- python code/analysis/stats.py --baseline data/processed/baseline_results.json --intervention data/processed/intervention_results.json --output data/processed/stats_report.json -> rc=1

Error running analysis: [Errno 2] No such file or directory: 'data/processed/baseline_results.json'

- python code/analysis/sensitivity.py --results data/processed/experiment_results.json --intervals,3,5 --output data/processed/sensitivity_analysis.json -> rc=2

usage: sensitivity.py [-h] [--results RESULTS] [--intervals INTERVALS]
                      [--output OUTPUT]
sensitivity.py: error: unrecognized arguments: --intervals,3,5

- python code/utils/generate_report.py --stats data/processed/stats_report.json --sensitivity data/processed/sensitivity_analysis.json --output docs/report.md -> rc=1

Stats file not found: data/processed/stats_report.json

- python -m pytest tests/unit/ -v -> rc=2
1-6f1866971868/_pytest/pathlib.py:591: in import_path
    importlib.import_module(module_name)
/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/importlib/__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
<frozen importlib._bootstrap>:1204: in _gcd_import
    ???
<frozen importlib._bootstrap>:1176: in _find_and_load
    ???
<frozen importlib._bootstrap>:1147: in _find_and_load_unlocked
    ???
<frozen importlib._bootstrap>:690: in _load_unlocked
    ???
/home/runner/.cache/llmxive/base-env/py311-6f1866971868/_pytest/assertion/rewrite.py:178: in exec_module
    exec(co, module.__dict__)
tests/unit/test_generator.py:10: in <module>
    from code.data.generator import (
E   ImportError: cannot import name 'FileState' from 'code.data.generator' (/home/runner/work/llmXive/llmXive/projects/PROJ-840-llmxive-follow-up-extending-agents-last/code/data/generator.py)
=========================== short test summary info ============================
ERROR tests/unit/test_generator.py
!!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
=============================== 1 error in 0.41s ===============================


- python -m pytest tests/integration/ -v -> rc=2
tlib._bootstrap>:1176: in _find_and_load
    ???
<frozen importlib._bootstrap>:1147: in _find_and_load_unlocked
    ???
<frozen importlib._bootstrap>:690: in _load_unlocked
    ???
/home/runner/.cache/llmxive/base-env/py311-6f1866971868/_pytest/assertion/rewrite.py:178: in exec_module
    exec(co, module.__dict__)
tests/integration/test_wrapper.py:19: in <module>
    from code.intervention.wrapper import ContextCheckpointWrapper, run_intervention
E   ImportError: cannot import name 'run_intervention' from 'code.intervention.wrapper' (/home/runner/work/llmXive/llmXive/projects/PROJ-840-llmxive-follow-up-extending-agents-last/code/intervention/wrapper.py)
=========================== short test summary info ============================
ERROR tests/integration/test_classification_golden.py
ERROR tests/integration/test_data_generation.py
ERROR tests/integration/test_experiment_execution.py
ERROR tests/integration/test_memory_limit.py
ERROR tests/integration/test_quickstart_validation.py
ERROR tests/integration/test_wrapper.py
!!!!!!!!!!!!!!!!!!! Interrupted: 6 errors during collection !!!!!!!!!!!!!!!!!!!!
============================== 6 errors in 0.23s ===============================


- python -m pytest tests/contract/ -v -> rc=5
============================= test session starts ==============================
platform linux -- Python 3.11.17, pytest-8.2.0, pluggy-1.6.0 -- /home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-840-llmxive-follow-up-extending-agents-last/bin/python
cachedir: .pytest_cache
rootdir: /home/runner/work/llmXive/llmXive/projects/PROJ-840-llmxive-follow-up-extending-agents-last
configfile: pyproject.toml
plugins: anyio-4.15.1
collecting ... collected 0 items

============================ no tests ran in 0.00s =============================



## Declared deliverables still missing

- data/processed/classification_report.json
- data/processed/sensitivity_N1.json
- data/processed/sensitivity_N3.json
- data/processed/sensitivity_N5.json
- data/processed/sensitivity_analysis.json
- data/processed/static_constraints.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/classification_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/classification/report_generator.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/classification_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/sensitivity_N1.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/sensitivity_aggregator.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/sensitivity_N1.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/sensitivity_N3.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/sensitivity_aggregator.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/sensitivity_N3.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/sensitivity_N5.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/sensitivity_aggregator.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/sensitivity_N5.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/sensitivity_analysis.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/report_generator.py` — NOT invoked by the run-book
    - `code/analysis/sensitivity.py` — IS a run-book command
    - `code/analysis/sensitivity_aggregator.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/sensitivity_analysis.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/static_constraints.json` is declared but was NOT written. Scripts referencing it:
    - `code/classification/goal_validator.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/static_constraints.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
