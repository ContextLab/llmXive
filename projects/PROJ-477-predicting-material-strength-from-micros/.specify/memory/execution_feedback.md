# Execution failures — fix these before the analysis can run

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python code/eval/metrics.py`
  - script usage: `metrics.py [-h] --predictions PREDICTIONS [--output OUTPUT]`
  - argparse error: `metrics.py: error: the following arguments are required: --predictions`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 run-book script(s) missing (plan/impl path mismatch): python code/models/train.py; python code/models/train_ablation.py; 8 command(s) failed: python code/data/download.py (rc=1); python code/data/preprocess.py (rc=1); python code/data/validate.py (rc=1)

## Failing / missing run-book commands

- python code/data/download.py -> rc=1
    2026-08-01 08:12:36,945 - download - ERROR - Download failed: Could not determine project root. Expected 'code' and 'data' directories.
- python code/data/preprocess.py -> rc=1
    e "/home/runner/work/llmXive/llmXive/projects/PROJ-477-predicting-material-strength-from-micros/code/data/preprocess.py", line 327, in main
    results = preprocess_dataset(
              ^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-477-predicting-material-strength-from-micros/code/data/preprocess.py", line 203, in preprocess_dataset
    raw_dir = get_raw_dir()
              ^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-477-predicting-material-strength-from-micros/code/utils/config.py", line 52, in get_raw_dir
    return get_data_dir() / "raw"
           ^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-477-predicting-material-strength-from-micros/code/utils/config.py", line 44, in get_data_dir
    return get_project_root() / "data"
           ^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-477-predicting-material-strength-from-micros/code/utils/config.py", line 38, in get_project_root
    raise FileNotFoundError("Could not determine project root. Expected 'code' and 'data' directories.")
FileNotFoundError: Could not determine project root. Expected 'code' and 'data' directories.
- python code/data/validate.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-477-predicting-material-strength-from-micros/code/data/validate.py", line 170, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-477-predicting-material-strength-from-micros/code/data/validate.py", line 124, in main
    data_dir = get_data_dir()
               ^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-477-predicting-material-strength-from-micros/code/utils/config.py", line 44, in get_data_dir
    return get_project_root() / "data"
           ^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-477-predicting-material-strength-from-micros/code/utils/config.py", line 38, in get_project_root
    raise FileNotFoundError("Could not determine project root. Expected 'code' and 'data' directories.")
FileNotFoundError: Could not determine project root. Expected 'code' and 'data' directories.
- python code/data/extract_features.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-477-predicting-material-strength-from-micros/code/data/extract_features.py", line 156, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-477-predicting-material-strength-from-micros/code/data/extract_features.py", line 143, in main
    raw_dir = get_raw_dir()
              ^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-477-predicting-material-strength-from-micros/code/utils/config.py", line 52, in get_raw_dir
    return get_data_dir() / "raw"
           ^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-477-predicting-material-strength-from-micros/code/utils/config.py", line 44, in get_data_dir
    return get_project_root() / "data"
           ^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-477-predicting-material-strength-from-micros/code/utils/config.py", line 38, in get_project_root
    raise FileNotFoundError("Could not determine project root. Expected 'code' and 'data' directories.")
FileNotFoundError: Could not determine project root. Expected 'code' and 'data' directories.
- python code/models/train.py -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-477-predicting-material-strength-from-micros/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-477-predicting-material-strength-from-micros/code/models/train.py': [Errno 2] No such file or directory
- python code/models/train_ablation.py -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-477-predicting-material-strength-from-micros/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-477-predicting-material-strength-from-micros/code/models/train_ablation.py': [Errno 2] No such file or directory
- python code/eval/metrics.py -> rc=2
    usage: metrics.py [-h] --predictions PREDICTIONS [--output OUTPUT]
                  [--alpha ALPHA] [--seed SEED]
metrics.py: error: the following arguments are required: --predictions
- python code/eval/interpret.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-477-predicting-material-strength-from-micros/code/eval/interpret.py", line 17, in <module>
    import torch
ModuleNotFoundError: No module named 'torch'
- python code/eval/predictor.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-477-predicting-material-strength-from-micros/code/eval/predictor.py", line 7, in <module>
    import torch
ModuleNotFoundError: No module named 'torch'
- python code/eval/sensitivity.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-477-predicting-material-strength-from-micros/code/eval/sensitivity.py", line 417, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-477-predicting-material-strength-from-micros/code/eval/sensitivity.py", line 383, in main
    project_root = get_project_root()
                   ^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-477-predicting-material-strength-from-micros/code/utils/config.py", line 38, in get_project_root
    raise FileNotFoundError("Could not determine project root. Expected 'code' and 'data' directories.")
FileNotFoundError: Could not determine project root. Expected 'code' and 'data' directories.
