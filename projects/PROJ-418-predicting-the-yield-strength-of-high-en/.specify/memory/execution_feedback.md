# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 command(s) failed: python -m src.pipeline.run  --seed 42  --output-dir output/ (rc=1); python -m pytest -q (rc=2); 5 declared deliverable(s) absent: data/input/compositions.csv; data/processed/hea_descriptors.csv; data/raw/elemental_properties.csv

## Failing / missing run-book commands

- python -m src.pipeline.run  --seed 42  --output-dir output/ -> rc=1

Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-418-predicting-the-yield-strength-of-high-en/src/pipeline/run.py", line 23, in <module>
    from data.pipeline import run_pipeline
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-418-predicting-the-yield-strength-of-high-en/code/data/pipeline.py", line 12, in <module>
    from data.preprocess import preprocess_data, normalize_units
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-418-predicting-the-yield-strength-of-high-en/code/data/preprocess.py", line 6, in <module>
    from utils.unit_utils import normalize_to_mpa
ModuleNotFoundError: No module named 'utils.unit_utils'

- python -m pytest -q -> rc=2
ject_disclaimer, finalize_report_markdown
E   ModuleNotFoundError: No module named 'utils.report_utils'
=============================== warnings summary ===============================
tests/integration/test_T200_descriptor_generation.py:17
  /home/runner/work/llmXive/llmXive/projects/PROJ-418-predicting-the-yield-strength-of-high-en/tests/integration/test_T200_descriptor_generation.py:17: PytestUnknownMarkWarning: Unknown pytest.mark.integration - is this a typo?  You can register custom marks to avoid this warning - for details, see https://docs.pytest.org/en/stable/how-to/mark.html
    @pytest.mark.integration

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=========================== short test summary info ============================
ERROR code/tests/test_setup_dirs.py
ERROR tests/integration/test_pipeline.py
ERROR tests/integration/test_t117_full_pipeline.py
ERROR tests/models/test_train_linear.py
ERROR tests/test_report_generator.py
ERROR tests/test_setup_dirs.py
ERROR tests/unit/test_preprocess.py
ERROR tests/unit/test_report_generator.py
!!!!!!!!!!!!!!!!!!! Interrupted: 8 errors during collection !!!!!!!!!!!!!!!!!!!!
1 warning, 8 errors in 1.80s



## Declared deliverables still missing

- data/input/compositions.csv
- data/processed/hea_descriptors.csv
- data/raw/elemental_properties.csv
- data/raw/heas_raw.csv
- data/results/power_analysis.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/input/compositions.csv` is declared but was NOT written. Scripts referencing it:
    - `code/data/descriptors.py` — NOT invoked by the run-book
    - `code/data/fetch_heas.py` — NOT invoked by the run-book
    - `code/data/pipeline.py` — NOT invoked by the run-book
    - `code/data/validate_user_composition.py` — NOT invoked by the run-book
    - `code/tests/test_user_composition.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/input/compositions.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/hea_descriptors.csv` is declared but was NOT written. Scripts referencing it:
    - `code/T015_generate.py` — NOT invoked by the run-book
    - `code/T061_compute_checksum.py` — NOT invoked by the run-book
    - `code/data/descriptors.py` — NOT invoked by the run-book
    - `code/data/pipeline.py` — NOT invoked by the run-book
    - `code/data/status_writer.py` — NOT invoked by the run-book
    - `code/models/evaluate.py` — NOT invoked by the run-book
    - `code/models/train.py` — NOT invoked by the run-book
    - `code/run_full_pipeline.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/hea_descriptors.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/elemental_properties.csv` is declared but was NOT written. Scripts referencing it:
    - `code/data/descriptors.py` — NOT invoked by the run-book
    - `code/tests/test_descriptors.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/elemental_properties.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/heas_raw.csv` is declared but was NOT written. Scripts referencing it:
    - `code/T015_generate.py` — NOT invoked by the run-book
    - `code/data/descriptors.py` — NOT invoked by the run-book
    - `code/data/download.py` — NOT invoked by the run-book
    - `code/data/fetch_heas.py` — NOT invoked by the run-book
    - `code/data/load_dataset.py` — NOT invoked by the run-book
    - `code/data/verify_dataset_presence.py` — NOT invoked by the run-book
    - `code/run_full_pipeline.py` — NOT invoked by the run-book
    - `code/run_pipeline_with_checksum.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/heas_raw.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/power_analysis.json` is declared but was NOT written. Scripts referencing it:
    - `code/data/pipeline.py` — NOT invoked by the run-book
    - `code/data/verify_dataset_presence.py` — NOT invoked by the run-book
    - `code/main.py` — NOT invoked by the run-book
    - `code/models/power_analysis.py` — NOT invoked by the run-book
    - `code/validate_quickstart.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/power_analysis.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
