# Execution failures — fix these before the analysis can run

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python code/main.py --mode static`
  - script usage: `main.py [-h] [--max-hours MAX_HOURS]`
  - argparse error: `main.py: error: unrecognized arguments: --mode static`
- run-book command: `python code/main.py --mode iterative`
  - script usage: `main.py [-h] [--max-hours MAX_HOURS]`
  - argparse error: `main.py: error: unrecognized arguments: --mode iterative`
- run-book command: `python code/main.py --mode stats`
  - script usage: `main.py [-h] [--max-hours MAX_HOURS]`
  - argparse error: `main.py: error: unrecognized arguments: --mode stats`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 6 command(s) failed: python code/data/download.py (rc=1); python code/data/curate.py (rc=1); python code/main.py --mode static (rc=2); 2 declared deliverable(s) absent: data/curated/synthetic_issues_meta.json; data/results/sensitivity_analysis.json

## Failing / missing run-book commands

- python code/data/download.py -> rc=1
--- T010: Robust Data Fetcher ---
Using config: {'paths': {'raw': '/home/runner/work/llmXive/llmXive/projects/PROJ-897-llmxive-follow-up-extending-swe-explore/raw', 'curated': '/home/runner/work/llmXive/llmXive/projects/PROJ-897-llmxive-follow-up-extending-swe-explore/curated', 'results': '/home/runner/work/llmXive/llmXive/projects/PROJ-897-llmxive-follow-up-extending-swe-explore/results', 'code': '/home/runner/work/llmXive/llmXive/projects/PROJ-897-llmxive-follow-up-extending-swe-explore/code', 'tests': '/home/runner/work/llmXive/llmXive/projects/PROJ-897-llmxive-follow-up-extending-swe-explore/tests', 'specs': '/home/runner/work/llmXive/llmXive/projects/specs'}, 'constants': {'HARD_INSTANCE_PERCENTILE': 0.2, 'COVERAGE_COLUMN_NAME': 'initial_coverage', 'SWEEP_SEED': 42, 'DEFAULT_TURN_LIMIT': 3, 'MIN_SYNTHETIC_ISSUES': 50, 'VALIDATION_SAMPLE_SIZE': 10, 'TIE_THRESHOLD': 0.5, 'MAX_RUNTIME_HOURS': 6.0, 'SWEEP_STABILITY_THRESHOLD': 0.05, 'MODEL_PRECISION': '-bit'}}

Task T010 Failed: The 'datasets' library is required. Please install it: pip install datasets

- python code/data/curate.py -> rc=1
llmxive-follow-up-extending-swe-explore/raw/swe_explore_with_gt.jsonl. Run T011 first.
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-897-llmxive-follow-up-extending-swe-explore/code/data/curate.py", line 243, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-897-llmxive-follow-up-extending-swe-explore/code/data/curate.py", line 226, in main
    synthetic_issues = generate_synthetic_issues()
                       ^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-897-llmxive-follow-up-extending-swe-explore/code/data/curate.py", line 165, in generate_synthetic_issues
    gt_data = load_derived_ground_truth()
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-897-llmxive-follow-up-extending-swe-explore/code/data/curate.py", line 38, in load_derived_ground_truth
    raise FileNotFoundError(f"Ground truth file not found at {path}. Run T011 first.")
FileNotFoundError: Ground truth file not found at /home/runner/work/llmXive/llmXive/projects/PROJ-897-llmxive-follow-up-extending-swe-explore/raw/swe_explore_with_gt.jsonl. Run T011 first.

- python code/main.py --mode static -> rc=2

usage: main.py [-h] [--max-hours MAX_HOURS]
main.py: error: unrecognized arguments: --mode static

- python code/main.py --mode iterative -> rc=2

usage: main.py [-h] [--max-hours MAX_HOURS]
main.py: error: unrecognized arguments: --mode iterative

- python code/main.py --mode stats -> rc=2

usage: main.py [-h] [--max-hours MAX_HOURS]
main.py: error: unrecognized arguments: --mode stats

- python -m pytest tests/ -> rc=2
e '/home/runner/work/llmXive/llmXive/projects/PROJ-897-llmxive-follow-up-extending-swe-explore/tests/unit/test_synthetic_generation.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/importlib/__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
tests/unit/test_synthetic_generation.py:10: in <module>
    from data.curate import (
E   ImportError: cannot import name 'compute_code_hash' from 'data.curate' (/home/runner/work/llmXive/llmXive/projects/PROJ-897-llmxive-follow-up-extending-swe-explore/code/data/curate.py)
=========================== short test summary info ============================
ERROR tests/integration/test_agent_loop.py
ERROR tests/unit/test_bonferroni.py
ERROR tests/unit/test_config.py
ERROR tests/unit/test_curate_filter.py
ERROR tests/unit/test_linting_config.py
ERROR tests/unit/test_stats.py
ERROR tests/unit/test_structure.py
ERROR tests/unit/test_synthetic_generation.py
!!!!!!!!!!!!!!!!!!! Interrupted: 8 errors during collection !!!!!!!!!!!!!!!!!!!!
============================== 8 errors in 1.02s ===============================



## Declared deliverables still missing

- data/curated/synthetic_issues_meta.json
- data/results/sensitivity_analysis.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/curated/synthetic_issues_meta.json` is declared but was NOT written. Scripts referencing it:
    - `code/data/generate_synthetic_metadata.py` — NOT invoked by the run-book
    - `code/data/mutate.py` — NOT invoked by the run-book
    - `code/validation_runner.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/curated/synthetic_issues_meta.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/sensitivity_analysis.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/sensitivity_check.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/sensitivity_analysis.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
## Platform-owned paths written inside the project

A script in this project created `state/` inside the project directory. Those names belong to the platform, and a copy of them here is a SHADOW: the verifier resolves the paths a task names relative to this project, so it reads the shadow instead of canonical state and rejects work on the strength of a stale record.

Write your outputs under `data/`, `figures/`, `code/` and `paper/`. Do not record artifact hashes, run state or project status yourself — the platform owns `state/` and derives hashes at verification time. Delete the directories listed above and drop whatever step created them.
