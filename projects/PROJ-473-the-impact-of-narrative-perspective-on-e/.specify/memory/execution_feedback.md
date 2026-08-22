# Execution failures — fix these before the analysis can run

## ⚠ REGRESSIONS — your last fix BROKE these (they passed before)

These commands were NOT failing in the previous round and ARE failing now — your last edit broke previously-working code. REVERT or correct whatever change broke each one BEFORE touching anything else; do not trade one passing script for another (that oscillation is what burns the fix-round budget toward escalation):

- `python -m spacy download en_core_web_sm`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 5 command(s) failed: python -m spacy download en_core_web_sm (rc=1); python code/main.py --config code/config.py (rc=1); python code/main.py --step extraction (rc=1); 9 declared deliverable(s) absent: data/artifacts/regression_plot.png; data/processed/aligned_dataset.csv; data/processed/aligned_reader_response.csv

## Failing / missing run-book commands

- python -m spacy download en_core_web_sm -> rc=1
    Collecting https://github.com/explosion/spacy-models/releases/download/-en_core_web_sm/-en_core_web_sm.tar.gz

  ERROR: HTTP error 404 while getting https://github.com/explosion/spacy-models/releases/download/-en_core_web_sm/-en_core_web_sm.tar.gz
ERROR: Could not install requirement https://github.com/explosion/spacy-models/releases/download/-en_core_web_sm/-en_core_web_sm.tar.gz because of HTTP error 404 Client Error: Not Found for url: https://github.com/explosion/spacy-models/releases/download/-en_core_web_sm/-en_core_web_sm.tar.gz for URL https://github.com/explosion/spacy-models/releases/download/-en_core_web_sm/-en_core_web_sm.tar.gz

[notice] A new release of pip is available: 24.0 -> 26.2.1
[notice] To update, run: python -m pip install --upgrade pip
- python code/main.py --config code/config.py -> rc=1
    il.load_model(
           ^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-473-the-impact-of-narrative-perspective-on-e/code/.venv/lib/python3.11/site-packages/spacy/util.py", line 472, in load_model
    raise IOError(Errors.E050.format(name=name))
OSError: [E050] Can't find model 'en_core_web_sm'. It doesn't seem to be a Python package or a valid path to a data directory.

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-473-the-impact-of-narrative-perspective-on-e/code/main.py", line 20, in <module>
    from extraction import extract_perspective_features
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-473-the-impact-of-narrative-perspective-on-e/code/extraction.py", line 14, in <module>
    subprocess.check_call(["python", "-m", "spacy", "download", "en_core_web_sm"])
  File "/opt/hostedtoolcache/Python/3.11.16/x64/lib/python3.11/subprocess.py", line 413, in check_call
    raise CalledProcessError(retcode, cmd)
subprocess.CalledProcessError: Command '['python', '-m', 'spacy', 'download', 'en_core_web_sm']' returned non-zero exit status 1.
- python code/main.py --step extraction -> rc=1
    il.load_model(
           ^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-473-the-impact-of-narrative-perspective-on-e/code/.venv/lib/python3.11/site-packages/spacy/util.py", line 472, in load_model
    raise IOError(Errors.E050.format(name=name))
OSError: [E050] Can't find model 'en_core_web_sm'. It doesn't seem to be a Python package or a valid path to a data directory.

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-473-the-impact-of-narrative-perspective-on-e/code/main.py", line 20, in <module>
    from extraction import extract_perspective_features
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-473-the-impact-of-narrative-perspective-on-e/code/extraction.py", line 14, in <module>
    subprocess.check_call(["python", "-m", "spacy", "download", "en_core_web_sm"])
  File "/opt/hostedtoolcache/Python/3.11.16/x64/lib/python3.11/subprocess.py", line 413, in check_call
    raise CalledProcessError(retcode, cmd)
subprocess.CalledProcessError: Command '['python', '-m', 'spacy', 'download', 'en_core_web_sm']' returned non-zero exit status 1.
- python code/main.py --step analysis -> rc=1
    il.load_model(
           ^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-473-the-impact-of-narrative-perspective-on-e/code/.venv/lib/python3.11/site-packages/spacy/util.py", line 472, in load_model
    raise IOError(Errors.E050.format(name=name))
OSError: [E050] Can't find model 'en_core_web_sm'. It doesn't seem to be a Python package or a valid path to a data directory.

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-473-the-impact-of-narrative-perspective-on-e/code/main.py", line 20, in <module>
    from extraction import extract_perspective_features
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-473-the-impact-of-narrative-perspective-on-e/code/extraction.py", line 14, in <module>
    subprocess.check_call(["python", "-m", "spacy", "download", "en_core_web_sm"])
  File "/opt/hostedtoolcache/Python/3.11.16/x64/lib/python3.11/subprocess.py", line 413, in check_call
    raise CalledProcessError(retcode, cmd)
subprocess.CalledProcessError: Command '['python', '-m', 'spacy', 'download', 'en_core_web_sm']' returned non-zero exit status 1.
- python -m pytest tests/contract/ -> rc=4
    ============================= test session starts ==============================
platform linux -- Python 3.11.16, pytest-7.4.3, pluggy-1.6.0 -- /home/runner/work/llmXive/llmXive/projects/PROJ-473-the-impact-of-narrative-perspective-on-e/code/.venv/bin/python
cachedir: .pytest_cache
rootdir: /home/runner/work/llmXive/llmXive/projects/PROJ-473-the-impact-of-narrative-perspective-on-e
configfile: pyproject.toml
collecting ... collected 0 items

============================ no tests ran in 0.00s =============================

ERROR: file or directory not found: tests/contract/

## Declared deliverables still missing

- data/artifacts/regression_plot.png
- data/processed/aligned_dataset.csv
- data/processed/aligned_reader_response.csv
- data/processed/analysis_results.json
- data/processed/matching_results.json
- data/processed/perspective_features.json
- data/processed/sensitivity_report.json
- data/processed/thresholds.json
- data/raw/gold_standard_annotations.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/artifacts/regression_plot.png` is declared but was NOT written. Scripts referencing it:
    - `code/analysis.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/artifacts/regression_plot.png` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/aligned_dataset.csv` is declared but was NOT written. Scripts referencing it:
    - `code/main.py` — IS a run-book command
    - `code/data_collection.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/aligned_dataset.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/aligned_reader_response.csv` is declared but was NOT written. Scripts referencing it:
    - `code/main.py` — IS a run-book command
    - `code/data_collection.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/aligned_reader_response.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/analysis_results.json` is declared but was NOT written. Scripts referencing it:
    - `code/main.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/analysis_results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/matching_results.json` is declared but was NOT written. Scripts referencing it:
    - `code/matching.py` — NOT invoked by the run-book
    - `code/main.py` — IS a run-book command
    - `code/analysis.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/matching_results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/perspective_features.json` is declared but was NOT written. Scripts referencing it:
    - `code/main.py` — IS a run-book command
    - `code/data_collection.py` — NOT invoked by the run-book
    - `code/extraction.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/perspective_features.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/sensitivity_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/main.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/sensitivity_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/thresholds.json` is declared but was NOT written. Scripts referencing it:
    - `code/matching.py` — NOT invoked by the run-book
    - `code/main.py` — IS a run-book command
    - `code/data_loader.py` — NOT invoked by the run-book
    - `code/analysis.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/thresholds.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/raw/gold_standard_annotations.csv` is declared but was NOT written. Scripts referencing it:
    - `code/config.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/gold_standard_annotations.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
