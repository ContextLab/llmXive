# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 6 command(s) failed: python code/data/download.py (rc=1); python code/data/curate.py (rc=1); python code/main.py --mode static (rc=1); 2 declared deliverable(s) absent: data/curated/synthetic_issues_meta.json; data/results/sensitivity_analysis.json

## Failing / missing run-book commands

- python code/data/download.py -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-897-llmxive-follow-up-extending-swe-explore/code/data/download.py", line 17, in <module>
    from config import get_path, get_config_summary, DATA_RAW
ImportError: cannot import name 'DATA_RAW' from 'config' (/home/runner/work/llmXive/llmXive/projects/PROJ-897-llmxive-follow-up-extending-swe-explore/code/config.py)

- python code/data/curate.py -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-897-llmxive-follow-up-extending-swe-explore/code/data/curate.py", line 12, in <module>
    from config import get_path, get_config_summary, DATA_CURATED, DATA_RAW, MIN_SYNTHETIC_ISSUES, HARD_INSTANCE_PERCENTILE, COVERAGE_COLUMN_NAME
ImportError: cannot import name 'DATA_CURATED' from 'config' (/home/runner/work/llmXive/llmXive/projects/PROJ-897-llmxive-follow-up-extending-swe-explore/code/config.py)

- python code/main.py --mode static -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-897-llmxive-follow-up-extending-swe-explore/code/main.py", line 17, in <module>
    from config import get_path, get_config_summary, MAX_EXECUTION_HOURS
ImportError: cannot import name 'MAX_EXECUTION_HOURS' from 'config' (/home/runner/work/llmXive/llmXive/projects/PROJ-897-llmxive-follow-up-extending-swe-explore/code/config.py)

- python code/main.py --mode iterative -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-897-llmxive-follow-up-extending-swe-explore/code/main.py", line 17, in <module>
    from config import get_path, get_config_summary, MAX_EXECUTION_HOURS
ImportError: cannot import name 'MAX_EXECUTION_HOURS' from 'config' (/home/runner/work/llmXive/llmXive/projects/PROJ-897-llmxive-follow-up-extending-swe-explore/code/config.py)

- python code/main.py --mode stats -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-897-llmxive-follow-up-extending-swe-explore/code/main.py", line 17, in <module>
    from config import get_path, get_config_summary, MAX_EXECUTION_HOURS
ImportError: cannot import name 'MAX_EXECUTION_HOURS' from 'config' (/home/runner/work/llmXive/llmXive/projects/PROJ-897-llmxive-follow-up-extending-swe-explore/code/config.py)

- python -m pytest tests/ -> rc=2
_summary, DATA_CURATED, DATA_RAW, MIN_SYNTHETIC_ISSUES, HARD_INSTANCE_PERCENTILE, COVERAGE_COLUMN_NAME
E   ImportError: cannot import name 'DATA_CURATED' from 'config' (/home/runner/work/llmXive/llmXive/projects/PROJ-897-llmxive-follow-up-extending-swe-explore/code/config.py)
=========================== short test summary info ============================
ERROR tests/integration/test_agent_loop.py
ERROR tests/unit/test_baseline_agent.py
ERROR tests/unit/test_bonferroni.py
ERROR tests/unit/test_curate_filter.py
ERROR tests/unit/test_derive_gt.py
ERROR tests/unit/test_derive_gt_streaming.py
ERROR tests/unit/test_download.py
ERROR tests/unit/test_download_robustness.py
ERROR tests/unit/test_linting_config.py
ERROR tests/unit/test_loop_detection.py
ERROR tests/unit/test_mutation.py
ERROR tests/unit/test_project_structure.py
ERROR tests/unit/test_setup_project_structure.py
ERROR tests/unit/test_stats.py
ERROR tests/unit/test_structure.py
ERROR tests/unit/test_synthetic_generation.py
ERROR tests/unit/test_synthetic_validity.py
!!!!!!!!!!!!!!!!!!! Interrupted: 17 errors during collection !!!!!!!!!!!!!!!!!!!
============================== 17 errors in 0.77s ==============================



## Declared deliverables still missing

- data/curated/synthetic_issues_meta.json
- data/results/sensitivity_analysis.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/curated/synthetic_issues_meta.json` is declared but was NOT written. Scripts referencing it:
    - `code/config.py` — NOT invoked by the run-book
    - `code/data/generate_synthetic_metadata.py` — NOT invoked by the run-book
    - `code/data/mutate.py` — NOT invoked by the run-book
    - `code/validation_runner.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/curated/synthetic_issues_meta.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/sensitivity_analysis.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/sensitivity_check.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/sensitivity_analysis.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
## Platform-owned paths written inside the project

A script in this project created `state/` inside the project directory. Those names belong to the platform, and a copy of them here is a SHADOW: the verifier resolves the paths a task names relative to this project, so it reads the shadow instead of canonical state and rejects work on the strength of a stale record.

Write your outputs under `data/`, `figures/`, `code/` and `paper/`. Do not record artifact hashes, run state or project status yourself — the platform owns `state/` and derives hashes at verification time. Delete the directories listed above and drop whatever step created them.
