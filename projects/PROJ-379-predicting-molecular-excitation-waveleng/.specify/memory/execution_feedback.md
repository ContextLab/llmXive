# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/evaluate.py: self-declared fabricated metric — “…graph prep,         # we will simulate the metric computation structure to ensu…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 fabricated/simulated-result signal(s) — results are not real measurements: code/evaluate.py: self-declared fabricated metric — “…graph prep,         # we will simulate the metric computation structure to ensu…”; 10 command(s) failed: python code/ingest.py (rc=1); python code/split.py (rc=1); python code/merge_split.py (rc=1); 12 declared deliverable(s) absent: data/processed/cleaned.csv; data/processed/collinearity_flags.json; data/processed/masked_attribution.json

## Failing / missing run-book commands

- python code/ingest.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-379-predicting-molecular-excitation-waveleng/code/ingest.py", line 18, in <module>
    from models import Molecule
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-379-predicting-molecular-excitation-waveleng/code/models.py", line 2, in <module>
    from pydantic import BaseModel, Field, field_validator
ModuleNotFoundError: No module named 'pydantic'
- python code/split.py -> rc=1
    2026-09-23 11:09:31,393 - __main__ - INFO - Starting split pipeline...
2026-09-23 11:09:31,393 - __main__ - ERROR - Split pipeline failed: Input file not found: data/processed/cleaned.csv
- python code/merge_split.py -> rc=1
    2026-09-23 11:09:31,703 - __main__ - INFO - Starting merge split pipeline...
2026-09-23 11:09:31,703 - __main__ - ERROR - Merge split pipeline failed: Cleaned data not found: data/processed/cleaned.csv
- python code/train.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-379-predicting-molecular-excitation-waveleng/code/train.py", line 24, in <module>
    import torch
ModuleNotFoundError: No module named 'torch'
- python code/evaluate.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-379-predicting-molecular-excitation-waveleng/code/evaluate.py", line 15, in <module>
    import torch
ModuleNotFoundError: No module named 'torch'
- python code/collinearity_check.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-379-predicting-molecular-excitation-waveleng/code/collinearity_check.py", line 12, in <module>
    from models import Molecule
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-379-predicting-molecular-excitation-waveleng/code/models.py", line 2, in <module>
    from pydantic import BaseModel, Field, field_validator
ModuleNotFoundError: No module named 'pydantic'
- python code/explain.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-379-predicting-molecular-excitation-waveleng/code/explain.py", line 8, in <module>
    import torch
ModuleNotFoundError: No module named 'torch'
- python code/sensitivity.py -> rc=1
    2026-09-23 11:09:32,634 - sensitivity - ERROR - Predictions file not found at data/processed/predictions.csv. Please run code/evaluate.py first to generate predictions.
- python code/analyze_results.py -> rc=1
    2026-09-23 11:09:32,689 - __main__ - INFO - Starting T027: Aggregating results...
2026-09-23 11:09:32,689 - __main__ - ERROR - Required artifact missing: /home/runner/work/llmXive/llmXive/projects/PROJ-379-predicting-molecular-excitation-waveleng/data/processed/metrics.json
2026-09-23 11:09:32,689 - __main__ - ERROR - Missing required input file: Required artifact missing: /home/runner/work/llmXive/llmXive/projects/PROJ-379-predicting-molecular-excitation-waveleng/data/processed/metrics.json
- python code/run_quickstart_validation.py -> rc=1
    O - Project Root: /home/runner/work/llmXive/llmXive/projects/PROJ-379-predicting-molecular-excitation-waveleng
