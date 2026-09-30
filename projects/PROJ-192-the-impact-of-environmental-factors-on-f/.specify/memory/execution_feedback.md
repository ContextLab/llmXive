# Execution failures — fix these before the analysis can run

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python -m src.cli.main --run-full`
  - script usage: `main.py [-h] [--mode {validation,research}] [--stratify-by STRATIFY_BY]`
  - argparse error: `main.py: error: unrecognized arguments: --run-full`
- run-book command: `python -m src.cli.main --run-full --stratify-by biome --sweep-thresholds`
  - script usage: `main.py [-h] [--mode {validation,research}] [--stratify-by STRATIFY_BY]`
  - argparse error: `main.py: error: unrecognized arguments: --run-full`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 3 command(s) failed: python code/utils/checksums.py --verify (rc=2); python -m src.cli.main --run-full (rc=2); python -m src.cli.main --run-full --stratify-by biome --sweep-thresholds (rc=2); 1 declared deliverable(s) absent: data/metadata/harmonized_matrix.csv

## Failing / missing run-book commands

- python code/utils/checksums.py --verify -> rc=2
    usage: checksums.py [-h] [--verify] [--file FILE] [--checksum CHECKSUM]
                    {verify,calculate,generate} ...
checksums.py: error: --verify requires --file and --checksum
- python -m src.cli.main --run-full -> rc=2
    usage: main.py [-h] [--mode {validation,research}] [--stratify-by STRATIFY_BY]
               [--sweep-thresholds]
main.py: error: unrecognized arguments: --run-full
- python -m src.cli.main --run-full --stratify-by biome --sweep-thresholds -> rc=2
    usage: main.py [-h] [--mode {validation,research}] [--stratify-by STRATIFY_BY]
               [--sweep-thresholds]
main.py: error: unrecognized arguments: --run-full

## Declared deliverables still missing

- data/metadata/harmonized_matrix.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/metadata/harmonized_matrix.csv` is declared but was NOT written. Scripts referencing it:
    - `code/tests/integration/test_stratification.py` — NOT invoked by the run-book
    - `code/tests/unit/test_ingest_t013d.py` — NOT invoked by the run-book
    - `code/src/pipelines/ingest.py` — NOT invoked by the run-book
    - `code/src/pipelines/preprocess.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/metadata/harmonized_matrix.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
