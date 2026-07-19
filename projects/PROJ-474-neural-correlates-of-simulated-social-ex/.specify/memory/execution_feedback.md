# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 4 command(s) failed: python code/src/main.py --step download_qc (rc=1); python code/src/main.py --step extract_connectivity (rc=1); python code/src/main.py --step stats_viz (rc=1); 1 declared deliverable(s) absent: data/processed/subject_qc_list.json

## Failing / missing run-book commands

- python code/src/main.py --step download_qc -> rc=1
    2026-07-19 06:40:36,787 - root - ERROR - Unknown step: --step
- python code/src/main.py --step extract_connectivity -> rc=1
    2026-07-19 06:40:37,149 - root - ERROR - Unknown step: --step
- python code/src/main.py --step stats_viz -> rc=1
    2026-07-19 06:40:37,512 - root - ERROR - Unknown step: --step
- python code/src/main.py --step report -> rc=1
    2026-07-19 06:40:37,874 - root - ERROR - Unknown step: --step

## Declared deliverables still missing

- data/processed/subject_qc_list.json

## ⚠ SHARED-MODULE CONTRACT — fix the DEFINITION, tolerant of ALL callers

One or more failures are API-CONTRACT errors on a symbol YOUR OWN code defines and that MANY scripts call in DIFFERENT ways. Rewriting the definition to match one caller breaks the others — that is why this keeps failing. Fix the DEFINITION **once** so it is compatible with EVERY call site listed below: accept ``*args, **kwargs``, branch on what was actually passed, and NEVER raise on an unexpected call shape. For an auxiliary utility (e.g. logging), doing nothing on an unrecognized shape is fine. Do NOT edit the call sites — edit only the defining module.

**CRITICAL — ADD, do not REPLACE.** Edit the defining module *in place*: ADD the missing methods/parameters and PRESERVE every function, method, and attribute that already exists. Do NOT rewrite the file from scratch and do NOT delete a definition to make room for another. Each round that deletes a previously-working symbol just moves the failure to that symbol next round — an infinite loop. The fix is cumulative: the module must satisfy ALL callers from ALL rounds simultaneously.

**This list is CUMULATIVE across every fix round** — it includes contracts you may have ALREADY satisfied in an earlier round. Keep satisfying them while you fix the rest. Do NOT remove a method or parameter merely because it is absent from this round's traceback; if it is listed here, some script still depends on it.

### `log_exception` — defined in `code/src/utils.py`; called 5 way(s):

- code/src/main.py: log_exception(logger)
- code/src/utils.py: - log_exception(logger)
- code/src/utils.py: - log_exception(logger, exc)
- code/src/utils.py: - log_exception(exc=exc)
- code/src/utils.py: - log_exception() (logs nothing if no logger/exc provided)

Make `log_exception` in `code/src/utils.py` accept ALL of the above.

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/subject_qc_list.json` is declared but was NOT written. Scripts referencing it:
    - `code/src/main.py` — IS a run-book command
    - `code/src/extraction.py` — NOT invoked by the run-book
    - `code/src/qc.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/subject_qc_list.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
