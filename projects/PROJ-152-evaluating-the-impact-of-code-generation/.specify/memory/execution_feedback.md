# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 run-book script(s) missing (plan/impl path mismatch): python code/viz.py; 6 command(s) failed: python code/download.py (rc=1); python code/generate.py (rc=1); python code/analyze.py (rc=1); 6 declared deliverable(s) absent: data/calibration/human_labels.csv; data/calibration/validation_report.json; data/generated/snippets.csv

## Failing / missing run-book commands

- python code/download.py -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-152-evaluating-the-impact-of-code-generation/code/download.py", line 9, in <module>
    from datasets import load_dataset
ModuleNotFoundError: No module named 'datasets'

- python code/generate.py -> rc=1
2026-10-14 15:33:57,181 - INFO - Starting Generation Loop (T014)
2026-10-14 15:33:57,181 - CRITICAL - Failed to load prompts: Manifest not found at /home/runner/work/llmXive/llmXive/projects/PROJ-152-evaluating-the-impact-of-code-generation/data/prompts/manifest.json. Run T010 first.


- python code/analyze.py -> rc=1
2026-10-14 15:33:57,544 - INFO - Starting vulnerability analysis pipeline...
2026-10-14 15:33:57,544 - ERROR - Severity map not found at /home/runner/work/llmXive/llmXive/projects/PROJ-152-evaluating-the-impact-of-code-generation/data/mappings/nist_severity_map.yaml
2026-10-14 15:33:57,544 - ERROR - Failed to load severity map: Severity map not found: /home/runner/work/llmXive/llmXive/projects/PROJ-152-evaluating-the-impact-of-code-generation/data/mappings/nist_severity_map.yaml


- python code/metrics.py -> rc=1
2026-10-14 15:33:57,901 - ERROR - Raw findings file not found: /home/runner/work/llmXive/llmXive/projects/PROJ-152-evaluating-the-impact-of-code-generation/data/findings/raw_findings.csv

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-152-evaluating-the-impact-of-code-generation/code/metrics.py", line 201, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-152-evaluating-the-impact-of-code-generation/code/metrics.py", line 178, in main
    raise FileNotFoundError(f"Raw findings file not found: {raw_findings_path}")
FileNotFoundError: Raw findings file not found: /home/runner/work/llmXive/llmXive/projects/PROJ-152-evaluating-the-impact-of-code-generation/data/findings/raw_findings.csv

- python code/stats.py -> rc=1

2026-10-14 15:33:58,497 - __main__ - INFO - Loading raw metrics...
2026-10-14 15:33:58,498 - __main__ - ERROR - Input file error: Raw metrics file not found: /home/runner/work/llmXive/llmXive/projects/PROJ-152-evaluating-the-impact-of-code-generation/data/results/raw_metrics.csv

- python code/viz.py -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-152-evaluating-the-impact-of-code-generation/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-152-evaluating-the-impact-of-code-generation/code/viz.py': [Errno 2] No such file or directory

- python -m pytest tests/integration/test_pipeline_subset.py -v -> rc=4
============================= test session starts ==============================
platform linux -- Python 3.11.17, pytest-7.4.3, pluggy-1.6.0 -- /home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-152-evaluating-the-impact-of-code-generation/bin/python
cachedir: .pytest_cache
rootdir: /home/runner/work/llmXive/llmXive/projects/PROJ-152-evaluating-the-impact-of-code-generation
plugins: anyio-4.15.1
collecting ... collected 0 items

============================ no tests ran in 0.00s =============================

ERROR: file or directory not found: tests/integration/test_pipeline_subset.py



## Declared deliverables still missing

- data/calibration/human_labels.csv
- data/calibration/validation_report.json
- data/generated/snippets.csv
- data/results/dunn_results.csv
- data/results/kw_results.csv
- data/results/raw_metrics.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/calibration/human_labels.csv` is declared but was NOT written. Scripts referencing it:
    - `code/calibration.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/calibration/human_labels.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/calibration/validation_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/calibration.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/calibration/validation_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/generated/snippets.csv` is declared but was NOT written. Scripts referencing it:
    - `code/align_plan.py` — NOT invoked by the run-book
    - `code/analyze.py` — IS a run-book command
    - `code/export_snippets.py` — NOT invoked by the run-book
    - `code/generate.py` — IS a run-book command
    - `code/metrics.py` — IS a run-book command
  Make ONE of these WRITE `data/generated/snippets.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/dunn_results.csv` is declared but was NOT written. Scripts referencing it:
    - `code/stats.py` — IS a run-book command
  Make ONE of these WRITE `data/results/dunn_results.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/kw_results.csv` is declared but was NOT written. Scripts referencing it:
    - `code/stats.py` — IS a run-book command
  Make ONE of these WRITE `data/results/kw_results.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/raw_metrics.csv` is declared but was NOT written. Scripts referencing it:
    - `code/stats.py` — IS a run-book command
  Make ONE of these WRITE `data/results/raw_metrics.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
