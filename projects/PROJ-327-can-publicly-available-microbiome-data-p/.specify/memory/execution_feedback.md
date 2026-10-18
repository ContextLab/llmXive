# Execution failures — fix these before the analysis can run

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python -m code.acquire   # downloads SRA parquet, validates checksum`
  - script usage: `acquire.py [-h] --url URL --out OUT`
  - argparse error: `acquire.py: error: the following arguments are required: --url, --out`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 8 command(s) failed: python -m code.acquire   # downloads SRA parquet, validates checksum (rc=2); python -m code.curate   # produces asv_table.csv (rc=1); python -m code.integrate   # produces merged_dataset.csv, runs missing‑data assessment (rc=1); 1 declared deliverable(s) absent: data/processed/asv_table.csv

## Failing / missing run-book commands

- python -m code.acquire   # downloads SRA parquet, validates checksum -> rc=2

usage: acquire.py [-h] --url URL --out OUT
acquire.py: error: the following arguments are required: --url, --out

- python -m code.curate   # produces asv_table.csv -> rc=1

Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-327-can-publicly-available-microbiome-data-p/code/curate.py", line 211, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-327-can-publicly-available-microbiome-data-p/code/curate.py", line 208, in main
    run_dada2(fastq_dir, output_path)
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-327-can-publicly-available-microbiome-data-p/code/curate.py", line 94, in run_dada2
    raise RuntimeError(
RuntimeError: DADA2 processing failed – aborting per FR-008

- python -m code.integrate   # produces merged_dataset.csv, runs missing‑data assessment -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-327-can-publicly-available-microbiome-data-p/bin/python: No module named code.integrate

- python -m code.model       # performs CV, reports R², saves figures -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-327-can-publicly-available-microbiome-data-p/bin/python: No module named code.model

- python -m code.permutation   # generates p‑value file (parallelised) -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-327-can-publicly-available-microbiome-data-p/bin/python: No module named code.permutation

- python -m code.sensitivity   # saves table of R² across configurations -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-327-can-publicly-available-microbiome-data-p/bin/python: No module named code.sensitivity

- python -m code.power         # computes effect‑size‑based power and writes summary -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-327-can-publicly-available-microbiome-data-p/bin/python: No module named code.power

- python -m code.report        # aggregates all results into `results/summary.md` -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-327-can-publicly-available-microbiome-data-p/bin/python: No module named code.report


## Declared deliverables still missing

- data/processed/asv_table.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/asv_table.csv` is declared but was NOT written. Scripts referencing it:
    - `code/curate.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/asv_table.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
