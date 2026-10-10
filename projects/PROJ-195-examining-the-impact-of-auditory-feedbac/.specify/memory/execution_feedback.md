# Execution failures — fix these before the analysis can run

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python -m pytest tests/integration/test_pipeline.py --subset`
  - argparse error: `python -m pytest: error: unrecognized arguments: --subset`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 7 command(s) failed: python code/download.py --dataset ds000246 --subset 5 (rc=1); python code/preprocess.py --mem-mb 6000 --nprocs 2 (rc=1); python code/glm_first_level.py --contrast perturbed_normal (rc=1); 4 declared deliverable(s) absent: data/processed/behavioral_metrics.csv; data/processed/correlation_results.json; data/processed/fdr_clusters.csv

## Failing / missing run-book commands

- python code/download.py --dataset ds000246 --subset 5 -> rc=1
2026-10-10 04:15:45,662 - INFO - Starting dataset download with subsampling for ds000246
2026-10-10 04:15:45,901 - ERROR - Failed to estimate dataset size: 401 Client Error: Unauthorized for url: https://huggingface.co/api/datasets/ds000246/tree/main
2026-10-10 04:15:45,901 - ERROR - Could not estimate size: 401 Client Error: Unauthorized for url: https://huggingface.co/api/datasets/ds000246/tree/main
2026-10-10 04:15:46,038 - ERROR - Failed to fetch dataset tree for ds000246: 401 Client Error: Unauthorized for url: https://huggingface.co/api/datasets/ds000246/tree/main
2026-10-10 04:15:46,038 - ERROR - Failed to select subjects: 401 Client Error: Unauthorized for url: https://huggingface.co/api/datasets/ds000246/tree/main


- python code/preprocess.py --mem-mb 6000 --nprocs 2 -> rc=1

2026-10-10 04:15:46,094 - utils_logger - INFO - Starting preprocessing pipeline.
2026-10-10 04:15:46,094 - utils_logger - ERROR - No subjects found in BIDS root.

- python code/glm_first_level.py --contrast perturbed_normal -> rc=1
2026-10-10 04:15:47,738 - ERROR - Valid subjects file not found: data/processed/valid_subjects.txt. Run T018 first.


- python code/glm_group.py --correction fdr --q 0.05 --test one-sample -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-195-examining-the-impact-of-auditory-feedbac/code/glm_group.py", line 23, in <module>
    from nilearn.glm.second_level import second_level_input
ImportError: cannot import name 'second_level_input' from 'nilearn.glm.second_level' (/home/runner/work/llmXive/llmXive/projects/PROJ-195-examining-the-impact-of-auditory-feedbac/code/.venv/lib/python3.11/site-packages/nilearn/glm/second_level/__init__.py)

- python code/correlation_analysis.py --roi auditory_cortex -> rc=1
2026-10-10 04:15:50,712 - correlation_analysis - INFO - Starting T033: Brain-Behavior Correlation Analysis
2026-10-10 04:15:50,712 - correlation_analysis - ERROR - Required input file not found: /home/runner/work/llmXive/llmXive/projects/PROJ-195-examining-the-impact-of-auditory-feedbac/data/processed/roi_betas.csv. Ensure T028 has been executed successfully.


- python -m pytest tests/unit/ -> rc=2
the-impact-of-auditory-feedbac/tests/unit/test_roi_extraction.py _
ImportError while importing test module '/home/runner/work/llmXive/llmXive/projects/PROJ-195-examining-the-impact-of-auditory-feedbac/tests/unit/test_roi_extraction.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/importlib/__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests/unit/test_roi_extraction.py:22: in <module>
    from roi_extraction import (
E   ModuleNotFoundError: No module named 'roi_extraction'
=========================== short test summary info ============================
ERROR tests/unit/test_fdr_correction.py
ERROR tests/unit/test_glm_fdr.py
ERROR tests/unit/test_glm_group.py
ERROR tests/unit/test_linting_config.py
ERROR tests/unit/test_null_result_handler.py
ERROR tests/unit/test_pull_fmriprep.py
ERROR tests/unit/test_roi_extraction.py
!!!!!!!!!!!!!!!!!!! Interrupted: 7 errors during collection !!!!!!!!!!!!!!!!!!!!
============================== 7 errors in 2.45s ===============================


- python -m pytest tests/integration/test_pipeline.py --subset -> rc=4

ERROR: usage: python -m pytest [options] [file_or_dir] [file_or_dir] [...]
python -m pytest: error: unrecognized arguments: --subset
  inifile: /home/runner/work/llmXive/llmXive/pyproject.toml
  rootdir: /home/runner/work/llmXive/llmXive



## Declared deliverables still missing

- data/processed/behavioral_metrics.csv
- data/processed/correlation_results.json
- data/processed/fdr_clusters.csv
- data/processed/learning_rates.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/behavioral_metrics.csv` is declared but was NOT written. Scripts referencing it:
    - `code/behavior.py` — NOT invoked by the run-book
    - `code/learning_rate_analysis.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/behavioral_metrics.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/correlation_results.json` is declared but was NOT written. Scripts referencing it:
    - `code/correlation_analysis.py` — IS a run-book command
    - `code/generate_report_summary.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/correlation_results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/fdr_clusters.csv` is declared but was NOT written. Scripts referencing it:
    - `code/generate_report_summary.py` — NOT invoked by the run-book
    - `code/glm_fdr_correction.py` — NOT invoked by the run-book
    - `code/run_fdr_correction.py` — NOT invoked by the run-book
    - `code/viz.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/fdr_clusters.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/learning_rates.csv` is declared but was NOT written. Scripts referencing it:
    - `code/correlation_analysis.py` — IS a run-book command
    - `code/learning_rate_analysis.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/learning_rates.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
