# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/scripts/validate_calibration.py: self-declared fabricated metric — “…sample_size: Number of simulated measurements.         seed: Random seed f…”
- code/main.py: synthetic/fake INPUT data not authorized by the spec — “…ore_true",         help="Generate synthetic data for testing"     )…”
- code/main.py: synthetic/fake INPUT data not authorized by the spec — “…mber of participants for synthetic data"     )     parser.add_ar…”
- code/main.py: synthetic/fake INPUT data not authorized by the spec — “…logger.info("Generating synthetic data...")         from script…”
- code/main.py: synthetic/fake INPUT data not authorized by the spec — “…)         logger.info(f"Synthetic data generated: {output_path}…”
- code/scripts/generate_synthetic_data.py: synthetic/fake INPUT data not authorized by the spec — “…""" Script to generate deterministic synthetic logs and task metrics fo…”
- code/scripts/generate_synthetic_data.py: synthetic/fake INPUT data not authorized by the spec — “…es realistic-looking but synthetic data to test the ingestion pi…”
- code/scripts/generate_synthetic_data.py: synthetic/fake INPUT data not authorized by the spec — “…> List[str]:     """     Generate synthetic JSONL logs for data inge…”

## ⛔ HOLLOW RESULTS — the analysis RAN but MEASURED NOTHING

Every command exited 0 and the files were written — but the numbers in them are missing. A result that is `null`, `NaN`, an empty `[]`, a header-only CSV, or a column left blank in every row is NOT a measurement. Writing an empty result file is not 'done' — it is the same failure as fabrication, just quieter. You MUST:

1. Find WHY the value is missing. A `null`/`NaN` correlation almost always means the inputs were empty, misaligned, or the wrong column was read — fix the computation, do NOT paper over it with a default.
2. Verify you loaded the REAL dataset the spec names. If the study is about behavioural confidence ratings, a stand-in dataset (a bundled sklearn toy set, a random frame) is NOT the data — it will produce exactly these null/NaN results.
3. Make sure the key measure is actually POPULATED before you compute on it: if the column the study depends on is blank in every row, the extraction step is broken and that is the real bug.
4. NEVER self-certify. A `{"status": "PASS"}` written by your own code proves nothing; the numbers must be there.

- data/processed/noise_logs_processed.csv: header only, ZERO data rows — the analysis produced no rows
- data/processed/task_performances_processed.csv: header only, ZERO data rows — the analysis produced no rows
- every produced artifact is gitignored (data/processed/noise_logs_processed.csv, data/processed/task_performances_processed.csv) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 9 fabricated/simulated-result signal(s) — results are not real measurements: code/scripts/validate_calibration.py: self-declared fabricated metric — “…sample_size: Number of simulated measurements.         seed: Random seed f…”; code/main.py: synthetic/fake INPUT data not authorized by the spec — “…ore_true",         help="Generate synthetic data for testing"     )…”; code/main.py: synthetic/fake INPUT data not authorized by the spec — “…mber of participants for synthetic data"     )     parser.add_ar…”; 2 hollow-result signal(s) — the analysis ran but computed nothing: data/processed/noise_logs_processed.csv: header only, ZERO data rows — the analysis produced no rows; data/processed/task_performances_processed.csv: header only, ZERO data rows — the analysis produced no rows; every produced artifact is gitignored (data/processed/noise_logs_processed.csv, data/processed/task_performances_processed.csv) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.; 3 command(s) failed: python code/main.py --ingest --raw data/raw/synthetic_logs.jsonl --validate (rc=1); python -m pytest tests/unit/ (rc=2); python -m pytest tests/integration/ (rc=2); 1 declared deliverable(s) absent: data/processed/calibration_validation_report.json

## Failing / missing run-book commands

- python -c "from datasets import load_dataset; load_dataset('jumplander/J6-CFI-HQ-20K', split='train').to_json('data/raw/cfi_train.jsonl')" -> rc=1

Traceback (most recent call last):
  File "<string>", line 1, in <module>
