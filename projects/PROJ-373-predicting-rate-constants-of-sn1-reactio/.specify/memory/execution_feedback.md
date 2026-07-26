# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/analysis/power.py: synthetic/fake INPUT data not authorized by the spec — “…ze(mde, variance):     # Dummy sample size     return 100  def…”

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python code/validation/validate_quickstart.py --quickstart specs/001-predict-sn1-rate-constants/quickstart.md --evidence artifacts/integration_test_report.md`
  - script usage: `validate_quickstart.py [-h] [--project-root PROJECT_ROOT]`
  - argparse error: `validate_quickstart.py: error: unrecognized arguments: --evidence artifacts/integration_test_report.md`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 fabricated/simulated-result signal(s) — results are not real measurements: code/analysis/power.py: synthetic/fake INPUT data not authorized by the spec — “…ze(mde, variance):     # Dummy sample size     return 100  def…”; 9 command(s) failed: python code/main.py --stage ingest (rc=1); python code/data/clean.py --input data/raw/sn1_raw.csv --output data/processed/cleaned_sn1.csv (rc=1); python code/data/descriptors.py --input data/processed/cleaned_sn1.csv --output data/processed/descriptors.csv (rc=1); 2 declared deliverable(s) absent: data/processed/cleaned_sn1.csv; data/processed/exclusion_report.csv

## Failing / missing run-book commands

- python code/main.py --stage ingest -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-373-predicting-rate-constants-of-sn1-reactio/code/main.py", line 40, in <module>
    from data.ingest import main as ingest_main
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-373-predicting-rate-constants-of-sn1-reactio/code/data/__init__.py", line 1, in <module>
    from .ingest import load_huggingface_data, load_uci_data, map_columns, save_exclusion_report, main
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-373-predicting-rate-constants-of-sn1-reactio/code/data/ingest.py", line 5, in <module>
    import pandas as pd
ModuleNotFoundError: No module named 'pandas'
- python code/data/clean.py --input data/raw/sn1_raw.csv --output data/processed/cleaned_sn1.csv -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-373-predicting-rate-constants-of-sn1-reactio/code/data/clean.py", line 5, in <module>
    import pandas as pd
ModuleNotFoundError: No module named 'pandas'
- python code/data/descriptors.py --input data/processed/cleaned_sn1.csv --output data/processed/descriptors.csv -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-373-predicting-rate-constants-of-sn1-reactio/code/data/descriptors.py", line 5, in <module>
    import pandas as pd
ModuleNotFoundError: No module named 'pandas'
- python code/data/split.py --input data/processed/descriptors.csv --output data/processed/ -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-373-predicting-rate-constants-of-sn1-reactio/code/data/split.py", line 5, in <module>
    import pandas as pd
ModuleNotFoundError: No module named 'pandas'
- python code/models/train.py --config config.yaml --data data/processed/train.csv --output artifacts/ -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-373-predicting-rate-constants-of-sn1-reactio/code/models/train.py", line 14, in <module>
    from models.mpnn import MPNNConfig, create_mpnn_from_config
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-373-predicting-rate-constants-of-sn1-reactio/code/models/__init__.py", line 1, in <module>
    from .mpnn import MPNNConfig, MPNNMessagePassingLayer, MPNN, create_mpnn_from_config, main
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-373-predicting-rate-constants-of-sn1-reactio/code/models/mpnn.py", line 1, in <module>
    import torch
ModuleNotFoundError: No module named 'torch'
- python code/models/evaluate.py --model artifacts/best_model.pt --data data/processed/test.csv -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-373-predicting-rate-constants-of-sn1-reactio/code/models/evaluate.py", line 61, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-373-predicting-rate-constants-of-sn1-reactio/code/models/evaluate.py", line 52, in main
    parser = argparse.ArgumentParser(description="Evaluate model")
             ^^^^^^^^
NameError: name 'argparse' is not defined
- python code/analysis/interpret.py --model artifacts/best_model.pt --data data/processed/test.csv --output artifacts/ -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-373-predicting-rate-constants-of-sn1-reactio/code/analysis/interpret.py", line 8, in <module>
    import numpy as np
ModuleNotFoundError: No module named 'numpy'
- python code/main.py --stage all -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-373-predicting-rate-constants-of-sn1-reactio/code/main.py", line 40, in <module>
    from data.ingest import main as ingest_main
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-373-predicting-rate-constants-of-sn1-reactio/code/data/__init__.py", line 1, in <module>
    from .ingest import load_huggingface_data, load_uci_data, map_columns, save_exclusion_report, main
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-373-predicting-rate-constants-of-sn1-reactio/code/data/ingest.py", line 5, in <module>
    import pandas as pd
ModuleNotFoundError: No module named 'pandas'
- python code/validation/validate_quickstart.py --quickstart specs/001-predict-sn1-rate-constants/quickstart.md --evidence artifacts/integration_test_report.md -> rc=2
    usage: validate_quickstart.py [-h] [--project-root PROJECT_ROOT]
                              [--quickstart QUICKSTART] [--output OUTPUT]
validate_quickstart.py: error: unrecognized arguments: --evidence artifacts/integration_test_report.md

## Declared deliverables still missing

- data/processed/cleaned_sn1.csv
- data/processed/exclusion_report.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/cleaned_sn1.csv` is declared but was NOT written. Scripts referencing it:
    - `code/main.py` — IS a run-book command
    - `code/analysis/collinearity.py` — NOT invoked by the run-book
    - `code/analysis/consistency.py` — NOT invoked by the run-book
    - `code/analysis/hyperparameter_sensitivity.py` — NOT invoked by the run-book
    - `code/analysis/sensitivity_runner.py` — NOT invoked by the run-book
    - `code/tests/integration/test_full_pipeline.py` — NOT invoked by the run-book
    - `code/data/split.py` — IS a run-book command
    - `code/data/descriptors.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/cleaned_sn1.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/exclusion_report.csv` is declared but was NOT written. Scripts referencing it:
    - `code/main.py` — IS a run-book command
    - `code/data/__init__.py` — NOT invoked by the run-book
    - `code/data/ingest.py` — NOT invoked by the run-book
    - `code/data/clean.py` — IS a run-book command
    - `code/data/finalize_dataset.py` — NOT invoked by the run-book
    - `code/data/exclusion_report.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/exclusion_report.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
