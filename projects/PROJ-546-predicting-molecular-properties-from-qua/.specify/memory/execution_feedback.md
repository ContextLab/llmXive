# Execution failures — fix these before the analysis can run

## ⚠ REGRESSIONS — your last fix BROKE these (they passed before)

These commands were NOT failing in the previous round and ARE failing now — your last edit broke previously-working code. REVERT or correct whatever change broke each one BEFORE touching anything else; do not trade one passing script for another (that oscillation is what burns the fix-round budget toward escalation):

- `python code/main.py fetch`
- `python code/main.py optimize`
- `python code/main.py run`
- `python code/main.py train`

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python code/main.py run`
  - script usage: `main.py [-h] [--skip-fetch]`
  - argparse error: `main.py: error: unrecognized arguments: run`
- run-book command: `python code/main.py fetch`
  - script usage: `main.py [-h] [--skip-fetch]`
  - argparse error: `main.py: error: unrecognized arguments: fetch`
- run-book command: `python code/main.py optimize`
  - script usage: `main.py [-h] [--skip-fetch]`
  - argparse error: `main.py: error: unrecognized arguments: optimize`
- run-book command: `python code/main.py train`
  - script usage: `main.py [-h] [--skip-fetch]`
  - argparse error: `main.py: error: unrecognized arguments: train`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 4 command(s) failed: python code/main.py run (rc=2); python code/main.py fetch (rc=2); python code/main.py optimize (rc=2); 4 declared deliverable(s) absent: data/confounds.csv; data/descriptors_dft.csv; data/descriptors_semi.csv

## Failing / missing run-book commands

- python code/main.py run -> rc=2
    usage: main.py [-h] [--skip-fetch]
main.py: error: unrecognized arguments: run
- python code/main.py fetch -> rc=2
    usage: main.py [-h] [--skip-fetch]
main.py: error: unrecognized arguments: fetch
- python code/main.py optimize -> rc=2
    usage: main.py [-h] [--skip-fetch]
main.py: error: unrecognized arguments: optimize
- python code/main.py train -> rc=2
    usage: main.py [-h] [--skip-fetch]
main.py: error: unrecognized arguments: train

## Declared deliverables still missing

- data/confounds.csv
- data/descriptors_dft.csv
- data/descriptors_semi.csv
- data/raw/barrier_dataset.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/confounds.csv` is declared but was NOT written. Scripts referencing it:
    - `code/generate_checksums.py` — IS a run-book command
    - `code/confounds.py` — NOT invoked by the run-book
    - `code/confound_analysis.py` — NOT invoked by the run-book
    - `code/dft_calculator.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/confounds.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/descriptors_dft.csv` is declared but was NOT written. Scripts referencing it:
    - `code/track_compute_resources.py` — NOT invoked by the run-book
    - `code/generate_checksums.py` — IS a run-book command
    - `code/validate_subset_alignment.py` — NOT invoked by the run-book
    - `code/evaluate_models.py` — NOT invoked by the run-book
    - `code/train_models.py` — NOT invoked by the run-book
    - `code/missing_dof_analysis.py` — NOT invoked by the run-book
    - `code/evaluators/missing_dof_analyzer.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/descriptors_dft.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/descriptors_semi.csv` is declared but was NOT written. Scripts referencing it:
    - `code/track_compute_resources.py` — NOT invoked by the run-book
    - `code/generate_checksums.py` — IS a run-book command
    - `code/descriptor_pipeline.py` — NOT invoked by the run-book
    - `code/physical_validator.py` — NOT invoked by the run-book
    - `code/validate_subset_alignment.py` — NOT invoked by the run-book
    - `code/sensitivity_analysis.py` — NOT invoked by the run-book
    - `code/evaluate_models.py` — NOT invoked by the run-book
    - `code/noise_injection.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/descriptors_semi.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/raw/barrier_dataset.csv` is declared but was NOT written. Scripts referencing it:
    - `code/confounds.py` — NOT invoked by the run-book
    - `code/descriptor_pipeline.py` — NOT invoked by the run-book
    - `code/generate_summary_report.py` — NOT invoked by the run-book
    - `code/fetch_data.py` — NOT invoked by the run-book
    - `code/dft_calculator.py` — NOT invoked by the run-book
    - `code/train_models.py` — NOT invoked by the run-book
    - `code/missing_dof_analysis.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/barrier_dataset.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.

## ⚠ CROSS-SCRIPT DATA CONTRACT — make the PRODUCER write what consumers read

One or more failures are DATA-SCHEMA mismatches BETWEEN scripts that exchange a file: a CONSUMER requires column/key names (or a file) that the PRODUCER did not write. The traceback you saw shows only the CONSUMER's EXPECTATION — never the producer's ACTUAL output — which is why this keeps failing. Below is the REAL schema each producer wrote on disk (read from the actual file) versus what the consumers require. Pick ONE canonical schema and make the **PRODUCER** write exactly the columns/keys the consumers read (preferred when one producer feeds several consumers), editing the producer IN PLACE. Do NOT fake or stub the data.

**This list is CUMULATIVE across every fix round** — keep satisfying a contract you already fixed while you fix the rest; do not drop a column merely because it is absent from this round's traceback.

### `data/raw/barrier_dataset.csv`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/confounds.py`, `code/descriptor_pipeline.py`, `code/generate_summary_report.py`, `code/fetch_data.py`, `code/dft_calculator.py`, `code/train_models.py`, `code/missing_dof_analysis.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `data/raw/barrier_dataset.csv`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/confounds.py`, `code/descriptor_pipeline.py`, `code/generate_summary_report.py`, `code/fetch_data.py`, `code/dft_calculator.py`, `code/train_models.py`, `code/missing_dof_analysis.py`.

### `home/runner/work/llmXive/llmXive/projects/PROJ-546-predicting-molecular-properties-from-qua/code/models/rf_semi.pkl`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/sensitivity_analysis.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `home/runner/work/llmXive/llmXive/projects/PROJ-546-predicting-molecular-properties-from-qua/code/models/rf_semi.pkl`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/sensitivity_analysis.py`.