2026-09-23 11:09:32,714 - INFO - Environment: CPU-only (CUDA_VISIBLE_DEVICES=)
2026-09-23 11:09:32,714 - INFO - --- Running Data Ingestion ---
2026-09-23 11:09:32,863 - ERROR - Data Ingestion failed: Command '['/home/runner/work/llmXive/llmXive/projects/PROJ-379-predicting-molecular-excitation-waveleng/code/.venv/bin/python', '/home/runner/work/llmXive/llmXive/projects/PROJ-379-predicting-molecular-excitation-waveleng/code/ingest.py']' returned non-zero exit status 1.
2026-09-23 11:09:32,863 - ERROR - stdout: 
2026-09-23 11:09:32,863 - ERROR - stderr: Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-379-predicting-molecular-excitation-waveleng/code/ingest.py", line 18, in <module>
    from models import Molecule
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-379-predicting-molecular-excitation-waveleng/code/models.py", line 2, in <module>
    from pydantic import BaseModel, Field, field_validator
ModuleNotFoundError: No module named 'pydantic'

2026-09-23 11:09:32,863 - ERROR - Pipeline failed at Data Ingestion. Aborting.

## Declared deliverables still missing

- data/processed/cleaned.csv
- data/processed/collinearity_flags.json
- data/processed/masked_attribution.json
- data/processed/metrics.json
- data/processed/metrics_partial.json
- data/processed/power_analysis.json
- data/processed/raw_attribution.json
- data/processed/sampling_log.json
- data/processed/sensitivity_report.csv
- data/processed/split_indices.json
- data/processed/timing.json
- data/processed/train_val_test.csv

## ✅ VERIFIED REAL DATA SOURCE — use THIS in the data loader

Do NOT invent or guess a download URL/API (a hallucinated endpoint will 404). A real source was discovered AND verified by actually loading real data from it:

- **Install**: add `PubChemPy` to the project's `requirements.txt` and `pip install PubChemPy`.
- **Verified**: this loads **3** real records with fields: smiles, compound_name, source_database, molecule_id.
- **Working access recipe** (this EXACT code was executed and returned real data — base the loader on it):

```python
import pubchempy as pcp

cids = [2244, 2519, 1983]
records = []
for cid in cids:
    comp = pcp.Compound.from_cid(cid)
    smiles = getattr(comp, "connectivity_smiles", None) or getattr(comp, "canonical_smiles", None)
    name = comp.iupac_name
    if not name:
        name = comp.synonyms[0] if getattr(comp, "synonyms", None) else None
    records.append({
        "smiles": smiles,
        "compound_name": name,
        "source_database": "PubChem",
        "molecule_id": cid,
    })

print(f"RECORDS={len(records)}")
print("FIELDS=" + ",".join(records[0].keys()) if records else "FIELDS=")
```

