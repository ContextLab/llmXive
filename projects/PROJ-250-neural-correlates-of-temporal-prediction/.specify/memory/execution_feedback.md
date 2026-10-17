# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 3 run-book script(s) missing (plan/impl path mismatch): python code/preprocess.py; python code/analysis.py; python code/visualize.py; 2 command(s) failed: python code/download.py --subjects 2 (rc=1); python -m pytest code/tests/ (rc=5); 1 declared deliverable(s) absent: data/results/citation_verification.json

## Failing / missing run-book commands

- python code/download.py --subjects 2 -> rc=1
ub-UTS01/ses-1/func/sub-UTS01_ses-1_task-presto_bold.nii.gz
SHA-256 3c0593a58a00a781...  sub-UTS01/ses-1/func/sub-UTS01_ses-1_task-sintel_bold.nii.gz
SHA-256 0684540bc8c466af...  sub-UTS02/ses-1/func/sub-UTS02_ses-1_task-AttendFemaleSpeaker_bold.nii.gz
SHA-256 33f2f93c64b9481d...  sub-UTS02/ses-1/func/sub-UTS02_ses-1_task-AttendMaleSpeaker_bold.nii.gz
SHA-256 bd61172f5cd49b1e...  sub-UTS02/ses-1/func/sub-UTS02_ses-1_task-ImaginedSpeech_bold.nii.gz
SHA-256 d6c15c2073fca5eb...  sub-UTS02/ses-1/func/sub-UTS02_ses-1_task-laluna_bold.nii.gz
SHA-256 7fb832cc34766356...  sub-UTS02/ses-1/func/sub-UTS02_ses-1_task-partlycloudy_bold.nii.gz
SHA-256 be0923095faca16c...  sub-UTS02/ses-1/func/sub-UTS02_ses-1_task-presto_bold.nii.gz
SHA-256 6b7362d702b3d2c4...  sub-UTS02/ses-1/func/sub-UTS02_ses-1_task-sintel_bold.nii.gz
Checksums for 14 files recorded in /home/runner/work/llmXive/llmXive/projects/PROJ-250-neural-correlates-of-temporal-prediction/data/raw/checksums.json

REFERENCE VERIFICATION FAILED: No events.tsv metadata files found under /home/runner/work/llmXive/llmXive/projects/PROJ-250-neural-correlates-of-temporal-prediction/data/raw; cannot verify conditions. Run code/download.py first.

- python code/preprocess.py -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-250-neural-correlates-of-temporal-prediction/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-250-neural-correlates-of-temporal-prediction/code/preprocess.py': [Errno 2] No such file or directory

- python code/analysis.py -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-250-neural-correlates-of-temporal-prediction/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-250-neural-correlates-of-temporal-prediction/code/analysis.py': [Errno 2] No such file or directory

- python code/visualize.py -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-250-neural-correlates-of-temporal-prediction/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-250-neural-correlates-of-temporal-prediction/code/visualize.py': [Errno 2] No such file or directory

- python -m pytest code/tests/ -> rc=5
============================= test session starts ==============================
platform linux -- Python 3.11.17, pytest-8.2.0, pluggy-1.7.0
rootdir: /home/runner/work/llmXive/llmXive
configfile: pyproject.toml
plugins: platformdirs-4.13.3
collected 0 items

============================ no tests ran in 0.15s =============================



## Declared deliverables still missing

- data/results/citation_verification.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/results/citation_verification.json` is declared but was NOT written. Scripts referencing it:
    - `code/verify_references.py` — IS a run-book command
  Make ONE of these WRITE `data/results/citation_verification.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
