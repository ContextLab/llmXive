# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 command(s) failed: python -m code.ingest --check (rc=1); python -m pytest -m contract (rc=5); 3 declared deliverable(s) absent: data/checksums.json; data/raw/tg_dataset.csv; data/raw/vk_fragments.csv

## Failing / missing run-book commands

- python -m code.ingest --check -> rc=1

2026-10-31 03:08:00,304 ERROR __main__: Checksums file not found at /home/runner/work/llmXive/llmXive/projects/PROJ-323-predicting-glass-transition-temperature-/data/checksums.json

- python -m pytest -m contract -> rc=5
======================
platform linux -- Python 3.11.17, pytest-8.2.0, pluggy-1.7.0
rootdir: /home/runner/work/llmXive/llmXive
configfile: pyproject.toml
collected 7 items / 7 deselected / 0 selected

=============================== warnings summary ===============================
tests/test_ingest_check.py:19
  /home/runner/work/llmXive/llmXive/projects/PROJ-323-predicting-glass-transition-temperature-/tests/test_ingest_check.py:19: PytestUnknownMarkWarning: Unknown pytest.mark.timeout - is this a typo?  You can register custom marks to avoid this warning - for details, see https://docs.pytest.org/en/stable/how-to/mark.html
    @pytest.mark.timeout(300)

tests/test_memory_usage.py:20
  /home/runner/work/llmXive/llmXive/projects/PROJ-323-predicting-glass-transition-temperature-/tests/test_memory_usage.py:20: PytestUnknownMarkWarning: Unknown pytest.mark.timeout - is this a typo?  You can register custom marks to avoid this warning - for details, see https://docs.pytest.org/en/stable/how-to/mark.html
    @pytest.mark.timeout(300)

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
====================== 7 deselected, 2 warnings in 0.30s =======================



## Declared deliverables still missing

- data/checksums.json
- data/raw/tg_dataset.csv
- data/raw/vk_fragments.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/checksums.json` is declared but was NOT written. Scripts referencing it:
    - `code/ingest.py` — IS a run-book command
    - `code/ingest_tg.py` — NOT invoked by the run-book
    - `code/ingest_vk.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/checksums.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/tg_dataset.csv` is declared but was NOT written. Scripts referencing it:
    - `code/ingest_tg.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/tg_dataset.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/vk_fragments.csv` is declared but was NOT written. Scripts referencing it:
    - `code/ingest_vk.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/vk_fragments.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
## Platform-owned paths written inside the project

A script in this project created `.github/` inside the project directory. Those names belong to the platform, and a copy of them here is a SHADOW: the verifier resolves the paths a task names relative to this project, so it reads the shadow instead of canonical state and rejects work on the strength of a stale record.

Write your outputs under `data/`, `figures/`, `code/` and `paper/`. Do not record artifact hashes, run state or project status yourself — the platform owns `state/` and derives hashes at verification time. Delete the directories listed above and drop whatever step created them.
