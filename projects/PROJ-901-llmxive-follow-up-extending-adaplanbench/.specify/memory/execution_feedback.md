# Execution failures — fix these before the analysis can run

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python code/dataset/annotator.py --input data/processed/execution_logs.csv --target-kappa-precision 0.10`
  - script usage: `annotator.py [-h] --input INPUT [--output OUTPUT]`
  - argparse error: `annotator.py: error: unrecognized arguments: --target-kappa-precision 0.10`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 6 command(s) failed: python code/dataset/loader.py --verify-only (rc=1); python code/dataset/loader.py --filter-min-constraints 5 --output data/processed/filtered_tasks.csv (rc=1); python code/analysis/power.py --input data/processed/filtered_tasks.csv (rc=1); 10 declared deliverable(s) absent: data/processed/adherence_verification.json; data/processed/agreement_rate_report.json; data/processed/annotation_sample.csv

## Failing / missing run-book commands

- python code/dataset/loader.py --verify-only -> rc=1
    Loading AdaPlanBench dataset...
Error: 'DatasetConfig' object has no attribute 'LOCAL_PATH'
- python code/dataset/loader.py --filter-min-constraints 5 --output data/processed/filtered_tasks.csv -> rc=1
    Loading AdaPlanBench dataset...
Error: 'DatasetConfig' object has no attribute 'LOCAL_PATH'
- python code/analysis/power.py --input data/processed/filtered_tasks.csv -> rc=1
    Error: Execution traces file not found: data/processed/filtered_tasks.csv
- python code/main.py --mode full --model phi-3-mini --output data/processed/execution_logs.csv -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-901-llmxive-follow-up-extending-adaplanbench/code/main.py", line 24, in <module>
    from agent.monolithic_runner import main as monolithic_main
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-901-llmxive-follow-up-extending-adaplanbench/code/agent/monolithic_runner.py", line 24, in <module>
    from agent.judges import AdaPlanJudge
ModuleNotFoundError: No module named 'agent.judges'
- python code/analysis/glmm.py --input data/processed/execution_logs.csv --output data/processed/results.json -> rc=1
    Running GLMM analysis on data/processed/execution_logs.csv...

Error during GLMM analysis: Execution traces file not found: data/processed/execution_logs.csv
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-901-llmxive-follow-up-extending-adaplanbench/code/analysis/glmm.py", line 419, in main
    results = run_statistical_analysis(args.input, args.output)
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-901-llmxive-follow-up-extending-adaplanbench/code/analysis/glmm.py", line 366, in run_statistical_analysis
    df = load_execution_traces(input_path)
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-901-llmxive-follow-up-extending-adaplanbench/code/analysis/glmm.py", line 76, in load_execution_traces
    raise FileNotFoundError(f"Execution traces file not found: {input_path}")
FileNotFoundError: Execution traces file not found: data/processed/execution_logs.csv
- python code/dataset/annotator.py --input data/processed/execution_logs.csv --target-kappa-precision 0.10 -> rc=2
    usage: annotator.py [-h] --input INPUT [--output OUTPUT]
                    [--sample-size SAMPLE_SIZE] [--seed SEED]
annotator.py: error: unrecognized arguments: --target-kappa-precision 0.10

## Declared deliverables still missing

- data/processed/adherence_verification.json
- data/processed/agreement_rate_report.json
- data/processed/annotation_sample.csv
- data/processed/dual_track_logs.json
- data/processed/execution_traces.csv
- data/processed/filtered_tasks.csv
- data/processed/monolithic_logs.json
- data/processed/power_report.json
- data/processed/resource_logs.json
- data/processed/statistical-results.json

## ⚠ SHARED-MODULE CONTRACT — fix the DEFINITION, tolerant of ALL callers

One or more failures are API-CONTRACT errors on a symbol YOUR OWN code defines and that MANY scripts call in DIFFERENT ways. Rewriting the definition to match one caller breaks the others — that is why this keeps failing. Fix the DEFINITION **once** so it is compatible with EVERY call site listed below: accept ``*args, **kwargs``, branch on what was actually passed, and NEVER raise on an unexpected call shape. For an auxiliary utility (e.g. logging), doing nothing on an unrecognized shape is fine. Do NOT edit the call sites — edit only the defining module.

**CRITICAL — ADD, do not REPLACE.** Edit the defining module *in place*: ADD the missing methods/parameters and PRESERVE every function, method, and attribute that already exists. Do NOT rewrite the file from scratch and do NOT delete a definition to make room for another. Each round that deletes a previously-working symbol just moves the failure to that symbol next round — an infinite loop. The fix is cumulative: the module must satisfy ALL callers from ALL rounds simultaneously.

**This list is CUMULATIVE across every fix round** — it includes contracts you may have ALREADY satisfied in an earlier round. Keep satisfying them while you fix the rest. Do NOT remove a method or parameter merely because it is absent from this round's traceback; if it is listed here, some script still depends on it.

### class `Paths` (in `code/config.py`) — accessed via method/attribute names this round: `DATA_RAW`

`Paths` is used like a logger: different scripts call DIFFERENT method names on it, and the set grows every round. Adding only the name(s) above will fail next round on the NEXT name. Make the class tolerant of ANY method name **without removing the ones it already has**, by either:
  1. defining the full method set explicitly (keep existing methods like the ones already in `code/config.py` AND add the missing ones), or
  2. adding a permissive fallback so unknown attributes resolve to a no-op callable, e.g.:

     ```python
     def __getattr__(self, name):
         # any logger-style call (.info/.debug/.warning/.error/...) becomes a tolerant no-op
         def _noop(*args, **kwargs):
             return None
         return _noop
     ```

Whichever you choose, every call site of `Paths` across the codebase must stop raising `AttributeError`/`TypeError`.

`Paths.DATA_RAW` call sites (0):

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/adherence_verification.json` is declared but was NOT written. Scripts referencing it:
    - `code/main.py` — IS a run-book command
    - `code/analysis/adherence_verifier.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/adherence_verification.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/agreement_rate_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/main.py` — IS a run-book command
    - `code/analysis/agreement_rate.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/agreement_rate_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/annotation_sample.csv` is declared but was NOT written. Scripts referencing it:
    - `code/main.py` — IS a run-book command
    - `code/dataset/annotator.py` — IS a run-book command
    - `code/analysis/agreement_rate.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/annotation_sample.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/dual_track_logs.json` is declared but was NOT written. Scripts referencing it:
    - `code/main.py` — IS a run-book command
    - `code/agent/dual_track.py` — NOT invoked by the run-book
    - `code/agent/dual_track_runner.py` — NOT invoked by the run-book
    - `code/analysis/log_aggregator.py` — NOT invoked by the run-book
    - `code/analysis/generate_execution_traces.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/dual_track_logs.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/execution_traces.csv` is declared but was NOT written. Scripts referencing it:
    - `code/main.py` — IS a run-book command
    - `code/quickstart_validator.py` — NOT invoked by the run-book
    - `code/analysis/log_aggregator.py` — NOT invoked by the run-book
    - `code/analysis/glmm.py` — IS a run-book command
    - `code/analysis/generate_execution_traces.py` — NOT invoked by the run-book
    - `code/analysis/agreement_rate.py` — NOT invoked by the run-book
    - `code/analysis/power.py` — IS a run-book command
    - `code/analysis/adherence_verifier.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/execution_traces.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/filtered_tasks.csv` is declared but was NOT written. Scripts referencing it:
    - `code/main.py` — IS a run-book command
    - `code/quickstart_validator.py` — NOT invoked by the run-book
    - `code/dataset/add_constraint_count.py` — NOT invoked by the run-book
    - `code/dataset/validate_subset.py` — NOT invoked by the run-book
    - `code/dataset/annotator.py` — IS a run-book command
    - `code/dataset/loader.py` — IS a run-book command
    - `code/agent/dual_track.py` — NOT invoked by the run-book
    - `code/agent/dual_track_runner.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/filtered_tasks.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/monolithic_logs.json` is declared but was NOT written. Scripts referencing it:
    - `code/main.py` — IS a run-book command
    - `code/agent/monolithic_runner.py` — NOT invoked by the run-book
    - `code/analysis/log_aggregator.py` — NOT invoked by the run-book
    - `code/analysis/generate_execution_traces.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/monolithic_logs.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/power_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/main.py` — IS a run-book command
    - `code/analysis/power.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/power_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/resource_logs.json` is declared but was NOT written. Scripts referencing it:
    - `code/main.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/resource_logs.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/statistical-results.json` is declared but was NOT written. Scripts referencing it:
    - `code/main.py` — IS a run-book command
    - `code/analysis/glmm.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/statistical-results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.

## ⚠ CROSS-SCRIPT DATA CONTRACT — make the PRODUCER write what consumers read

One or more failures are DATA-SCHEMA mismatches BETWEEN scripts that exchange a file: a CONSUMER requires column/key names (or a file) that the PRODUCER did not write. The traceback you saw shows only the CONSUMER's EXPECTATION — never the producer's ACTUAL output — which is why this keeps failing. Below is the REAL schema each producer wrote on disk (read from the actual file) versus what the consumers require. Pick ONE canonical schema and make the **PRODUCER** write exactly the columns/keys the consumers read (preferred when one producer feeds several consumers), editing the producer IN PLACE. Do NOT fake or stub the data.

**This list is CUMULATIVE across every fix round** — keep satisfying a contract you already fixed while you fix the rest; do not drop a column merely because it is absent from this round's traceback.

### `data/processed/filtered_tasks.csv`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/main.py`, `code/dataset/add_constraint_count.py`, `code/dataset/loader.py`, `code/agent/dual_track.py`, `code/agent/dual_track_runner.py`, `code/agent/monolithic_runner.py`, `code/analysis/generate_execution_traces.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `data/processed/filtered_tasks.csv`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/main.py`, `code/dataset/add_constraint_count.py`, `code/dataset/validate_subset.py`, `code/dataset/loader.py`, `code/agent/dual_track.py`, `code/agent/dual_track_runner.py`, `code/agent/monolithic_runner.py`, `code/analysis/generate_execution_traces.py`.
