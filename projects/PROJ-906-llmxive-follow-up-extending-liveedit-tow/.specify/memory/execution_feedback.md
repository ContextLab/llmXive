# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 5 command(s) failed: python code/main.py --stage data_prep --dataset davis --stratify (rc=1); python code/main.py --stage flow_compute --method farneback (rc=1); python code/main.py --stage inference --model baseline (rc=1); 7 declared deliverable(s) absent: data/flow/magnitudes.json; data/metrics/analysis_results.json; data/metrics/baseline_results.json

## Failing / missing run-book commands

- python code/main.py --stage data_prep --dataset davis --stratify -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-906-llmxive-follow-up-extending-liveedit-tow/code/main.py", line 17, in <module>
    from data.processor import process_dataset_stratification, main as processor_main
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-906-llmxive-follow-up-extending-liveedit-tow/code/data/processor.py", line 51, in <module>
    thresholds: Optional[Set[float]] = None
                         ^^^
NameError: name 'Set' is not defined. Did you mean: 'set'?
- python code/main.py --stage flow_compute --method farneback -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-906-llmxive-follow-up-extending-liveedit-tow/code/main.py", line 17, in <module>
    from data.processor import process_dataset_stratification, main as processor_main
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-906-llmxive-follow-up-extending-liveedit-tow/code/data/processor.py", line 51, in <module>
    thresholds: Optional[Set[float]] = None
                         ^^^
NameError: name 'Set' is not defined. Did you mean: 'set'?
- python code/main.py --stage inference --model baseline -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-906-llmxive-follow-up-extending-liveedit-tow/code/main.py", line 17, in <module>
    from data.processor import process_dataset_stratification, main as processor_main
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-906-llmxive-follow-up-extending-liveedit-tow/code/data/processor.py", line 51, in <module>
    thresholds: Optional[Set[float]] = None
                         ^^^
NameError: name 'Set' is not defined. Did you mean: 'set'?
- python code/main.py --stage inference --model flow_coherence -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-906-llmxive-follow-up-extending-liveedit-tow/code/main.py", line 17, in <module>
    from data.processor import process_dataset_stratification, main as processor_main
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-906-llmxive-follow-up-extending-liveedit-tow/code/data/processor.py", line 51, in <module>
    thresholds: Optional[Set[float]] = None
                         ^^^
NameError: name 'Set' is not defined. Did you mean: 'set'?
- python code/main.py --stage analysis --method ks_test --sweep 0.01,0.05,0.1 -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-906-llmxive-follow-up-extending-liveedit-tow/code/main.py", line 17, in <module>
    from data.processor import process_dataset_stratification, main as processor_main
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-906-llmxive-follow-up-extending-liveedit-tow/code/data/processor.py", line 51, in <module>
    thresholds: Optional[Set[float]] = None
                         ^^^
NameError: name 'Set' is not defined. Did you mean: 'set'?

## Declared deliverables still missing

- data/flow/magnitudes.json
- data/metrics/analysis_results.json
- data/metrics/baseline_results.json
- data/metrics/flow_results.json
- data/metrics/ks_test.json
- data/metrics/sensitivity_analysis.json
- data/metrics/stratification_report.json

## ⚠ SHARED-MODULE CONTRACT — fix the DEFINITION, tolerant of ALL callers

One or more failures are API-CONTRACT errors on a symbol YOUR OWN code defines and that MANY scripts call in DIFFERENT ways. Rewriting the definition to match one caller breaks the others — that is why this keeps failing. Fix the DEFINITION **once** so it is compatible with EVERY call site listed below: accept ``*args, **kwargs``, branch on what was actually passed, and NEVER raise on an unexpected call shape. For an auxiliary utility (e.g. logging), doing nothing on an unrecognized shape is fine. Do NOT edit the call sites — edit only the defining module.

**CRITICAL — ADD, do not REPLACE.** Edit the defining module *in place*: ADD the missing methods/parameters and PRESERVE every function, method, and attribute that already exists. Do NOT rewrite the file from scratch and do NOT delete a definition to make room for another. Each round that deletes a previously-working symbol just moves the failure to that symbol next round — an infinite loop. The fix is cumulative: the module must satisfy ALL callers from ALL rounds simultaneously.

**This list is CUMULATIVE across every fix round** — it includes contracts you may have ALREADY satisfied in an earlier round. Keep satisfying them while you fix the rest. Do NOT remove a method or parameter merely because it is absent from this round's traceback; if it is listed here, some script still depends on it.

### `ensure_directories` — defined in `code/config.py`; called 17 way(s):

- code/main.py: ensure_directories(output_dir)
- code/main.py: ensure_directories(args.output_dir)
- code/config.py: 1. ensure_directories() -> No-op
- code/config.py: 2. ensure_directories(path_str) -> Creates single path
- code/config.py: 3. ensure_directories(path_obj) -> Creates single path
- code/config.py: 4. ensure_directories([path1, path2, ...]) -> Creates all paths in list
- code/config.py: 5. ensure_directories(*paths) -> Creates all paths passed as args
- code/utils/logger.py: ensure_directories(target_dir)
- code/utils/checkpoint.py: ensure_directories(self.checkpoint_dir)
- code/data/flow.py: ensure_directories([output_dir])
- code/data/flow.py: ensure_directories([os.path.dirname(output_path)])
- code/data/processor.py: ensure_directories(args.output)
- code/data/downloader.py: ensure_directories([output_dir])
- code/analysis/reporter.py: ensure_directories(output_path)
- code/analysis/stats.py: ensure_directories(KS_TEST_PATH)
- code/analysis/stats.py: ensure_directories(PIECEWISE_PATH)
- code/analysis/stats.py: ensure_directories(SENSITIVITY_PATH)

Make `ensure_directories` in `code/config.py` accept ALL of the above.

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/flow/magnitudes.json` is declared but was NOT written. Scripts referencing it:
    - `code/models/flow_coherence.py` — NOT invoked by the run-book
    - `code/metrics/ssim.py` — NOT invoked by the run-book
    - `code/data/flow.py` — NOT invoked by the run-book
    - `code/data/processor.py` — NOT invoked by the run-book
    - `code/analysis/stats.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/flow/magnitudes.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/metrics/analysis_results.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/reporter.py` — NOT invoked by the run-book
    - `code/analysis/stats.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/metrics/analysis_results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/metrics/baseline_results.json` is declared but was NOT written. Scripts referencing it:
    - `code/main.py` — IS a run-book command
    - `code/analysis/reporter.py` — NOT invoked by the run-book
    - `code/analysis/stats.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/metrics/baseline_results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/metrics/flow_results.json` is declared but was NOT written. Scripts referencing it:
    - `code/main.py` — IS a run-book command
    - `code/data/flow.py` — NOT invoked by the run-book
    - `code/analysis/reporter.py` — NOT invoked by the run-book
    - `code/analysis/stats.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/metrics/flow_results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/metrics/ks_test.json` is declared but was NOT written. Scripts referencing it:
    - `code/contracts/analysis_validator.py` — NOT invoked by the run-book
    - `code/analysis/reporter.py` — NOT invoked by the run-book
    - `code/analysis/stats.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/metrics/ks_test.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/metrics/sensitivity_analysis.json` is declared but was NOT written. Scripts referencing it:
    - `code/main.py` — IS a run-book command
    - `code/analysis/reporter.py` — NOT invoked by the run-book
    - `code/analysis/stats.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/metrics/sensitivity_analysis.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/metrics/stratification_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/data/processor.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/metrics/stratification_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
