# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 6 run-book script(s) missing (plan/impl path mismatch): python code/download_data.py; python code/structural_metrics.py; python code/dynamic_metrics.py; 2 command(s) failed: python code/analysis/completeness_report.py (rc=1); python -m pytest tests/ (rc=2); 1 declared deliverable(s) absent: data/logs/exclusion_log.json

## Failing / missing run-book commands

- python code/download_data.py -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-128-investigating-the-influence-of-network-t/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-128-investigating-the-influence-of-network-t/code/download_data.py': [Errno 2] No such file or directory

- python code/analysis/completeness_report.py -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-128-investigating-the-influence-of-network-t/code/analysis/completeness_report.py", line 135, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-128-investigating-the-influence-of-network-t/code/analysis/completeness_report.py", line 105, in main
    total_cohort_size = structural_metrics['subject_id'].nunique() + len(exclusion_log)
                        ~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-128-investigating-the-influence-of-network-t/lib/python3.11/site-packages/pandas/core/frame.py", line 4378, in __getitem__
    indexer = self.columns.get_loc(key)
              ^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-128-investigating-the-influence-of-network-t/lib/python3.11/site-packages/pandas/core/indexes/range.py", line 535, in get_loc
    raise KeyError(key)
KeyError: 'subject_id'

- python code/structural_metrics.py -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-128-investigating-the-influence-of-network-t/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-128-investigating-the-influence-of-network-t/code/structural_metrics.py': [Errno 2] No such file or directory

- python code/dynamic_metrics.py -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-128-investigating-the-influence-of-network-t/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-128-investigating-the-influence-of-network-t/code/dynamic_metrics.py': [Errno 2] No such file or directory

- python code/correlation_analysis.py -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-128-investigating-the-influence-of-network-t/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-128-investigating-the-influence-of-network-t/code/correlation_analysis.py': [Errno 2] No such file or directory

- python code/sensitivity_analysis.py -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-128-investigating-the-influence-of-network-t/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-128-investigating-the-influence-of-network-t/code/sensitivity_analysis.py': [Errno 2] No such file or directory

- python code/report_generator.py -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-128-investigating-the-influence-of-network-t/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-128-investigating-the-influence-of-network-t/code/report_generator.py': [Errno 2] No such file or directory

- python -m pytest tests/ -> rc=2
: Dict[str, Any]
E   NameError: name 'Any' is not defined
_________ ERROR collecting tests/unit/test_tractography_sensitivity.py _________
tests/unit/test_tractography_sensitivity.py:20: in <module>
    from analysis.tractography_sensitivity import (
code/analysis/tractography_sensitivity.py:27: in <module>
    from preprocess.structural import calculate_graph_metrics
code/preprocess/structural.py:126: in <module>
    config: Dict[str, Any]
E   NameError: name 'Any' is not defined
=========================== short test summary info ============================
ERROR tests/integration/test_robustness.py
ERROR tests/integration/test_single_subject.py - NameError: name 'Any' is not...
ERROR tests/integration/test_t019_batch_processing.py - NameError: name 'Any'...
ERROR tests/unit/test_loader.py
ERROR tests/unit/test_structural.py - NameError: name 'Any' is not defined
ERROR tests/unit/test_tractography.py - NameError: name 'Any' is not defined
ERROR tests/unit/test_tractography_sensitivity.py - NameError: name 'Any' is ...
!!!!!!!!!!!!!!!!!!! Interrupted: 7 errors during collection !!!!!!!!!!!!!!!!!!!!
============================== 7 errors in 1.67s ===============================



## Declared deliverables still missing

- data/logs/exclusion_log.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/logs/exclusion_log.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/completeness_report.py` — IS a run-book command
    - `code/main.py` — NOT invoked by the run-book
    - `code/preprocess/functional_t017.py` — NOT invoked by the run-book
    - `code/reports/generate_report.py` — NOT invoked by the run-book
    - `code/setup_data_structure.py` — NOT invoked by the run-book
    - `code/validate_quickstart.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/logs/exclusion_log.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
