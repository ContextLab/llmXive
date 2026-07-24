# Execution failures — fix these before the analysis can run

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python code/main.py --mode full`
  - script usage: `main.py [-h] [--max-hours MAX_HOURS]`
  - argparse error: `main.py: error: unrecognized arguments: --mode full`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 7 command(s) failed: python code/data/download.py (rc=1); python code/data/derive_gt.py (rc=1); python code/data/curate.py (rc=1); 3 declared deliverable(s) absent: data/curated/synthetic_issues_meta.json; data/results/final_metrics.json; data/results/sweep_results.json

## Failing / missing run-book commands

- python code/data/download.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-897-llmxive-follow-up-extending-swe-explore/code/data/download.py", line 10, in <module>
    from datasets import load_dataset
ModuleNotFoundError: No module named 'datasets'
- python code/data/derive_gt.py -> rc=1
    Error: Input file not found: /home/runner/work/llmXive/llmXive/projects/PROJ-897-llmxive-follow-up-extending-swe-explore/data/data/raw/bench.final.public.jsonl
- python code/data/curate.py -> rc=1
    2026-07-24 09:08:05,533 - INFO - Starting T014b: Synthetic Issue Generation
2026-07-24 09:08:05,533 - INFO - Loading ground truth data...
2026-07-24 09:08:05,533 - ERROR - Ground truth file not found at /home/runner/work/llmXive/llmXive/projects/PROJ-897-llmxive-follow-up-extending-swe-explore/data/data/curated/ground_truth.jsonl. Run T013 first.
- python code/data/validate_hard.py -> rc=1
    Generating Validation Report...
Loading hard subset...

Error: Hard subset not found at /home/runner/work/llmXive/llmXive/projects/PROJ-897-llmxive-follow-up-extending-swe-explore/data/curated/hard_subset.jsonl. Ensure T014a has been executed.
Ensure T014a (curate.py) has been run to generate hard_subset.jsonl.
- python code/main.py --mode full -> rc=2
    usage: main.py [-h] [--max-hours MAX_HOURS]
main.py: error: unrecognized arguments: --mode full
- python code/analysis/stats.py --input data/results/metrics.csv -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-897-llmxive-follow-up-extending-swe-explore/code/analysis/stats.py", line 9, in <module>
    from lifelines import CoxPHFitter
ModuleNotFoundError: No module named 'lifelines'
- python code/analysis/plots.py --input data/results/stats_summary.json --output docs/figures/ -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-897-llmxive-follow-up-extending-swe-explore/code/analysis/plots.py", line 20, in <module>
    from analysis.stats import (
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-897-llmxive-follow-up-extending-swe-explore/code/analysis/stats.py", line 9, in <module>
    from lifelines import CoxPHFitter
ModuleNotFoundError: No module named 'lifelines'

## Declared deliverables still missing

- data/curated/synthetic_issues_meta.json
- data/results/final_metrics.json
- data/results/sweep_results.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/curated/synthetic_issues_meta.json` is declared but was NOT written. Scripts referencing it:
    - `code/validation_runner.py` — NOT invoked by the run-book
    - `code/data/curate.py` — IS a run-book command
  Make ONE of these WRITE `data/curated/synthetic_issues_meta.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/results/final_metrics.json` is declared but was NOT written. Scripts referencing it:
    - `code/validate_quickstart.py` — NOT invoked by the run-book
    - `code/analysis/report_generator.py` — NOT invoked by the run-book
    - `code/analysis/generate_final_metrics.py` — NOT invoked by the run-book
    - `code/analysis/plots.py` — IS a run-book command
    - `code/analysis/stats.py` — IS a run-book command
    - `code/analysis/run_hash_pipeline.py` — NOT invoked by the run-book
    - `code/analysis/hash_final_metrics.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/final_metrics.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/results/sweep_results.json` is declared but was NOT written. Scripts referencing it:
    - `code/agent/sweep_turns.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/sweep_results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.

## ⚠ CROSS-SCRIPT DATA CONTRACT — make the PRODUCER write what consumers read

One or more failures are DATA-SCHEMA mismatches BETWEEN scripts that exchange a file: a CONSUMER requires column/key names (or a file) that the PRODUCER did not write. The traceback you saw shows only the CONSUMER's EXPECTATION — never the producer's ACTUAL output — which is why this keeps failing. Below is the REAL schema each producer wrote on disk (read from the actual file) versus what the consumers require. Pick ONE canonical schema and make the **PRODUCER** write exactly the columns/keys the consumers read (preferred when one producer feeds several consumers), editing the producer IN PLACE. Do NOT fake or stub the data.

**This list is CUMULATIVE across every fix round** — keep satisfying a contract you already fixed while you fix the rest; do not drop a column merely because it is absent from this round's traceback.

### `home/runner/work/llmXive/llmXive/projects/PROJ-897-llmxive-follow-up-extending-swe-explore/data/data/curated/ground_truth.json`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/utils/validation.py`, `code/data/curate.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `home/runner/work/llmXive/llmXive/projects/PROJ-897-llmxive-follow-up-extending-swe-explore/data/data/curated/ground_truth.json`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/utils/validation.py`, `code/data/curate.py`.

### `home/runner/work/llmXive/llmXive/projects/PROJ-897-llmxive-follow-up-extending-swe-explore/data/data/raw/bench.final.public.json`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/analysis/report_generator.py`, `code/data/download.py`, `code/data/derive_gt.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `home/runner/work/llmXive/llmXive/projects/PROJ-897-llmxive-follow-up-extending-swe-explore/data/data/raw/bench.final.public.json`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/analysis/report_generator.py`, `code/data/derive_gt.py`.
