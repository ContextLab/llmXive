# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/dft_runner.py: synthetic/fake INPUT data not authorized by the spec — “…er started.")          # Mock data for demonstration if no…”

## ⛔ HOLLOW RESULTS — the analysis RAN but MEASURED NOTHING

Every command exited 0 and the files were written — but the numbers in them are missing. A result that is `null`, `NaN`, an empty `[]`, a header-only CSV, or a column left blank in every row is NOT a measurement. Writing an empty result file is not 'done' — it is the same failure as fabrication, just quieter. You MUST:

1. Find WHY the value is missing. A `null`/`NaN` correlation almost always means the inputs were empty, misaligned, or the wrong column was read — fix the computation, do NOT paper over it with a default.
2. Verify you loaded the REAL dataset the spec names. If the study is about behavioural confidence ratings, a stand-in dataset (a bundled sklearn toy set, a random frame) is NOT the data — it will produce exactly these null/NaN results.
3. Make sure the key measure is actually POPULATED before you compute on it: if the column the study depends on is blank in every row, the extraction step is broken and that is the real bug.
4. NEVER self-certify. A `{"status": "PASS"}` written by your own code proves nothing; the numbers must be there.

- every produced artifact is gitignored (data/processed/defect_density_metrics.json, data/processed/download_summary.json) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 fabricated/simulated-result signal(s) — results are not real measurements: code/dft_runner.py: synthetic/fake INPUT data not authorized by the spec — “…er started.")          # Mock data for demonstration if no…”; every produced artifact is gitignored (data/processed/defect_density_metrics.json, data/processed/download_summary.json) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.; 3 command(s) failed: python code/validate.py (rc=2); python code/semi_empirical.py --all (rc=1); python code/analysis.py (rc=1); 3 declared deliverable(s) absent: data/processed/citation_status.json; data/processed/semi_empirical_results.json; data/raw/citations_cache.json

## Failing / missing run-book commands

- python code/validate.py -> rc=2
    usage: validate.py [-h] [--structures STRUCTURES] [--summary SUMMARY]
                   [--output OUTPUT]
validate.py: error: Either --structures or --summary must be provided
- python code/semi_empirical.py --all -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-045-investigating-the-relationship-between-d/code/semi_empirical.py", line 18, in <module>
    from pymatgen.analysis.bond_valence import BondValenceAnalyzer
ImportError: cannot import name 'BondValenceAnalyzer' from 'pymatgen.analysis.bond_valence' (/home/runner/work/llmXive/llmXive/projects/PROJ-045-investigating-the-relationship-between-d/code/.venv/lib/python3.11/site-packages/pymatgen/analysis/bond_valence.py)
- python code/analysis.py -> rc=1
    full analysis pipeline
2026-08-17 03:10:24 - __main__ - INFO - Loading processed data from data/processed/processed_data.json
2026-08-17 03:10:24 - __main__ - ERROR - Analysis failed: Data file not found: data/processed/processed_data.json

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-045-investigating-the-relationship-between-d/code/analysis.py", line 325, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-045-investigating-the-relationship-between-d/code/analysis.py", line 310, in main
    results = run_full_analysis(data_path, output_dir)
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-045-investigating-the-relationship-between-d/code/analysis.py", line 259, in run_full_analysis
    df = load_processed_data(data_path)
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-045-investigating-the-relationship-between-d/code/analysis.py", line 27, in load_processed_data
    raise FileNotFoundError(f"Data file not found: {data_path}")
FileNotFoundError: Data file not found: data/processed/processed_data.json

## Declared deliverables still missing

- data/processed/citation_status.json
- data/processed/semi_empirical_results.json
- data/raw/citations_cache.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/citation_status.json` is declared but was NOT written. Scripts referencing it:
    - `code/citation_validator.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/citation_status.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/semi_empirical_results.json` is declared but was NOT written. Scripts referencing it:
    - `code/semi_empirical.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/semi_empirical_results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/raw/citations_cache.json` is declared but was NOT written. Scripts referencing it:
    - `code/validate_citations.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/citations_cache.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.

## ⚠ CROSS-SCRIPT DATA CONTRACT — make the PRODUCER write what consumers read

One or more failures are DATA-SCHEMA mismatches BETWEEN scripts that exchange a file: a CONSUMER requires column/key names (or a file) that the PRODUCER did not write. The traceback you saw shows only the CONSUMER's EXPECTATION — never the producer's ACTUAL output — which is why this keeps failing. Below is the REAL schema each producer wrote on disk (read from the actual file) versus what the consumers require. Pick ONE canonical schema and make the **PRODUCER** write exactly the columns/keys the consumers read (preferred when one producer feeds several consumers), editing the producer IN PLACE. Do NOT fake or stub the data.

**This list is CUMULATIVE across every fix round** — keep satisfying a contract you already fixed while you fix the rest; do not drop a column merely because it is absent from this round's traceback.

### `data/processed/processed_data.json`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/analysis.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `data/processed/processed_data.json`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/analysis.py`.
