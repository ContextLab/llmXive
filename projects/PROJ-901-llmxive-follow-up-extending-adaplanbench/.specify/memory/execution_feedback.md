# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 6 command(s) failed: python code/dataset/loader.py --verify-only (rc=1); python code/dataset/loader.py --filter-min-constraints 5 --output data/processed/filtered_tasks.csv (rc=1); python code/analysis/power.py --input data/processed/filtered_tasks.csv (rc=1); 3 declared deliverable(s) absent: data/processed/annotation_sample.csv; data/processed/execution_traces.csv; data/processed/filtered_tasks.csv

## Failing / missing run-book commands

- python code/dataset/loader.py --verify-only -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-901-llmxive-follow-up-extending-adaplanbench/code/dataset/loader.py", line 22, in <module>
    from config import Paths, DatasetConfig
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-901-llmxive-follow-up-extending-adaplanbench/code/config.py", line 161, in <module>
    @dataclass
     ^^^^^^^^^
NameError: name 'dataclass' is not defined
- python code/dataset/loader.py --filter-min-constraints 5 --output data/processed/filtered_tasks.csv -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-901-llmxive-follow-up-extending-adaplanbench/code/dataset/loader.py", line 22, in <module>
    from config import Paths, DatasetConfig
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-901-llmxive-follow-up-extending-adaplanbench/code/config.py", line 161, in <module>
    @dataclass
     ^^^^^^^^^
NameError: name 'dataclass' is not defined
- python code/analysis/power.py --input data/processed/filtered_tasks.csv -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-901-llmxive-follow-up-extending-adaplanbench/code/analysis/power.py", line 12, in <module>
    from config import Paths
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-901-llmxive-follow-up-extending-adaplanbench/code/config.py", line 161, in <module>
    @dataclass
     ^^^^^^^^^
NameError: name 'dataclass' is not defined
- python code/main.py --mode full --model phi-3-mini --output data/processed/execution_logs.csv -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-901-llmxive-follow-up-extending-adaplanbench/code/main.py", line 25, in <module>
    from config import Paths, ResourceLimits, set_all_seeds, AnalysisConfig
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-901-llmxive-follow-up-extending-adaplanbench/code/config.py", line 161, in <module>
    @dataclass
     ^^^^^^^^^
NameError: name 'dataclass' is not defined
- python code/analysis/glmm.py --input data/processed/execution_logs.csv --output data/processed/results.json -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-901-llmxive-follow-up-extending-adaplanbench/code/analysis/glmm.py", line 36, in <module>
    from config import Paths
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-901-llmxive-follow-up-extending-adaplanbench/code/config.py", line 161, in <module>
    @dataclass
     ^^^^^^^^^
NameError: name 'dataclass' is not defined
- python code/dataset/annotator.py --input data/processed/execution_logs.csv --target-kappa-precision 0.10 -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-901-llmxive-follow-up-extending-adaplanbench/code/dataset/annotator.py", line 14, in <module>
    from config import Paths
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-901-llmxive-follow-up-extending-adaplanbench/code/config.py", line 161, in <module>
    @dataclass
     ^^^^^^^^^
NameError: name 'dataclass' is not defined

## Declared deliverables still missing

- data/processed/annotation_sample.csv
- data/processed/execution_traces.csv
- data/processed/filtered_tasks.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/annotation_sample.csv` is declared but was NOT written. Scripts referencing it:
    - `code/config.py` — NOT invoked by the run-book
    - `code/dataset/annotator.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/annotation_sample.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/execution_traces.csv` is declared but was NOT written. Scripts referencing it:
    - `code/main.py` — IS a run-book command
    - `code/config.py` — NOT invoked by the run-book
    - `code/quickstart_validator.py` — NOT invoked by the run-book
    - `code/agent/dual_track.py` — NOT invoked by the run-book
    - `code/analysis/glmm.py` — IS a run-book command
    - `code/analysis/generate_execution_traces.py` — NOT invoked by the run-book
    - `code/analysis/agreement_rate.py` — NOT invoked by the run-book
    - `code/analysis/power.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/execution_traces.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/filtered_tasks.csv` is declared but was NOT written. Scripts referencing it:
    - `code/config.py` — NOT invoked by the run-book
    - `code/quickstart_validator.py` — NOT invoked by the run-book
    - `code/dataset/add_constraint_count.py` — NOT invoked by the run-book
    - `code/dataset/validate_subset.py` — NOT invoked by the run-book
    - `code/dataset/annotator.py` — IS a run-book command
    - `code/dataset/loader.py` — IS a run-book command
    - `code/agent/dual_track.py` — NOT invoked by the run-book
    - `code/analysis/generate_execution_traces.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/filtered_tasks.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
