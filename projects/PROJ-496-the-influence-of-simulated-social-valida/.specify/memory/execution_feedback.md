# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 5 command(s) failed: python code/search.py (rc=1); python code/preprocess.py --dataset-id <ID> (rc=1); python code/analyze.py (rc=1); 7 declared deliverable(s) absent: data/processed/p300_measures.csv; data/results/categorization_log.json; data/results/erp_waveform.png

## Failing / missing run-book commands

- python code/search.py -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-496-the-influence-of-simulated-social-valida/code/search.py", line 11, in <module>
    from utils import verify_real_data_source
ModuleNotFoundError: No module named 'utils'

- python code/preprocess.py --dataset-id <ID> -> rc=1
2026-10-09 12:19:08,761 - __main__ - INFO - Starting preprocessing phase

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-496-the-influence-of-simulated-social-valida/code/preprocess.py", line 358, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-496-the-influence-of-simulated-social-valida/code/preprocess.py", line 349, in main
    run_preprocess_phase(
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-496-the-influence-of-simulated-social-valida/code/preprocess.py", line 248, in run_preprocess_phase
    ensure_dirs([output_dir, log_dir])
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-496-the-influence-of-simulated-social-valida/code/config.py", line 49, in ensure_dirs
    d.mkdir(parents=True, exist_ok=True)
    ^^^^^^^
AttributeError: 'list' object has no attribute 'mkdir'

- python code/analyze.py -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-496-the-influence-of-simulated-social-valida/code/analyze.py", line 223, in <module>
    sys.exit(main())
             ^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-496-the-influence-of-simulated-social-valida/code/analyze.py", line 216, in main
    logger = get_logger()
             ^^^^^^^^^^^^
TypeError: get_logger() missing 1 required positional argument: 'name'

- python code/report.py -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-496-the-influence-of-simulated-social-valida/code/report.py", line 356, in <module>
    sys.exit(main())
             ^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-496-the-influence-of-simulated-social-valida/code/report.py", line 347, in main
    logger = get_logger()
             ^^^^^^^^^^^^
TypeError: get_logger() missing 1 required positional argument: 'name'

- python -m pytest tests/ -> rc=1

/home/runner/work/llmXive/llmXive/projects/PROJ-496-the-influence-of-simulated-social-valida/code/.venv/bin/python: No module named pytest


## Declared deliverables still missing

- data/processed/p300_measures.csv
- data/results/categorization_log.json
- data/results/erp_waveform.png
- data/results/model_summary.csv
- data/results/negative_finding_report_v1.pdf
- data/results/report.pdf
- data/results/sensitivity_comparison.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/p300_measures.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analyze.py` — IS a run-book command
    - `code/preprocess.py` — IS a run-book command
    - `code/report.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/p300_measures.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/categorization_log.json` is declared but was NOT written. Scripts referencing it:
    - `code/report_generator.py` — NOT invoked by the run-book
    - `code/search.py` — IS a run-book command
  Make ONE of these WRITE `data/results/categorization_log.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/erp_waveform.png` is declared but was NOT written. Scripts referencing it:
    - `code/report.py` — IS a run-book command
  Make ONE of these WRITE `data/results/erp_waveform.png` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/model_summary.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analyze.py` — IS a run-book command
    - `code/report.py` — IS a run-book command
  Make ONE of these WRITE `data/results/model_summary.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/negative_finding_report_v1.pdf` is declared but was NOT written. Scripts referencing it:
    - `code/analyze.py` — IS a run-book command
    - `code/error_handler.py` — NOT invoked by the run-book
    - `code/generate_negative_finding_report.py` — NOT invoked by the run-book
    - `code/report.py` — IS a run-book command
    - `code/report_generator.py` — NOT invoked by the run-book
    - `code/search.py` — IS a run-book command
  Make ONE of these WRITE `data/results/negative_finding_report_v1.pdf` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/report.pdf` is declared but was NOT written. Scripts referencing it:
    - `code/analyze.py` — IS a run-book command
    - `code/error_handler.py` — NOT invoked by the run-book
    - `code/generate_negative_finding_report.py` — NOT invoked by the run-book
    - `code/generate_negative_finding_report_separate.py` — NOT invoked by the run-book
    - `code/main.py` — NOT invoked by the run-book
    - `code/report.py` — IS a run-book command
    - `code/report_generator.py` — NOT invoked by the run-book
    - `code/search.py` — IS a run-book command
  Make ONE of these WRITE `data/results/report.pdf` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/sensitivity_comparison.csv` is declared but was NOT written. Scripts referencing it:
    - `code/report.py` — IS a run-book command
  Make ONE of these WRITE `data/results/sensitivity_comparison.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
