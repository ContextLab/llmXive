# Execution failures — fix these before the analysis can run

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python code/main.py --step ingestion --sample-ratio 0.1`
  - script usage: `main.py [-h]`
  - argparse error: `main.py: error: unrecognized arguments: --step ingestion`
- run-book command: `python code/main.py --step stats --alpha 0.01`
  - script usage: `main.py [-h]`
  - argparse error: `main.py: error: unrecognized arguments: --step stats`
- run-book command: `python code/main.py --step sensitivity --thresholds 0.01,0.05,0.10`
  - script usage: `main.py [-h]`
  - argparse error: `main.py: error: unrecognized arguments: --step sensitivity`
- run-book command: `python code/main.py --step regression`
  - script usage: `main.py [-h]`
  - argparse error: `main.py: error: unrecognized arguments: --step regression`
- run-book command: `python code/main.py --full-run --sample-ratio 0.1`
  - script usage: `main.py [-h]`
  - argparse error: `main.py: error: unrecognized arguments: --full-run`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 5 command(s) failed: python code/main.py --step ingestion --sample-ratio 0.1 (rc=2); python code/main.py --step stats --alpha 0.01 (rc=2); python code/main.py --step sensitivity --thresholds 0.01,0.05,0.10 (rc=2); 1 declared deliverable(s) absent: data/derived/energy_samples.csv

## Failing / missing run-book commands

- python code/main.py --step ingestion --sample-ratio 0.1 -> rc=2
    usage: main.py [-h]
               [--stage {all,checksum_raw,hash_artifacts,ingest,stats,sensitivity,regression}]
               [--config CONFIG] [--verbose] [--sample-ratio SAMPLE_RATIO]
               [--alpha ALPHA] [--thresholds THRESHOLDS]
main.py: error: unrecognized arguments: --step ingestion
- python code/main.py --step stats --alpha 0.01 -> rc=2
    usage: main.py [-h]
               [--stage {all,checksum_raw,hash_artifacts,ingest,stats,sensitivity,regression}]
               [--config CONFIG] [--verbose] [--sample-ratio SAMPLE_RATIO]
               [--alpha ALPHA] [--thresholds THRESHOLDS]
main.py: error: unrecognized arguments: --step stats
- python code/main.py --step sensitivity --thresholds 0.01,0.05,0.10 -> rc=2
    usage: main.py [-h]
               [--stage {all,checksum_raw,hash_artifacts,ingest,stats,sensitivity,regression}]
               [--config CONFIG] [--verbose] [--sample-ratio SAMPLE_RATIO]
               [--alpha ALPHA] [--thresholds THRESHOLDS]
main.py: error: unrecognized arguments: --step sensitivity
- python code/main.py --step regression -> rc=2
    usage: main.py [-h]
               [--stage {all,checksum_raw,hash_artifacts,ingest,stats,sensitivity,regression}]
               [--config CONFIG] [--verbose] [--sample-ratio SAMPLE_RATIO]
               [--alpha ALPHA] [--thresholds THRESHOLDS]
main.py: error: unrecognized arguments: --step regression
- python code/main.py --full-run --sample-ratio 0.1 -> rc=2
    usage: main.py [-h]
               [--stage {all,checksum_raw,hash_artifacts,ingest,stats,sensitivity,regression}]
               [--config CONFIG] [--verbose] [--sample-ratio SAMPLE_RATIO]
               [--alpha ALPHA] [--thresholds THRESHOLDS]
main.py: error: unrecognized arguments: --full-run

## Declared deliverables still missing

- data/derived/energy_samples.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/derived/energy_samples.csv` is declared but was NOT written. Scripts referencing it:
    - `code/main.py` — IS a run-book command
    - `code/stats.py` — NOT invoked by the run-book
    - `code/ingestion.py` — NOT invoked by the run-book
    - `code/generate_statistical_results.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/derived/energy_samples.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
