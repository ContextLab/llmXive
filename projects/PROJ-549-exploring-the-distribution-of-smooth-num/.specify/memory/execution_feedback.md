# Execution failures — fix these before the analysis can run

## ⛔ HOLLOW RESULTS — the analysis RAN but MEASURED NOTHING

Every command exited 0 and the files were written — but the numbers in them are missing. A result that is `null`, `NaN`, an empty `[]`, a header-only CSV, or a column left blank in every row is NOT a measurement. Writing an empty result file is not 'done' — it is the same failure as fabrication, just quieter. You MUST:

1. Find WHY the value is missing. A `null`/`NaN` correlation almost always means the inputs were empty, misaligned, or the wrong column was read — fix the computation, do NOT paper over it with a default.
2. Verify you loaded the REAL dataset the spec names. If the study is about behavioural confidence ratings, a stand-in dataset (a bundled sklearn toy set, a random frame) is NOT the data — it will produce exactly these null/NaN results.
3. Make sure the key measure is actually POPULATED before you compute on it: if the column the study depends on is blank in every row, the extraction step is broken and that is the real bug.
4. NEVER self-certify. A `{"status": "PASS"}` written by your own code proves nothing; the numbers must be there.

- every produced artifact is gitignored (data/primes_1e9.csv) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python code/smoothness.py  --primes data/primes_1e9.csv  --output data/density_measurements.csv  --grid-file specs/001-exploring-the-distribution-of-smooth-numbers/grid_config.yaml`
  - script usage: `smoothness.py [-h] [--primes PRIMES] [--x X] [--h H] [--y Y]`
  - argparse error: `smoothness.py: error: unrecognized arguments: --output data/density_measurements.csv --grid-file specs/001-exploring-the-distribution-of-smooth-numbers/grid_config.yaml`
- run-book command: `python code/analysis.py  --input data/density_measurements.csv  --output data/model_fits.json  --plot-dir data/figures`
  - script usage: `analysis.py [-h] [--task {plan,spec,chi2}]`
  - argparse error: `analysis.py: error: unrecognized arguments: --input data/density_measurements.csv --output data/model_fits.json --plot-dir data/figures`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: every produced artifact is gitignored (data/primes_1e9.csv) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.; 2 command(s) failed: python code/smoothness.py  --primes data/primes_1e9.csv  --output data/density_measurements.csv  --grid-file specs/001-exploring-the-distribution-of-smooth-numbers/grid_config.yaml (rc=2); python code/analysis.py  --input data/density_measurements.csv  --output data/model_fits.json  --plot-dir data/figures (rc=2); 3 declared deliverable(s) absent: data/density_measurements_plan.csv; data/density_measurements_spec.csv; data/model_fits.json

## Failing / missing run-book commands

- python code/smoothness.py  --primes data/primes_1e9.csv  --output data/density_measurements.csv  --grid-file specs/001-exploring-the-distribution-of-smooth-numbers/grid_config.yaml -> rc=2
    usage: smoothness.py [-h] [--primes PRIMES] [--x X] [--h H] [--y Y]
smoothness.py: error: unrecognized arguments: --output data/density_measurements.csv --grid-file specs/001-exploring-the-distribution-of-smooth-numbers/grid_config.yaml
- python code/analysis.py  --input data/density_measurements.csv  --output data/model_fits.json  --plot-dir data/figures -> rc=2
    usage: analysis.py [-h] [--task {plan,spec,chi2}]
analysis.py: error: unrecognized arguments: --input data/density_measurements.csv --output data/model_fits.json --plot-dir data/figures

## Declared deliverables still missing

- data/density_measurements_plan.csv
- data/density_measurements_spec.csv
- data/model_fits.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/density_measurements_plan.csv` is declared but was NOT written. Scripts referencing it:
    - `code/main.py` — NOT invoked by the run-book
    - `code/verify_grid.py` — NOT invoked by the run-book
    - `code/viz.py` — NOT invoked by the run-book
    - `code/analysis.py` — IS a run-book command
  Make ONE of these WRITE `data/density_measurements_plan.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/density_measurements_spec.csv` is declared but was NOT written. Scripts referencing it:
    - `code/main.py` — NOT invoked by the run-book
    - `code/verify_grid.py` — NOT invoked by the run-book
    - `code/viz.py` — NOT invoked by the run-book
    - `code/analysis.py` — IS a run-book command
  Make ONE of these WRITE `data/density_measurements_spec.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/model_fits.json` is declared but was NOT written. Scripts referencing it:
    - `code/main.py` — NOT invoked by the run-book
    - `code/viz.py` — NOT invoked by the run-book
    - `code/generate_captions.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/model_fits.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
