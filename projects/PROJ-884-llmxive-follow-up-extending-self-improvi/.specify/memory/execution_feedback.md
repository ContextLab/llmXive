# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/bes/population.py: function `_roulette_selection` returns a bare RNG draw (line 305) — a reported value computed from no real input
- code/config.py: self-declared fabricated metric — “…# The task T007b requires a placeholder value that warns if not overwritten…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 fabricated/simulated-result signal(s) — results are not real measurements: code/bes/population.py: function `_roulette_selection` returns a bare RNG draw (line 305) — a reported value computed from no real input; code/config.py: self-declared fabricated metric — “…# The task T007b requires a placeholder value that warns if not overwritten…”; 1 command(s) failed: python -m pytest tests/unit/ (rc=2); 2 declared deliverable(s) absent: data/processed/bes_results.json; data/processed/exclusions.json

## Failing / missing run-book commands

- python -m pytest tests/unit/ -> rc=2
arser.py ______________
ImportError while importing test module '/home/runner/work/llmXive/llmXive/projects/PROJ-884-llmxive-follow-up-extending-self-improvi/tests/unit/test_symbolic_parser.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/importlib/__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
tests/unit/test_symbolic_parser.py:11: in <module>
    from code.symbolic.parser import (
E   ImportError: cannot import name 'main' from 'code.symbolic.parser' (/home/runner/work/llmXive/llmXive/projects/PROJ-884-llmxive-follow-up-extending-self-improvi/code/symbolic/parser.py)
=========================== short test summary info ============================
ERROR tests/unit/test_calibrate_tdp.py
ERROR tests/unit/test_generate_tdp_constant.py
ERROR tests/unit/test_logging.py
ERROR tests/unit/test_population.py
ERROR tests/unit/test_result_aggregator.py
ERROR tests/unit/test_symbolic_parser.py
!!!!!!!!!!!!!!!!!!! Interrupted: 6 errors during collection !!!!!!!!!!!!!!!!!!!!
============================== 6 errors in 0.78s ===============================



## Declared deliverables still missing

- data/processed/bes_results.json
- data/processed/exclusions.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/bes_results.json` is declared but was NOT written. Scripts referencing it:
    - `code/bes/main.py` — NOT invoked by the run-book
    - `code/bes/result_aggregator.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/bes_results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/exclusions.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/final_report_generator.py` — NOT invoked by the run-book
    - `code/bes/evolutionary_loop.py` — NOT invoked by the run-book
    - `code/bes/main.py` — NOT invoked by the run-book
    - `code/bes/result_aggregator.py` — NOT invoked by the run-book
    - `code/symbolic/exclusion_logger.py` — NOT invoked by the run-book
    - `code/symbolic/planner.py` — NOT invoked by the run-book
    - `code/tests/test_symbolic_planner.py` — NOT invoked by the run-book
    - `code/verification/final_artifact_verification.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/exclusions.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