Write the loader to use this source/recipe, persist the records to the declared raw/processed data files, and DELETE any old code that fetches from a guessed website endpoint.

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/cleaned.csv` is declared but was NOT written. Scripts referencing it:
    - `code/merge_split.py` — IS a run-book command
    - `code/ingest.py` — IS a run-book command
    - `code/collinearity_check.py` — IS a run-book command
    - `code/run_ingest_validation.py` — NOT invoked by the run-book
    - `code/generate_final_state.py` — NOT invoked by the run-book
    - `code/validate_data.py` — NOT invoked by the run-book
    - `code/split.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/cleaned.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/collinearity_flags.json` is declared but was NOT written. Scripts referencing it:
    - `code/generate_final_state.py` — NOT invoked by the run-book
    - `code/analyze_results.py` — IS a run-book command
    - `code/verify_metrics.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/collinearity_flags.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/masked_attribution.json` is declared but was NOT written. Scripts referencing it:
    - `code/collinearity_check.py` — IS a run-book command
    - `code/sensitivity_sweep_runner.py` — NOT invoked by the run-book
    - `code/generate_final_state.py` — NOT invoked by the run-book
    - `code/apply_mask.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/masked_attribution.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/metrics.json` is declared but was NOT written. Scripts referencing it:
    - `code/sensitivity.py` — IS a run-book command
    - `code/run_quickstart_validation.py` — IS a run-book command
    - `code/generate_sensitivity_report.py` — NOT invoked by the run-book
    - `code/timing_logger.py` — NOT invoked by the run-book
    - `code/evaluate.py` — IS a run-book command
    - `code/generate_final_state.py` — NOT invoked by the run-book
    - `code/analyze_results.py` — IS a run-book command
    - `code/verify_metrics.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/metrics.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/metrics_partial.json` is declared but was NOT written. Scripts referencing it:
    - `code/evaluate.py` — IS a run-book command
    - `code/generate_final_state.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/metrics_partial.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/power_analysis.json` is declared but was NOT written. Scripts referencing it:
    - `code/evaluate.py` — IS a run-book command
    - `code/generate_final_state.py` — NOT invoked by the run-book
    - `code/analyze_results.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/power_analysis.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/raw_attribution.json` is declared but was NOT written. Scripts referencing it:
    - `code/sensitivity_sweep_runner.py` — NOT invoked by the run-book
    - `code/generate_final_state.py` — NOT invoked by the run-book
    - `code/apply_mask.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/raw_attribution.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/sampling_log.json` is declared but was NOT written. Scripts referencing it:
    - `code/ingest.py` — IS a run-book command
    - `code/run_ingest_validation.py` — NOT invoked by the run-book
    - `code/verify_sampling_log.py` — NOT invoked by the run-book
    - `code/generate_final_state.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/sampling_log.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/sensitivity_report.csv` is declared but was NOT written. Scripts referencing it:
    - `code/sensitivity.py` — IS a run-book command
    - `code/generate_sensitivity_report.py` — NOT invoked by the run-book
    - `code/sensitivity_sweep_runner.py` — NOT invoked by the run-book
    - `code/generate_final_state.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/sensitivity_report.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/split_indices.json` is declared but was NOT written. Scripts referencing it:
    - `code/merge_split.py` — IS a run-book command
    - `code/evaluate.py` — IS a run-book command
    - `code/generate_final_state.py` — NOT invoked by the run-book
    - `code/split.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/split_indices.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/timing.json` is declared but was NOT written. Scripts referencing it:
    - `code/timing_logger.py` — NOT invoked by the run-book
    - `code/generate_final_state.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/timing.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/train_val_test.csv` is declared but was NOT written. Scripts referencing it:
    - `code/train.py` — IS a run-book command
    - `code/merge_split.py` — IS a run-book command
    - `code/evaluate.py` — IS a run-book command
    - `code/generate_final_state.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/train_val_test.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.

## ⚠ CROSS-SCRIPT DATA CONTRACT — make the PRODUCER write what consumers read

One or more failures are DATA-SCHEMA mismatches BETWEEN scripts that exchange a file: a CONSUMER requires column/key names (or a file) that the PRODUCER did not write. The traceback you saw shows only the CONSUMER's EXPECTATION — never the producer's ACTUAL output — which is why this keeps failing. Below is the REAL schema each producer wrote on disk (read from the actual file) versus what the consumers require. Pick ONE canonical schema and make the **PRODUCER** write exactly the columns/keys the consumers read (preferred when one producer feeds several consumers), editing the producer IN PLACE. Do NOT fake or stub the data.

**This list is CUMULATIVE across every fix round** — keep satisfying a contract you already fixed while you fix the rest; do not drop a column merely because it is absent from this round's traceback.

### `data/processed/cleaned.csv`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/merge_split.py`, `code/collinearity_check.py`, `code/run_ingest_validation.py`, `code/validate_data.py`, `code/split.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `data/processed/cleaned.csv`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/merge_split.py`, `code/collinearity_check.py`, `code/run_ingest_validation.py`, `code/generate_final_state.py`, `code/validate_data.py`, `code/split.py`.

### `data/processed/predictions.csv`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/sensitivity.py`, `code/sensitivity_sweep_runner.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `data/processed/predictions.csv`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/sensitivity.py`, `code/sensitivity_sweep_runner.py`.
