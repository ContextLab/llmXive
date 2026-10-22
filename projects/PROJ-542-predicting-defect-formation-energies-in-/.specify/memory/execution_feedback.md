# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 6 command(s) failed: python -m src.featurize data/raw/materials_defects.csv data/processed/features.csv (rc=1); python -m src.validate data/processed/features.csv (rc=1); python -m src.split data/processed/features.csv data/processed/train.csv data/processed/test.csv (rc=1); 9 declared deliverable(s) absent: data/processed/cv_metrics.json; data/processed/features.csv; data/processed/features_augmented.csv

## Failing / missing run-book commands

- python -m src.featurize data/raw/materials_defects.csv data/processed/features.csv -> rc=1

2026-10-22 04:28:16,854 INFO src.data.featurize: Input file data/raw/materials_defects.csv not found – attempting to download raw dataset.
Materials Project API key not provided

- python -m src.validate data/processed/features.csv -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-542-predicting-defect-formation-energies-in-/bin/python: No module named src.validate

- python -m src.split data/processed/features.csv data/processed/train.csv data/processed/test.csv -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-542-predicting-defect-formation-energies-in-/bin/python: No module named src.split

- python -m src.train data/processed/train.csv data/processed/cv_metrics.json -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-542-predicting-defect-formation-energies-in-/bin/python: No module named src.train

- python -m src.evaluate data/processed/train.csv data/processed/test.csv data/processed/performance.json -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-542-predicting-defect-formation-energies-in-/bin/python: No module named src.evaluate

- python -m pytest -q -> rc=1
            capture_output=True,
            text=True,
        )
        # The script should exit with status 0.
>       assert result.returncode == 0, f"Checksum script failed: {result.stderr}"
E       AssertionError: Checksum script failed: 2026-10-22 04:28:18,187 INFO __main__: Computing checksum for raw data: /home/runner/work/llmXive/llmXive/projects/PROJ-542-predicting-defect-formation-energies-in-/data/raw/materials_defects.csv
E         2026-10-22 04:28:18,187 ERROR __main__: Input file for checksum not found: /home/runner/work/llmXive/llmXive/projects/PROJ-542-predicting-defect-formation-energies-in-/data/raw/materials_defects.csv
E         
E       assert 1 == 0
E        +  where 1 = CompletedProcess(args=['/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-542-predicting-defect-formation-energies...nner/work/llmXive/llmXive/projects/PROJ-542-predicting-defect-formation-energies-in-/data/raw/materials_defects.csv\n').returncode

tests/test_generate_checksums.py:30: AssertionError
=========================== short test summary info ============================
FAILED tests/test_generate_checksums.py::test_checksum_files_created - Assert...
1 failed, 3 passed in 0.96s



## Declared deliverables still missing

- data/processed/cv_metrics.json
- data/processed/features.csv
- data/processed/features_augmented.csv
- data/processed/performance.json
- data/processed/performance_partial.json
- data/processed/test.csv
- data/processed/train.csv
- data/raw/materials_defects.csv
- figures/feature_importance.png

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/cv_metrics.json` is declared but was NOT written. Scripts referencing it:
    - `src/models/evaluate.py` — NOT invoked by the run-book
    - `src/models/train.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/cv_metrics.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/features.csv` is declared but was NOT written. Scripts referencing it:
    - `src/data/featurize.py` — NOT invoked by the run-book
    - `src/data/validate.py` — NOT invoked by the run-book
    - `src/featurize.py` — IS a run-book command
    - `src/models/evaluate.py` — NOT invoked by the run-book
    - `src/models/split.py` — NOT invoked by the run-book
    - `src/models/train.py` — NOT invoked by the run-book
    - `src/tests/test_descriptor_gaps.py` — NOT invoked by the run-book
    - `src/utils/check_descriptor_gaps.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/features.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/features_augmented.csv` is declared but NOT written and NO script references it — create the script that produces it and add it to quickstart.md.
- `data/processed/performance.json` is declared but was NOT written. Scripts referencing it:
    - `src/models/evaluate.py` — NOT invoked by the run-book
    - `src/models/train.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/performance.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/performance_partial.json` is declared but NOT written and NO script references it — create the script that produces it and add it to quickstart.md.
- `data/processed/test.csv` is declared but was NOT written. Scripts referencing it:
    - `src/data/download.py` — NOT invoked by the run-book
    - `src/models/evaluate.py` — NOT invoked by the run-book
    - `src/models/split.py` — NOT invoked by the run-book
    - `src/models/train.py` — NOT invoked by the run-book
    - `src/pipeline/run.py` — NOT invoked by the run-book
    - `src/tests/__init__.py` — NOT invoked by the run-book
    - `src/tests/test_descriptor_gaps.py` — NOT invoked by the run-book
    - `src/tests/test_quickstart.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/test.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/train.csv` is declared but was NOT written. Scripts referencing it:
    - `src/models/__init__.py` — NOT invoked by the run-book
    - `src/models/evaluate.py` — NOT invoked by the run-book
    - `src/models/split.py` — NOT invoked by the run-book
    - `src/models/train.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/train.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/materials_defects.csv` is declared but was NOT written. Scripts referencing it:
    - `src/data/download.py` — NOT invoked by the run-book
    - `src/data/featurize.py` — NOT invoked by the run-book
    - `src/pipeline/run.py` — NOT invoked by the run-book
    - `src/utils/checksum_all.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/materials_defects.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `figures/feature_importance.png` is declared but NOT written and NO script references it — create the script that produces it and add it to quickstart.md.
