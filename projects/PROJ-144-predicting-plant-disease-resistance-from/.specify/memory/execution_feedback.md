# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 command(s) failed: python code/data/preprocess.py --input data/raw --output data/processed (rc=1); python code/modeling/interpret.py --input results/shap_analysis.json --output results/pathway_analysis.json (rc=1); 2 declared deliverable(s) absent: data/processed/heterogeneity_report.json; data/raw/study_manifest.json

## Failing / missing run-book commands

- python code/data/preprocess.py --input data/raw --output data/processed -> rc=1
    2026-09-03 22:51:11,295 - INFO - Starting preprocessing. Input: data/raw, Output: data/processed
2026-09-03 22:51:11,295 - INFO - Loading data from data/raw
2026-09-03 22:51:11,295 - ERROR - Preprocessing failed: [Errno 21] Is a directory: 'data/raw'
2026-09-03 22:51:11,295 - ERROR - Pipeline failed: [Errno 21] Is a directory: 'data/raw'
- python code/modeling/interpret.py --input results/shap_analysis.json --output results/pathway_analysis.json -> rc=1
    2026-09-03 22:51:11,714 - __main__ - INFO - Starting T043: Verifying KEGG API fallback/retry in pathway interpretation
2026-09-03 22:51:11,714 - __main__ - ERROR - Required input file missing: results/shap_analysis.json
2026-09-03 22:51:11,714 - __main__ - ERROR - Input file not found: results/shap_analysis.json

## Declared deliverables still missing

- data/processed/heterogeneity_report.json
- data/raw/study_manifest.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/heterogeneity_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/data/detect_heterogeneity.py` — NOT invoked by the run-book
    - `code/data/harmonize.py` — NOT invoked by the run-book
    - `code/data/harmonize_labels.py` — NOT invoked by the run-book
    - `code/data/detect_label_heterogeneity.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/heterogeneity_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/raw/study_manifest.json` is declared but was NOT written. Scripts referencing it:
    - `code/research/verify_studies.py` — NOT invoked by the run-book
    - `code/research/verify_artifact_tracking.py` — NOT invoked by the run-book
    - `code/data/discover_studies.py` — NOT invoked by the run-book
    - `code/data/detect_heterogeneity.py` — NOT invoked by the run-book
    - `code/data/validate_temporal.py` — NOT invoked by the run-book
    - `code/data/harmonize.py` — NOT invoked by the run-book
    - `code/data/download_study.py` — NOT invoked by the run-book
    - `code/data/filter_studies.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/study_manifest.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.

## ⚠ CROSS-SCRIPT DATA CONTRACT — make the PRODUCER write what consumers read

One or more failures are DATA-SCHEMA mismatches BETWEEN scripts that exchange a file: a CONSUMER requires column/key names (or a file) that the PRODUCER did not write. The traceback you saw shows only the CONSUMER's EXPECTATION — never the producer's ACTUAL output — which is why this keeps failing. Below is the REAL schema each producer wrote on disk (read from the actual file) versus what the consumers require. Pick ONE canonical schema and make the **PRODUCER** write exactly the columns/keys the consumers read (preferred when one producer feeds several consumers), editing the producer IN PLACE. Do NOT fake or stub the data.

**This list is CUMULATIVE across every fix round** — keep satisfying a contract you already fixed while you fix the rest; do not drop a column merely because it is absent from this round's traceback.

### `results/shap_analysis.json`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/research/verify_artifact_tracking.py`, `code/modeling/generate_framing_report.py`, `code/modeling/aggregate_results.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `results/shap_analysis.json`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/research/verify_artifact_tracking.py`, `code/modeling/generate_framing_report.py`, `code/modeling/aggregate_results.py`.
