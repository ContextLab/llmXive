# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 run-book script(s) missing (plan/impl path mismatch): python code/download.py; python code/analysis.py; 2 command(s) failed: python code/data/validate_data.py (rc=1); python code/data/preprocess.py (rc=1); 5 declared deliverable(s) absent: data/derived/trial_data.csv; data/results/bootstrap_config.json; data/results/primary_analysis.json

## Failing / missing run-book commands

- python code/download.py -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-179-the-influence-of-metacognitive-awareness/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-179-the-influence-of-metacognitive-awareness/code/download.py': [Errno 2] No such file or directory
- python code/data/validate_data.py -> rc=1
    2026-06-30 13:03:18,853 - INFO - Starting data validation (T006)...
2026-06-30 13:03:18,854 - INFO - Loading dataset from data/ds003386_behavioral.csv...
2026-06-30 13:03:18,854 - ERROR - Dataset not found at data/ds003386_behavioral.csv. Ensure T005 (download.py) has successfully executed.
2026-06-30 13:03:18,854 - INFO - Validation report written to data/validation_report.json
- python code/data/preprocess.py -> rc=1
    ognitive-awareness/code/data/preprocess.py", line 196, in <module>
    sys.exit(main())
             ^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-179-the-influence-of-metacognitive-awareness/code/data/preprocess.py", line 147, in main
    log_level = config.get('logging', {}).get('level', 'INFO')
                ^^^^^^^^^^
AttributeError: 'AppConfig' object has no attribute 'get'
- python code/analysis.py -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-179-the-influence-of-metacognitive-awareness/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-179-the-influence-of-metacognitive-awareness/code/analysis.py': [Errno 2] No such file or directory

## Declared deliverables still missing

- data/derived/trial_data.csv
- data/results/bootstrap_config.json
- data/results/primary_analysis.json
- data/results/regression_analysis.json
- data/results/robustness_analysis.json

## ⚠ SHARED-MODULE CONTRACT — fix the DEFINITION, tolerant of ALL callers

One or more failures are API-CONTRACT errors on a symbol YOUR OWN code defines and that MANY scripts call in DIFFERENT ways. Rewriting the definition to match one caller breaks the others — that is why this keeps failing. Fix the DEFINITION **once** so it is compatible with EVERY call site listed below: accept ``*args, **kwargs``, branch on what was actually passed, and NEVER raise on an unexpected call shape. For an auxiliary utility (e.g. logging), doing nothing on an unrecognized shape is fine. Do NOT edit the call sites — edit only the defining module.

**CRITICAL — ADD, do not REPLACE.** Edit the defining module *in place*: ADD the missing methods/parameters and PRESERVE every function, method, and attribute that already exists. Do NOT rewrite the file from scratch and do NOT delete a definition to make room for another. Each round that deletes a previously-working symbol just moves the failure to that symbol next round — an infinite loop. The fix is cumulative: the module must satisfy ALL callers from ALL rounds simultaneously.

**This list is CUMULATIVE across every fix round** — it includes contracts you may have ALREADY satisfied in an earlier round. Keep satisfying them while you fix the rest. Do NOT remove a method or parameter merely because it is absent from this round's traceback; if it is listed here, some script still depends on it.

### class `AppConfig` (in `code/config/env_config.py`) — accessed via method/attribute names this round: `get`

`AppConfig` is used like a logger: different scripts call DIFFERENT method names on it, and the set grows every round. Adding only the name(s) above will fail next round on the NEXT name. Make the class tolerant of ANY method name **without removing the ones it already has**, by either:
  1. defining the full method set explicitly (keep existing methods like the ones already in `code/config/env_config.py` AND add the missing ones), or
  2. adding a permissive fallback so unknown attributes resolve to a no-op callable, e.g.:

     ```python
     def __getattr__(self, name):
         # any logger-style call (.info/.debug/.warning/.error/...) becomes a tolerant no-op
         def _noop(*args, **kwargs):
             return None
         return _noop
     ```

Whichever you choose, every call site of `AppConfig` across the codebase must stop raising `AttributeError`/`TypeError`.

