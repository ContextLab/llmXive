# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/benchmark_perturbation.py: synthetic/fake INPUT data not authorized by the spec — “…t) -> tuple:     """     Generate synthetic embeddings and model mat…”
- code/benchmark_perturbation.py: synthetic/fake INPUT data not authorized by the spec — “…logger.info(f"Generating synthetic benchmark data: {n_samples} samples, di…”
- code/benchmark_perturbation.py: synthetic/fake INPUT data not authorized by the spec — “…xist_ok=True)          # Generate synthetic data for benchmarking…”

## ⚠ REGRESSIONS — your last fix BROKE these (they passed before)

These commands were NOT failing in the previous round and ARE failing now — your last edit broke previously-working code. REVERT or correct whatever change broke each one BEFORE touching anything else; do not trade one passing script for another (that oscillation is what burns the fix-round budget toward escalation):

- `python code/data_loader.py --fetch`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 3 fabricated/simulated-result signal(s) — results are not real measurements: code/benchmark_perturbation.py: synthetic/fake INPUT data not authorized by the spec — “…t) -> tuple:     """     Generate synthetic embeddings and model mat…”; code/benchmark_perturbation.py: synthetic/fake INPUT data not authorized by the spec — “…logger.info(f"Generating synthetic benchmark data: {n_samples} samples, di…”; code/benchmark_perturbation.py: synthetic/fake INPUT data not authorized by the spec — “…xist_ok=True)          # Generate synthetic data for benchmarking…”; 2 command(s) failed: python code/data_loader.py --fetch (rc=1); python code/main.py (rc=1); 12 declared deliverable(s) absent: data/processed/baseline_vectors.csv; data/processed/filtered_pairs_for_analysis.csv; data/processed/filtered_pairs_input_drift.csv

## Failing / missing run-book commands

- python code/data_loader.py --fetch -> rc=1
    t import Dataset
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-862-llmxive-follow-up-extending-formalizing/code/.venv/lib/python3.11/site-packages/datasets/arrow_dataset.py", line 67, in <module>
    from .arrow_writer import ArrowWriter, OptimizedTypedSequence
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-862-llmxive-follow-up-extending-formalizing/code/.venv/lib/python3.11/site-packages/datasets/arrow_writer.py", line 27, in <module>
    from .features import Features, Image, Value
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-862-llmxive-follow-up-extending-formalizing/code/.venv/lib/python3.11/site-packages/datasets/features/__init__.py", line 18, in <module>
    from .features import Array2D, Array3D, Array4D, Array5D, ClassLabel, Features, Sequence, Value
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-862-llmxive-follow-up-extending-formalizing/code/.venv/lib/python3.11/site-packages/datasets/features/features.py", line 634, in <module>
    class _ArrayXDExtensionType(pa.PyExtensionType):
                                ^^^^^^^^^^^^^^^^^^
AttributeError: module 'pyarrow' has no attribute 'PyExtensionType'. Did you mean: 'ExtensionType'?
- python code/main.py -> rc=1
    t import Dataset
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-862-llmxive-follow-up-extending-formalizing/code/.venv/lib/python3.11/site-packages/datasets/arrow_dataset.py", line 67, in <module>
    from .arrow_writer import ArrowWriter, OptimizedTypedSequence
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-862-llmxive-follow-up-extending-formalizing/code/.venv/lib/python3.11/site-packages/datasets/arrow_writer.py", line 27, in <module>
    from .features import Features, Image, Value
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-862-llmxive-follow-up-extending-formalizing/code/.venv/lib/python3.11/site-packages/datasets/features/__init__.py", line 18, in <module>
    from .features import Array2D, Array3D, Array4D, Array5D, ClassLabel, Features, Sequence, Value
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-862-llmxive-follow-up-extending-formalizing/code/.venv/lib/python3.11/site-packages/datasets/features/features.py", line 634, in <module>
    class _ArrayXDExtensionType(pa.PyExtensionType):
                                ^^^^^^^^^^^^^^^^^^
AttributeError: module 'pyarrow' has no attribute 'PyExtensionType'. Did you mean: 'ExtensionType'?

## Declared deliverables still missing

- data/processed/baseline_vectors.csv
- data/processed/filtered_pairs_for_analysis.csv
- data/processed/filtered_pairs_input_drift.csv
- data/processed/filtered_pairs_output_validity.csv
- data/processed/global_trade_off_curve.csv
- data/processed/memory_profile.json
- data/processed/pairing_config.json
- data/processed/perturbed_vectors.csv
- data/processed/sensitivity_report.json
- data/processed/statistical_results.json
- data/processed/trade_off_curve.csv
- data/processed/validity_log.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/baseline_vectors.csv` is declared but was NOT written. Scripts referencing it:
    - `code/main.py` — IS a run-book command
    - `code/analysis.py` — NOT invoked by the run-book
    - `code/config.py` — NOT invoked by the run-book
    - `code/validate_quickstart.py` — NOT invoked by the run-book
    - `code/validate_vectors.py` — NOT invoked by the run-book
    - `code/save_perturbed_vectors.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/baseline_vectors.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/filtered_pairs_for_analysis.csv` is declared but was NOT written. Scripts referencing it:
    - `code/config.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/filtered_pairs_for_analysis.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/filtered_pairs_input_drift.csv` is declared but was NOT written. Scripts referencing it:
    - `code/config.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/filtered_pairs_input_drift.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/filtered_pairs_output_validity.csv` is declared but was NOT written. Scripts referencing it:
    - `code/config.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/filtered_pairs_output_validity.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/global_trade_off_curve.csv` is declared but was NOT written. Scripts referencing it:
    - `code/config.py` — NOT invoked by the run-book
    - `code/validate_quickstart.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/global_trade_off_curve.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/memory_profile.json` is declared but was NOT written. Scripts referencing it:
    - `code/main.py` — IS a run-book command
    - `code/config.py` — NOT invoked by the run-book
    - `code/validate_quickstart.py` — NOT invoked by the run-book
    - `code/save_perturbed_vectors.py` — NOT invoked by the run-book
    - `code/memory_monitor.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/memory_profile.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/pairing_config.json` is declared but was NOT written. Scripts referencing it:
    - `code/main.py` — IS a run-book command
    - `code/config.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/pairing_config.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/perturbed_vectors.csv` is declared but was NOT written. Scripts referencing it:
    - `code/main.py` — IS a run-book command
    - `code/analysis.py` — NOT invoked by the run-book
    - `code/config.py` — NOT invoked by the run-book
    - `code/validate_quickstart.py` — NOT invoked by the run-book
    - `code/save_perturbed_vectors.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/perturbed_vectors.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/sensitivity_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/config.py` — NOT invoked by the run-book
    - `code/validate_quickstart.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/sensitivity_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/statistical_results.json` is declared but was NOT written. Scripts referencing it:
    - `code/config.py` — NOT invoked by the run-book
    - `code/validate_quickstart.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/statistical_results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/trade_off_curve.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis.py` — NOT invoked by the run-book
    - `code/config.py` — NOT invoked by the run-book
    - `code/validate_quickstart.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/trade_off_curve.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/validity_log.csv` is declared but was NOT written. Scripts referencing it:
    - `code/main.py` — IS a run-book command
    - `code/inconclusive_report.py` — NOT invoked by the run-book
    - `code/analysis.py` — NOT invoked by the run-book
    - `code/config.py` — NOT invoked by the run-book
    - `code/validate_quickstart.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/validity_log.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
