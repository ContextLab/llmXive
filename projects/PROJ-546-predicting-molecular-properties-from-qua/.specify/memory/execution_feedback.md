# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 4 command(s) failed: python code/main.py run (rc=1); python code/main.py fetch (rc=1); python code/main.py optimize (rc=1); 4 declared deliverable(s) absent: data/confounds.csv; data/descriptors_dft.csv; data/descriptors_semi.csv

## Failing / missing run-book commands

- python code/main.py run -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-546-predicting-molecular-properties-from-qua/code/main.py", line 17, in <module>
    from evaluate_models import main as evaluate_models_main
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-546-predicting-molecular-properties-from-qua/code/evaluate_models.py", line 21, in <module>
    from config import PROJECT_ROOT
ImportError: cannot import name 'PROJECT_ROOT' from 'config' (/home/runner/work/llmXive/llmXive/projects/PROJ-546-predicting-molecular-properties-from-qua/code/config.py)

- python code/main.py fetch -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-546-predicting-molecular-properties-from-qua/code/main.py", line 17, in <module>
    from evaluate_models import main as evaluate_models_main
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-546-predicting-molecular-properties-from-qua/code/evaluate_models.py", line 21, in <module>
    from config import PROJECT_ROOT
ImportError: cannot import name 'PROJECT_ROOT' from 'config' (/home/runner/work/llmXive/llmXive/projects/PROJ-546-predicting-molecular-properties-from-qua/code/config.py)

- python code/main.py optimize -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-546-predicting-molecular-properties-from-qua/code/main.py", line 17, in <module>
    from evaluate_models import main as evaluate_models_main
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-546-predicting-molecular-properties-from-qua/code/evaluate_models.py", line 21, in <module>
    from config import PROJECT_ROOT
ImportError: cannot import name 'PROJECT_ROOT' from 'config' (/home/runner/work/llmXive/llmXive/projects/PROJ-546-predicting-molecular-properties-from-qua/code/config.py)

- python code/main.py train -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-546-predicting-molecular-properties-from-qua/code/main.py", line 17, in <module>
    from evaluate_models import main as evaluate_models_main
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-546-predicting-molecular-properties-from-qua/code/evaluate_models.py", line 21, in <module>
    from config import PROJECT_ROOT
ImportError: cannot import name 'PROJECT_ROOT' from 'config' (/home/runner/work/llmXive/llmXive/projects/PROJ-546-predicting-molecular-properties-from-qua/code/config.py)


## Declared deliverables still missing

- data/confounds.csv
- data/descriptors_dft.csv
- data/descriptors_semi.csv
- data/raw/barrier_dataset.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/confounds.csv` is declared but was NOT written. Scripts referencing it:
    - `code/confound_analysis.py` — NOT invoked by the run-book
    - `code/confounds.py` — NOT invoked by the run-book
    - `code/dft_calculator.py` — NOT invoked by the run-book
    - `code/generate_checksums.py` — IS a run-book command
    - `code/main.py` — IS a run-book command
  Make ONE of these WRITE `data/confounds.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/descriptors_dft.csv` is declared but was NOT written. Scripts referencing it:
    - `code/evaluate_models.py` — NOT invoked by the run-book
    - `code/evaluators/missing_dof_analyzer.py` — NOT invoked by the run-book
    - `code/generate_checksums.py` — IS a run-book command
    - `code/missing_dof_analysis.py` — NOT invoked by the run-book
    - `code/track_compute_resources.py` — NOT invoked by the run-book
    - `code/train_models.py` — NOT invoked by the run-book
    - `code/validate_subset_alignment.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/descriptors_dft.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/descriptors_semi.csv` is declared but was NOT written. Scripts referencing it:
    - `code/descriptor_pipeline.py` — NOT invoked by the run-book
    - `code/evaluate_models.py` — NOT invoked by the run-book
    - `code/evaluators/missing_dof_analyzer.py` — NOT invoked by the run-book
    - `code/generate_checksums.py` — IS a run-book command
    - `code/missing_dof_analysis.py` — NOT invoked by the run-book
    - `code/noise_injection.py` — NOT invoked by the run-book
    - `code/outputs/us1_artifacts.py` — NOT invoked by the run-book
    - `code/physical_validator.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/descriptors_semi.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/barrier_dataset.csv` is declared but was NOT written. Scripts referencing it:
    - `code/confounds.py` — NOT invoked by the run-book
    - `code/descriptor_pipeline.py` — NOT invoked by the run-book
    - `code/dft_calculator.py` — NOT invoked by the run-book
    - `code/extract_archive.py` — NOT invoked by the run-book
    - `code/fetch_data.py` — NOT invoked by the run-book
    - `code/missing_dof_analysis.py` — NOT invoked by the run-book
    - `code/normalize_data.py` — NOT invoked by the run-book
    - `code/train_models.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/barrier_dataset.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
