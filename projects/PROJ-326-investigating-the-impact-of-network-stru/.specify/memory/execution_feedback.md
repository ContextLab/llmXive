# Execution failures — fix these before the analysis can run

## ⚠ REGRESSIONS — your last fix BROKE these (they passed before)

These commands were NOT failing in the previous round and ARE failing now — your last edit broke previously-working code. REVERT or correct whatever change broke each one BEFORE touching anything else; do not trade one passing script for another (that oscillation is what burns the fix-round budget toward escalation):

- `python code/main.py --phase analyze --config code/config.yaml`
- `python code/main.py --phase generate --config code/config.yaml`
- `python code/main.py --phase sensitivity --config code/config.yaml`
- `python code/main.py --phase simulate --config code/config.yaml`

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python code/main.py --phase generate --config code/config.yaml`
  - script usage: `main.py [-h] [--config CONFIG] [--output OUTPUT]`
  - argparse error: `main.py: error: unrecognized arguments: --phase generate`
- run-book command: `python code/main.py --phase simulate --config code/config.yaml`
  - script usage: `main.py [-h] [--config CONFIG] [--output OUTPUT]`
  - argparse error: `main.py: error: unrecognized arguments: --phase simulate`
- run-book command: `python code/main.py --phase sensitivity --config code/config.yaml`
  - script usage: `main.py [-h] [--config CONFIG] [--output OUTPUT]`
  - argparse error: `main.py: error: unrecognized arguments: --phase sensitivity`
- run-book command: `python code/main.py --phase analyze --config code/config.yaml`
  - script usage: `main.py [-h] [--config CONFIG] [--output OUTPUT]`
  - argparse error: `main.py: error: unrecognized arguments: --phase analyze`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 4 command(s) failed: python code/main.py --phase generate --config code/config.yaml (rc=2); python code/main.py --phase simulate --config code/config.yaml (rc=2); python code/main.py --phase sensitivity --config code/config.yaml (rc=2); 5 declared deliverable(s) absent: data/analysis/aggregated_results.json; data/analysis/final_results.json; data/analysis/sensitivity_sweep.json

## Failing / missing run-book commands

- python code/main.py --phase generate --config code/config.yaml -> rc=2
    2026-07-25 08:09:53,637 - matplotlib.font_manager - INFO - Failed to extract font properties from /usr/share/fonts/truetype/noto/NotoColorEmoji.ttf: Non-scalable fonts are not supported
2026-07-25 08:09:53,755 - matplotlib.font_manager - INFO - generated new fontManager
usage: main.py [-h] [--config CONFIG] [--output OUTPUT]
main.py: error: unrecognized arguments: --phase generate
- python code/main.py --phase simulate --config code/config.yaml -> rc=2
    usage: main.py [-h] [--config CONFIG] [--output OUTPUT]
main.py: error: unrecognized arguments: --phase simulate
- python code/main.py --phase sensitivity --config code/config.yaml -> rc=2
    usage: main.py [-h] [--config CONFIG] [--output OUTPUT]
main.py: error: unrecognized arguments: --phase sensitivity
- python code/main.py --phase analyze --config code/config.yaml -> rc=2
    usage: main.py [-h] [--config CONFIG] [--output OUTPUT]
main.py: error: unrecognized arguments: --phase analyze

## Declared deliverables still missing

- data/analysis/aggregated_results.json
- data/analysis/final_results.json
- data/analysis/sensitivity_sweep.json
- data/analysis/simulation_results.json
- data/run_log.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/analysis/aggregated_results.json` is declared but was NOT written. Scripts referencing it:
    - `code/src/analysis/aggregate_results.py` — NOT invoked by the run-book
    - `code/src/analysis/run_analysis.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/analysis/aggregated_results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/analysis/final_results.json` is declared but was NOT written. Scripts referencing it:
    - `code/tests/test_run_analysis.py` — NOT invoked by the run-book
    - `code/scripts/run_final_serialization.py` — NOT invoked by the run-book
    - `code/scripts/run_analysis.py` — NOT invoked by the run-book
    - `code/src/analysis/serialize_final.py` — NOT invoked by the run-book
    - `code/src/analysis/run_analysis.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/analysis/final_results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/analysis/sensitivity_sweep.json` is declared but was NOT written. Scripts referencing it:
    - `code/tests/test_run_analysis.py` — NOT invoked by the run-book
    - `code/tests/test_sensitivity.py` — NOT invoked by the run-book
    - `code/tests/test_validation.py` — NOT invoked by the run-book
    - `code/tests/test_analysis.py` — NOT invoked by the run-book
    - `code/scripts/run_sensitivity_sweep.py` — NOT invoked by the run-book
    - `code/src/analysis/report.py` — NOT invoked by the run-book
    - `code/src/analysis/sensitivity.py` — NOT invoked by the run-book
    - `code/src/analysis/serialize_final.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/analysis/sensitivity_sweep.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/analysis/simulation_results.json` is declared but was NOT written. Scripts referencing it:
    - `code/tests/test_run_analysis.py` — NOT invoked by the run-book
    - `code/tests/test_sensitivity.py` — NOT invoked by the run-book
    - `code/tests/test_validation.py` — NOT invoked by the run-book
    - `code/tests/test_analysis.py` — NOT invoked by the run-book
    - `code/tests/test_serialization.py` — NOT invoked by the run-book
    - `code/scripts/run_sensitivity_sweep.py` — NOT invoked by the run-book
    - `code/src/analysis/aggregate_results.py` — NOT invoked by the run-book
    - `code/src/analysis/power.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/analysis/simulation_results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/run_log.json` is declared but was NOT written. Scripts referencing it:
    - `code/main.py` — IS a run-book command
    - `code/tests/test_integration.py` — NOT invoked by the run-book
    - `code/tests/test_logging.py` — NOT invoked by the run-book
    - `code/tests/test_reproducibility.py` — NOT invoked by the run-book
    - `code/tests/test_generators.py` — NOT invoked by the run-book
    - `code/scripts/test_logging_demo.py` — NOT invoked by the run-book
    - `code/scripts/inject_seed.py` — NOT invoked by the run-book
    - `code/scripts/verify_config_reproducibility.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/run_log.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