`AppConfig.get` call sites (18):
- code/src/analysis/robustness.py: base_dir = Path(CONFIG.get("paths", {}).get("derived_data", "data/derived"))
- code/src/analysis/robustness.py: output_dir = Path(CONFIG.get("paths", {}).get("results", "data/results"))
- code/src/analysis/robustness.py: n_resamples = CONFIG.get("analysis", {}).get("bootstrap_count", 1000)
- code/models/data_models.py: modality_str = str(row.get('stimulus_modality', 'unknown')).lower()
- code/models/data_models.py: source_str = str(row.get('source_label', 'unknown')).lower()
- code/models/data_models.py: trial_id=str(row.get('trial_id', str(uuid.uuid4()))),
- code/models/data_models.py: participant_id=str(row.get('participant_id')),
- code/models/data_models.py: participant_response=str(row.get('participant_response', '')),
- code/models/data_models.py: confidence_rating=float(row.get('confidence_rating', 0.0)),
- code/models/data_models.py: reaction_time=float(row.get('reaction_time')) if row.get('reaction_time') is not None else None
- code/data/preprocess.py: 'participant_id': config.get('columns', {}).get('participant_id', 'participant_id'),
- code/data/preprocess.py: 'trial_id': config.get('columns', {}).get('trial_id', 'trial_id'),
- code/data/preprocess.py: 'stimulus_modality': config.get('columns', {}).get('stimulus_modality', 'stimulus_modality'),
- code/data/preprocess.py: 'source_label': config.get('columns', {}).get('source_label', 'source_label'),
- code/data/preprocess.py: 'participant_response': config.get('columns', {}).get('participant_response', 'participant_response'),
- code/data/preprocess.py: 'confidence_rating': config.get('columns', {}).get('confidence_rating', 'confidence_rating')
- code/data/preprocess.py: log_level = config.get('logging', {}).get('level', 'INFO')
- code/code/performance_optimizer.py: logger.info(f"Regression result: R2={reg_res.get('rsquared', 'N/A')}")

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/derived/trial_data.csv` is declared but was NOT written. Scripts referencing it:
    - `code/quickstart_validator.py` — NOT invoked by the run-book
    - `code/src/utils/security.py` — NOT invoked by the run-book
    - `code/src/utils/stats.py` — NOT invoked by the run-book
    - `code/src/analysis/bootstrap.py` — NOT invoked by the run-book
    - `code/src/analysis/filter.py` — NOT invoked by the run-book
    - `code/src/analysis/regression.py` — NOT invoked by the run-book
    - `code/tests/unit/test_filter.py` — NOT invoked by the run-book
    - `code/data/preprocess.py` — IS a run-book command
  Make ONE of these WRITE `data/derived/trial_data.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/results/bootstrap_config.json` is declared but was NOT written. Scripts referencing it:
    - `code/quickstart_validator.py` — NOT invoked by the run-book
    - `code/src/analysis/bootstrap.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/bootstrap_config.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/results/primary_analysis.json` is declared but was NOT written. Scripts referencing it:
    - `code/quickstart_validator.py` — NOT invoked by the run-book
    - `code/src/analysis/bootstrap.py` — NOT invoked by the run-book
    - `code/src/analysis/regression.py` — NOT invoked by the run-book
    - `code/tests/unit/test_generate_report.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/primary_analysis.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/results/regression_analysis.json` is declared but was NOT written. Scripts referencing it:
    - `code/quickstart_validator.py` — NOT invoked by the run-book
    - `code/src/analysis/regression.py` — NOT invoked by the run-book
    - `code/tests/unit/test_regression.py` — NOT invoked by the run-book
    - `code/code/performance_optimizer.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/regression_analysis.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/results/robustness_analysis.json` is declared but was NOT written. Scripts referencing it:
    - `code/quickstart_validator.py` — NOT invoked by the run-book
    - `code/src/analysis/robustness.py` — NOT invoked by the run-book
    - `code/src/report/generate.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/robustness_analysis.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
