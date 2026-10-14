# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 5 command(s) failed: python code/main.py --step download (rc=1); python code/main.py --step ingest (rc=1); python code/main.py --step analyze (rc=1); 5 declared deliverable(s) absent: data/final/permutation_results.csv; data/final/regression_summary.csv; data/final/sensitivity_analysis.csv

## Failing / missing run-book commands

- python code/main.py --step download -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-200-the-impact-of-incidental-music-on-autobi/code/main.py", line 4, in <module>
    from utils import setup_logging, get_logger
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-200-the-impact-of-incidental-music-on-autobi/code/utils.py", line 6, in <module>
    import pyarrow.parquet as pq
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-200-the-impact-of-incidental-music-on-autobi/lib/python3.11/site-packages/pyarrow/__init__.py", line 59, in <module>
    from pyarrow.lib import (BuildInfo, CppBuildInfo, RuntimeInfo, set_timezone_db_path,
  File "pyarrow/lib.pyx", line 42, in init pyarrow.lib
ImportError: pyarrow requires NumPy 2.0 or newer, found 1.26.4

- python code/main.py --step ingest -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-200-the-impact-of-incidental-music-on-autobi/code/main.py", line 4, in <module>
    from utils import setup_logging, get_logger
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-200-the-impact-of-incidental-music-on-autobi/code/utils.py", line 6, in <module>
    import pyarrow.parquet as pq
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-200-the-impact-of-incidental-music-on-autobi/lib/python3.11/site-packages/pyarrow/__init__.py", line 59, in <module>
    from pyarrow.lib import (BuildInfo, CppBuildInfo, RuntimeInfo, set_timezone_db_path,
  File "pyarrow/lib.pyx", line 42, in init pyarrow.lib
ImportError: pyarrow requires NumPy 2.0 or newer, found 1.26.4

- python code/main.py --step analyze -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-200-the-impact-of-incidental-music-on-autobi/code/main.py", line 4, in <module>
    from utils import setup_logging, get_logger
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-200-the-impact-of-incidental-music-on-autobi/code/utils.py", line 6, in <module>
    import pyarrow.parquet as pq
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-200-the-impact-of-incidental-music-on-autobi/lib/python3.11/site-packages/pyarrow/__init__.py", line 59, in <module>
    from pyarrow.lib import (BuildInfo, CppBuildInfo, RuntimeInfo, set_timezone_db_path,
  File "pyarrow/lib.pyx", line 42, in init pyarrow.lib
ImportError: pyarrow requires NumPy 2.0 or newer, found 1.26.4

- python code/main.py --step verify -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-200-the-impact-of-incidental-music-on-autobi/code/main.py", line 4, in <module>
    from utils import setup_logging, get_logger
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-200-the-impact-of-incidental-music-on-autobi/code/utils.py", line 6, in <module>
    import pyarrow.parquet as pq
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-200-the-impact-of-incidental-music-on-autobi/lib/python3.11/site-packages/pyarrow/__init__.py", line 59, in <module>
    from pyarrow.lib import (BuildInfo, CppBuildInfo, RuntimeInfo, set_timezone_db_path,
  File "pyarrow/lib.pyx", line 42, in init pyarrow.lib
ImportError: pyarrow requires NumPy 2.0 or newer, found 1.26.4

- python code/main.py --full-run -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-200-the-impact-of-incidental-music-on-autobi/code/main.py", line 4, in <module>
    from utils import setup_logging, get_logger
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-200-the-impact-of-incidental-music-on-autobi/code/utils.py", line 6, in <module>
    import pyarrow.parquet as pq
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-200-the-impact-of-incidental-music-on-autobi/lib/python3.11/site-packages/pyarrow/__init__.py", line 59, in <module>
    from pyarrow.lib import (BuildInfo, CppBuildInfo, RuntimeInfo, set_timezone_db_path,
  File "pyarrow/lib.pyx", line 42, in init pyarrow.lib
ImportError: pyarrow requires NumPy 2.0 or newer, found 1.26.4


## Declared deliverables still missing

- data/final/permutation_results.csv
- data/final/regression_summary.csv
- data/final/sensitivity_analysis.csv
- data/processed/ingested_cohort.parquet
- data/processed/user_track_pairs.parquet

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/final/permutation_results.csv` is declared but was NOT written. Scripts referencing it:
    - `code/generate_final_results.py` — NOT invoked by the run-book
    - `code/generate_permutation_results.py` — NOT invoked by the run-book
    - `code/quickstart_validator.py` — NOT invoked by the run-book
    - `code/security.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/final/permutation_results.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/final/regression_summary.csv` is declared but was NOT written. Scripts referencing it:
    - `code/05_model.py` — NOT invoked by the run-book
    - `code/08_visualize.py` — NOT invoked by the run-book
    - `code/generate_diagnostic_plots.py` — NOT invoked by the run-book
    - `code/generate_permutation_results.py` — NOT invoked by the run-book
    - `code/generate_regression_summary.py` — NOT invoked by the run-book
    - `code/quickstart_validator.py` — NOT invoked by the run-book
    - `code/security.py` — NOT invoked by the run-book
    - `code/verify_artifacts.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/final/regression_summary.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/final/sensitivity_analysis.csv` is declared but was NOT written. Scripts referencing it:
    - `code/08_visualize.py` — NOT invoked by the run-book
    - `code/generate_final_results.py` — NOT invoked by the run-book
    - `code/generate_sensitivity_analysis.py` — NOT invoked by the run-book
    - `code/modeling.py` — NOT invoked by the run-book
    - `code/quickstart_validator.py` — NOT invoked by the run-book
    - `code/security.py` — NOT invoked by the run-book
    - `code/verify_artifacts.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/final/sensitivity_analysis.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/ingested_cohort.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/02_preprocess.py` — NOT invoked by the run-book
    - `code/03_aggregate.py` — NOT invoked by the run-book
    - `code/aggregation.py` — NOT invoked by the run-book
    - `code/data_ingestion.py` — NOT invoked by the run-book
    - `code/generate_ingested_cohort.py` — NOT invoked by the run-book
    - `code/generate_user_track_pairs.py` — NOT invoked by the run-book
    - `code/modeling.py` — NOT invoked by the run-book
    - `code/quickstart_validator.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/ingested_cohort.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/user_track_pairs.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/03_aggregate.py` — NOT invoked by the run-book
    - `code/05_model.py` — NOT invoked by the run-book
    - `code/08_visualize.py` — NOT invoked by the run-book
    - `code/aggregation.py` — NOT invoked by the run-book
    - `code/generate_diagnostic_plots.py` — NOT invoked by the run-book
    - `code/generate_regression_summary.py` — NOT invoked by the run-book
    - `code/generate_sensitivity_analysis.py` — NOT invoked by the run-book
    - `code/generate_user_track_pairs.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/user_track_pairs.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
