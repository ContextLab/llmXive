# Execution failures — fix these before the analysis can run

## ⚠ DATA-UNAVAILABLE failure — switch to a REAL, REACHABLE data source

These commands failed because the external dataset is NOT reachable AS WRITTEN on the free CI runner: a Hugging Face dataset that was renamed (canonical names like `openai_humaneval` now require a `namespace/name`), had its loading script removed (`datasets` >= 3 dropped `trust_remote_code` script datasets), is gated, or needs network the runner lacks. RE-TRYING THE DOWNLOAD AS-IS WILL NEVER SUCCEED. Fix it with REAL data, in this order:

1. CORRECT the source: use the dataset's current canonical id (`namespace/name`), a public mirror, or a direct file URL, and stream / download only a SMALL REAL SAMPLE (the first N rows, one split, a few files). A verified real source may be injected below — use it.
2. If that exact dataset is truly unreachable, switch to a DIFFERENT but genuinely-public dataset that supports the SAME analysis/metric, and say so honestly in the README.
3. Do NOT substitute synthetic / fake / hand-built data for the real dataset. A result computed on invented data is NOT a real finding and is REJECTED by the deterministic fabrication gate — swapping in synthetic data is the single most common reason this loop never converges. The ONLY exception is a project whose OWN research question is about synthetic / simulated data (its idea says so).
4. If, after the above, NO real data can be obtained on the CI runner, do NOT fabricate a result: leave the run to FAIL so it escalates honestly (model-tier escalation / re-plan), rather than producing a fake finding.

- `python code/02_ingest_data.py`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 4 run-book script(s) missing (plan/impl path mismatch): python code/04_fit_pgls_base.py; python code/05_fit_pgls_interaction.py; python code/06_sensitivity_power.py   # LOOCV/jackknife + power simulation; 3 command(s) failed: python code/01_discover_data.py   # discovers Dryad DOIs; aborts on Data Availability Error (rc=1); python code/02_ingest_data.py (rc=1); python code/03_clean_merge.py (rc=1); 1 declared deliverable(s) absent: data/processed/merged_analysis.csv

## Failing / missing run-book commands

- python code/01_discover_data.py   # discovers Dryad DOIs; aborts on Data Availability Error -> rc=1
2026-10-24 15:10:10 - telomere_pipeline - INFO - Starting Dryad dataset discovery (T002)...
2026-10-24 15:10:10 - telomere_pipeline - INFO - Searching Dryad for query: 'telomere bird'
2026-10-24 15:10:11 - telomere_pipeline - ERROR - Dryad API returned no results.


- python code/02_ingest_data.py -> rc=1

Warning: No Dryad dataset IDs discovered; only AnAge will be downloaded.
Failed to download AnAge data: 404 Client Error: Not Found for url: https://genomics.senescence.info/species/animalia.csv

- python code/03_clean_merge.py -> rc=1

No raw telomere CSV files found. Exiting.

- python code/04_fit_pgls_base.py -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-055-investigating-the-impact-of-telomere-len/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-055-investigating-the-impact-of-telomere-len/code/04_fit_pgls_base.py': [Errno 2] No such file or directory

- python code/05_fit_pgls_interaction.py -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-055-investigating-the-impact-of-telomere-len/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-055-investigating-the-impact-of-telomere-len/code/05_fit_pgls_interaction.py': [Errno 2] No such file or directory

- python code/06_sensitivity_power.py   # LOOCV/jackknife + power simulation -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-055-investigating-the-impact-of-telomere-len/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-055-investigating-the-impact-of-telomere-len/code/06_sensitivity_power.py': [Errno 2] No such file or directory

- python code/07_visualize.py -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-055-investigating-the-impact-of-telomere-len/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-055-investigating-the-impact-of-telomere-len/code/07_visualize.py': [Errno 2] No such file or directory


## Declared deliverables still missing

- data/processed/merged_analysis.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/merged_analysis.csv` is declared but was NOT written. Scripts referencing it:
    - `code/03_clean_merge.py` — IS a run-book command
    - `code/04_model_pglS.py` — NOT invoked by the run-book
    - `code/05_visualize.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/merged_analysis.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
## Platform-owned paths written inside the project

A script in this project created `state/` inside the project directory. Those names belong to the platform, and a copy of them here is a SHADOW: the verifier resolves the paths a task names relative to this project, so it reads the shadow instead of canonical state and rejects work on the strength of a stale record.

Write your outputs under `data/`, `figures/`, `code/` and `paper/`. Do not record artifact hashes, run state or project status yourself — the platform owns `state/` and derives hashes at verification time. Delete the directories listed above and drop whatever step created them.
