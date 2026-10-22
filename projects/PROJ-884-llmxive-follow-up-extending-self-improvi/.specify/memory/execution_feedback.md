# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/bes/population.py: function `_roulette_selection` returns a bare RNG draw (line 305) — a reported value computed from no real input
- code/config.py: self-declared fabricated metric — “…# The task T007b requires a placeholder value that warns if not overwritten…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 fabricated/simulated-result signal(s) — results are not real measurements: code/bes/population.py: function `_roulette_selection` returns a bare RNG draw (line 305) — a reported value computed from no real input; code/config.py: self-declared fabricated metric — “…# The task T007b requires a placeholder value that warns if not overwritten…”; 6 command(s) failed: python -m code.main --pilot (rc=1); python -m code.main --method symbolic --pop-size 50 --generations 20 --output data/processed/symbolic_run.jsonl (rc=1); python -m code.main --method neural --pop-size 50 --generations 20 --output data/processed/neural_run.jsonl (rc=1); 2 declared deliverable(s) absent: data/processed/bes_results.json; data/processed/exclusions.json

## Failing / missing run-book commands

- python -m code.main --pilot -> rc=1

Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-884-llmxive-follow-up-extending-self-improvi/code/main.py", line 23, in <module>
    from code.bes.forward_step import ForwardStep
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-884-llmxive-follow-up-extending-self-improvi/code/bes/__init__.py", line 10, in <module>
    from .population import Population, Individual, SelectionMethod
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-884-llmxive-follow-up-extending-self-improvi/code/bes/population.py", line 22, in <module>
    from code.bes.backward_step import BackwardStep, BackwardStepResult
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-884-llmxive-follow-up-extending-self-improvi/code/bes/backward_step.py", line 19, in <module>
    from code.symbolic.parser import PuzzleParser, parse_dataset_file
ImportError: cannot import name 'parse_dataset_file' from 'code.symbolic.parser' (/home/runner/work/llmXive/llmXive/projects/PROJ-884-llmxive-follow-up-extending-self-improvi/code/symbolic/parser.py)

- python -m code.main --method symbolic --pop-size 50 --generations 20 --output data/processed/symbolic_run.jsonl -> rc=1

Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-884-llmxive-follow-up-extending-self-improvi/code/main.py", line 23, in <module>
    from code.bes.forward_step import ForwardStep
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-884-llmxive-follow-up-extending-self-improvi/code/bes/__init__.py", line 10, in <module>
    from .population import Population, Individual, SelectionMethod
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-884-llmxive-follow-up-extending-self-improvi/code/bes/population.py", line 22, in <module>
    from code.bes.backward_step import BackwardStep, BackwardStepResult
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-884-llmxive-follow-up-extending-self-improvi/code/bes/backward_step.py", line 19, in <module>
    from code.symbolic.parser import PuzzleParser, parse_dataset_file
ImportError: cannot import name 'parse_dataset_file' from 'code.symbolic.parser' (/home/runner/work/llmXive/llmXive/projects/PROJ-884-llmxive-follow-up-extending-self-improvi/code/symbolic/parser.py)

- python -m code.main --method neural --pop-size 50 --generations 20 --output data/processed/neural_run.jsonl -> rc=1

Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-884-llmxive-follow-up-extending-self-improvi/code/main.py", line 23, in <module>
    from code.bes.forward_step import ForwardStep
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-884-llmxive-follow-up-extending-self-improvi/code/bes/__init__.py", line 10, in <module>
    from .population import Population, Individual, SelectionMethod
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-884-llmxive-follow-up-extending-self-improvi/code/bes/population.py", line 22, in <module>
    from code.bes.backward_step import BackwardStep, BackwardStepResult
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-884-llmxive-follow-up-extending-self-improvi/code/bes/backward_step.py", line 19, in <module>
    from code.symbolic.parser import PuzzleParser, parse_dataset_file
ImportError: cannot import name 'parse_dataset_file' from 'code.symbolic.parser' (/home/runner/work/llmXive/llmXive/projects/PROJ-884-llmxive-follow-up-extending-self-improvi/code/symbolic/parser.py)

