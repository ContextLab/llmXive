# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 5 command(s) failed: python -m src.featurize data/raw/materials_defects.csv data/processed/features.csv (rc=1); python -m src.train data/processed/features.csv data/processed/cv_metrics.json (rc=1); python -m src.evaluate data/processed/features.csv data/processed/performance.json (rc=1); 8 declared deliverable(s) absent: data/processed/cv_metrics.json; data/processed/features.csv; data/processed/performance.json

## Failing / missing run-book commands

- python -m src.featurize data/raw/materials_defects.csv data/processed/features.csv -> rc=1

2026-10-19 01:25:32,791 INFO src.data.featurize: Input file data/raw/materials_defects.csv not found – attempting to download raw dataset.
2026-10-19 01:25:32,791 ERROR src.data.download: MP_API_KEY environment variable not set. The script cannot proceed without a Materials Project API key.

- python -m src.train data/processed/features.csv data/processed/cv_metrics.json -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-542-predicting-defect-formation-energies-in-/bin/python: No module named src.train

- python -m src.evaluate data/processed/features.csv data/processed/performance.json -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-542-predicting-defect-formation-energies-in-/bin/python: No module named src.evaluate

- python -m pytest -q -> rc=1
          exc.stdout, exc.stderr = process.communicate()
                else:
                    # POSIX _communicate already populated the output so
                    # far into the TimeoutExpired exception.
                    process.wait()
                raise
            except:  # Including KeyboardInterrupt, communicate handled that.
                process.kill()
                # We don't call process.wait() as .__exit__ does that for us.
                raise
            retcode = process.poll()
            if check and retcode:
>               raise CalledProcessError(retcode, process.args,
                                         output=stdout, stderr=stderr)
E               subprocess.CalledProcessError: Command '['/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-542-predicting-defect-formation-energies-in-/bin/python', '-m', 'src.pipeline.run']' returned non-zero exit status 1.

/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/subprocess.py:571: CalledProcessError
=========================== short test summary info ============================
FAILED src/tests/test_quickstart.py::test_quickstart_pipeline - subprocess.Ca...
1 failed, 2 passed in 0.70s


- python -m src.pipeline  # the notebook respects the env var -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-542-predicting-defect-formation-energies-in-/bin/python: No module named src.pipeline.__main__; 'src.pipeline' is a package and cannot be directly executed


## Declared deliverables still missing

- data/processed/cv_metrics.json
- data/processed/features.csv
- data/processed/performance.json
- data/processed/test.csv
- data/processed/train.csv
- data/raw/materials_defects.csv
- figures/feature_importance.png
- figures/pred_vs_actual.png

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
- `data/processed/performance.json` is declared but was NOT written. Scripts referencing it:
    - `src/models/evaluate.py` — NOT invoked by the run-book
    - `src/models/train.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/performance.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
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
  Make ONE of these WRITE `data/raw/materials_defects.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `figures/feature_importance.png` is declared but NOT written and NO script references it — create the script that produces it and add it to quickstart.md.
- `figures/pred_vs_actual.png` is declared but was NOT written. Scripts referencing it:
    - `src/models/evaluate.py` — NOT invoked by the run-book
  Make ONE of these WRITE `figures/pred_vs_actual.png` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
