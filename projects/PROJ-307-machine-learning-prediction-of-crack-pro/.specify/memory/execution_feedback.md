# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 7 command(s) failed: python code/main.py --step download (rc=1); python code/main.py --step preprocess (rc=1); python code/main.py --step baseline (rc=1)

## Failing / missing run-book commands

- python code/main.py --step download -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-307-machine-learning-prediction-of-crack-pro/code/main.py", line 135, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-307-machine-learning-prediction-of-crack-pro/code/main.py", line 132, in main
    run_pipeline()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-307-machine-learning-prediction-of-crack-pro/code/main.py", line 30, in run_pipeline
    ensure_dirs(config)
TypeError: ensure_dirs() takes 0 positional arguments but 1 was given

- python code/main.py --step preprocess -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-307-machine-learning-prediction-of-crack-pro/code/main.py", line 135, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-307-machine-learning-prediction-of-crack-pro/code/main.py", line 132, in main
    run_pipeline()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-307-machine-learning-prediction-of-crack-pro/code/main.py", line 30, in run_pipeline
    ensure_dirs(config)
TypeError: ensure_dirs() takes 0 positional arguments but 1 was given

- python code/main.py --step baseline -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-307-machine-learning-prediction-of-crack-pro/code/main.py", line 135, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-307-machine-learning-prediction-of-crack-pro/code/main.py", line 132, in main
    run_pipeline()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-307-machine-learning-prediction-of-crack-pro/code/main.py", line 30, in run_pipeline
    ensure_dirs(config)
TypeError: ensure_dirs() takes 0 positional arguments but 1 was given

- python code/main.py --step augmented -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-307-machine-learning-prediction-of-crack-pro/code/main.py", line 135, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-307-machine-learning-prediction-of-crack-pro/code/main.py", line 132, in main
    run_pipeline()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-307-machine-learning-prediction-of-crack-pro/code/main.py", line 30, in run_pipeline
    ensure_dirs(config)
TypeError: ensure_dirs() takes 0 positional arguments but 1 was given

- python code/main.py --step regimes -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-307-machine-learning-prediction-of-crack-pro/code/main.py", line 135, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-307-machine-learning-prediction-of-crack-pro/code/main.py", line 132, in main
    run_pipeline()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-307-machine-learning-prediction-of-crack-pro/code/main.py", line 30, in run_pipeline
    ensure_dirs(config)
TypeError: ensure_dirs() takes 0 positional arguments but 1 was given

- python code/main.py --step full -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-307-machine-learning-prediction-of-crack-pro/code/main.py", line 135, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-307-machine-learning-prediction-of-crack-pro/code/main.py", line 132, in main
    run_pipeline()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-307-machine-learning-prediction-of-crack-pro/code/main.py", line 30, in run_pipeline
    ensure_dirs(config)
TypeError: ensure_dirs() takes 0 positional arguments but 1 was given

- python -m pytest tests/ -> rc=2
tegration/test_permutation.py:64
  /home/runner/work/llmXive/llmXive/projects/PROJ-307-machine-learning-prediction-of-crack-pro/tests/integration/test_permutation.py:64: PytestUnknownMarkWarning: Unknown pytest.mark.integration - is this a typo?  You can register custom marks to avoid this warning - for details, see https://docs.pytest.org/en/stable/how-to/mark.html
    @pytest.mark.integration

tests/integration/test_permutation.py:135
  /home/runner/work/llmXive/llmXive/projects/PROJ-307-machine-learning-prediction-of-crack-pro/tests/integration/test_permutation.py:135: PytestUnknownMarkWarning: Unknown pytest.mark.integration - is this a typo?  You can register custom marks to avoid this warning - for details, see https://docs.pytest.org/en/stable/how-to/mark.html
    @pytest.mark.integration

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=========================== short test summary info ============================
ERROR tests/integration/test_baseline.py
ERROR tests/unit/test_augmented.py
!!!!!!!!!!!!!!!!!!! Interrupted: 2 errors during collection !!!!!!!!!!!!!!!!!!!!
======================== 2 warnings, 2 errors in 1.18s =========================


