# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 6 command(s) failed: python code/download.py (rc=1); python code/scan.py (rc=1); python code/visualize.py (rc=1); 3 declared deliverable(s) absent: data/processed/enrichment_matrix.csv; data/processed/silhouette_score.json; data/processed/validation_report.json

## Failing / missing run-book commands

- python code/download.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-019-exploring-the-mechanisms-of-gene-regulat/code/download.py", line 7, in <module>
    from code.utils.network import fetch_file_with_retry, MaxRetriesError
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-019-exploring-the-mechanisms-of-gene-regulat/code/utils/network.py", line 51, in <module>
    def fetch_file_with_retry(url: str, dest_path: Union[str, Path]) -> Path:
                                                              ^^^^
NameError: name 'Path' is not defined
- python code/scan.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-019-exploring-the-mechanisms-of-gene-regulat/code/scan.py", line 8, in <module>
    from joblib import Parallel, delayed
ModuleNotFoundError: No module named 'joblib'
- python code/visualize.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-019-exploring-the-mechanisms-of-gene-regulat/code/visualize.py", line 6, in <module>
    import pandas as pd
ModuleNotFoundError: No module named 'pandas'
- python code/validate.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-019-exploring-the-mechanisms-of-gene-regulat/code/validate.py", line 8, in <module>
    import pandas as pd
ModuleNotFoundError: No module named 'pandas'
- python code/summary_table.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-019-exploring-the-mechanisms-of-gene-regulat/code/summary_table.py", line 7, in <module>
    import pandas as pd
ModuleNotFoundError: No module named 'pandas'
- python code/main.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-019-exploring-the-mechanisms-of-gene-regulat/code/main.py", line 12, in <module>
    from code.scan import scan_cell_type, parse_fimo_output
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-019-exploring-the-mechanisms-of-gene-regulat/code/scan.py", line 8, in <module>
    from joblib import Parallel, delayed
ModuleNotFoundError: No module named 'joblib'

## Declared deliverables still missing

- data/processed/enrichment_matrix.csv
- data/processed/silhouette_score.json
- data/processed/validation_report.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/enrichment_matrix.csv` is declared but was NOT written. Scripts referencing it:
    - `code/main.py` — IS a run-book command
    - `code/visualize.py` — IS a run-book command
    - `code/config.py` — NOT invoked by the run-book
    - `code/validate.py` — IS a run-book command
    - `code/summary_table.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/enrichment_matrix.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/silhouette_score.json` is declared but was NOT written. Scripts referencing it:
    - `code/main.py` — IS a run-book command
    - `code/visualize.py` — IS a run-book command
    - `code/validate.py` — IS a run-book command
    - `code/summary_table.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/silhouette_score.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/validation_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/main.py` — IS a run-book command
    - `code/config.py` — NOT invoked by the run-book
    - `code/summary_table.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/validation_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
