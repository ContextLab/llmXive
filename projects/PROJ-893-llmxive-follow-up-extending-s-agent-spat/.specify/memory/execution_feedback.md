# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 5 command(s) failed: python code/data/download.py --sample-size 1000 (rc=1); python code/data/extract_geometry.py --input data/raw --output data/derived/constraints.jsonl (rc=1); python code/solver/run_solver.py --input data/derived/constraints.jsonl --output data/derived/predictions.jsonl (rc=1); 1 declared deliverable(s) absent: data/results/benchmark_results.csv

## Failing / missing run-book commands

- python code/data/download.py --sample-size 1000 -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-893-llmxive-follow-up-extending-s-agent-spat/code/data/download.py", line 20, in <module>
    from huggingface_hub import snapshot_download, hf_hub_download, HfApi, RepositoryNotFoundError, RevisionNotFoundError
ImportError: cannot import name 'RepositoryNotFoundError' from 'huggingface_hub' (/home/runner/work/llmXive/llmXive/projects/PROJ-893-llmxive-follow-up-extending-s-agent-spat/code/.venv/lib/python3.11/site-packages/huggingface_hub/__init__.py)
- python code/data/extract_geometry.py --input data/raw --output data/derived/constraints.jsonl -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-893-llmxive-follow-up-extending-s-agent-spat/code/data/extract_geometry.py", line 21, in <module>
    from data.verify_checksum import verify_directory_integrity
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-893-llmxive-follow-up-extending-s-agent-spat/code/data/verify_checksum.py", line 29, in <module>
    MANIFEST_PATH = CONFIG.DATA_DIR / "manifest.json"
                    ^^^^^^^^^^^^^^^
AttributeError: 'Config' object has no attribute 'DATA_DIR'
- python code/solver/run_solver.py --input data/derived/constraints.jsonl --output data/derived/predictions.jsonl -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-893-llmxive-follow-up-extending-s-agent-spat/code/solver/run_solver.py", line 13, in <module>
    from solver.csp_engine import CSPEngine, SolveResult
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-893-llmxive-follow-up-extending-s-agent-spat/code/solver/csp_engine.py", line 58, in <module>
    class CSPEngine:
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-893-llmxive-follow-up-extending-s-agent-spat/code/solver/csp_engine.py", line 75, in CSPEngine
    def _create_problem(self) -> constraint.Problem:
                                 ^^^^^^^^^^
NameError: name 'constraint' is not defined
- python code/benchmark/metrics.py --predictions data/derived/predictions.jsonl --baseline data/raw/merged.csv --output data/derived/benchmark_results.csv -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-893-llmxive-follow-up-extending-s-agent-spat/code/benchmark/metrics.py", line 303, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-893-llmxive-follow-up-extending-s-agent-spat/code/benchmark/metrics.py", line 253, in main
    predictions_path = config.DERIVED_PATH / "predictions.jsonl"
                       ^^^^^^^^^^^^^^^^^^^
AttributeError: 'Config' object has no attribute 'DERIVED_PATH'
- python code/benchmark/analyze_failures.py --results data/derived/benchmark_results.csv --output data/derived/failure_report.json -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-893-llmxive-follow-up-extending-s-agent-spat/code/benchmark/analyze_failures.py", line 238, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-893-llmxive-follow-up-extending-s-agent-spat/code/benchmark/analyze_failures.py", line 187, in main
    predictions_path = config.DATA_DERIVED / "predictions.jsonl"
                       ^^^^^^^^^^^^^^^^^^^
AttributeError: 'Config' object has no attribute 'DATA_DERIVED'

## Declared deliverables still missing

- data/results/benchmark_results.csv

## ⚠ SHARED-MODULE CONTRACT — fix the DEFINITION, tolerant of ALL callers

One or more failures are API-CONTRACT errors on a symbol YOUR OWN code defines and that MANY scripts call in DIFFERENT ways. Rewriting the definition to match one caller breaks the others — that is why this keeps failing. Fix the DEFINITION **once** so it is compatible with EVERY call site listed below: accept ``*args, **kwargs``, branch on what was actually passed, and NEVER raise on an unexpected call shape. For an auxiliary utility (e.g. logging), doing nothing on an unrecognized shape is fine. Do NOT edit the call sites — edit only the defining module.

**CRITICAL — ADD, do not REPLACE.** Edit the defining module *in place*: ADD the missing methods/parameters and PRESERVE every function, method, and attribute that already exists. Do NOT rewrite the file from scratch and do NOT delete a definition to make room for another. Each round that deletes a previously-working symbol just moves the failure to that symbol next round — an infinite loop. The fix is cumulative: the module must satisfy ALL callers from ALL rounds simultaneously.

**This list is CUMULATIVE across every fix round** — it includes contracts you may have ALREADY satisfied in an earlier round. Keep satisfying them while you fix the rest. Do NOT remove a method or parameter merely because it is absent from this round's traceback; if it is listed here, some script still depends on it.

### class `Config` (in `code/config.py`) — accessed via method/attribute names this round: `DATA_DERIVED`, `DATA_DIR`, `DERIVED_PATH`

`Config` is used like a logger: different scripts call DIFFERENT method names on it, and the set grows every round. Adding only the name(s) above will fail next round on the NEXT name. Make the class tolerant of ANY method name **without removing the ones it already has**, by either:
  1. defining the full method set explicitly (keep existing methods like the ones already in `code/config.py` AND add the missing ones), or
  2. adding a permissive fallback so unknown attributes resolve to a no-op callable, e.g.:

     ```python
     def __getattr__(self, name):
         # any logger-style call (.info/.debug/.warning/.error/...) becomes a tolerant no-op
         def _noop(*args, **kwargs):
             return None
         return _noop
     ```

Whichever you choose, every call site of `Config` across the codebase must stop raising `AttributeError`/`TypeError`.

`Config.DATA_DERIVED` call sites (0):

`Config.DATA_DIR` call sites (0):

`Config.DERIVED_PATH` call sites (0):

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/results/benchmark_results.csv` is declared but was NOT written. Scripts referencing it:
    - `code/verify_acceptance_scenarios.py` — NOT invoked by the run-book
    - `code/benchmark/generate_failure_report.py` — NOT invoked by the run-book
    - `code/benchmark/metrics.py` — IS a run-book command
    - `code/benchmark/generate_benchmark_results.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/benchmark_results.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
