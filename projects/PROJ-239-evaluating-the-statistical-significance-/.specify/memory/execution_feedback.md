# Execution failures — fix these before the analysis can run

## ⛔ HOLLOW RESULTS — the analysis RAN but MEASURED NOTHING

Every command exited 0 and the files were written — but the numbers in them are missing. A result that is `null`, `NaN`, an empty `[]`, a header-only CSV, or a column left blank in every row is NOT a measurement. Writing an empty result file is not 'done' — it is the same failure as fabrication, just quieter. You MUST:

1. Find WHY the value is missing. A `null`/`NaN` correlation almost always means the inputs were empty, misaligned, or the wrong column was read — fix the computation, do NOT paper over it with a default.
2. Verify you loaded the REAL dataset the spec names. If the study is about behavioural confidence ratings, a stand-in dataset (a bundled sklearn toy set, a random frame) is NOT the data — it will produce exactly these null/NaN results.
3. Make sure the key measure is actually POPULATED before you compute on it: if the column the study depends on is blank in every row, the extraction step is broken and that is the real bug.
4. NEVER self-certify. A `{"status": "PASS"}` written by your own code proves nothing; the numbers must be there.

- data/derived/robustResults.csv: results file is EMPTY — the analysis produced no rows

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 hollow-result signal(s) — the analysis ran but computed nothing: data/derived/robustResults.csv: results file is EMPTY — the analysis produced no rows; 1 command(s) failed: python code/simulation_runner.py (rc=1); 1 declared deliverable(s) absent: data/derived/final_report.csv

## Failing / missing run-book commands

- python code/simulation_runner.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-239-evaluating-the-statistical-significance-/code/simulation_runner.py", line 420, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-239-evaluating-the-statistical-significance-/code/simulation_runner.py", line 381, in main
    cfg = parse_cli_args(args, cfg)
          ^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-239-evaluating-the-statistical-significance-/code/config.py", line 269, in parse_cli_args
    validate_config(cfg)
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-239-evaluating-the-statistical-significance-/code/config.py", line 54, in validate_config
    if icc < 0.0 or icc > 1.0:
       ^^^^^^^^^
TypeError: '<' not supported between instances of 'NoneType' and 'float'

## Declared deliverables still missing

- data/derived/final_report.csv

## ⚠ SHARED-MODULE CONTRACT — fix the DEFINITION, tolerant of ALL callers

One or more failures are API-CONTRACT errors on a symbol YOUR OWN code defines and that MANY scripts call in DIFFERENT ways. Rewriting the definition to match one caller breaks the others — that is why this keeps failing. Fix the DEFINITION **once** so it is compatible with EVERY call site listed below: accept ``*args, **kwargs``, branch on what was actually passed, and NEVER raise on an unexpected call shape. For an auxiliary utility (e.g. logging), doing nothing on an unrecognized shape is fine. Do NOT edit the call sites — edit only the defining module.

**CRITICAL — ADD, do not REPLACE.** Edit the defining module *in place*: ADD the missing methods/parameters and PRESERVE every function, method, and attribute that already exists. Do NOT rewrite the file from scratch and do NOT delete a definition to make room for another. Each round that deletes a previously-working symbol just moves the failure to that symbol next round — an infinite loop. The fix is cumulative: the module must satisfy ALL callers from ALL rounds simultaneously.

**This list is CUMULATIVE across every fix round** — it includes contracts you may have ALREADY satisfied in an earlier round. Keep satisfying them while you fix the rest. Do NOT remove a method or parameter merely because it is absent from this round's traceback; if it is listed here, some script still depends on it.

### `parse_cli_args` — defined in `code/config.py`; called 5 way(s):

- code/config.py: 1. parse_cli_args() -> Returns config with defaults
- code/config.py: 2. parse_cli_args(args) -> Parses args and returns new config
- code/config.py: 3. parse_cli_args(args, cfg) -> Parses args and updates existing config
- code/config.py: 4. parse_cli_args(cfg) -> Updates existing config with defaults (no CLI)
- code/simulation_runner.py: cfg = parse_cli_args(args, cfg)

Make `parse_cli_args` in `code/config.py` accept ALL of the above.

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/derived/final_report.csv` is declared but was NOT written. Scripts referencing it:
    - `code/generate_final_report.py` — NOT invoked by the run-book
    - `code/generate_report.py` — NOT invoked by the run-book
    - `code/scripts/merge_results.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/derived/final_report.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
