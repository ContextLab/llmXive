# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: overall deadline 300s exceeded; 4 command(s) failed: python -m pytest tests/ -v (rc=2); python -m src.extraction.fetch_prs --test-set 10 (rc=-1); python -m src.cli.main --run all --max-prs 500 --seed 42 (rc=-1); 1 declared deliverable(s) absent: data/raw/checksums.json

## Failing / missing run-book commands

- python -m pytest tests/ -v -> rc=2
___________
ImportError while importing test module '/home/runner/work/llmXive/llmXive/projects/PROJ-370-evaluating-the-impact-of-code-generation/tests/unit/test_utils.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/importlib/__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
tests/unit/test_utils.py:6: in <module>
    from src.utils.timeout_wrapper import check_global_timeout, START_TIME_FILE, TIMEOUT_LOG_PATH, TIMEOUT_LIMIT_SECONDS
E   ImportError: cannot import name 'check_global_timeout' from 'src.utils.timeout_wrapper' (/home/runner/work/llmXive/llmXive/projects/PROJ-370-evaluating-the-impact-of-code-generation/src/utils/timeout_wrapper.py)
=========================== short test summary info ============================
ERROR tests/test_preprocess.py
ERROR tests/unit/test_preprocess_and_ground_truth.py
ERROR tests/unit/test_setup_project_structure.py
ERROR tests/unit/test_utils.py
!!!!!!!!!!!!!!!!!!! Interrupted: 4 errors during collection !!!!!!!!!!!!!!!!!!!!
============================== 4 errors in 0.27s ===============================


- python -m src.extraction.fetch_prs --test-set 10 -> rc=-1

2026-10-16 12:25:32,737 - __main__ - INFO - Target repositories: ['microsoft/vscode', 'pytorch/pytorch', 'tensorflow/tensorflow']
2026-10-16 12:25:32,737 - __main__ - INFO - Fetching PRs for microsoft/vscode...

[TIMEOUT after 120s]
- python -m src.cli.main --run all --max-prs 500 --seed 42 -> rc=-1
2026-10-16 12:27:32,843 [INFO] __main__: Global timeout set to 6.00 hours
2026-10-16 12:27:32,843 [INFO] __main__: Phases to execute: ['extraction', 'detection', 'inference', 'analysis', 'reporting']
2026-10-16 12:27:32,843 [INFO] __main__: Remaining time budget: 21600.00 seconds
2026-10-16 12:27:32,843 [INFO] root: === Extraction Phase ===
2026-10-16 12:27:32,866 [INFO] root: Running src.extraction.fetch_prs.main()
2026-10-16 12:27:32,866 [INFO] src.extraction.fetch_prs: Target repositories: ['microsoft/vscode', 'pytorch/pytorch', 'tensorflow/tensorflow']
2026-10-16 12:27:32,866 [INFO] src.extraction.fetch_prs: Fetching PRs for microsoft/vscode...
2026-10-16 12:28:47,586 [WARNING] src.extraction.fetch_prs: Rate limit hit for https://api.github.com/repos/microsoft/vscode/pulls?state=all&page=35&per_page=100.
2026-10-16 12:28:47,587 [WARNING] src.extraction.fetch_prs: Rate limit hit. Sleeping for 60 seconds.


[TIMEOUT after 120s]
- python -m src.extraction.fetch_prs --repos microsoft/vscode pytorch/pytorch tensorflow/tensorflow --max-prs 500 -> rc=-1

2026-10-16 12:29:32,889 - __main__ - INFO - Target repositories: ['microsoft/vscode', 'pytorch/pytorch', 'tensorflow/tensorflow']
2026-10-16 12:29:32,889 - __main__ - INFO - Fetching PRs for microsoft/vscode...
2026-10-16 12:29:32,966 - __main__ - WARNING - Rate limit hit for https://api.github.com/repos/microsoft/vscode/pulls?state=all&page=1&per_page=100.
2026-10-16 12:29:32,966 - __main__ - WARNING - Rate limit hit. Sleeping for 60 seconds.
2026-10-16 12:30:33,066 - __main__ - WARNING - Rate limit hit for https://api.github.com/repos/microsoft/vscode/pulls?state=all&page=1&per_page=100.
2026-10-16 12:30:33,066 - __main__ - WARNING - Rate limit hit. Sleeping for 60 seconds.

[TIMEOUT after 120s]

## Declared deliverables still missing

- data/raw/checksums.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/raw/checksums.json` is declared but was NOT written. Scripts referencing it:
    - `code/src/extraction/fetch_human_comments.py` — NOT invoked by the run-book
    - `code/src/extraction/fetch_prs.py` — NOT invoked by the run-book
    - `code/src/extraction/preprocess.py` — NOT invoked by the run-book
    - `code/tests/test_preprocess.py` — NOT invoked by the run-book
    - `src/extraction/fetch_prs.py` — IS a run-book command
    - `src/extraction/preprocess.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/checksums.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
## Platform-owned paths written inside the project

A script in this project created `.github/` inside the project directory. Those names belong to the platform, and a copy of them here is a SHADOW: the verifier resolves the paths a task names relative to this project, so it reads the shadow instead of canonical state and rejects work on the strength of a stale record.

Write your outputs under `data/`, `figures/`, `code/` and `paper/`. Do not record artifact hashes, run state or project status yourself — the platform owns `state/` and derives hashes at verification time. Delete the directories listed above and drop whatever step created them.
