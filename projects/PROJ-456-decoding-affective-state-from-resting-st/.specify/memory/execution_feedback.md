# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 6 run-book script(s) missing (plan/impl path mismatch): python main.py --stage download; python main.py --stage preprocess; python main.py --stage segment; 1 command(s) failed: python -m pytest tests/ (rc=2); 2 declared deliverable(s) absent: data/raw/dataset_manifest.json; data/templates/microstate_template.npy

## Failing / missing run-book commands

- python main.py --stage download -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-456-decoding-affective-state-from-resting-st/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-456-decoding-affective-state-from-resting-st/main.py': [Errno 2] No such file or directory

- python main.py --stage preprocess -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-456-decoding-affective-state-from-resting-st/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-456-decoding-affective-state-from-resting-st/main.py': [Errno 2] No such file or directory

- python main.py --stage segment -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-456-decoding-affective-state-from-resting-st/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-456-decoding-affective-state-from-resting-st/main.py': [Errno 2] No such file or directory

- python main.py --stage analyze -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-456-decoding-affective-state-from-resting-st/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-456-decoding-affective-state-from-resting-st/main.py': [Errno 2] No such file or directory

- python main.py --stage sensitivity -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-456-decoding-affective-state-from-resting-st/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-456-decoding-affective-state-from-resting-st/main.py': [Errno 2] No such file or directory

- python -m pytest tests/ -> rc=2
11/dataclasses.py:545: in _init_fn
    raise TypeError(f'non-default argument {f.name!r} '
E   TypeError: non-default argument 'method' follows default argument
_ ERROR collecting projects/PROJ-456-decoding-affective-state-from-resting-st/tests/unit/test_preprocessing.py _
tests/unit/test_preprocessing.py:4: in <module>
    from code.preprocessing import apply_average_rereference, apply_bandpass_filter, run_ica_artifact_removal
code/preprocessing.py:80: in <module>
    def apply_average_rereference(raw_data: mne.io.Raw) -> mne.io.io.Raw:
../../.llmxive-venvs/PROJ-456-decoding-affective-state-from-resting-st/lib/python3.11/site-packages/lazy_loader/__init__.py:110: in __getattr__
    raise AttributeError(f"No {package_name} attribute {name}")
E   AttributeError: No mne.io attribute io
=========================== short test summary info ============================
ERROR tests/unit/test_microstate.py - TypeError: non-default argument 'method...
ERROR tests/unit/test_preprocessing.py - AttributeError: No mne.io attribute io
!!!!!!!!!!!!!!!!!!! Interrupted: 2 errors during collection !!!!!!!!!!!!!!!!!!!!
============================== 2 errors in 0.83s ===============================


- python main.py --stage validate -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-456-decoding-affective-state-from-resting-st/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-456-decoding-affective-state-from-resting-st/main.py': [Errno 2] No such file or directory


## Declared deliverables still missing

- data/raw/dataset_manifest.json
- data/templates/microstate_template.npy

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/raw/dataset_manifest.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis.py` — NOT invoked by the run-book
    - `code/utils.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/dataset_manifest.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/templates/microstate_template.npy` is declared but was NOT written. Scripts referencing it:
    - `code/microstate.py` — NOT invoked by the run-book
    - `code/preprocessing.py` — NOT invoked by the run-book
    - `code/save_processed.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/templates/microstate_template.npy` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
