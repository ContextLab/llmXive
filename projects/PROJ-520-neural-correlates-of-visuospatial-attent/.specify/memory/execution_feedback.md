# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 4 command(s) failed: python code/main.py --task download (rc=1); python code/main.py --task preprocess (rc=1); python code/main.py --task features (rc=1); 2 declared deliverable(s) absent: data/processed/feature_metadata.json; data/processed/features_matrix.csv

## Failing / missing run-book commands

- python code/main.py --task download -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-520-neural-correlates-of-visuospatial-attent/code/main.py", line 12, in <module>
    from config import load_config, get_paths
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-520-neural-correlates-of-visuospatial-attent/code/config.py", line 9, in <module>
    from ci_limits import get_environment_report
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-520-neural-correlates-of-visuospatial-attent/code/ci_limits.py", line 24, in <module>
    from config import load_config, get_paths
ImportError: cannot import name 'load_config' from partially initialized module 'config' (most likely due to a circular import) (/home/runner/work/llmXive/llmXive/projects/PROJ-520-neural-correlates-of-visuospatial-attent/code/config.py)
- python code/main.py --task preprocess -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-520-neural-correlates-of-visuospatial-attent/code/main.py", line 12, in <module>
    from config import load_config, get_paths
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-520-neural-correlates-of-visuospatial-attent/code/config.py", line 9, in <module>
    from ci_limits import get_environment_report
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-520-neural-correlates-of-visuospatial-attent/code/ci_limits.py", line 24, in <module>
    from config import load_config, get_paths
ImportError: cannot import name 'load_config' from partially initialized module 'config' (most likely due to a circular import) (/home/runner/work/llmXive/llmXive/projects/PROJ-520-neural-correlates-of-visuospatial-attent/code/config.py)
- python code/main.py --task features -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-520-neural-correlates-of-visuospatial-attent/code/main.py", line 12, in <module>
    from config import load_config, get_paths
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-520-neural-correlates-of-visuospatial-attent/code/config.py", line 9, in <module>
    from ci_limits import get_environment_report
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-520-neural-correlates-of-visuospatial-attent/code/ci_limits.py", line 24, in <module>
    from config import load_config, get_paths
ImportError: cannot import name 'load_config' from partially initialized module 'config' (most likely due to a circular import) (/home/runner/work/llmXive/llmXive/projects/PROJ-520-neural-correlates-of-visuospatial-attent/code/config.py)
- python code/main.py --task classify -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-520-neural-correlates-of-visuospatial-attent/code/main.py", line 12, in <module>
    from config import load_config, get_paths
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-520-neural-correlates-of-visuospatial-attent/code/config.py", line 9, in <module>
    from ci_limits import get_environment_report
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-520-neural-correlates-of-visuospatial-attent/code/ci_limits.py", line 24, in <module>
    from config import load_config, get_paths
ImportError: cannot import name 'load_config' from partially initialized module 'config' (most likely due to a circular import) (/home/runner/work/llmXive/llmXive/projects/PROJ-520-neural-correlates-of-visuospatial-attent/code/config.py)

## Declared deliverables still missing

- data/processed/feature_metadata.json
- data/processed/features_matrix.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/feature_metadata.json` is declared but was NOT written. Scripts referencing it:
    - `code/analyze_correlations.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/feature_metadata.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/features_matrix.csv` is declared but was NOT written. Scripts referencing it:
    - `code/save_features.py` — NOT invoked by the run-book
    - `code/config.py` — NOT invoked by the run-book
    - `code/feature_validation.py` — NOT invoked by the run-book
    - `code/analyze_correlations.py` — NOT invoked by the run-book
    - `code/feature_extraction.py` — NOT invoked by the run-book
    - `code/classification.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/features_matrix.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
