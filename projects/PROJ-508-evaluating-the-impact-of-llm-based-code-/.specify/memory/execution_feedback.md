# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 3 command(s) failed: python code/ingest.py (rc=1); python code/analyze.py (rc=1); python code/report.py (rc=1); 3 declared deliverable(s) absent: data/derived/analysis_results.json; data/derived/master_dataset.csv; data/derived/sensitivity_analysis.json

## Failing / missing run-book commands

- python code/ingest.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-508-evaluating-the-impact-of-llm-based-code-/code/ingest.py", line 312, in <module>
    run_ingestion()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-508-evaluating-the-impact-of-llm-based-code-/code/ingest.py", line 275, in run_ingestion
    github_client = GitHubClient(
                    ^^^^^^^^^^^^^
TypeError: GitHubClient.__init__() got an unexpected keyword argument 'base_url'
- python code/analyze.py -> rc=1
    INFO:__main__:Starting Analysis Pipeline
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-508-evaluating-the-impact-of-llm-based-code-/code/analyze.py", line 328, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-508-evaluating-the-impact-of-llm-based-code-/code/analyze.py", line 316, in main
    results = run_analysis()
              ^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-508-evaluating-the-impact-of-llm-based-code-/code/analyze.py", line 282, in run_analysis
    df = load_master_dataset()
         ^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-508-evaluating-the-impact-of-llm-based-code-/code/analyze.py", line 21, in load_master_dataset
    raise FileNotFoundError(f"Master dataset not found at {path}")
FileNotFoundError: Master dataset not found at data/derived/master_dataset.csv
- python code/report.py -> rc=1
    WARNING:root:reportlab not installed. PDF generation will be skipped; Markdown report generated instead.
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-508-evaluating-the-impact-of-llm-based-code-/code/report.py", line 339, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-508-evaluating-the-impact-of-llm-based-code-/code/report.py", line 336, in main
    run_report_pipeline()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-508-evaluating-the-impact-of-llm-based-code-/code/report.py", line 296, in run_report_pipeline
    output_dir, figures_dir = ensure_directories()
                              ^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-508-evaluating-the-impact-of-llm-based-code-/code/report.py", line 36, in ensure_directories
    output_dir = Path(config['paths']['output_dir'])
                      ~~~~~~^^^^^^^^^
TypeError: 'Config' object is not subscriptable

## Declared deliverables still missing

- data/derived/analysis_results.json
- data/derived/master_dataset.csv
- data/derived/sensitivity_analysis.json

## ⚠ SHARED-MODULE CONTRACT — fix the DEFINITION, tolerant of ALL callers

One or more failures are API-CONTRACT errors on a symbol YOUR OWN code defines and that MANY scripts call in DIFFERENT ways. Rewriting the definition to match one caller breaks the others — that is why this keeps failing. Fix the DEFINITION **once** so it is compatible with EVERY call site listed below: accept ``*args, **kwargs``, branch on what was actually passed, and NEVER raise on an unexpected call shape. For an auxiliary utility (e.g. logging), doing nothing on an unrecognized shape is fine. Do NOT edit the call sites — edit only the defining module.

**CRITICAL — ADD, do not REPLACE.** Edit the defining module *in place*: ADD the missing methods/parameters and PRESERVE every function, method, and attribute that already exists. Do NOT rewrite the file from scratch and do NOT delete a definition to make room for another. Each round that deletes a previously-working symbol just moves the failure to that symbol next round — an infinite loop. The fix is cumulative: the module must satisfy ALL callers from ALL rounds simultaneously.

**This list is CUMULATIVE across every fix round** — it includes contracts you may have ALREADY satisfied in an earlier round. Keep satisfying them while you fix the rest. Do NOT remove a method or parameter merely because it is absent from this round's traceback; if it is listed here, some script still depends on it.

### class `GitHubClient` (in `code/utils/github_client.py`) — accessed via method/attribute names this round: `__init__`

`GitHubClient` is used like a logger: different scripts call DIFFERENT method names on it, and the set grows every round. Adding only the name(s) above will fail next round on the NEXT name. Make the class tolerant of ANY method name **without removing the ones it already has**, by either:
  1. defining the full method set explicitly (keep existing methods like the ones already in `code/utils/github_client.py` AND add the missing ones), or
  2. adding a permissive fallback so unknown attributes resolve to a no-op callable, e.g.:

     ```python
     def __getattr__(self, name):
         # any logger-style call (.info/.debug/.warning/.error/...) becomes a tolerant no-op
         def _noop(*args, **kwargs):
             return None
         return _noop
     ```

Whichever you choose, every call site of `GitHubClient` across the codebase must stop raising `AttributeError`/`TypeError`.

`GitHubClient.__init__` call sites (0):

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/derived/analysis_results.json` is declared but was NOT written. Scripts referencing it:
    - `code/report_analysis.py` — NOT invoked by the run-book
    - `code/report.py` — IS a run-book command
    - `code/validate_quickstart.py` — NOT invoked by the run-book
    - `code/generate_manifest.py` — NOT invoked by the run-book
    - `code/derive_analysis_results.py` — NOT invoked by the run-book
    - `code/analyze.py` — IS a run-book command
    - `code/optimize_performance.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/derived/analysis_results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/derived/master_dataset.csv` is declared but was NOT written. Scripts referencing it:
    - `code/report_analysis.py` — NOT invoked by the run-book
    - `code/validate_quickstart.py` — NOT invoked by the run-book
    - `code/generate_manifest.py` — NOT invoked by the run-book
    - `code/generate_master_dataset.py` — NOT invoked by the run-book
    - `code/derive_analysis_results.py` — NOT invoked by the run-book
    - `code/analyze.py` — IS a run-book command
    - `code/ingest.py` — IS a run-book command
    - `code/optimize_performance.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/derived/master_dataset.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/derived/sensitivity_analysis.json` is declared but was NOT written. Scripts referencing it:
    - `code/derive_sensitivity_analysis.py` — NOT invoked by the run-book
    - `code/report.py` — IS a run-book command
    - `code/validate_quickstart.py` — NOT invoked by the run-book
    - `code/analyze.py` — IS a run-book command
  Make ONE of these WRITE `data/derived/sensitivity_analysis.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.

## ⚠ CROSS-SCRIPT DATA CONTRACT — make the PRODUCER write what consumers read

One or more failures are DATA-SCHEMA mismatches BETWEEN scripts that exchange a file: a CONSUMER requires column/key names (or a file) that the PRODUCER did not write. The traceback you saw shows only the CONSUMER's EXPECTATION — never the producer's ACTUAL output — which is why this keeps failing. Below is the REAL schema each producer wrote on disk (read from the actual file) versus what the consumers require. Pick ONE canonical schema and make the **PRODUCER** write exactly the columns/keys the consumers read (preferred when one producer feeds several consumers), editing the producer IN PLACE. Do NOT fake or stub the data.

**This list is CUMULATIVE across every fix round** — keep satisfying a contract you already fixed while you fix the rest; do not drop a column merely because it is absent from this round's traceback.

### `data/derived/master_dataset.csv`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/report_analysis.py`, `code/generate_manifest.py`, `code/generate_master_dataset.py`, `code/derive_analysis_results.py`, `code/analyze.py`, `code/ingest.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `data/derived/master_dataset.csv`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/report_analysis.py`, `code/validate_quickstart.py`, `code/generate_manifest.py`, `code/generate_master_dataset.py`, `code/derive_analysis_results.py`, `code/analyze.py`, `code/ingest.py`.
