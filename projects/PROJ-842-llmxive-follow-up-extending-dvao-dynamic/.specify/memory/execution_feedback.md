# Execution failures — fix these before the analysis can run

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python src/environment/synthetic_mdp.py  --n 50  --rho 0.0  --distribution gaussian  --seed 42`
  - script usage: `synthetic_mdp.py [-h] [--n-objectives N_OBJECTIVES]`
  - argparse error: `synthetic_mdp.py: error: ambiguous option: --n could match --n-objectives, --n-states, --n-actions, --noise-correlation`
- run-book command: `python src/environment/synthetic_mdp.py  --n 20 --rho 0.0 --distribution heavy_tailed --seed 999  --held-out`
  - script usage: `synthetic_mdp.py [-h] [--n-objectives N_OBJECTIVES]`
  - argparse error: `synthetic_mdp.py: error: ambiguous option: --n could match --n-objectives, --n-states, --n-actions, --noise-correlation`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 run-book script(s) missing (plan/impl path mismatch): python src/derivation/verify_symbolic.py; python src/analysis/statistics.py --sweep window_size  --values 0.01,0.05,0.1; 4 command(s) failed: python src/verification/verify_citations.py (rc=1); python src/environment/synthetic_mdp.py  --n 50  --rho 0.0  --distribution gaussian  --seed 42 (rc=2); python code/src/main.py --config configs/default.yaml (rc=1); 4 declared deliverable(s) absent: data/processed/construct_validity_results.json; data/processed/empirical_results.json; data/processed/noise_properties.json

## Failing / missing run-book commands

- python src/verification/verify_citations.py -> rc=1

2026-10-18 07:49:26,664 INFO __main__: Pinning random seeds for reproducibility (seed=42)
2026-10-18 07:49:26,664 INFO __main__: Running lightweight citation verification...
2026-10-18 07:49:26,664 ERROR __main__: Citation verification failed: 'docs/citations.md' missing or empty.

- python src/derivation/verify_symbolic.py -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-842-llmxive-follow-up-extending-dvao-dynamic/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-842-llmxive-follow-up-extending-dvao-dynamic/src/derivation/verify_symbolic.py': [Errno 2] No such file or directory

- python src/environment/synthetic_mdp.py  --n 50  --rho 0.0  --distribution gaussian  --seed 42 -> rc=2

usage: synthetic_mdp.py [-h] [--n-objectives N_OBJECTIVES]
                        [--n-states N_STATES] [--n-actions N_ACTIONS]
                        [--noise-correlation NOISE_CORRELATION]
                        [--distribution {linear,sparse,non_convex}]
                        [--seed SEED]
synthetic_mdp.py: error: ambiguous option: --n could match --n-objectives, --n-states, --n-actions, --noise-correlation

- python code/src/main.py --config configs/default.yaml -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-842-llmxive-follow-up-extending-dvao-dynamic/code/src/main.py", line 28, in <module>
    logging.FileHandler('logs/integration_suite.log'),
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/logging/__init__.py", line 1181, in __init__
    StreamHandler.__init__(self, self._open())
                                 ^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/logging/__init__.py", line 1213, in _open
    return open_func(self.baseFilename, self.mode,
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
FileNotFoundError: [Errno 2] No such file or directory: '/home/runner/work/llmXive/llmXive/projects/PROJ-842-llmxive-follow-up-extending-dvao-dynamic/logs/integration_suite.log'

- python src/analysis/statistics.py --sweep window_size  --values 0.01,0.05,0.1 -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-842-llmxive-follow-up-extending-dvao-dynamic/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-842-llmxive-follow-up-extending-dvao-dynamic/src/analysis/statistics.py': [Errno 2] No such file or directory

- python src/environment/synthetic_mdp.py  --n 20 --rho 0.0 --distribution heavy_tailed --seed 999  --held-out -> rc=2

usage: synthetic_mdp.py [-h] [--n-objectives N_OBJECTIVES]
                        [--n-states N_STATES] [--n-actions N_ACTIONS]
                        [--noise-correlation NOISE_CORRELATION]
                        [--distribution {linear,sparse,non_convex}]
                        [--seed SEED]
synthetic_mdp.py: error: ambiguous option: --n could match --n-objectives, --n-states, --n-actions, --noise-correlation


## Declared deliverables still missing

- data/processed/construct_validity_results.json
- data/processed/empirical_results.json
- data/processed/noise_properties.json
- data/processed/statistical_report.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/construct_validity_results.json` is declared but was NOT written. Scripts referencing it:
    - `code/scripts/validate_construct_validity.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/construct_validity_results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/empirical_results.json` is declared but was NOT written. Scripts referencing it:
    - `code/scripts/validate_construct_validity.py` — IS a run-book command
    - `code/scripts/verify_reproducibility.py` — NOT invoked by the run-book
    - `code/src/analysis/stats.py` — NOT invoked by the run-book
    - `code/src/environment/runner.py` — NOT invoked by the run-book
    - `code/src/main.py` — IS a run-book command
    - `src/analysis/stats.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/empirical_results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/noise_properties.json` is declared but was NOT written. Scripts referencing it:
    - `code/scripts/verify_reproducibility.py` — NOT invoked by the run-book
    - `code/src/environment/synthetic_mdp.py` — NOT invoked by the run-book
    - `code/tests/unit/test_mdp_noise_logging.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/noise_properties.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/statistical_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/scripts/verify_reproducibility.py` — NOT invoked by the run-book
    - `code/src/main.py` — IS a run-book command
    - `src/analysis/stats.py` — NOT invoked by the run-book
    - `scripts/run_full_suite.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/statistical_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
