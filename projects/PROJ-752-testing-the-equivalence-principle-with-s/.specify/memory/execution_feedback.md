# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/analysis/validation.py: self-declared fabricated metric — “…dof, n, eta_value          # Mock values for demonstration if real es…”
- code/scripts/validate_quickstart.py: self-declared fabricated metric — “…culation logic...")         # Mock values for logic check         mock…”

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python code/analysis/eotvos.py --config code/config.yaml`
  - script usage: `eotvos.py [-h] --input INPUT --output OUTPUT`
  - argparse error: `eotvos.py: error: the following arguments are required: --input, --output`
- run-book command: `python code/analysis/validation.py --config code/config.yaml`
  - script usage: `validation.py [-h] --data DATA [--models MODELS [MODELS ...]]`
  - argparse error: `validation.py: error: the following arguments are required: --data`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 fabricated/simulated-result signal(s) — results are not real measurements: code/analysis/validation.py: self-declared fabricated metric — “…dof, n, eta_value          # Mock values for demonstration if real es…”; code/scripts/validate_quickstart.py: self-declared fabricated metric — “…culation logic...")         # Mock values for logic check         mock…”; 2 run-book script(s) missing (plan/impl path mismatch): python code/ingestion/downloader.py --config code/config.yaml; python code/dynamics/solver.py --config code/config.yaml; 4 command(s) failed: python code/analysis/eotvos.py --config code/config.yaml (rc=2); python code/analysis/validation.py --config code/config.yaml (rc=2); python -m pytest tests/unit/ -v (rc=4); 3 declared deliverable(s) absent: data/processed/cleaned_slr_data.csv; data/results/eotvos_metrics.json; data/results/orbit_solutions.json

## Failing / missing run-book commands

- python code/ingestion/downloader.py --config code/config.yaml -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-752-testing-the-equivalence-principle-with-s/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-752-testing-the-equivalence-principle-with-s/code/ingestion/downloader.py': [Errno 2] No such file or directory

- python code/dynamics/solver.py --config code/config.yaml -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-752-testing-the-equivalence-principle-with-s/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-752-testing-the-equivalence-principle-with-s/code/dynamics/solver.py': [Errno 2] No such file or directory

- python code/analysis/eotvos.py --config code/config.yaml -> rc=2

usage: eotvos.py [-h] --input INPUT --output OUTPUT
eotvos.py: error: the following arguments are required: --input, --output

- python code/analysis/validation.py --config code/config.yaml -> rc=2

Matplotlib is building the font cache; this may take a moment.
usage: validation.py [-h] --data DATA [--models MODELS [MODELS ...]]
validation.py: error: the following arguments are required: --data

- python -m pytest tests/unit/ -v -> rc=4

ImportError while loading conftest '/home/runner/work/llmXive/llmXive/projects/PROJ-752-testing-the-equivalence-principle-with-s/tests/conftest.py'.
tests/conftest.py:18: in <module>
    from code.data.ingestion import DataUnavailableError
code/data/ingestion.py:153: in <module>
    def aggregate_satellites(satellite_ids: List[str], year: int) -> pd.DataFrame:
E   NameError: name 'pd' is not defined

- python -m pytest tests/contract/ -v -> rc=4

ImportError while loading conftest '/home/runner/work/llmXive/llmXive/projects/PROJ-752-testing-the-equivalence-principle-with-s/tests/conftest.py'.
tests/conftest.py:18: in <module>
    from code.data.ingestion import DataUnavailableError
code/data/ingestion.py:153: in <module>
    def aggregate_satellites(satellite_ids: List[str], year: int) -> pd.DataFrame:
E   NameError: name 'pd' is not defined


## Declared deliverables still missing

- data/processed/cleaned_slr_data.csv
- data/results/eotvos_metrics.json
- data/results/orbit_solutions.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/cleaned_slr_data.csv` is declared but was NOT written. Scripts referencing it:
    - `code/data/output.py` — NOT invoked by the run-book
    - `code/data/preprocessing.py` — NOT invoked by the run-book
    - `code/main.py` — NOT invoked by the run-book
    - `code/scripts/run_ingestion_pipeline.py` — NOT invoked by the run-book
    - `code/scripts/validate_quickstart.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/cleaned_slr_data.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/eotvos_metrics.json` is declared but was NOT written. Scripts referencing it:
    - `code/data/output.py` — NOT invoked by the run-book
    - `code/scripts/validate_quickstart.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/eotvos_metrics.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/orbit_solutions.json` is declared but was NOT written. Scripts referencing it:
    - `code/scripts/validate_quickstart.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/orbit_solutions.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
