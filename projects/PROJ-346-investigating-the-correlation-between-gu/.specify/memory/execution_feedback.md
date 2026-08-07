# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/03_correlation.py: self-declared fabricated metric — “…ta Gap).")         # Create a placeholder result indicating N/A to satisfy the…”
- code/08_literature_synthesis.py: self-declared fabricated metric — “…t instructions, we should not fake results.         # We will write an…”
- code/08_literature_synthesis.py: synthetic/fake INPUT data not authorized by the spec — “…:             # Create a synthetic evidence record based on the abstract…”

## ⛔ HOLLOW RESULTS — the analysis RAN but MEASURED NOTHING

Every command exited 0 and the files were written — but the numbers in them are missing. A result that is `null`, `NaN`, an empty `[]`, a header-only CSV, or a column left blank in every row is NOT a measurement. Writing an empty result file is not 'done' — it is the same failure as fabrication, just quieter. You MUST:

1. Find WHY the value is missing. A `null`/`NaN` correlation almost always means the inputs were empty, misaligned, or the wrong column was read — fix the computation, do NOT paper over it with a default.
2. Verify you loaded the REAL dataset the spec names. If the study is about behavioural confidence ratings, a stand-in dataset (a bundled sklearn toy set, a random frame) is NOT the data — it will produce exactly these null/NaN results.
3. Make sure the key measure is actually POPULATED before you compute on it: if the column the study depends on is blank in every row, the extraction step is broken and that is the real bug.
4. NEVER self-certify. A `{"status": "PASS"}` written by your own code proves nothing; the numbers must be there.

- every produced artifact is gitignored (data/processed/correlation_results.json) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.

## ⚠ REGRESSIONS — your last fix BROKE these (they passed before)

These commands were NOT failing in the previous round and ARE failing now — your last edit broke previously-working code. REVERT or correct whatever change broke each one BEFORE touching anything else; do not trade one passing script for another (that oscillation is what burns the fix-round budget toward escalation):

- `python code/07_gap_report.py`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 3 fabricated/simulated-result signal(s) — results are not real measurements: code/03_correlation.py: self-declared fabricated metric — “…ta Gap).")         # Create a placeholder result indicating N/A to satisfy the…”; code/08_literature_synthesis.py: self-declared fabricated metric — “…t instructions, we should not fake results.         # We will write an…”; code/08_literature_synthesis.py: synthetic/fake INPUT data not authorized by the spec — “…:             # Create a synthetic evidence record based on the abstract…”; every produced artifact is gitignored (data/processed/correlation_results.json) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.; 2 command(s) failed: python code/02_preprocess.py (rc=1); python code/07_gap_report.py (rc=1); 1 declared deliverable(s) absent: data/raw/literature_metadata.json

## Failing / missing run-book commands

- python code/02_preprocess.py -> rc=1
    Raw data files missing. Cannot perform preprocessing.
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-346-investigating-the-correlation-between-gu/code/02_preprocess.py", line 130, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-346-investigating-the-correlation-between-gu/code/02_preprocess.py", line 106, in main
    raise FileNotFoundError("Raw data files missing.")
FileNotFoundError: Raw data files missing.
- python code/07_gap_report.py -> rc=1
    Generating Data Gap Report (FR-008 fallback)...
2026-08-07 20:47:28,852 - gap_report - INFO - Writing gap report to /home/runner/work/llmXive/llmXive/projects/PROJ-346-investigating-the-correlation-between-gu/data/processed/data_gap_report.json

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-346-investigating-the-correlation-between-gu/code/07_gap_report.py", line 81, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-346-investigating-the-correlation-between-gu/code/07_gap_report.py", line 77, in main
    generate_gap_report(reason=reason)
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-346-investigating-the-correlation-between-gu/code/07_gap_report.py", line 65, in generate_gap_report
    write_json_log(report_data, report_file)
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-346-investigating-the-correlation-between-gu/code/utils.py", line 125, in write_json_log
    with open(path, 'w') as f:
         ^^^^^^^^^^^^^^^