ModuleNotFoundError: No module named 'datasets'

- python code/main.py --ingest --raw data/raw/synthetic_logs.jsonl --validate -> rc=1
jsonl:56
2026-10-13 15:40:05 - data_ingestion - WARNING - Unknown record type in data/raw/P100_raw.jsonl:57
2026-10-13 15:40:05 - data_ingestion - WARNING - Unknown record type in data/raw/P100_raw.jsonl:58
2026-10-13 15:40:05 - data_ingestion - WARNING - Unknown record type in data/raw/P100_raw.jsonl:59
2026-10-13 15:40:05 - data_ingestion - WARNING - Unknown record type in data/raw/P100_raw.jsonl:60
2026-10-13 15:40:05 - data_ingestion - INFO - Processed 151 files. Found 0 participants, 0 noise logs, 3 task performances.
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-114-the-impact-of-ambient-noise-on-cognitive/code/main.py", line 117, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-114-the-impact-of-ambient-noise-on-cognitive/code/main.py", line 94, in main
    run_ingestion_pipeline(input_dir=raw_dir)
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-114-the-impact-of-ambient-noise-on-cognitive/code/data_ingestion.py", line 605, in run_ingestion_pipeline
    "zero_db_cases": outlier_audit["zero_db_edge_cases"],
                     ~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^
KeyError: 'zero_db_edge_cases'

- python -m pytest tests/unit/ -> rc=2
llecting tests/unit/test_validate_calibration.py ___________
ImportError while importing test module '/home/runner/work/llmXive/llmXive/projects/PROJ-114-the-impact-of-ambient-noise-on-cognitive/tests/unit/test_validate_calibration.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/importlib/__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
tests/unit/test_validate_calibration.py:16: in <module>
    from code.scripts.validate_calibration import simulate_device_response, run_calibration_validation
code/scripts/validate_calibration.py:22: in <module>
    from code.config import (
E   ImportError: cannot import name 'REFERENCE_TONE_PARAMS' from 'code.config' (/home/runner/work/llmXive/llmXive/projects/PROJ-114-the-impact-of-ambient-noise-on-cognitive/code/config.py)
=========================== short test summary info ============================
ERROR tests/unit/test_validate_calibration.py
!!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
=============================== 1 error in 0.47s ===============================


- python -m pytest tests/integration/ -> rc=2
RRORS ====================================
________ ERROR collecting tests/integration/test_ingestion_pipeline.py _________
ImportError while importing test module '/home/runner/work/llmXive/llmXive/projects/PROJ-114-the-impact-of-ambient-noise-on-cognitive/tests/integration/test_ingestion_pipeline.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/importlib/__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
tests/integration/test_ingestion_pipeline.py:24: in <module>
    from code.config import ROOT_DIR, CALIBRATION_ERROR_THRESHOLD_DB, MIN_VALID_LOGGING_PROPORTION
E   ImportError: cannot import name 'CALIBRATION_ERROR_THRESHOLD_DB' from 'code.config' (/home/runner/work/llmXive/llmXive/projects/PROJ-114-the-impact-of-ambient-noise-on-cognitive/code/config.py)
=========================== short test summary info ============================
ERROR tests/integration/test_ingestion_pipeline.py
!!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
=============================== 1 error in 0.41s ===============================



## Declared deliverables still missing

- data/processed/calibration_validation_report.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/calibration_validation_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/scripts/validate_calibration.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/calibration_validation_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
## Platform-owned paths written inside the project

A script in this project created `.github/`, `state/` inside the project directory. Those names belong to the platform, and a copy of them here is a SHADOW: the verifier resolves the paths a task names relative to this project, so it reads the shadow instead of canonical state and rejects work on the strength of a stale record.

Write your outputs under `data/`, `figures/`, `code/` and `paper/`. Do not record artifact hashes, run state or project status yourself — the platform owns `state/` and derives hashes at verification time. Delete the directories listed above and drop whatever step created them.
