# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 5 command(s) failed: python code/data/download.py --sample-size 1000 (rc=1); python code/data/extract_geometry.py --input data/raw --output data/derived/constraints.jsonl (rc=1); python code/solver/run_solver.py --input data/derived/constraints.jsonl --output data/derived/predictions.jsonl (rc=1); 1 declared deliverable(s) absent: data/results/benchmark_results.csv

## Failing / missing run-book commands

- python code/data/download.py --sample-size 1000 -> rc=1
    ERROR: Dataset llmXive/S-AgentK not found at HuggingFace Hub
- python code/data/extract_geometry.py --input data/raw --output data/derived/constraints.jsonl -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-893-llmxive-follow-up-extending-s-agent-spat/code/data/extract_geometry.py", line 96, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-893-llmxive-follow-up-extending-s-agent-spat/code/data/extract_geometry.py", line 73, in main
    scenes = load_scene_data(input_dir)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-893-llmxive-follow-up-extending-s-agent-spat/code/data/extract_geometry.py", line 16, in load_scene_data
    raise FileNotFoundError(f"Raw data file not found: {raw_file}")
FileNotFoundError: Raw data file not found: data/raw/s_agent_k_subset.jsonl
- python code/solver/run_solver.py --input data/derived/constraints.jsonl --output data/derived/predictions.jsonl -> rc=1
    Warning: python-constraint not installed. Using mock solver.

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-893-llmxive-follow-up-extending-s-agent-spat/code/solver/run_solver.py", line 11, in <module>
    from solver.csp_engine import CSPEngine, SolveResult
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-893-llmxive-follow-up-extending-s-agent-spat/code/solver/csp_engine.py", line 15, in <module>
    from solver.run_solver import ConstraintSatisfactionError
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-893-llmxive-follow-up-extending-s-agent-spat/code/solver/run_solver.py", line 11, in <module>
    from solver.csp_engine import CSPEngine, SolveResult
ImportError: cannot import name 'CSPEngine' from partially initialized module 'solver.csp_engine' (most likely due to a circular import) (/home/runner/work/llmXive/llmXive/projects/PROJ-893-llmxive-follow-up-extending-s-agent-spat/code/solver/csp_engine.py)
- python code/benchmark/metrics.py --predictions data/derived/predictions.jsonl --baseline data/raw/merged.csv --output data/derived/benchmark_results.csv -> rc=1
    Loading predictions from data/derived/predictions.jsonl...

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-893-llmxive-follow-up-extending-s-agent-spat/code/benchmark/metrics.py", line 278, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-893-llmxive-follow-up-extending-s-agent-spat/code/benchmark/metrics.py", line 159, in main
    predictions = load_jsonl(args.predictions)
                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-893-llmxive-follow-up-extending-s-agent-spat/code/benchmark/metrics.py", line 22, in load_jsonl
    with open(file_path, 'r', encoding='utf-8') as f:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
FileNotFoundError: [Errno 2] No such file or directory: 'data/derived/predictions.jsonl'
- python code/benchmark/analyze_failures.py --results data/derived/benchmark_results.csv --output data/derived/failure_report.json -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-893-llmxive-follow-up-extending-s-agent-spat/code/benchmark/analyze_failures.py", line 9, in <module>
    def classify_failure(scene_id: str, symbolic_pred: Any, vlm_pred: Any, ground_truth: Any) -> Dict[str, Any]:
                                                       ^^^
NameError: name 'Any' is not defined. Did you mean: 'any'?

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

## ⚠ CROSS-SCRIPT DATA CONTRACT — make the PRODUCER write what consumers read

One or more failures are DATA-SCHEMA mismatches BETWEEN scripts that exchange a file: a CONSUMER requires column/key names (or a file) that the PRODUCER did not write. The traceback you saw shows only the CONSUMER's EXPECTATION — never the producer's ACTUAL output — which is why this keeps failing. Below is the REAL schema each producer wrote on disk (read from the actual file) versus what the consumers require. Pick ONE canonical schema and make the **PRODUCER** write exactly the columns/keys the consumers read (preferred when one producer feeds several consumers), editing the producer IN PLACE. Do NOT fake or stub the data.

**This list is CUMULATIVE across every fix round** — keep satisfying a contract you already fixed while you fix the rest; do not drop a column merely because it is absent from this round's traceback.

### `data/derived/predictions.json`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/benchmark/metrics.py`, `code/benchmark/generate_benchmark_results.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `data/derived/predictions.json`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/data/load_vlm_baseline.py`, `code/benchmark/metrics.py`, `code/benchmark/generate_benchmark_results.py`.

### `data/raw/s_agent_k_subset.json`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/data/extract_geometry.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `data/raw/s_agent_k_subset.json`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/data/download.py`, `code/data/extract_geometry.py`.
