# Execution failures — fix these before the analysis can run

## ⛔ HOLLOW RESULTS — the analysis RAN but MEASURED NOTHING

Every command exited 0 and the files were written — but the numbers in them are missing. A result that is `null`, `NaN`, an empty `[]`, a header-only CSV, or a column left blank in every row is NOT a measurement. Writing an empty result file is not 'done' — it is the same failure as fabrication, just quieter. You MUST:

1. Find WHY the value is missing. A `null`/`NaN` correlation almost always means the inputs were empty, misaligned, or the wrong column was read — fix the computation, do NOT paper over it with a default.
2. Verify you loaded the REAL dataset the spec names. If the study is about behavioural confidence ratings, a stand-in dataset (a bundled sklearn toy set, a random frame) is NOT the data — it will produce exactly these null/NaN results.
3. Make sure the key measure is actually POPULATED before you compute on it: if the column the study depends on is blank in every row, the extraction step is broken and that is the real bug.
4. NEVER self-certify. A `{"status": "PASS"}` written by your own code proves nothing; the numbers must be there.

- every produced artifact is gitignored (data/processed/asv_table.csv) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python -m code.acquire   # downloads SRA parquet, validates checksum`
  - script usage: `acquire.py [-h] {metabolomics,sra} ...`
  - argparse error: `acquire.py: error: argument command: invalid choice: '#' (choose from 'metabolomics', 'sra')`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: every produced artifact is gitignored (data/processed/asv_table.csv) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.; 7 command(s) failed: python -m code.acquire   # downloads SRA parquet, validates checksum (rc=2); python -m code.integrate   # produces merged_dataset.csv, runs missing‑data assessment (rc=1); python -m code.model       # performs CV, reports R², saves figures (rc=1)

## Failing / missing run-book commands

- python -m code.acquire   # downloads SRA parquet, validates checksum -> rc=2

usage: acquire.py [-h] {metabolomics,sra} ...
acquire.py: error: argument command: invalid choice: '#' (choose from 'metabolomics', 'sra')

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

