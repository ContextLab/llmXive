# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/data/generate_synthetic_data.py: metric `latency` assigned from an RNG draw (line 36)
- code/data/generate_synthetic_data.py: synthetic/fake INPUT data not authorized by the spec — “…""" T013: Generate synthetic data IF download_status…”
- code/data/generate_synthetic_data.py: synthetic/fake INPUT data not authorized by the spec — “…int = 150):     """     Generate synthetic human-avatar interaction…”
- code/data/generate_synthetic_data.py: synthetic/fake INPUT data not authorized by the spec — “…f"Generating {n_samples} synthetic samples.")          # 1. Generat…”
- code/data/generate_synthetic_data.py: synthetic/fake INPUT data not authorized by the spec — “…:         logger.error(f"Synthetic data failed independence chec…”
- code/data/generate_synthetic_data.py: synthetic/fake INPUT data not authorized by the spec — “…logger.info(f"Saved synthetic data to {output_path}")…”
- code/download_data.py: synthetic/fake INPUT data not authorized by the spec — “…ne should fall back to   synthetic data generation - ``timestamp…”
- code/download_data.py: synthetic/fake INPUT data not authorized by the spec — “…line to     fall back to synthetic data generation.     """…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 22 fabricated/simulated-result signal(s) — results are not real measurements: code/data/generate_synthetic_data.py: metric `latency` assigned from an RNG draw (line 36); code/data/generate_synthetic_data.py: synthetic/fake INPUT data not authorized by the spec — “…""" T013: Generate synthetic data IF download_status…”; code/data/generate_synthetic_data.py: synthetic/fake INPUT data not authorized by the spec — “…int = 150):     """     Generate synthetic human-avatar interaction…”; 1 run-book script(s) missing (plan/impl path mismatch): bash run_pipeline.sh; 5 declared deliverable(s) absent: data/processed/modeling_config.json; data/processed/vif_report.json; data/raw/synthetic_data.csv

## Failing / missing run-book commands

- bash run_pipeline.sh -> rc=-1

shell script must be an existing project-local .sh file

## Declared deliverables still missing

- data/processed/modeling_config.json
- data/processed/vif_report.json
- data/raw/synthetic_data.csv
- data/results/model_metrics.json
- data/results/sensitivity_analysis.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/modeling_config.json` is declared but was NOT written. Scripts referencing it:
    - `code/modeling/model_fitting.py` — NOT invoked by the run-book
    - `code/preprocessing/enforce_sample_gate.py` — NOT invoked by the run-book
    - `code/preprocessing/filter_covariates.py` — NOT invoked by the run-book
    - `code/utils/power_analysis.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/modeling_config.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/vif_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/preprocessing/output_cleaned_data.py` — NOT invoked by the run-book
    - `code/preprocessing/preprocess.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/vif_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/synthetic_data.csv` is declared but was NOT written. Scripts referencing it:
    - `code/data/__init__.py` — NOT invoked by the run-book
    - `code/data/generate_synthetic_data.py` — NOT invoked by the run-book
    - `code/generate_synthetic_data.py` — NOT invoked by the run-book
    - `code/modeling/generate_metrics_json.py` — NOT invoked by the run-book
    - `code/preprocessing/preprocess.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/synthetic_data.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/model_metrics.json` is declared but was NOT written. Scripts referencing it:
    - `code/interpretation_logic.py` — NOT invoked by the run-book
    - `code/modeling/add_correlational_framing.py` — NOT invoked by the run-book
    - `code/modeling/generate_metrics_json.py` — NOT invoked by the run-book
    - `code/modeling/model_fitting.py` — NOT invoked by the run-book
    - `code/modeling/sensitivity_analysis.py` — NOT invoked by the run-book
    - `code/visualization/t032_save_plots_and_interpret.py` — NOT invoked by the run-book
    - `code/visualization.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/model_metrics.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/sensitivity_analysis.csv` is declared but was NOT written. Scripts referencing it:
    - `code/modeling/__init__.py` — NOT invoked by the run-book
    - `code/modeling/sensitivity_analysis.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/sensitivity_analysis.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
