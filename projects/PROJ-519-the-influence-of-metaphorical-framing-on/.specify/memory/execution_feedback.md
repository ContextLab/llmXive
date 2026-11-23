# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/src/survey_interface.py: self-declared fabricated metric — “…# For simulation, we use placeholder values that are valid but not fabri…”

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python code/src/data_ingestion.py --mode simulate --seed 42`
  - script usage: `data_ingestion.py [-h] [--input INPUT] [--output OUTPUT]`
  - argparse error: `data_ingestion.py: error: unrecognized arguments: --mode simulate --seed 42`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 fabricated/simulated-result signal(s) — results are not real measurements: code/src/survey_interface.py: self-declared fabricated metric — “…# For simulation, we use placeholder values that are valid but not fabri…”; 4 run-book script(s) missing (plan/impl path mismatch): python code/src/statistical_modeling.py --analysis anova --input data/processed/experimental_data.csv; python code/src/statistical_modeling.py --analysis regression --input data/processed/discourse_data.csv; python code/src/visualization.py --type anova --output data/derived/figures/; 2 command(s) failed: python code/src/data_ingestion.py --mode simulate --seed 42 (rc=2); python -m pytest code/tests/ -v (rc=2); 4 declared deliverable(s) absent: data/processed/cami_scores.csv; data/processed/experimental_assignments.csv; data/processed/experimental_results.csv

## Failing / missing run-book commands

- python code/src/data_ingestion.py --mode simulate --seed 42 -> rc=2

usage: data_ingestion.py [-h] [--input INPUT] [--output OUTPUT]
data_ingestion.py: error: unrecognized arguments: --mode simulate --seed 42

- python code/src/statistical_modeling.py --analysis anova --input data/processed/experimental_data.csv -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-519-the-influence-of-metaphorical-framing-on/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-519-the-influence-of-metaphorical-framing-on/code/src/statistical_modeling.py': [Errno 2] No such file or directory

- python code/src/statistical_modeling.py --analysis regression --input data/processed/discourse_data.csv -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-519-the-influence-of-metaphorical-framing-on/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-519-the-influence-of-metaphorical-framing-on/code/src/statistical_modeling.py': [Errno 2] No such file or directory

- python code/src/visualization.py --type anova --output data/derived/figures/ -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-519-the-influence-of-metaphorical-framing-on/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-519-the-influence-of-metaphorical-framing-on/code/src/visualization.py': [Errno 2] No such file or directory

- python code/src/visualization.py --type regression --output data/derived/figures/ -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-519-the-influence-of-metaphorical-framing-on/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-519-the-influence-of-metaphorical-framing-on/code/src/visualization.py': [Errno 2] No such file or directory

- python -m pytest code/tests/ -v -> rc=2
module
    return _bootstrap._gcd_import(name[level:], package, level)
code/tests/test_data_validation.py:15: in <module>
    from src.data_validation import (
E   ModuleNotFoundError: No module named 'src.data_validation'
_____________ ERROR collecting code/tests/test_survey_interface.py _____________
ImportError while importing test module '/home/runner/work/llmXive/llmXive/projects/PROJ-519-the-influence-of-metaphorical-framing-on/code/tests/test_survey_interface.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/importlib/__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
code/tests/test_survey_interface.py:17: in <module>
    from src.survey_interface import (
E   ModuleNotFoundError: No module named 'src.survey_interface'
=========================== short test summary info ============================
ERROR code/tests/test_data_validation.py
ERROR code/tests/test_survey_interface.py
!!!!!!!!!!!!!!!!!!! Interrupted: 2 errors during collection !!!!!!!!!!!!!!!!!!!!
============================== 2 errors in 0.09s ===============================



## Declared deliverables still missing

- data/processed/cami_scores.csv
- data/processed/experimental_assignments.csv
- data/processed/experimental_results.csv
- data/raw/survey_responses.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/cami_scores.csv` is declared but was NOT written. Scripts referencing it:
    - `code/src/cami_scoring.py` — NOT invoked by the run-book
    - `src/cami_scoring.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/cami_scores.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/experimental_assignments.csv` is declared but was NOT written. Scripts referencing it:
    - `code/src/experimental_export.py` — NOT invoked by the run-book
    - `code/src/survey_interface.py` — NOT invoked by the run-book
    - `code/tests/test_survey_interface.py` — NOT invoked by the run-book
    - `src/data_ingestion.py` — NOT invoked by the run-book
    - `src/experiment_runner.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/experimental_assignments.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/experimental_results.csv` is declared but was NOT written. Scripts referencing it:
    - `code/src/data_validation.py` — NOT invoked by the run-book
    - `code/src/experimental_export.py` — NOT invoked by the run-book
    - `code/tests/test_data_validation.py` — NOT invoked by the run-book
    - `code/tests/test_experimental_export.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/experimental_results.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/survey_responses.json` is declared but was NOT written. Scripts referencing it:
    - `code/src/cami_scoring.py` — NOT invoked by the run-book
    - `code/src/data_ingestion.py` — IS a run-book command
    - `code/src/experimental_export.py` — NOT invoked by the run-book
    - `code/src/survey_interface.py` — NOT invoked by the run-book
    - `code/tests/test_experimental_export.py` — NOT invoked by the run-book
    - `code/tests/test_survey_interface.py` — NOT invoked by the run-book
    - `src/cami_scoring.py` — NOT invoked by the run-book
    - `src/data_ingestion.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/survey_responses.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