IsADirectoryError: [Errno 21] Is a directory: '/home/runner/work/llmXive/llmXive/projects/PROJ-346-investigating-the-correlation-between-gu/data/processed/data_gap_report.json'

## Declared deliverables still missing

- data/raw/literature_metadata.json

## ⚠ SHARED-MODULE CONTRACT — fix the DEFINITION, tolerant of ALL callers

One or more failures are API-CONTRACT errors on a symbol YOUR OWN code defines and that MANY scripts call in DIFFERENT ways. Rewriting the definition to match one caller breaks the others — that is why this keeps failing. Fix the DEFINITION **once** so it is compatible with EVERY call site listed below: accept ``*args, **kwargs``, branch on what was actually passed, and NEVER raise on an unexpected call shape. For an auxiliary utility (e.g. logging), doing nothing on an unrecognized shape is fine. Do NOT edit the call sites — edit only the defining module.

**CRITICAL — ADD, do not REPLACE.** Edit the defining module *in place*: ADD the missing methods/parameters and PRESERVE every function, method, and attribute that already exists. Do NOT rewrite the file from scratch and do NOT delete a definition to make room for another. Each round that deletes a previously-working symbol just moves the failure to that symbol next round — an infinite loop. The fix is cumulative: the module must satisfy ALL callers from ALL rounds simultaneously.

**This list is CUMULATIVE across every fix round** — it includes contracts you may have ALREADY satisfied in an earlier round. Keep satisfying them while you fix the rest. Do NOT remove a method or parameter merely because it is absent from this round's traceback; if it is listed here, some script still depends on it.

### `get_data_processed_path` — defined in `code/utils.py`; called 12 way(s):

- code/03_correlation.py: data_dir = get_data_processed_path(root)
- code/03_correlation.py: data_dir = get_data_processed_path()
- code/06_visualize.py: data_path = get_data_processed_path()
- code/04_regression.py: processed_dir = get_data_processed_path()
- code/04_regression.py: output_dir = get_data_processed_path()
- code/02_preprocess.py: processed_dir = get_data_processed_path()
- code/05_save_results.py: processed_dir = get_data_processed_path()
- code/05_sensitivity.py: processed_dir = get_data_processed_path()
- code/07_gap_report.py: processed_path = get_data_processed_path()
- code/utils.py: - get_data_processed_path()
- code/utils.py: - get_data_processed_path(root)
- code/utils.py: - get_data_processed_path(root, sub_dir)

Make `get_data_processed_path` in `code/utils.py` accept ALL of the above.

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/raw/literature_metadata.json` is declared but was NOT written. Scripts referencing it:
    - `code/08_mechanistic_synthesis.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/literature_metadata.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.

## ⚠ CROSS-SCRIPT DATA CONTRACT — make the PRODUCER write what consumers read

One or more failures are DATA-SCHEMA mismatches BETWEEN scripts that exchange a file: a CONSUMER requires column/key names (or a file) that the PRODUCER did not write. The traceback you saw shows only the CONSUMER's EXPECTATION — never the producer's ACTUAL output — which is why this keeps failing. Below is the REAL schema each producer wrote on disk (read from the actual file) versus what the consumers require. Pick ONE canonical schema and make the **PRODUCER** write exactly the columns/keys the consumers read (preferred when one producer feeds several consumers), editing the producer IN PLACE. Do NOT fake or stub the data.

**This list is CUMULATIVE across every fix round** — keep satisfying a contract you already fixed while you fix the rest; do not drop a column merely because it is absent from this round's traceback.

### `home/runner/work/llmXive/llmXive/projects/PROJ-346-investigating-the-correlation-between-gu/data/qc/sensitivity_analysis_results.json`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/05_sensitivity.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `home/runner/work/llmXive/llmXive/projects/PROJ-346-investigating-the-correlation-between-gu/data/qc/sensitivity_analysis_results.json`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/05_sensitivity.py`.
