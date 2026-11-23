# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/src/data/align.py: synthetic/fake INPUT data not authorized by the spec — “…grity checks fail (e.g., synthetic data detected)."""     pass…”
- code/src/data/align.py: synthetic/fake INPUT data not authorized by the spec — “…urn          # Check for synthetic data     synthetic_rows = df[…”
- code/src/data/align.py: synthetic/fake INPUT data not authorized by the spec — “…_)         error_msg = f"Synthetic data detected in {data_type}.…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 3 fabricated/simulated-result signal(s) — results are not real measurements: code/src/data/align.py: synthetic/fake INPUT data not authorized by the spec — “…grity checks fail (e.g., synthetic data detected)."""     pass…”; code/src/data/align.py: synthetic/fake INPUT data not authorized by the spec — “…urn          # Check for synthetic data     synthetic_rows = df[…”; code/src/data/align.py: synthetic/fake INPUT data not authorized by the spec — “…_)         error_msg = f"Synthetic data detected in {data_type}.…”; 5 run-book script(s) missing (plan/impl path mismatch): python src/main.py --task ingest --dataset openneuro-fslr64k; python src/main.py --task preprocess --subject 001; python src/main.py --task align --subject 001; 4 declared deliverable(s) absent: data/accuracy_blocks.csv; data/aligned_data.csv; data/interim_lagged_mmns.csv

## Failing / missing run-book commands

- python src/main.py --task ingest --dataset openneuro-fslr64k -> rc=2

/home/runner/work/llmXive/llmXive/projects/PROJ-500-neural-correlates-of-predictive-error-si/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-500-neural-correlates-of-predictive-error-si/src/main.py': [Errno 2] No such file or directory

- python src/main.py --task preprocess --subject 001 -> rc=2

/home/runner/work/llmXive/llmXive/projects/PROJ-500-neural-correlates-of-predictive-error-si/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-500-neural-correlates-of-predictive-error-si/src/main.py': [Errno 2] No such file or directory

- python src/main.py --task align --subject 001 -> rc=2

/home/runner/work/llmXive/llmXive/projects/PROJ-500-neural-correlates-of-predictive-error-si/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-500-neural-correlates-of-predictive-error-si/src/main.py': [Errno 2] No such file or directory

- python src/main.py --task model --all -> rc=2

/home/runner/work/llmXive/llmXive/projects/PROJ-500-neural-correlates-of-predictive-error-si/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-500-neural-correlates-of-predictive-error-si/src/main.py': [Errno 2] No such file or directory

- python src/main.py --task robustness --windows "140-240,160-260" -> rc=2

/home/runner/work/llmXive/llmXive/projects/PROJ-500-neural-correlates-of-predictive-error-si/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-500-neural-correlates-of-predictive-error-si/src/main.py': [Errno 2] No such file or directory


## Declared deliverables still missing

- data/accuracy_blocks.csv
- data/aligned_data.csv
- data/interim_lagged_mmns.csv
- data/power_report.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/accuracy_blocks.csv` is declared but was NOT written. Scripts referencing it:
    - `code/src/data/align.py` — NOT invoked by the run-book
    - `code/src/data/clean.py` — NOT invoked by the run-book
    - `code/src/data/finalize.py` — NOT invoked by the run-book
    - `code/tests/integration/test_alignment.py` — NOT invoked by the run-book
    - `code/tests/integration/test_t026_finalization.py` — NOT invoked by the run-book
    - `code/tests/integration/test_t048_synthetic_rejection.py` — NOT invoked by the run-book
    - `code/tests/unit/test_t021_behavioral_binning.py` — NOT invoked by the run-book
    - `code/tests/unit/test_t022_lagged_alignment.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/accuracy_blocks.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/aligned_data.csv` is declared but was NOT written. Scripts referencing it:
    - `code/src/analysis/model.py` — NOT invoked by the run-book
    - `code/src/data/align.py` — NOT invoked by the run-book
    - `code/src/data/finalize.py` — NOT invoked by the run-book
    - `code/src/data/finalize_aligned.py` — NOT invoked by the run-book
    - `code/src/data/preprocess.py` — NOT invoked by the run-book
    - `code/tests/contract/test_schemas.py` — NOT invoked by the run-book
    - `code/tests/integration/test_t026_finalization.py` — NOT invoked by the run-book
    - `code/tests/unit/test_t024_finalization.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/aligned_data.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/interim_lagged_mmns.csv` is declared but was NOT written. Scripts referencing it:
    - `code/src/data/align.py` — NOT invoked by the run-book
    - `code/src/data/clean.py` — NOT invoked by the run-book
    - `code/src/data/finalize.py` — NOT invoked by the run-book
    - `code/tests/integration/test_alignment.py` — NOT invoked by the run-book
    - `code/tests/integration/test_t026_finalization.py` — NOT invoked by the run-book
    - `code/tests/integration/test_t048_synthetic_rejection.py` — NOT invoked by the run-book
    - `code/tests/unit/test_t022_lagged_alignment.py` — NOT invoked by the run-book
    - `code/tests/unit/test_t022b_learning_phase.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/interim_lagged_mmns.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/power_report.csv` is declared but was NOT written. Scripts referencing it:
    - `code/src/data/finalize.py` — NOT invoked by the run-book
    - `code/tests/unit/test_t024_finalization.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/power_report.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
