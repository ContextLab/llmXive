# Execution failures — fix these before the analysis can run

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python code/main.py --step ingest --dataset tng100`
  - script usage: `main.py [-h] [--config CONFIG]`
  - argparse error: `main.py: error: unrecognized arguments: --step ingest --dataset tng100`
- run-book command: `python code/main.py --step compute_shapes`
  - script usage: `main.py [-h] [--config CONFIG]`
  - argparse error: `main.py: error: unrecognized arguments: --step compute_shapes`
- run-book command: `python code/main.py --step null_control --iterations 10000`
  - script usage: `main.py [-h] [--config CONFIG]`
  - argparse error: `main.py: error: unrecognized arguments: --step null_control --iterations 10000`
- run-book command: `python code/main.py --step analyze --mass-match`
  - script usage: `main.py [-h] [--config CONFIG]`
  - argparse error: `main.py: error: unrecognized arguments: --step analyze --mass-match`
- run-book command: `python code/main.py --step sensitivity --thresholds "0.45,0.55,0.75,0.85"`
  - script usage: `main.py [-h] [--config CONFIG]`
  - argparse error: `main.py: error: unrecognized arguments: --step sensitivity --thresholds 0.45,0.55,0.75,0.85`
- run-book command: `python code/main.py --step report`
  - script usage: `main.py [-h] [--config CONFIG]`
  - argparse error: `main.py: error: unrecognized arguments: --step report`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 7 command(s) failed: python code/main.py --step ingest --dataset tng100 (rc=2); python code/main.py --step compute_shapes (rc=2); python code/main.py --step null_control --iterations 10000 (rc=2); 4 declared deliverable(s) absent: data/processed/alignment_angles.csv; data/processed/galaxy_properties.csv; data/processed/halo_shapes.csv

## Failing / missing run-book commands

- python code/main.py --step ingest --dataset tng100 -> rc=2

usage: main.py [-h] [--config CONFIG]
               [--stage {dry_run,ingestion,processing,statistics,alignment,report}]
main.py: error: unrecognized arguments: --step ingest --dataset tng100

- python code/main.py --step compute_shapes -> rc=2

usage: main.py [-h] [--config CONFIG]
               [--stage {dry_run,ingestion,processing,statistics,alignment,report}]
main.py: error: unrecognized arguments: --step compute_shapes

- python code/main.py --step null_control --iterations 10000 -> rc=2

usage: main.py [-h] [--config CONFIG]
               [--stage {dry_run,ingestion,processing,statistics,alignment,report}]
main.py: error: unrecognized arguments: --step null_control --iterations 10000

- python code/main.py --step analyze --mass-match -> rc=2

usage: main.py [-h] [--config CONFIG]
               [--stage {dry_run,ingestion,processing,statistics,alignment,report}]
main.py: error: unrecognized arguments: --step analyze --mass-match

- python code/main.py --step sensitivity --thresholds "0.45,0.55,0.75,0.85" -> rc=2

usage: main.py [-h] [--config CONFIG]
               [--stage {dry_run,ingestion,processing,statistics,alignment,report}]
main.py: error: unrecognized arguments: --step sensitivity --thresholds 0.45,0.55,0.75,0.85

- python code/main.py --step report -> rc=2

usage: main.py [-h] [--config CONFIG]
               [--stage {dry_run,ingestion,processing,statistics,alignment,report}]
main.py: error: unrecognized arguments: --step report

- python -m pytest code/tests/ -v -> rc=2
init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
<frozen importlib._bootstrap>:1204: in _gcd_import
    ???
<frozen importlib._bootstrap>:1176: in _find_and_load
    ???
<frozen importlib._bootstrap>:1147: in _find_and_load_unlocked
    ???
<frozen importlib._bootstrap>:690: in _load_unlocked
    ???
/home/runner/.cache/llmxive/base-env/py311-6f1866971868/_pytest/assertion/rewrite.py:178: in exec_module
    exec(co, module.__dict__)
code/tests/test_stats_regression.py:12: in <module>
    from analysis.stats import linear_regression_with_mass_control, run_statistical_tests
E   ImportError: cannot import name 'linear_regression_with_mass_control' from 'analysis.stats' (/home/runner/work/llmXive/llmXive/projects/PROJ-107-quantifying-the-effects-of-dark-matter-h/code/analysis/stats.py)
=========================== short test summary info ============================
ERROR code/tests/test_logging.py
ERROR code/tests/test_pipeline_runner.py
ERROR code/tests/test_stats_regression.py
!!!!!!!!!!!!!!!!!!! Interrupted: 3 errors during collection !!!!!!!!!!!!!!!!!!!!
============================== 3 errors in 1.31s ===============================



## Declared deliverables still missing

- data/processed/alignment_angles.csv
- data/processed/galaxy_properties.csv
- data/processed/halo_shapes.csv
- data/processed/statistical_results.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/alignment_angles.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/correlation_analysis.py` — NOT invoked by the run-book
    - `code/analysis/generate_alignment_report.py` — NOT invoked by the run-book
    - `code/analysis/integrate_alignment_report.py` — NOT invoked by the run-book
    - `code/analysis/metadata_utils.py` — NOT invoked by the run-book
    - `code/processing/alignment.py` — NOT invoked by the run-book
    - `code/tests/test_alignment_report.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/alignment_angles.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/galaxy_properties.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/correlation_analysis.py` — NOT invoked by the run-book
    - `code/analysis/generate_alignment_report.py` — NOT invoked by the run-book
    - `code/analysis/generate_statistical_results.py` — NOT invoked by the run-book
    - `code/analysis/run_statistical_analysis.py` — NOT invoked by the run-book
    - `code/ingestion/galaxy_loader.py` — NOT invoked by the run-book
    - `code/ingestion/tng_loader.py` — NOT invoked by the run-book
    - `code/processing/alignment.py` — NOT invoked by the run-book
    - `code/tests/test_alignment_report.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/galaxy_properties.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/halo_shapes.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/correlation_analysis.py` — NOT invoked by the run-book
    - `code/analysis/generate_alignment_report.py` — NOT invoked by the run-book
    - `code/analysis/generate_statistical_results.py` — NOT invoked by the run-book
    - `code/analysis/integrate_alignment_report.py` — NOT invoked by the run-book
    - `code/analysis/metadata_utils.py` — NOT invoked by the run-book
    - `code/analysis/run_statistical_analysis.py` — NOT invoked by the run-book
    - `code/processing/alignment.py` — NOT invoked by the run-book
    - `code/processing/pipeline_runner.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/halo_shapes.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/statistical_results.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/cross_dataset_comparison.py` — NOT invoked by the run-book
    - `code/analysis/generate_sensitivity_report.py` — NOT invoked by the run-book
    - `code/analysis/generate_statistical_results.py` — NOT invoked by the run-book
    - `code/analysis/integrate_alignment_report.py` — NOT invoked by the run-book
    - `code/analysis/log_hypothesis_rejections.py` — NOT invoked by the run-book
    - `code/analysis/metadata_utils.py` — NOT invoked by the run-book
    - `code/analysis/run_statistical_analysis.py` — NOT invoked by the run-book
    - `code/analysis/sensitivity.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/statistical_results.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
## Platform-owned paths written inside the project

A script in this project created `state/` inside the project directory. Those names belong to the platform, and a copy of them here is a SHADOW: the verifier resolves the paths a task names relative to this project, so it reads the shadow instead of canonical state and rejects work on the strength of a stale record.

Write your outputs under `data/`, `figures/`, `code/` and `paper/`. Do not record artifact hashes, run state or project status yourself — the platform owns `state/` and derives hashes at verification time. Delete the directories listed above and drop whatever step created them.
