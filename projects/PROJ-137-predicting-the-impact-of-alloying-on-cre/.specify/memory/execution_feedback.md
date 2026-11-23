# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 run-book script(s) missing (plan/impl path mismatch): python src/main.py --mode synthetic; python src/main.py --mode real; 3 command(s) failed: python src/data/generate.py --output data/processed/synthetic_data.csv (rc=1); python src/models/train.py --input data/processed/synthetic_data.csv (rc=1); python src/models/interpret.py --model-path models/gbr_thermo.pkl (rc=1)

## Failing / missing run-book commands

- python src/main.py --mode synthetic -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-137-predicting-the-impact-of-alloying-on-cre/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-137-predicting-the-impact-of-alloying-on-cre/src/main.py': [Errno 2] No such file or directory
- python src/main.py --mode real -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-137-predicting-the-impact-of-alloying-on-cre/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-137-predicting-the-impact-of-alloying-on-cre/src/main.py': [Errno 2] No such file or directory
- python src/data/generate.py --output data/processed/synthetic_data.csv -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-137-predicting-the-impact-of-alloying-on-cre/src/data/generate.py", line 257, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-137-predicting-the-impact-of-alloying-on-cre/src/data/generate.py", line 219, in main
    from config.settings import load_config
ModuleNotFoundError: No module named 'config.settings'
- python src/models/train.py --input data/processed/synthetic_data.csv -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-137-predicting-the-impact-of-alloying-on-cre/src/models/train.py", line 39, in <module>
    from src.utils.validators import validate_dataset_schema
ImportError: cannot import name 'validate_dataset_schema' from 'src.utils.validators' (/home/runner/work/llmXive/llmXive/projects/PROJ-137-predicting-the-impact-of-alloying-on-cre/src/utils/validators.py)
- python src/models/interpret.py --model-path models/gbr_thermo.pkl -> rc=1
    ing-the-impact-of-alloying-on-cre/src/models/interpret.py", line 57, in load_data_and_model
    raise FileNotFoundError(
FileNotFoundError: Processed data not found at /home/runner/work/llmXive/llmXive/projects/PROJ-137-predicting-the-impact-of-alloying-on-cre/data/processed/alloy_dataset_clean.csv. Please run the data pipeline (T019) first.

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-137-predicting-the-impact-of-alloying-on-cre/src/models/interpret.py", line 213, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-137-predicting-the-impact-of-alloying-on-cre/src/models/interpret.py", line 189, in main
    X, model, feature_names = load_data_and_model()
                              ^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-137-predicting-the-impact-of-alloying-on-cre/src/models/interpret.py", line 57, in load_data_and_model
    raise FileNotFoundError(
FileNotFoundError: Processed data not found at /home/runner/work/llmXive/llmXive/projects/PROJ-137-predicting-the-impact-of-alloying-on-cre/data/processed/alloy_dataset_clean.csv. Please run the data pipeline (T019) first.