- python -m code.analysis.stats --symbolic data/processed/symbolic_run.jsonl --neural data/processed/neural_run.jsonl --output data/processed/results.json -> rc=1
2026-10-22 06:46:10,123 - __main__ - ERROR - Analysis failed: Log file not found: data/processed/symbolic_run.jsonl


- python -m pytest tests/unit/ -> rc=4

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-884-llmxive-follow-up-extending-self-improvi/lib/python3.11/site-packages/_pytest/config/__init__.py:328: PluggyTeardownRaisedWarning: A plugin raised an exception during an old-style hookwrapper teardown.
Plugin: helpconfig, Hook: pytest_cmdline_parse
UsageError: /home/runner/work/llmXive/llmXive/projects/PROJ-884-llmxive-follow-up-extending-self-improvi/pyproject.toml: Invalid value (at line 3, column 18)
For more information see https://pluggy.readthedocs.io/en/stable/api_reference.html#pluggy.PluggyTeardownRaisedWarning
  config = pluginmanager.hook.pytest_cmdline_parse(
ERROR: /home/runner/work/llmXive/llmXive/projects/PROJ-884-llmxive-follow-up-extending-self-improvi/pyproject.toml: Invalid value (at line 3, column 18)


- python -m pytest tests/integration/ -> rc=4

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-884-llmxive-follow-up-extending-self-improvi/lib/python3.11/site-packages/_pytest/config/__init__.py:328: PluggyTeardownRaisedWarning: A plugin raised an exception during an old-style hookwrapper teardown.
Plugin: helpconfig, Hook: pytest_cmdline_parse
UsageError: /home/runner/work/llmXive/llmXive/projects/PROJ-884-llmxive-follow-up-extending-self-improvi/pyproject.toml: Invalid value (at line 3, column 18)
For more information see https://pluggy.readthedocs.io/en/stable/api_reference.html#pluggy.PluggyTeardownRaisedWarning
  config = pluginmanager.hook.pytest_cmdline_parse(
ERROR: /home/runner/work/llmXive/llmXive/projects/PROJ-884-llmxive-follow-up-extending-self-improvi/pyproject.toml: Invalid value (at line 3, column 18)



## Declared deliverables still missing

- data/processed/bes_results.json
- data/processed/exclusions.json

## ✅ VERIFIED REAL DATA SOURCE — use THIS in the data loader

Do NOT invent or guess a download URL/API (a hallucinated endpoint will 404). A real source was discovered AND verified by actually loading real data from it:

- **Install**: add `datasets` to the project's `requirements.txt` and `pip install datasets`.
- **Verified**: this loads **16951130** real records with fields: puzzle, solution, missing, difficulty, set, solving_time.
- **Working access recipe** (this EXACT code was executed and returned real data — base the loader on it):

```python
import sys
from datasets import load_dataset
# Load the Sudoku dataset from Hugging Face Hub
ds = load_dataset("Ritvik19/Sudoku-Dataset", split="train")
records = len(ds)
print(f"RECORDS={records}")
# List the fields (column names) present in the dataset
if records:
    first = ds[0]
    fields = list(first.keys())
    print("FIELDS=" + ",".join(fields))
else:
    print("FIELDS=")
```

Write the loader to use this source/recipe, persist the records to the declared raw/processed data files, and DELETE any old code that fetches from a guessed website endpoint.

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/bes_results.json` is declared but was NOT written. Scripts referencing it:
    - `code/bes/result_aggregator.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/bes_results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/exclusions.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/final_report_generator.py` — NOT invoked by the run-book
    - `code/bes/evolutionary_loop.py` — NOT invoked by the run-book
    - `code/bes/result_aggregator.py` — NOT invoked by the run-book
    - `code/symbolic/exclusion_logger.py` — NOT invoked by the run-book
    - `code/symbolic/parser.py` — NOT invoked by the run-book
    - `code/symbolic/planner.py` — NOT invoked by the run-book
    - `code/verification/final_artifact_verification.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/exclusions.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
