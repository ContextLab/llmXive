# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: overall deadline 300s exceeded; 4 command(s) failed: python -m pytest tests/ -v (rc=2); python -m src.extraction.fetch_prs --test-set 10 (rc=-1); python -m src.cli.main --run all --max-prs 500 --seed 42 (rc=-1); 3 declared deliverable(s) absent: data/annotations/human_annotations.json; data/derived/prs_cleaned.json; data/raw/checksums.json

## Failing / missing run-book commands

- python -m pytest tests/ -v -> rc=2
on
cachedir: .pytest_cache
rootdir: /home/runner/work/llmXive/llmXive/projects/PROJ-370-evaluating-the-impact-of-code-generation
configfile: pyproject.toml
plugins: anyio-4.15.1
collecting ... collected 30 items / 1 error

==================================== ERRORS ====================================
_________ ERROR collecting tests/unit/test_setup_project_structure.py __________
import file mismatch:
imported module 'test_setup_project_structure' has this __file__ attribute:
  /home/runner/work/llmXive/llmXive/projects/PROJ-370-evaluating-the-impact-of-code-generation/tests/test_setup_project_structure.py
which is not the same as the test file we want to collect:
  /home/runner/work/llmXive/llmXive/projects/PROJ-370-evaluating-the-impact-of-code-generation/tests/unit/test_setup_project_structure.py
HINT: remove __pycache__ / .pyc files and/or use a unique basename for your test file modules
=========================== short test summary info ============================
ERROR tests/unit/test_setup_project_structure.py
!!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
=============================== 1 error in 0.21s ===============================


- python -m src.extraction.fetch_prs --test-set 10 -> rc=-1

2026-10-26 08:24:22,161 - __main__ - INFO - Target repositories: ['microsoft/vscode', 'pytorch/pytorch', 'tensorflow/tensorflow']
2026-10-26 08:24:22,161 - __main__ - INFO - Fetching PRs for microsoft/vscode...

[TIMEOUT after 120s]
- python -m src.cli.main --run all --max-prs 500 --seed 42 -> rc=-1


[TIMEOUT after 120s]
- python -m src.extraction.fetch_prs --repos microsoft/vscode pytorch/pytorch tensorflow/tensorflow --max-prs 500 -> rc=-1

2026-10-26 08:28:22,344 - __main__ - INFO - Target repositories: ['microsoft/vscode', 'pytorch/pytorch', 'tensorflow/tensorflow']
2026-10-26 08:28:22,345 - __main__ - INFO - Fetching PRs for microsoft/vscode...
2026-10-26 08:28:30,336 - __main__ - WARNING - Rate limit hit for https://api.github.com/repos/microsoft/vscode/pulls?state=all&page=5&per_page=100.
2026-10-26 08:28:30,336 - __main__ - WARNING - Rate limit hit. Sleeping for 60 seconds.
2026-10-26 08:29:50,532 - __main__ - WARNING - Rate limit hit for https://api.github.com/repos/microsoft/vscode/pulls?state=all&page=14&per_page=100.
2026-10-26 08:29:50,532 - __main__ - WARNING - Rate limit hit. Sleeping for 60 seconds.

[TIMEOUT after 120s]

## Declared deliverables still missing

- data/annotations/human_annotations.json
- data/derived/prs_cleaned.json
- data/raw/checksums.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/annotations/human_annotations.json` is declared but was NOT written. Scripts referencing it:
    - `code/src/extraction/preprocess_and_ground_truth.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/annotations/human_annotations.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/derived/prs_cleaned.json` is declared but was NOT written. Scripts referencing it:
    - `code/src/extraction/preprocess_and_ground_truth.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/derived/prs_cleaned.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/checksums.json` is declared but was NOT written. Scripts referencing it:
    - `code/src/extraction/fetch_human_comments.py` — NOT invoked by the run-book
    - `code/src/extraction/fetch_prs.py` — NOT invoked by the run-book
    - `code/src/extraction/preprocess.py` — NOT invoked by the run-book
    - `code/src/extraction/preprocess_and_ground_truth.py` — NOT invoked by the run-book
    - `code/tests/test_preprocess.py` — NOT invoked by the run-book
    - `src/extraction/fetch_prs.py` — IS a run-book command
    - `src/extraction/preprocess.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/checksums.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
## Platform-owned paths written inside the project

A script in this project created `.github/` inside the project directory. Those names belong to the platform, and a copy of them here is a SHADOW: the verifier resolves the paths a task names relative to this project, so it reads the shadow instead of canonical state and rejects work on the strength of a stale record.

Write your outputs under `data/`, `figures/`, `code/` and `paper/`. Do not record artifact hashes, run state or project status yourself — the platform owns `state/` and derives hashes at verification time. Delete the directories listed above and drop whatever step created them.
