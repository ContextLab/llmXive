# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 4 run-book script(s) missing (plan/impl path mismatch): python code/04_fit_pgls_base.py; python code/05_fit_pgls_interaction.py; python code/06_sensitivity_power.py   # LOOCV/jackknife + power simulation; 3 command(s) failed: python code/01_discover_data.py   # discovers Dryad DOIs; aborts on Data Availability Error (rc=1); python code/02_ingest_data.py (rc=1); python code/03_clean_merge.py (rc=1); 1 declared deliverable(s) absent: data/processed/merged_analysis.csv

## Failing / missing run-book commands

- python code/01_discover_data.py   # discovers Dryad DOIs; aborts on Data Availability Error -> rc=1
jects/PROJ-055-investigating-the-impact-of-telomere-len/code/01_discover_data.py", line 122, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-055-investigating-the-impact-of-telomere-len/code/01_discover_data.py", line 90, in main
    logger = setup_logging(log_file=str(LOG_FILE))
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-055-investigating-the-impact-of-telomere-len/code/logging_config.py", line 71, in setup_logging
    file_handler = logging.FileHandler(log_path)
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/logging/__init__.py", line 1181, in __init__
    StreamHandler.__init__(self, self._open())
                                 ^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/logging/__init__.py", line 1213, in _open
    return open_func(self.baseFilename, self.mode,
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
FileNotFoundError: [Errno 2] No such file or directory: '/home/runner/work/llmXive/llmXive/projects/PROJ-055-investigating-the-impact-of-telomere-len/logs/logs/discover_data.log'

- python code/02_ingest_data.py -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-055-investigating-the-impact-of-telomere-len/code/02_ingest_data.py", line 44, in <module>
    def _discover_csv_file_id(dataset_id: str) -> Optional[str]:
                                                  ^^^^^^^^
NameError: name 'Optional' is not defined

- python code/03_clean_merge.py -> rc=1

No raw telomere CSV files found. Exiting.

- python code/04_fit_pgls_base.py -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-055-investigating-the-impact-of-telomere-len/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-055-investigating-the-impact-of-telomere-len/code/04_fit_pgls_base.py': [Errno 2] No such file or directory

- python code/05_fit_pgls_interaction.py -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-055-investigating-the-impact-of-telomere-len/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-055-investigating-the-impact-of-telomere-len/code/05_fit_pgls_interaction.py': [Errno 2] No such file or directory

- python code/06_sensitivity_power.py   # LOOCV/jackknife + power simulation -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-055-investigating-the-impact-of-telomere-len/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-055-investigating-the-impact-of-telomere-len/code/06_sensitivity_power.py': [Errno 2] No such file or directory

- python code/07_visualize.py -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-055-investigating-the-impact-of-telomere-len/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-055-investigating-the-impact-of-telomere-len/code/07_visualize.py': [Errno 2] No such file or directory


## Declared deliverables still missing

- data/processed/merged_analysis.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/merged_analysis.csv` is declared but was NOT written. Scripts referencing it:
    - `code/03_clean_merge.py` — IS a run-book command
    - `code/04_model_pglS.py` — NOT invoked by the run-book
    - `code/05_visualize.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/merged_analysis.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
## Platform-owned paths written inside the project

A script in this project created `state/` inside the project directory. Those names belong to the platform, and a copy of them here is a SHADOW: the verifier resolves the paths a task names relative to this project, so it reads the shadow instead of canonical state and rejects work on the strength of a stale record.

Write your outputs under `data/`, `figures/`, `code/` and `paper/`. Do not record artifact hashes, run state or project status yourself — the platform owns `state/` and derives hashes at verification time. Delete the directories listed above and drop whatever step created them.
