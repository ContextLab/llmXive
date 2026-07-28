# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 run-book script(s) missing (plan/impl path mismatch): python code/analyze.py; python code/report.py; 2 command(s) failed: python code/search.py (rc=1); python code/preprocess.py --dataset-id <ID> (rc=1); 1 declared deliverable(s) absent: data/results/negative_finding_report_v1.pdf

## Failing / missing run-book commands

- python code/search.py -> rc=1
    Found 1 datasets with 'None' status. Triggering negative finding report.
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-496-the-influence-of-simulated-social-valida/code/search.py", line 149, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-496-the-influence-of-simulated-social-valida/code/search.py", line 146, in main
    run_search_phase()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-496-the-influence-of-simulated-social-valida/code/search.py", line 139, in run_search_phase
    from generate_negative_finding_report import main as generate_report_main
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-496-the-influence-of-simulated-social-valida/code/generate_negative_finding_report.py", line 9, in <module>
    from report_generator import generate_negative_finding_report
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-496-the-influence-of-simulated-social-valida/code/report_generator.py", line 4, in <module>
    from reportlab.lib.pagesizes import letter
ModuleNotFoundError: No module named 'reportlab'
- python code/preprocess.py --dataset-id <ID> -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-496-the-influence-of-simulated-social-valida/code/preprocess.py", line 8, in <module>
    import mne
ModuleNotFoundError: No module named 'mne'
- python code/analyze.py -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-496-the-influence-of-simulated-social-valida/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-496-the-influence-of-simulated-social-valida/code/analyze.py': [Errno 2] No such file or directory
- python code/report.py -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-496-the-influence-of-simulated-social-valida/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-496-the-influence-of-simulated-social-valida/code/report.py': [Errno 2] No such file or directory

## Declared deliverables still missing

- data/results/negative_finding_report_v1.pdf

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/results/negative_finding_report_v1.pdf` is declared but was NOT written. Scripts referencing it:
    - `code/generate_negative_finding_report.py` — NOT invoked by the run-book
    - `code/error_handler.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/negative_finding_report_v1.pdf` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
