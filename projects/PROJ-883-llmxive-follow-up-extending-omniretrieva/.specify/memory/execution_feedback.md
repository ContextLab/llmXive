# Execution failures — fix these before the analysis can run

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python code/query_generator.py --levels 1 2 3 4 --count [sufficient sample size] --seed 42`
  - script usage: `query_generator.py [-h] --levels LEVELS [LEVELS ...] [--count COUNT]`
  - argparse error: `query_generator.py: error: unrecognized arguments: sample size]`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 command(s) failed: python code/query_generator.py --levels 1 2 3 4 --count [sufficient sample size] --seed 42 (rc=2); python -m code.main (rc=1)

## Failing / missing run-book commands

- python code/query_generator.py --levels 1 2 3 4 --count [sufficient sample size] --seed 42 -> rc=2

usage: query_generator.py [-h] --levels LEVELS [LEVELS ...] [--count COUNT]
                          [--seed SEED] [--output OUTPUT]
query_generator.py: error: unrecognized arguments: sample size]

- python -m code.main -> rc=1

2026-10-14 06:09:31,420 INFO __main__: Verifying required datasets (real fetch)...
2026-10-14 06:09:31,420 INFO utils.data_fetcher: Dataset file /home/runner/work/llmXive/llmXive/projects/PROJ-883-llmxive-follow-up-extending-omniretrieva/data/raw/microsoft_ms_marco_v1.1_train.jsonl missing – fetching.
2026-10-14 06:09:31,649 ERROR utils.data_fetcher: Failed to import datasets library: pyarrow requires NumPy 2.0 or newer, found 1.26.4
2026-10-14 06:09:31,649 WARNING __main__: Skipping real dataset verification due to import error or fetch failure: Unable to import datasets library and synthetic fallback is disabled.
2026-10-14 06:09:31,649 INFO __main__: Proceeding with synthetic execution – the benchmark uses only synthetic queries and lightweight executors.
2026-10-14 06:09:31,649 ERROR __main__: CPU throttling could not be applied: Failed to create cgroup directory /sys/fs/cgroup/llmxive_throttle_2575: [Errno 13] Permission denied: '/sys/fs/cgroup/llmxive_throttle_2575'

