# Execution failures — fix these before the analysis can run

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python code/main.py --permutations [variable] --threshold 0.3 --sweep`
  - script usage: `main.py [-h] [--permutations PERMUTATIONS] [--threshold THRESHOLD]`
  - argparse error: `main.py: error: argument --permutations: invalid int value: '[variable]'`

## ⚠ DATA-UNAVAILABLE failure — switch to a REAL, REACHABLE data source

These commands failed because the external dataset is NOT reachable AS WRITTEN on the free CI runner: a Hugging Face dataset that was renamed (canonical names like `openai_humaneval` now require a `namespace/name`), had its loading script removed (`datasets` >= 3 dropped `trust_remote_code` script datasets), is gated, or needs network the runner lacks. RE-TRYING THE DOWNLOAD AS-IS WILL NEVER SUCCEED. Fix it with REAL data, in this order:

1. CORRECT the source: use the dataset's current canonical id (`namespace/name`), a public mirror, or a direct file URL, and stream / download only a SMALL REAL SAMPLE (the first N rows, one split, a few files). A verified real source may be injected below — use it.
2. If that exact dataset is truly unreachable, switch to a DIFFERENT but genuinely-public dataset that supports the SAME analysis/metric, and say so honestly in the README.
3. Do NOT substitute synthetic / fake / hand-built data for the real dataset. A result computed on invented data is NOT a real finding and is REJECTED by the deterministic fabrication gate — swapping in synthetic data is the single most common reason this loop never converges. The ONLY exception is a project whose OWN research question is about synthetic / simulated data (its idea says so).
4. If, after the above, NO real data can be obtained on the CI runner, do NOT fabricate a result: leave the run to FAIL so it escalates honestly (model-tier escalation / re-plan), rather than producing a fake finding.

- `python code/loaders.py --output data/processed/`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 command(s) failed: python code/loaders.py --output data/processed/ (rc=1); python code/main.py --permutations [variable] --threshold 0.3 --sweep (rc=2); 1 declared deliverable(s) absent: data/raw/checksums.json

## Failing / missing run-book commands

- python code/loaders.py --output data/processed/ -> rc=1
    .edu/ml/machine-learning-databases/isolet/isolet1_train_data
2026-07-19 12:28:10,664 - loaders - ERROR - Failed to download isolet1_train_data: 404 Client Error: Not Found for url: https://archive.ics.uci.edu/ml/machine-learning-databases/isolet/isolet1_train_data
2026-07-19 12:28:10,664 - loaders - ERROR - Failed to load fallback dataset isolet: 404 Client Error: Not Found for url: https://archive.ics.uci.edu/ml/machine-learning-databases/isolet/isolet1_train_data
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-297-assessing-statistical-significance-of-ob/code/loaders.py", line 365, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-297-assessing-statistical-significance-of-ob/code/loaders.py", line 352, in main
    datasets = load_all_datasets(min_datasets=args.min_datasets)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-297-assessing-statistical-significance-of-ob/code/loaders.py", line 325, in load_all_datasets
    raise ValueError(
ValueError: Failed to load minimum required datasets. Loaded 0 datasets, need at least 3. Available: []
- python code/main.py --permutations [variable] --threshold 0.3 --sweep -> rc=2
    usage: main.py [-h] [--permutations PERMUTATIONS] [--threshold THRESHOLD]
               [--sweep] [--output OUTPUT]
main.py: error: argument --permutations: invalid int value: '[variable]'

## Declared deliverables still missing

- data/raw/checksums.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/raw/checksums.json` is declared but was NOT written. Scripts referencing it:
    - `code/main.py` — IS a run-book command
    - `code/loaders.py` — IS a run-book command
  Make ONE of these WRITE `data/raw/checksums.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
