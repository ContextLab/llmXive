# Execution failures — fix these before the analysis can run

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python code/main.py --mode full  --replicates 900  --batch-size 100  --seed 12345`
  - script usage: `main.py [-h] [--mode {dry-run,full}] [--seed SEED]`
  - argparse error: `main.py: error: unrecognized arguments: --replicates 900 --batch-size 100`
- run-book command: `python code/main.py --mode dry-run  --replicates 10  --tau-squared 0.5 1.0  --batch-size 5  --seed 42`
  - script usage: `main.py [-h] [--mode {dry-run,full}] [--seed SEED]`
  - argparse error: `main.py: error: unrecognized arguments: --replicates 10 --tau-squared 0.5 1.0 --batch-size 5`
- run-book command: `python code/main.py --validate-contracts`
  - script usage: `main.py [-h] [--mode {dry-run,full}] [--seed SEED]`
  - argparse error: `main.py: error: unrecognized arguments: --validate-contracts`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 5 command(s) failed: python code/main.py --mode full  --replicates 900  --batch-size 100  --seed 12345 (rc=2); python code/main.py --mode dry-run  --replicates 10  --tau-squared 0.5 1.0  --batch-size 5  --seed 42 (rc=2); python code/main.py --validate-contracts (rc=2); 2 declared deliverable(s) absent: data/results/aggregated_metrics.csv; data/results/reml_failures.json

## Failing / missing run-book commands

- python code/main.py --mode full  --replicates 900  --batch-size 100  --seed 12345 -> rc=2

usage: main.py [-h] [--mode {dry-run,full}] [--seed SEED]
main.py: error: unrecognized arguments: --replicates 900 --batch-size 100

- python code/main.py --mode dry-run  --replicates 10  --tau-squared 0.5 1.0  --batch-size 5  --seed 42 -> rc=2

usage: main.py [-h] [--mode {dry-run,full}] [--seed SEED]
main.py: error: unrecognized arguments: --replicates 10 --tau-squared 0.5 1.0 --batch-size 5

- python code/main.py --validate-contracts -> rc=2

usage: main.py [-h] [--mode {dry-run,full}] [--seed SEED]
main.py: error: unrecognized arguments: --validate-contracts

- python -m pytest tests/unit/ -> rc=2
mary ===============================
tests/unit/test_generate_base.py:17
  /home/runner/work/llmXive/llmXive/projects/PROJ-417-assessing-the-impact-of-data-heterogenei/tests/unit/test_generate_base.py:17: PytestUnknownMarkWarning: Unknown pytest.mark.timeout - is this a typo?  You can register custom marks to avoid this warning - for details, see https://docs.pytest.org/en/stable/how-to/mark.html
    @pytest.mark.timeout(60)

tests/unit/test_validate_cochrane_download.py:16
  /home/runner/work/llmXive/llmXive/projects/PROJ-417-assessing-the-impact-of-data-heterogenei/tests/unit/test_validate_cochrane_download.py:16: PytestUnknownMarkWarning: Unknown pytest.mark.timeout - is this a typo?  You can register custom marks to avoid this warning - for details, see https://docs.pytest.org/en/stable/how-to/mark.html
    @pytest.mark.timeout(60)

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=========================== short test summary info ============================
ERROR tests/unit/test_generator.py
!!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
========================= 2 warnings, 1 error in 0.89s =========================


- python -m pytest tests/integration/ -> rc=1

E            +    where <bound method Path.is_file of PosixPath('/home/runner/work/llmXive/llmXive/projects/PROJ-417-assessing-the-impact-of-data-heterogenei/data/results/estimation_results.csv')> = PosixPath('/home/runner/work/llmXive/llmXive/projects/PROJ-417-assessing-the-impact-of-data-heterogenei/data/results/estimation_results.csv').is_file

tests/integration/test_pipeline.py:58: AssertionError
=============================== warnings summary ===============================
tests/integration/test_pipeline.py:30
  /home/runner/work/llmXive/llmXive/projects/PROJ-417-assessing-the-impact-of-data-heterogenei/tests/integration/test_pipeline.py:30: PytestUnknownMarkWarning: Unknown pytest.mark.timeout - is this a typo?  You can register custom marks to avoid this warning - for details, see https://docs.pytest.org/en/stable/how-to/mark.html
    @pytest.mark.timeout(300)

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=========================== short test summary info ============================
FAILED tests/integration/test_pipeline.py::test_full_pipeline_dry_run - Asser...
========================= 1 failed, 1 warning in 1.47s =========================



## Declared deliverables still missing

- data/results/aggregated_metrics.csv
- data/results/reml_failures.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/results/aggregated_metrics.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/aggregate_metrics.py` — NOT invoked by the run-book
    - `code/analysis/stats.py` — NOT invoked by the run-book
    - `code/main.py` — IS a run-book command
    - `code/reporting/report_gen.py` — NOT invoked by the run-book
    - `code/run_aggregated_metrics.py` — NOT invoked by the run-book
    - `code/visualization/plots.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/aggregated_metrics.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/reml_failures.json` is declared but was NOT written. Scripts referencing it:
    - `code/reporting/report_gen.py` — NOT invoked by the run-book
    - `code/simulation/estimators.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/reml_failures.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
## Platform-owned paths written inside the project

A script in this project created `state/` inside the project directory. Those names belong to the platform, and a copy of them here is a SHADOW: the verifier resolves the paths a task names relative to this project, so it reads the shadow instead of canonical state and rejects work on the strength of a stale record.

Write your outputs under `data/`, `figures/`, `code/` and `paper/`. Do not record artifact hashes, run state or project status yourself — the platform owns `state/` and derives hashes at verification time. Delete the directories listed above and drop whatever step created them.
